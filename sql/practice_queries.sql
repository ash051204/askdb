-- 1. Which tracks are longer than 5 minutes?
SELECT name, milliseconds
FROM track
WHERE milliseconds > 300000;

-- 2. List every album with its artist's name
SELECT album.title, artist.name
FROM album
JOIN artist ON album.artist_id = artist.artist_id;

-- 3. How many invoices came from each billing country?
SELECT billing_country, COUNT(*) AS invoice_count
FROM invoice
GROUP BY billing_country
ORDER BY invoice_count DESC;

-- 4. Which customers are in Canada?
SELECT first_name, last_name, city
FROM customer
WHERE country = 'Canada';

-- 5. What are the 10 most expensive tracks?
SELECT name, unit_price
FROM track
ORDER BY unit_price DESC
LIMIT 10;

-- 6. List every track name with its genre name
SELECT track.name AS track_name, genre.name AS genre_name
FROM track
JOIN genre ON track.genre_id = genre.genre_id;

-- 7. Which employee is the support rep for each customer?
SELECT customer.first_name, customer.last_name,
       employee.first_name AS rep_first, employee.last_name AS rep_last
FROM customer
JOIN employee ON customer.support_rep_id = employee.employee_id;

-- 8. Show every invoice with the customer's first and last name
SELECT invoice.invoice_id, invoice.invoice_date, invoice.total,
       customer.first_name, customer.last_name
FROM invoice
JOIN customer ON invoice.customer_id = customer.customer_id;

-- 9. List track name, album title, and artist name together
SELECT track.name AS track_name, album.title AS album_title, artist.name AS artist_name
FROM track
JOIN album ON track.album_id = album.album_id
JOIN artist ON album.artist_id = artist.artist_id;

-- 10. Which tracks did customer ID 1 buy?
SELECT track.name
FROM invoice
JOIN invoice_line ON invoice.invoice_id = invoice_line.invoice_id
JOIN track ON invoice_line.track_id = track.track_id
WHERE invoice.customer_id = 1;

-- 11. List each track with its album title and genre name
SELECT track.name AS track_name, album.title AS album_title, genre.name AS genre_name
FROM track
JOIN album ON track.album_id = album.album_id
JOIN genre ON track.genre_id = genre.genre_id;

-- 12. How many tracks does each genre have?
SELECT genre.name AS genre_name, COUNT(*) AS track_count
FROM track
JOIN genre ON track.genre_id = genre.genre_id
GROUP BY genre.name
ORDER BY track_count DESC;

-- 13. Which 5 artists have the most albums?
SELECT artist.name AS artist_name, COUNT(*) AS album_count
FROM album
JOIN artist ON album.artist_id = artist.artist_id
GROUP BY artist.name
ORDER BY album_count DESC
LIMIT 5;

-- 14. What was the total revenue in 2021?
SELECT SUM(total) AS revenue
FROM invoice
WHERE invoice_date >= '2021-01-01'
  AND invoice_date <  '2022-01-01';

-- 15. Which tracks cost more than the average track price?
SELECT name, unit_price
FROM track
WHERE unit_price > (SELECT AVG(unit_price) FROM track);