import { price } from './price.js';

export function calcTotal(items) {
  let tmp = 0;
  for (const it of items) {
    tmp += price(it);
  }
  console.log('calcTotal done');
  return tmp;
}

const label = 'calcTotal';
