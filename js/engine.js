// 执行引擎：在内存中的行数组上执行 AST。
// 类型规则：
//   - 数字和数字按数值比，字符串和字符串按字典序比，布尔和布尔比。
//   - 不做隐式转换："9" 和 100 不会按字符串比，跨类型比较按固定的类型顺序
//     （null < 数字 < 字符串 < 布尔），保证结果确定。
//   - null 和任何值比较（包括 null = null）结果都是 null（未知），
//     WHERE / HAVING 只保留结果为 true 的行，所以含 null 的条件会过滤掉该行。
//   - null 不会当成 0 或空串：SUM/AVG/MIN/MAX 都跳过 null；COUNT(列) 只数非 null。

import { SqlError } from './lexer.js';

const TYPE_RANK = new Map([
  ['null', 0],
  ['number', 1],
  ['string', 2],
  ['boolean', 3],
]);

function typeOf(v) {
  if (v === null || v === undefined) return 'null';
  return typeof v; // 'number' | 'string' | 'boolean'
}

// 三值比较：返回 -1 / 0 / 1；任一边是 null 返回 null。
export function compare(a, b) {
  const ta = typeOf(a);
  const tb = typeOf(b);
  if (ta === 'null' || tb === 'null') return null;
  if (ta !== tb) return TYPE_RANK.get(ta) - TYPE_RANK.get(tb);
  if (a < b) return -1;
  if (a > b) return 1;
  return 0;
}

// LIKE 模式 → RegExp。% 匹配任意串，_ 匹配单个字符，其余字符原样。
function likeToRegExp(pattern) {
  let out = '^';
  for (const ch of pattern) {
    if (ch === '%') out += '[\\s\\S]*';
    else if (ch === '_') out += '[\\s\\S]';
    else out += ch.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }
  out += '$';
  return new RegExp(out);
}

function truthy(v) {
  return v === true;
}

function logicNot(v) {
  if (v === null) return null;
  return !v;
}

function logicAnd(a, b) {
  if (a === false || b === false) return false;
  if (a === null || b === null) return null;
  return true;
}

function logicOr(a, b) {
  if (a === true || b === true) return true;
  if (a === null || b === null) return null;
  return false;
}

function evalBool(node, resolve) {
  switch (node.kind) {
    case 'logic': {
      const l = evalBool(node.left, resolve);
      const r = evalBool(node.right, resolve);
      return node.op === 'AND' ? logicAnd(l, r) : logicOr(l, r);
    }
    case 'not':
      return logicNot(evalBool(node.operand, resolve));
    case 'cmp': {
      const c = compare(resolve(node.left), resolve(node.right));
      if (c === null) return null;
      switch (node.op) {
        case '=': return c === 0;
        case '<>': return c !== 0;
        case '<': return c < 0;
        case '<=': return c <= 0;
        case '>': return c > 0;
        case '>=': return c >= 0;
        default: throw new SqlError(`不支持的运算符 ${node.op}`);
      }
    }
    case 'isnull': {
      const v = resolve(node.expr);
      const isNull = v === null || v === undefined;
      return node.negated ? !isNull : isNull;
    }
    case 'in': {
      const v = resolve(node.expr);
      let sawNull = false;
      let hit = false;
      for (const item of node.values) {
        const c = compare(v, item.value);
        if (c === null) sawNull = true;
        else if (c === 0) hit = true;
      }
      const result = hit ? true : (sawNull ? null : false);
      return node.negated ? logicNot(result) : result;
    }
    case 'like': {
      const v = resolve(node.expr);
      let result;
      if (v === null || v === undefined) {
        result = null;
      } else if (typeof v !== 'string') {
        throw new SqlError(`LIKE 只能用在字符串列上，这里拿到的是 ${typeOf(v) === 'number' ? '数字' : '布尔'} 值`, node.pos);
      } else {
        result = likeToRegExp(node.pattern).test(v);
      }
      return node.negated ? logicNot(result) : result;
    }
    default:
      throw new SqlError(`这里不能写这种表达式`, node.pos);
  }
}

function collectColumns(node, out = []) {
  if (!node) return out;
  switch (node.kind) {
    case 'column':
      out.push(node);
      return out;
    case 'func':
      if (node.arg) collectColumns(node.arg, out);
      return out;
    case 'logic':
      collectColumns(node.left, out);
      collectColumns(node.right, out);
      return out;
    case 'not':
      return collectColumns(node.operand, out);
    case 'cmp':
      collectColumns(node.left, out);
      collectColumns(node.right, out);
      return out;
    case 'isnull':
    case 'like':
      return collectColumns(node.expr, out);
    case 'in':
      return collectColumns(node.expr, out);
    default:
      return out;
  }
}

function hasAggregate(columns) {
  return columns.some(c => c.expr.kind === 'func');
}

