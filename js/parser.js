// 语法分析：递归下降解析器，把 token 序列解析成 AST。
// 所有报错都带字符位置（pos，从 0 计）和"期待什么"的说明。

import { SqlError } from './lexer.js';

const AGG_FUNCS = new Set(['COUNT', 'SUM', 'AVG', 'MIN', 'MAX']);

function describe(tok) {
  if (tok.type === 'eof') return '语句结尾';
  if (tok.type === 'string') return `字符串 '${tok.value}'`;
  return `'${tok.value}'`;
}

class Parser {
  constructor(tokens) {
    this.tokens = tokens;
    this.i = 0;
  }

  peek(offset = 0) {
    return this.tokens[Math.min(this.i + offset, this.tokens.length - 1)];
  }

  next() {
    return this.tokens[this.i++];
  }

  atEnd() {
    return this.peek().type === 'eof';
  }

  error(message, tok = this.peek()) {
    return new SqlError(`第 ${tok.pos + 1} 个字符：${message}`, tok.pos);
  }

  expectKeyword(word, what) {
    const tok = this.peek();
    if (tok.type === 'keyword' && tok.value === word) {
      this.next();
      return tok;
    }
    throw this.error(`期待 ${what || `关键字 ${word}`}，但遇到了 ${describe(tok)}`, tok);
  }

  acceptKeyword(word) {
    const tok = this.peek();
    if (tok.type === 'keyword' && tok.value === word) {
      this.next();
      return tok;
    }
    return null;
  }

  expectPunct(ch, what) {
    const tok = this.peek();
    if (tok.type === 'punct' && tok.value === ch) {
      this.next();
      return tok;
    }
    throw this.error(`期待 ${what || `'${ch}'`}，但遇到了 ${describe(tok)}`, tok);
  }

  acceptPunct(ch) {
    const tok = this.peek();
    if (tok.type === 'punct' && tok.value === ch) {
      this.next();
      return tok;
    }
    return null;
  }

  expectIdent(what) {
    const tok = this.peek();
    if (tok.type === 'ident') {
      this.next();
      return tok;
    }
    throw this.error(`期待 ${what || '列名'}，但遇到了 ${describe(tok)}`, tok);
  }

  // SELECT 列表：列、*、聚合函数、字面量，可带 AS 别名
  parseSelectList() {
    const columns = [];
    do {
      const tok = this.peek();
      if (tok.type === 'keyword') {
        throw this.error(
          `SELECT 后面缺少要查询的列（遇到了关键字 '${tok.value}'）。` +
          `如果你想查所有列，请写 SELECT *`
        , tok);
      }
      const expr = this.parseSelectExpr();
      let alias = null;
      if (this.acceptKeyword('AS')) {
        alias = this.expectIdent('AS 后面的别名').value;
      } else if (this.peek().type === 'ident') {
        // 允许省略 AS：SELECT amount total
        alias = this.next().value;
      }
      columns.push({ expr, alias, pos: expr.pos });
    } while (this.acceptPunct(','));
    return columns;
  }

  parseSelectExpr() {
    const tok = this.peek();
    if (tok.type === 'punct' && tok.value === '*') {
      this.next();
      return { kind: 'star', pos: tok.pos };
    }
    return this.parseValueExpr('要查询的列或表达式');
  }

  // 值表达式：列名 / 字面量 / 聚合函数调用
  parseValueExpr(what = '表达式') {
    const tok = this.peek();

    if (tok.type === 'number') {
      this.next();
      return { kind: 'literal', value: Number(tok.value), pos: tok.pos };
    }
    if (tok.type === 'string') {
      this.next();
      return { kind: 'literal', value: tok.value, pos: tok.pos };
    }
    if (tok.type === 'keyword' && tok.value === 'NULL') {
      this.next();
      return { kind: 'literal', value: null, pos: tok.pos };
    }
    if (tok.type === 'keyword' && tok.value === 'TRUE') {
      this.next();
      return { kind: 'literal', value: true, pos: tok.pos };
    }
    if (tok.type === 'keyword' && tok.value === 'FALSE') {
      this.next();
      return { kind: 'literal', value: false, pos: tok.pos };
    }
    if (tok.type === 'ident') {
      const upper = tok.value.toUpperCase();
      if (AGG_FUNCS.has(upper) && this.peek(1).type === 'punct' && this.peek(1).value === '(') {
        return this.parseFuncCall();
      }
      this.next();
      return { kind: 'column', name: tok.value, pos: tok.pos };
    }
    throw this.error(`期待${what}（列名、数字、字符串或 COUNT/SUM/AVG/MIN/MAX 函数），但遇到了 ${describe(tok)}`, tok);
  }

