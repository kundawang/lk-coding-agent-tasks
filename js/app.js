// 页面逻辑：加载 JSONL、跑查询、渲染解释面板和结果表格。

import { tokenize, SqlError } from './lexer.js';
import { parse } from './parser.js';
import { execute, compare } from './engine.js';

const sqlInput = document.getElementById('sql-input');
const runBtn = document.getElementById('run-btn');
const errorBox = document.getElementById('error-box');
const errorMsg = document.getElementById('error-msg');
const errorLoc = document.getElementById('error-loc');
const explainBox = document.getElementById('explain-box');
const resultBox = document.getElementById('result-box');
const resultMeta = document.getElementById('result-meta');
const dataStatus = document.getElementById('data-status');
const fileInput = document.getElementById('file-input');
const exampleSelect = document.getElementById('example-select');

const MAX_RENDER_ROWS = 500; // 一次最多渲染的行数，数据量大时保护页面

let tables = {};        // { 表名: 行数组 }
let tableName = 'orders';
let lastResult = null;  // 最近一次查询结果，排序用
let sortState = null;   // { col, dir }

// ---------- 数据加载 ----------

function parseJsonl(text) {
  const rows = [];
  const lines = text.split('\n');
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) continue;
    try {
      rows.push(JSON.parse(line));
    } catch (e) {
      throw new Error(`JSONL 第 ${i + 1} 行不是合法的 JSON：${e.message}`);
    }
  }
  return rows;
}

function setData(name, rows) {
  tableName = name;
  tables = { [name]: rows };
  dataStatus.textContent = `表 ${name} · ${rows.length} 行`;
  dataStatus.className = 'ok';
}

async function loadDefault() {
  try {
    const resp = await fetch('samples/orders.jsonl');
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    setData('orders', parseJsonl(await resp.text()));
  } catch (e) {
    dataStatus.textContent = `samples/orders.jsonl 加载失败：${e.message}（请用本地服务器打开，见 README）`;
    dataStatus.className = 'err';
  }
}

fileInput.addEventListener('change', () => {
  const file = fileInput.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = () => {
    try {
      const name = file.name.replace(/\.(jsonl|json|txt)$/i, '') || 'data';
      setData(name, parseJsonl(reader.result));
      sqlInput.value = sqlInput.value.replace(/\bFROM\s+\w+/i, `FROM ${name}`);
    } catch (e) {
      dataStatus.textContent = e.message;
      dataStatus.className = 'err';
    }
  };
  reader.readAsText(file);
});

// ---------- 示例查询 ----------

async function loadExamples() {
  try {
    const resp = await fetch('samples/queries.sql');
    if (!resp.ok) return;
    const text = await resp.text();
    const queries = text.split(/\n\s*\n/).map(s => s.trim()).filter(Boolean);
    queries.forEach((q, i) => {
      const opt = document.createElement('option');
      opt.value = String(i);
      opt.textContent = q.split('\n')[0].slice(0, 60);
      exampleSelect.appendChild(opt);
    });
    exampleSelect._queries = queries;
    if (queries.length) sqlInput.value = queries[0];
  } catch (e) { /* 示例加载失败就算了 */ }
}

exampleSelect.addEventListener('change', () => {
  const q = exampleSelect._queries && exampleSelect._queries[Number(exampleSelect.value)];
  if (q) sqlInput.value = q;
});

// ---------- 解释面板 ----------

