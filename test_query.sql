-- SQLite
SELECT subscribers.id, subscribers.email FROM subscribers
LEFT JOIN notifications n ON subscribers.id = n.subscriber_id AND n.ticket_id = 2460
WHERE subscribers.day = 'day3' AND subscribers.camping = 'a' AND subscribers.active = 1 AND n.ticket_id IS NULL
GROUP BY subscribers.id, subscribers.email