  parseFuncCall() {
    const nameTok = this.next(); // 函数名
    const name = nameTok.value.toUpperCase();
    this.expectPunct('(', `函数 ${name} 后面的 '('`);

    let arg = null;
    let star = false;
    const tok = this.peek();
    if (tok.type === 'punct' && tok.value === '*') {
      if (name !== 'COUNT') {
        throw this.error(`${name}(*) 不支持，只有 COUNT 可以用 *。请写成 ${name}(列名)`, tok);
      }
      this.next();
      star = true;
    } else {
      arg = this.parseValueExpr(`函数 ${name} 的参数`);
      if (arg.kind !== 'column') {
        throw this.error(`函数 ${name} 的参数只能是列名，不能是字面量`, { pos: arg.pos });
      }
    }
    this.expectPunct(')', `函数 ${name} 参数后面的 ')'`);
    return { kind: 'func', name, arg, star, pos: nameTok.pos };
  }

  // 条件表达式：OR < AND < NOT < 谓词
  parseCondition() {
    return this.parseOr();
  }

  parseOr() {
    let left = this.parseAnd();
    while (this.acceptKeyword('OR')) {
      const right = this.parseAnd();
      left = { kind: 'logic', op: 'OR', left, right, pos: left.pos };
    }
    return left;
  }

  parseAnd() {
    let left = this.parseNot();
    while (this.acceptKeyword('AND')) {
      const right = this.parseNot();
      left = { kind: 'logic', op: 'AND', left, right, pos: left.pos };
    }
    return left;
  }

  parseNot() {
    const tok = this.peek();
    if (tok.type === 'keyword' && tok.value === 'NOT') {
      this.next();
      const operand = this.parseNot();
      return { kind: 'not', operand, pos: tok.pos };
    }
    return this.parsePredicate();
  }

  parsePredicate() {
    const tok = this.peek();

    // 括号
    if (tok.type === 'punct' && tok.value === '(') {
      this.next();
      const inner = this.parseCondition();
      this.expectPunct(')', "条件括号里对应的 ')'");
      return inner;
    }

    const left = this.parseValueExpr('列名或值');

    // IS [NOT] NULL
    if (this.acceptKeyword('IS')) {
      const negated = !!this.acceptKeyword('NOT');
      this.expectKeyword('NULL', "IS 后面的 NULL（这里只支持 IS NULL / IS NOT NULL）");
      return { kind: 'isnull', expr: left, negated, pos: left.pos };
    }

    // [NOT] IN / [NOT] LIKE
    let negated = false;
    const save = this.i;
    if (this.acceptKeyword('NOT')) {
      const t = this.peek();
      if (t.type === 'keyword' && (t.value === 'IN' || t.value === 'LIKE')) {
        negated = true;
      } else {
        this.i = save; // 不是 NOT IN / NOT LIKE，回退
      }
    }

    if (this.acceptKeyword('IN')) {
      this.expectPunct('(', "IN 后面的 '('");
      const values = [];
      do {
        const v = this.parseValueExpr('IN 列表里的值');
        if (v.kind !== 'literal') {
          throw this.error('IN 列表里只能写字面量（数字、字符串、NULL），不能写列名或函数', { pos: v.pos });
        }
        values.push(v);
      } while (this.acceptPunct(','));
      this.expectPunct(')', "IN 列表后面的 ')'");
      return { kind: 'in', expr: left, values, negated, pos: left.pos };
    }

    if (this.acceptKeyword('LIKE')) {
      const pat = this.parseValueExpr('LIKE 后面的模式串');
      if (pat.kind !== 'literal' || typeof pat.value !== 'string') {
        throw this.error("LIKE 后面要跟一个字符串模式，例如 LIKE '%重试%'", { pos: pat.pos });
      }
      return { kind: 'like', expr: left, pattern: pat.value, negated, pos: left.pos };
    }

    if (negated) {
      throw this.error(`NOT 后面只支持 IN 或 LIKE`, this.peek());
    }

    // 比较运算
    const opTok = this.peek();
    if (opTok.type === 'op') {
      this.next();
      const right = this.parseValueExpr('比较运算符右边的值');
      return { kind: 'cmp', op: opTok.value, left, right, pos: left.pos };
    }

    throw this.error(
      `期待比较运算符（=、<>、<、<=、>、>=）或 IS NULL / IN / LIKE，但遇到了 ${describe(opTok)}`,
      opTok
    );
  }