function esc(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function literalText(v) {
  if (v === null) return 'NULL';
  if (typeof v === 'string') return `'${v}'`;
  return String(v);
}

function valueExprText(expr) {
  switch (expr.kind) {
    case 'column': return expr.name;
    case 'literal': return literalText(expr.value);
    case 'func': return `${expr.name}(${expr.star ? '*' : expr.arg.name})`;
    case 'star': return '*';
    default: return '?';
  }
}

function condText(node) {
  switch (node.kind) {
    case 'logic': return `${condText(node.left)} ${node.op} ${condText(node.right)}`;
    case 'not': return `NOT ${condText(node.operand)}`;
    case 'cmp': return `${valueExprText(node.left)} ${node.op} ${valueExprText(node.right)}`;
    case 'isnull': return `${valueExprText(node.expr)} IS ${node.negated ? 'NOT ' : ''}NULL`;
    case 'in': return `${valueExprText(node.expr)} ${node.negated ? 'NOT ' : ''}IN (${node.values.map(v => literalText(v.value)).join(', ')})`;
    case 'like': return `${valueExprText(node.expr)} ${node.negated ? 'NOT ' : ''}LIKE '${node.pattern}'`;
    default: return '?';
  }
}

function renderExplain(ast) {
  const parts = [];

  const cols = ast.columns.map(c => {
    const label = valueExprText(c.expr);
    return c.alias
      ? `<li><code>${esc(label)}</code> <span class="alias">AS ${esc(c.alias)}</span></li>`
      : `<li><code>${esc(label)}</code></li>`;
  }).join('');
  parts.push(`<div><span class="k">查询列</span><ul>${cols}</ul></div>`);

  parts.push(`<div><span class="k">FROM</span> <code>${esc(ast.from.name)}</code></div>`);

  if (ast.where) {
    parts.push(`<div><span class="k">WHERE</span><ul><li><code>${esc(condText(ast.where))}</code></li></ul></div>`);
  }
  if (ast.groupBy) {
    const g = ast.groupBy.map(x => `<li><code>${esc(x.name)}</code></li>`).join('');
    parts.push(`<div><span class="k">GROUP BY</span><ul>${g}</ul></div>`);
  }
  if (ast.having) {
    parts.push(`<div><span class="k">HAVING</span><ul><li><code>${esc(condText(ast.having))}</code></li></ul></div>`);
  }
  if (ast.orderBy) {
    const o = ast.orderBy.map(x => `<li><code>${esc(x.name)}</code> ${x.dir}</li>`).join('');
    parts.push(`<div><span class="k">ORDER BY</span><ul>${o}</ul></div>`);
  }
  if (ast.limit !== null) parts.push(`<div><span class="k">LIMIT</span> <code>${ast.limit}</code></div>`);
  if (ast.offset) parts.push(`<div><span class="k">OFFSET</span> <code>${ast.offset}</code></div>`);

  explainBox.innerHTML = parts.join('');
}

// ---------- 结果表格 ----------

function formatCell(v) {
  if (v === null || v === undefined) return { text: 'NULL', cls: 'null' };
  if (typeof v === 'number') return { text: String(Math.round(v * 1e6) / 1e6), cls: 'num' };
  if (typeof v === 'boolean') return { text: String(v), cls: 'bool' };
  return { text: v, cls: '' };
}

function renderTable(result) {
  const { columns, rows } = result;
  if (!rows.length) {
    resultBox.innerHTML = '<div class="empty-tip">没有命中任何行。</div>';
    return;
  }
  const shown = rows.slice(0, MAX_RENDER_ROWS);
  const thead = '<tr>' + columns.map(c => {
    let arrow = '';
    if (sortState && sortState.col === c) arrow = `<span class="arrow">${sortState.dir === 'ASC' ? '▲' : '▼'}</span>`;
    return `<th data-col="${esc(c)}">${esc(c)}${arrow}</th>`;
  }).join('') + '</tr>';
  const tbody = shown.map(row =>
    '<tr>' + columns.map(c => {
      const cell = formatCell(row[c]);
      return `<td class="${cell.cls}">${esc(cell.text)}</td>`;
    }).join('') + '</tr>'
  ).join('');
  resultBox.innerHTML = `<table><thead>${thead}</thead><tbody>${tbody}</tbody></table>`;

  resultBox.querySelectorAll('th').forEach(th => {
    th.addEventListener('click', () => sortBy(th.dataset.col));
  });
}

function sortBy(col) {
  if (!lastResult) return;
  const dir = sortState && sortState.col === col && sortState.dir === 'ASC' ? 'DESC' : 'ASC';
  sortState = { col, dir };
  lastResult.rows.sort((a, b) => {
    const va = a[col];
    const vb = b[col];
    const aNull = va === null || va === undefined;
    const bNull = vb === null || vb === undefined;
    if (aNull && bNull) return 0;
    if (aNull) return 1; // null 一律排最后
    if (bNull) return -1;
    const c = compare(va, vb);
    return dir === 'ASC' ? c : -c;
  });
  renderTable(lastResult);
}

// ---------- 错误展示 ----------

function showError(err, sql) {
  errorBox.classList.remove('hidden');
  errorMsg.textContent = err.message;
  if (err instanceof SqlError && err.pos !== null && err.pos !== undefined) {
    const before = sql.slice(0, err.pos);
    const lineNo = before.split('\n').length;
    const lineStart = before.lastIndexOf('\n') + 1;
    let lineEnd = sql.indexOf('\n', err.pos);
    if (lineEnd === -1) lineEnd = sql.length;
    const line = sql.slice(lineStart, lineEnd);
    const col = err.pos - lineStart;
    errorLoc.textContent = `第 ${lineNo} 行：\n${line}\n${' '.repeat(col)}^`;
  } else {
    errorLoc.textContent = '';
  }
}

function clearError() {
  errorBox.classList.add('hidden');
}

// ---------- 运行 ----------

function run() {
  const sql = sqlInput.value;
  clearError();
  if (!sql.trim()) return;
  try {
    const tokens = tokenize(sql);
    const ast = parse(tokens);
    renderExplain(ast);
    const result = execute(ast, tables);
    lastResult = result;
    sortState = null;
    const shown = Math.min(result.rows.length, MAX_RENDER_ROWS);
    let meta = `命中 ${result.matched} 行`;
    if (result.matched !== result.rows.length) meta += `，LIMIT/OFFSET 后 ${result.rows.length} 行`;
    if (result.rows.length > shown) meta += `，页面只渲染前 ${shown} 行`;
    meta += '（点表头可排序）';
    resultMeta.textContent = meta;
    renderTable(result);
  } catch (err) {
    lastResult = null;
    resultMeta.textContent = '';
    if (err instanceof SqlError) {
      showError(err, sql);
    } else {
      errorBox.classList.remove('hidden');
      errorMsg.textContent = `内部错误：${err.message}`;
      errorLoc.textContent = '';
      throw err;
    }
  }
}

runBtn.addEventListener('click', run);
sqlInput.addEventListener('keydown', e => {
  if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') run();
});

loadDefault();
loadExamples();
