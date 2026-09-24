// 一个用来试编辑器的样例文件
const cache = new Map();

function fib(n) {
  if (n < 2) return n;
  if (cache.has(n)) return cache.get(n);
  const value = fib(n - 1) + fib(n - 2);
  cache.set(n, value);
  return value;
}

/* 一段块注释
   跨了好几行 */
export function run(list) {
  let total = 0;
  for (let i = 0; i < list.length; i += 1) {
    total += fib(list[i]);
  }
  return total;
}