function funcLabel(fn) {
  return `${fn.name}(${fn.star ? '*' : fn.arg.name})`;
}

// 输出列名：别名 > 列名 > 函数文本
function columnLabel(col) {
  if (col.alias) return col.alias;
  if (col.expr.kind === 'column') return col.expr.name;
  if (col.expr.kind === 'func') return funcLabel(col.expr);
  if (col.expr.kind === 'star') return '*';
  return '?column?';
}

function evalValueExpr(expr, row, ctx) {
  if (expr.kind === 'literal') return expr.value;
  if (expr.kind === 'column') return ctx.resolveColumn(expr.name, expr.pos, row);
  throw new SqlError(`这里不能写函数调用`, expr.pos);
}

function makeRowResolver(schema, tableName) {
  return (name, pos, row) => {
    if (!schema.has(name)) {
      throw new SqlError(
        `列 '${name}' 在表 ${tableName} 里不存在。可用的列：${[...schema].join(', ')}`,
        pos
      );
    }
    const v = row[name];
    return v === undefined ? null : v;
  };
}

function aggregate(fn, rows, resolveCol) {
  if (fn.star) return rows.length; // COUNT(*)
  const name = fn.arg.name;
  const values = [];
  for (const row of rows) {
    const v = resolveCol(name, fn.arg.pos, row);
    if (v !== null && v !== undefined) values.push(v);
  }
  switch (fn.name) {
    case 'COUNT':
      return values.length;
    case 'SUM': {
      if (values.length === 0) return null;
      let s = 0;
      for (const v of values) {
        if (typeof v !== 'number') throw new SqlError(`SUM 只能对数字列求和，列 '${name}' 里有非数字值`, fn.pos);
        s += v;
      }
      return s;
    }
    case 'AVG': {
      if (values.length === 0) return null;
      let s = 0;
      for (const v of values) {
        if (typeof v !== 'number') throw new SqlError(`AVG 只能对数字列求平均，列 '${name}' 里有非数字值`, fn.pos);
        s += v;
      }
      return s / values.length;
    }
    case 'MIN':
    case 'MAX': {
      if (values.length === 0) return null;
      let best = values[0];
      for (let i = 1; i < values.length; i++) {
        const c = compare(values[i], best);
        if (c !== null && (fn.name === 'MIN' ? c < 0 : c > 0)) best = values[i];
      }
      return best;
    }
    default:
      throw new SqlError(`不支持的函数 ${fn.name}`, fn.pos);
  }
}

// 执行查询。tables: { 表名: 行数组 }。
// 返回 { columns, rows, matched }：matched 是 LIMIT/OFFSET 之前命中的行数。
export function execute(ast, tables) {
  const table = tables[ast.from.name];
  if (!table) {
    throw new SqlError(
      `表 '${ast.from.name}' 不存在。当前加载的表：${Object.keys(tables).join(', ')}`,
      ast.from.pos
    );
  }

  const schema = new Set();
  for (const row of table) {
    for (const k of Object.keys(row)) schema.add(k);
  }
  const resolveCol = makeRowResolver(schema, ast.from.name);

  // WHERE
  let rows = table;
  if (ast.where) {
    const resolve = (expr) => evalValueExpr(expr, null, { resolveColumn: (n, p) => resolveCol(n, p, currentRow) });
    let currentRow = null;
    rows = table.filter(row => {
      currentRow = row;
      return truthy(evalBool(ast.where, resolve));
    });
  }

  const grouped = ast.groupBy || hasAggregate(ast.columns);

  let outRows;
  if (grouped) {
    outRows = runGrouped(ast, rows, resolveCol);
  } else {
    outRows = runPlain(ast, rows, resolveCol, schema);
  }

  const matched = outRows.length;

  // ORDER BY：先按输出列名（别名）找，找不到再按源列名找
  if (ast.orderBy) {
    const keys = ast.orderBy.map(item => {
      if (!outRows.length) return item;
      const sample = outRows[0];
      if (Object.prototype.hasOwnProperty.call(sample.values, item.name)) {
        return { ...item, get: r => r.values[item.name] };
      }
      if (Object.prototype.hasOwnProperty.call(sample.extra, item.name)) {
        return { ...item, get: r => r.extra[item.name] };
      }
      throw new SqlError(
        `ORDER BY 的 '${item.name}' 既不是查询结果里的列，也不是分组列。` +
        `结果列有：${Object.keys(sample.values).join(', ')}`,
        item.pos
      );
    });
    if (outRows.length) {
      outRows.sort((ra, rb) => {
        for (const k of keys) {
          const va = k.get(ra);
          const vb = k.get(rb);
          const aNull = va === null || va === undefined;
          const bNull = vb === null || vb === undefined;
          if (aNull && bNull) continue;
          if (aNull) return 1;  // null 一律排最后
          if (bNull) return -1;
          const c = compare(va, vb);
          if (c !== 0) return k.dir === 'DESC' ? -c : c;
        }
        return 0;
      });
    }
  }

  // LIMIT / OFFSET
  const offset = ast.offset || 0;
  let sliced = outRows.slice(offset);
  if (ast.limit !== null) sliced = sliced.slice(0, ast.limit);

  const columns = sliced.length
    ? Object.keys(sliced[0].values)
    : ast.columns[0].expr.kind === 'star'
      ? [...schema]
      : ast.columns.map(columnLabel);

  return { columns, rows: sliced.map(r => r.values), matched };
}

