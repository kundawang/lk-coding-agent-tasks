SELECT COUNT(*) AS total FROM orders;

SELECT channel, COUNT(*) AS n, SUM(amount) AS total
FROM orders
WHERE status <> 'cancelled'
GROUP BY channel
ORDER BY total DESC;

SELECT id, channel, amount
FROM orders
WHERE amount > 500 AND channel IN ('h5', 'miniapp')
ORDER BY amount DESC
LIMIT 10;

SELECT status, AVG(amount) AS avg_amount
FROM orders
GROUP BY status
HAVING avg_amount > 300
ORDER BY avg_amount DESC;

SELECT id FROM orders WHERE note IS NULL OR note LIKE '%重试%';
