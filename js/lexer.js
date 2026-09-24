// 词法分析：把 SQL 字符串切成 token 序列。
// 每个 token 都带 pos（在源串中的下标，从 0 开始），报错时能定位到具体字符。

export class SqlError extends Error {
  constructor(message, pos = null) {
    super(message);
    this.name = 'SqlError';
    this.pos = pos; // 在源串中的字符下标；运行时错误（如列不存在）可能没有位置
  }
}

const KEYWORDS = new Set([
  'SELECT', 'FROM', 'WHERE', 'GROUP', 'BY', 'HAVING', 'ORDER',
  'LIMIT', 'OFFSET', 'AS', 'AND', 'OR', 'NOT', 'IN', 'LIKE',
  'IS', 'NULL', 'ASC', 'DESC', 'TRUE', 'FALSE',
]);

const PUNCT = new Set(['(', ')', ',', '*', ';']);

function isDigit(ch) {
  return ch >= '0' && ch <= '9';
}

function isIdentStart(ch) {
  return (ch >= 'a' && ch <= 'z') || (ch >= 'A' && ch <= 'Z') || ch === '_';
}

function isIdentPart(ch) {
  return isIdentStart(ch) || isDigit(ch);
}

// 返回 token 数组：{ type, value, pos }
// type: 'keyword' | 'ident' | 'number' | 'string' | 'op' | 'punct' | 'eof'
export function tokenize(src) {
  const tokens = [];
  let i = 0;
  const n = src.length;

  while (i < n) {
    const ch = src[i];

    // 空白
    if (ch === ' ' || ch === '\t' || ch === '\r' || ch === '\n') {
      i++;
      continue;
    }

    // 行注释 -- ...
    if (ch === '-' && src[i + 1] === '-') {
      while (i < n && src[i] !== '\n') i++;
      continue;
    }

    // 数字：123 或 12.5
    if (isDigit(ch) || (ch === '.' && isDigit(src[i + 1]))) {
      const start = i;
      let seenDot = false;
      while (i < n && (isDigit(src[i]) || (src[i] === '.' && !seenDot && isDigit(src[i + 1])))) {
        if (src[i] === '.') seenDot = true;
        i++;
      }
      tokens.push({ type: 'number', value: src.slice(start, i), pos: start });
      continue;
    }

    // 字符串：'...'，两个连续单引号表示转义
    if (ch === "'") {
      const start = i;
      i++;
      let value = '';
      let closed = false;
      while (i < n) {
        if (src[i] === "'") {
          if (src[i + 1] === "'") {
            value += "'";
            i += 2;
          } else {
            i++;
            closed = true;
            break;
          }
        } else {
          value += src[i];
          i++;
        }
      }
      if (!closed) {
        throw new SqlError(`字符串没有结束：从第 ${start + 1} 个字符开始的 ' 缺少配对的结束引号`, start);
      }
      tokens.push({ type: 'string', value, pos: start });
      continue;
    }

    // 双引号标识符："col name"
    if (ch === '"') {
      const start = i;
      i++;
      let value = '';
      let closed = false;
      while (i < n) {
        if (src[i] === '"') {
          if (src[i + 1] === '"') {
            value += '"';
            i += 2;
          } else {
            i++;
            closed = true;
            break;
          }
        } else {
          value += src[i];
          i++;
        }
      }
      if (!closed) {
        throw new SqlError(`标识符没有结束：从第 ${start + 1} 个字符开始的 " 缺少配对的结束引号`, start);
      }
      tokens.push({ type: 'ident', value, pos: start });
      continue;
    }

    // 比较运算符（先长后短）
    const two = src.slice(i, i + 2);
    if (two === '<>' || two === '!=' || two === '<=' || two === '>=') {
      tokens.push({ type: 'op', value: two === '!=' ? '<>' : two, pos: i });
      i += 2;
      continue;
    }
    if (ch === '=' || ch === '<' || ch === '>') {
      tokens.push({ type: 'op', value: ch, pos: i });
      i++;
      continue;
    }

    // 标点
    if (PUNCT.has(ch)) {
      tokens.push({ type: 'punct', value: ch, pos: i });
      i++;
      continue;
    }

    // 标识符 / 关键字
    if (isIdentStart(ch)) {
      const start = i;
      while (i < n && isIdentPart(src[i])) i++;
      const word = src.slice(start, i);
      const upper = word.toUpperCase();
      if (KEYWORDS.has(upper)) {
        tokens.push({ type: 'keyword', value: upper, pos: start });
      } else {
        tokens.push({ type: 'ident', value: word, pos: start });
      }
      continue;
    }

    throw new SqlError(`第 ${i + 1} 个字符 '${ch}' 无法识别`, i);
  }

  tokens.push({ type: 'eof', value: '', pos: n });
  return tokens;
}