function projectStar(schema, row) {
  const out = {};
  for (const k of schema) out[k] = row[k] === undefined ? null : row[k];
  return out;
}

function runPlain(ast, rows, resolveCol, schema) {
  const star = ast.columns.length === 1 && ast.columns[0].expr.kind === 'star';
  return rows.map(row => {
    if (star) return { values: projectStar(schema, row), extra: {} };
    const values = {};
    for (const col of ast.columns) {
      const label = columnLabel(col);
      if (col.expr.kind === 'star') {
        throw new SqlError(`* 不能和其他列混着写，要么 SELECT *，要么写具体列名`, col.pos);
      }
      if (col.expr.kind === 'func') {
        throw new SqlError(`函数 ${col.expr.name} 是聚合函数，要配合 GROUP BY 用，或者整条 SELECT 都是聚合`, col.pos);
      }
      values[label] = evalValueExpr(col.expr, row, { resolveColumn: (n, p) => resolveCol(n, p, row) });
    }
    return { values, extra: {} };
  });
}

function runGrouped(ast, rows, resolveCol) {
  const groupCols = (ast.groupBy || []).map(g => g.name);
  for (const g of ast.groupBy || []) {
    resolveCol(g.name, g.pos, rows[0] || {}); // 提前校验列存在
  }

  // 分组查询里，SELECT 的普通列必须出现在 GROUP BY 里
  for (const col of ast.columns) {
    if (col.expr.kind === 'column' && !groupCols.includes(col.expr.name)) {
      throw new SqlError(
        `列 '${col.expr.name}' 不在 GROUP BY 里。分组查询的 SELECT 只能写分组列和聚合函数`,
        col.pos
      );
    }
  }

  // 分组
  const groups = new Map(); // key -> { keyValues, rows }
  for (const row of rows) {
    const keyValues = groupCols.map(name => {
      const v = row[name];
      return v === undefined ? null : v;
    });
    const key = JSON.stringify(keyValues);
    let g = groups.get(key);
    if (!g) {
      g = { keyValues, rows: [] };
      groups.set(key, g);
    }
    g.rows.push(row);
  }
  // 没有 GROUP BY 但整条是聚合：所有行算一组（空表也产出一行）
  if (!ast.groupBy && groups.size === 0) {
    groups.set('[]', { keyValues: [], rows: [] });
  }

  let result = [...groups.values()].map(g => {
    const groupRow = {};
    groupCols.forEach((name, i) => { groupRow[name] = g.keyValues[i]; });

    const values = {};
    for (const col of ast.columns) {
      const label = columnLabel(col);
      if (col.expr.kind === 'star') {
        throw new SqlError(`分组查询不能用 SELECT *，请写具体的分组列和聚合函数`, col.pos);
      }
      if (col.expr.kind === 'column') {
        values[label] = groupRow[col.expr.name];
      } else if (col.expr.kind === 'func') {
        values[label] = aggregate(col.expr, g.rows, (n, p, row) => resolveCol(n, p, row));
      } else {
        values[label] = col.expr.value;
      }
    }
    return { values, extra: groupRow, groupRows: g.rows };
  });

  // HAVING：别名先查输出列，其次分组列；聚合函数现场算
  if (ast.having) {
    const resolve = expr => {
      if (expr.kind === 'literal') return expr.value;
      if (expr.kind === 'column') {
        const r = currentResult;
        if (Object.prototype.hasOwnProperty.call(r.values, expr.name)) return r.values[expr.name];
        if (Object.prototype.hasOwnProperty.call(r.extra, expr.name)) return r.extra[expr.name];
        throw new SqlError(
          `HAVING 里的 '${expr.name}' 不存在。HAVING 可以用 SELECT 的别名、分组列或聚合函数`,
          expr.pos
        );
      }
      if (expr.kind === 'func') {
        return aggregate(expr, currentResult.groupRows, (n, p, row) => resolveCol(n, p, row));
      }
      throw new SqlError(`HAVING 里不支持的表达式`, expr.pos);
    };
    let currentResult = null;
    result = result.filter(r => {
      currentResult = r;
      return truthy(evalBool(ast.having, resolve));
    });
  }

  return result;
}
