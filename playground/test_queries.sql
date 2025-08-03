-- SQLite
SELECT subscribers.id, subscribers.email FROM subscribers
LEFT JOIN notifications n ON subscribers.id = n.subscriber_id AND n.ticket_id = 2460
WHERE subscribers.day = 'day3' AND subscribers.camping = 'a' AND subscribers.active = 1 AND n.ticket_id IS NULL
GROUP BY subscribers.id, subscribers.email;

SELECT day, camping, COUNT(*) as count, MIN(price) as lowest_price, MAX(url) as url
FROM tickets
GROUP BY day, camping;


-- Lowest price per day and camping with URL
SELECT 
    day,
    camping,
    COUNT(*) as ticket_count,
    MIN(price) as lowest_price,
    (SELECT url 
     FROM tickets t2 
     WHERE t2.day = t1.day 
       AND t2.camping = t1.camping 
       AND t2.price = (SELECT MIN(price) 
                       FROM tickets t3 
                       WHERE t3.day = t1.day 
                         AND t3.camping = t1.camping)
     LIMIT 1) as lowest_price_url
FROM tickets t1
GROUP BY day, camping
ORDER BY day, camping;

--- Subscribers to notify
SELECT subscribers.id, subscribers.email FROM subscribers
LEFT JOIN notifications n ON subscribers.id = n.subscriber_id AND n.ticket_id = 
WHERE subscribers.day = ? AND subscribers.camping = ? AND subscribers.active = 1 AND n.ticket_id IS NULL
GROUP BY subscribers.id, subscribers.email