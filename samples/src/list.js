export function render(list) {
  if (!list.length) return t('order.list.empty');
  return list.map((it) => `<li>${t('order.detail.pay')}</li>`).join('');
}

const title = '订单列表';
