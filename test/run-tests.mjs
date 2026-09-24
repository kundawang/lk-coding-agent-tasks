// 无依赖的冒烟测试：node test/run-tests.mjs
import { readFileSync } from 'node:fs';
import { tokenize, SqlError } from '../js/lexer.js';
import { parse } from '../js/parser.js';
import { execute, compare } from '../js/engine.js';

const rows = readFileSync(new URL('../samples/orders.jsonl', import.meta.url), 'utf8')
  .split('\n').filter(Boolean).map(JSON.parse);
const tables = { orders: rows };

let passed = 0, failed = 0;
function check(name, fn) {
  try { fn(); passed++; console.log(`ok   ${name}`); }
  catch (e) { failed++; console.log(`FAIL ${name}: ${e.message}`); }
}
function eq(a, b, what = '') {
  if (JSON.stringify(a) !== JSON.stringify(b)) {
    throw new Error(`${what} 期望 ${JSON.stringify(b)}，实际 ${JSON.stringify(a)}`);
  }
}
function run(sql) {
  return execute(parse(tokenize(sql)), tables);
}
function expectError(sql, needle) {
  try { run(sql); } catch (e) {
    if (!(e instanceof SqlError)) throw new Error(`抛的不是 SqlError：${e}`);
    if (!e.message.includes(needle)) throw new Error(`报错不含「${needle}」：${e.message}`);
    if (e.pos === null) throw new Error('报错没有字符位置');
    return;
  }
  throw new Error('本该报错却没有报错');
}

// ---- samples/queries.sql 全部跑通 ----
const queries = readFileSync(new URL('../samples/queries.sql', import.meta.url), 'utf8')
  .split(/\n\s*\n/).map(s => s.trim()).filter(Boolean);
queries.forEach((q, i) => check(`样例查询 ${i + 1} 跑通`, () => { run(q); }));

// ---- 具体结果校验 ----
check('COUNT(*) 等于 160', () => {
  eq(run('SELECT COUNT(*) AS total FROM orders').rows[0].total, 160);
});
check('数字比较不是字符串比较', () => {
  // 若按字符串比，'9' > '100' 会出错；这里直接验证 9 < 100 语义
  eq(run('SELECT COUNT(*) AS n FROM orders WHERE amount > 100').rows[0].n,
     rows.filter(r => r.amount > 100).length);
  eq(run('SELECT COUNT(*) AS n FROM orders WHERE id > 9').rows[0].n,
     rows.filter(r => r.id > 9).length);
});
check('GROUP BY + SUM 对得上', () => {
  const res = run(`SELECT channel, COUNT(*) AS n, SUM(amount) AS total FROM orders
                   WHERE status <> 'cancelled' GROUP BY channel ORDER BY total DESC`);
  const expect = {};
  for (const r of rows) if (r.status !== 'cancelled') {
    expect[r.channel] = expect[r.channel] || { n: 0, total: 0 };
    expect[r.channel].n++; expect[r.channel].total += r.amount;
  }
  for (const row of res.rows) {
    eq(row.n, expect[row.channel].n, `${row.channel}.n`);
    if (Math.abs(row.total - expect[row.channel].total) > 1e-6) throw new Error(`${row.channel}.total 不符`);
  }
});
check('HAVING 用别名', () => {
  const res = run('SELECT status, AVG(amount) AS a FROM orders GROUP BY status HAVING a > 300');
  for (const r of res.rows) if (!(r.a > 300)) throw new Error('HAVING 没生效');
});
check('IS NULL / IS NOT NULL', () => {
  eq(run('SELECT COUNT(*) AS n FROM orders WHERE note IS NULL').rows[0].n,
     rows.filter(r => r.note === null).length);
  eq(run('SELECT COUNT(*) AS n FROM orders WHERE note IS NOT NULL').rows[0].n,
     rows.filter(r => r.note !== null).length);
});
check('null 不等于 null（三值逻辑）', () => {
  eq(run('SELECT COUNT(*) AS n FROM orders WHERE note = NULL').rows[0].n, 0);
  eq(run('SELECT COUNT(*) AS n FROM orders WHERE note <> NULL').rows[0].n, 0);
});
check('LIKE 的 % 和 _', () => {
  eq(run("SELECT COUNT(*) AS n FROM orders WHERE note LIKE '%重试%'").rows[0].n,
     rows.filter(r => r.note !== null && r.note.includes('重试')).length);
  eq(run("SELECT COUNT(*) AS n FROM orders WHERE channel LIKE 'h_'").rows[0].n,
     rows.filter(r => r.channel.length === 2 && r.channel[0] === 'h').length);
  eq(run("SELECT COUNT(*) AS n FROM orders WHERE note LIKE '%'").rows[0].n,
     rows.filter(r => r.note !== null).length); // null 不匹配 LIKE '%'
});
check('IN / NOT IN，null 不进 IN', () => {
  eq(run("SELECT COUNT(*) AS n FROM orders WHERE channel IN ('h5', 'miniapp')").rows[0].n,
     rows.filter(r => r.channel === 'h5' || r.channel === 'miniapp').length);
  eq(run("SELECT COUNT(*) AS n FROM orders WHERE channel NOT IN ('h5')").rows[0].n,
     rows.filter(r => r.channel !== 'h5').length);
});
check('LIMIT / OFFSET', () => {
  const all = run('SELECT id FROM orders ORDER BY id');
  const page = run('SELECT id FROM orders ORDER BY id LIMIT 10 OFFSET 5');
  eq(page.rows.length, 10);
  eq(page.rows[0].id, all.rows[5].id);
  eq(page.matched, 160);
});
check('ORDER BY 多列 + DESC', () => {
  const res = run('SELECT channel, amount FROM orders ORDER BY channel ASC, amount DESC LIMIT 5');
  for (let i = 1; i < res.rows.length; i++) {
    const a = res.rows[i - 1], b = res.rows[i];
    if (a.channel > b.channel) throw new Error('channel 没按 ASC');
    if (a.channel === b.channel && a.amount < b.amount) throw new Error('amount 没按 DESC');
  }
});
check('AND / OR / NOT / 括号优先级', () => {
  eq(run("SELECT COUNT(*) AS n FROM orders WHERE vip = true AND (channel = 'app' OR channel = 'h5')").rows[0].n,
     rows.filter(r => r.vip === true && (r.channel === 'app' || r.channel === 'h5')).length);
  eq(run("SELECT COUNT(*) AS n FROM orders WHERE NOT channel = 'app'").rows[0].n,
     rows.filter(r => r.channel !== 'app').length);
});
check('MIN/MAX/AVG', () => {
  const res = run('SELECT MIN(amount) AS lo, MAX(amount) AS hi, AVG(amount) AS avg FROM orders');
  eq(res.rows[0].lo, Math.min(...rows.map(r => r.amount)));
  eq(res.rows[0].hi, Math.max(...rows.map(r => r.amount)));
});
check('聚合跳过 null：COUNT(note) < COUNT(*)', () => {
  const res = run('SELECT COUNT(*) AS a, COUNT(note) AS b FROM orders');
  eq(res.rows[0].b, rows.filter(r => r.note !== null).length);
});
check('空表聚合仍出一行', () => {
  const res = run('SELECT COUNT(*) AS n, SUM(amount) AS s FROM orders WHERE id > 99999');
  eq(res.rows.length, 1);
  eq(res.rows[0].n, 0);
  eq(res.rows[0].s, null);
});
check('SELECT * 展开全部列', () => {
  const res = run('SELECT * FROM orders LIMIT 1');
  eq(res.columns, ['id', 'channel', 'status', 'amount', 'created_at', 'note', 'vip']);
});
check('compare 不隐式转换', () => {
  eq(compare('9', 100) === null || compare('9', 100) === undefined, false); // 跨类型有确定顺序
  if (!(compare(9, 100) < 0)) throw new Error('9 < 100 数值比较失败');
  eq(compare(null, 1), null);
  eq(compare(null, null), null);
});
check('ORDER BY 里 null 排最后', () => {
  const res = run('SELECT note FROM orders ORDER BY note LIMIT 200');
  const nullIdx = res.rows.findIndex(r => r.note === null);
  const nonNull = res.rows.filter(r => r.note !== null);
  if (nullIdx !== -1 && nullIdx < nonNull.length) throw new Error('null 没排在最后');
});

