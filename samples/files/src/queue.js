// 队列实现
const items = [];

export function push(v) {
  items.push(v);
}

export function peek() {
  return items[0];
}

export function pop() {
  return items.shift();
}

export function size() {
  return items.length;
}