  // ORDER BY 后面：列名或别名，可跟 ASC / DESC
  parseOrderList() {
    const items = [];
    do {
      const tok = this.peek();
      if (tok.type !== 'ident') {
        throw this.error(`ORDER BY 后面期待列名或别名，但遇到了 ${describe(tok)}`, tok);
      }
      this.next();
      let dir = 'ASC';
      if (this.acceptKeyword('DESC')) dir = 'DESC';
      else this.acceptKeyword('ASC');
      items.push({ name: tok.value, dir, pos: tok.pos });
    } while (this.acceptPunct(','));
    return items;
  }

  parseNonNegInt(what) {
    const tok = this.peek();
    if (tok.type !== 'number' || !Number.isInteger(Number(tok.value)) || Number(tok.value) < 0) {
      throw this.error(`${what} 后面期待一个非负整数，但遇到了 ${describe(tok)}`, tok);
    }
    this.next();
    return Number(tok.value);
  }

  parseStatement() {
    this.expectKeyword('SELECT', 'SELECT（目前只支持 SELECT 查询）');
    const columns = this.parseSelectList();

    this.expectKeyword('FROM', 'FROM（SELECT 后面要指定查哪张表）');
    const fromTok = this.expectIdent('表名（比如 orders）');
    const from = { name: fromTok.value, pos: fromTok.pos };

    let where = null;
    if (this.acceptKeyword('WHERE')) {
      where = this.parseCondition();
    }

    let groupBy = null;
    if (this.acceptKeyword('GROUP')) {
      this.expectKeyword('BY', "GROUP 后面的 BY（分组写法是 GROUP BY 列名）");
      groupBy = [];
      do {
        const tok = this.expectIdent('GROUP BY 后面的列名');
        groupBy.push({ name: tok.value, pos: tok.pos });
      } while (this.acceptPunct(','));
    }

    let having = null;
    if (this.acceptKeyword('HAVING')) {
      having = this.parseCondition();
    }

    let orderBy = null;
    if (this.acceptKeyword('ORDER')) {
      this.expectKeyword('BY', "ORDER 后面的 BY（排序写法是 ORDER BY 列名）");
      orderBy = this.parseOrderList();
    }

    let limit = null;
    if (this.acceptKeyword('LIMIT')) {
      limit = this.parseNonNegInt('LIMIT');
    }

    let offset = 0;
    if (this.acceptKeyword('OFFSET')) {
      offset = this.parseNonNegInt('OFFSET');
    }

    this.acceptPunct(';');

    if (!this.atEnd()) {
      const tok = this.peek();
      throw this.error(`语句到这里应该结束了，但又遇到了 ${describe(tok)}。一次只能执行一条 SELECT`, tok);
    }

    return { type: 'select', columns, from, where, groupBy, having, orderBy, limit, offset };
  }
}

export function parse(tokens) {
  const parser = new Parser(tokens);
  return parser.parseStatement();
}