// ---- 报错说人话 ----
check('SELECT FROM orders 报缺少列', () => expectError('SELECT FROM orders', '缺少要查询的列'));
check('缺 FROM', () => expectError('SELECT id orders', 'FROM'));
check('未闭合字符串', () => expectError("SELECT id FROM orders WHERE note = 'abc", '字符串没有结束'));
check('列不存在，列出可用列', () => expectError('SELECT nope FROM orders', '可用的列'));
check('表不存在', () => expectError('SELECT id FROM nowhere', "表 'nowhere' 不存在"));
check('LIMIT 不是数字', () => expectError('SELECT id FROM orders LIMIT abc', '非负整数'));
check('多余语句', () => expectError('SELECT id FROM orders; SELECT id FROM orders', '一次只能执行一条'));
check('报错带字符位置', () => {
  try { run('SELECT id FROM orders WHERE amount >> 5'); } catch (e) {
    if (typeof e.pos !== 'number') throw new Error('没有 pos');
    return;
  }
  throw new Error('没报错');
});
check('GROUP BY 校验非分组列', () => expectError('SELECT channel, status FROM orders GROUP BY channel', '不在 GROUP BY 里'));

// ---- 大数据量性能 ----
check('5 万行不卡死', () => {
  const big = [];
  for (let i = 0; i < 50000; i++) big.push(rows[i % rows.length]);
  const t0 = Date.now();
  const res = execute(parse(tokenize(
    "SELECT channel, COUNT(*) AS n, SUM(amount) AS s FROM orders WHERE amount > 100 GROUP BY channel HAVING n > 10 ORDER BY s DESC LIMIT 5"
  )), { orders: big });
  const ms = Date.now() - t0;
  if (ms > 1000) throw new Error(`太慢：${ms}ms`);
  console.log(`     (5 万行分组聚合 ${ms}ms)`);
});

console.log(`\n${passed} 通过, ${failed} 失败`);
process.exit(failed ? 1 : 0);
