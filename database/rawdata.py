import mysql.connector

# Establish connection to MySQL
conn = mysql.connector.connect(
    host="127.0.0.1",         # e.g., 'localhost' or '127.0.0.1'
    user="root",              # your MySQL username
    password="",              # your MySQL password
    database="supermarket"    # your database name
)

cursor = conn.cursor()

# List of product-category associations
product_category_data = [
   (1, 1),  (2, 1),  (3, 2),  (4, 3),
(5, 4),  (6, 5),  (7, 2),  (8, 1),
(9, 3),  (10, 4), (11, 5), (12, 2),
(13, 1), (14, 3), (15, 4), (16, 1),
(17, 2), (18, 5), (19, 3), (20, 4),
(21, 1), (22, 3), (23, 2), (24, 4),
(25, 5), (26, 1), (27, 3), (28, 4),
(29, 2), (30, 5), (31, 3), (32, 1),
(33, 2), (34, 4), (35, 5), (36, 3),
(37, 1), (38, 4), (39, 2), (40, 5),
(41, 3), (42, 1), (43, 2), (44, 4),
(45, 5), (46, 3), (47, 1), (48, 2),
(49, 3), (50, 4), (51, 5), (52, 1),
(53, 2), (54, 4), (55, 3), (56, 1),
(57, 4), (58, 5), (59, 2), (60, 3),
(61, 1), (62, 4), (63, 5), (64, 2),
(65, 3), (66, 1), (67, 4), (68, 5),
(69, 2), (70, 3), (71, 1), (72, 4),
(73, 5), (74, 2), (75, 3), (76, 1),
(77, 4), (78, 5), (79, 2), (80, 3),
(81, 1), (82, 4), (83, 5), (84, 2),
(85, 3), (86, 1), (87, 4), (88, 5),
(89, 2), (90, 3), (91, 1), (92, 4),
(93, 5), (94, 2), (95, 3), (96, 1),
(97, 4), (98, 5), (99, 2), (100, 3),
(101, 1), (102, 4), (103, 5), (104, 2),
(105, 3), (106, 1), (107, 4), (108, 5),
(109, 2), (110, 3), (111, 1), (112, 4),
(113, 5)

]

# SQL query to insert data into 'product_category' table
insert_query = "INSERT INTO categories (product_id, category_id) VALUES (%s, %s)"

# Execute the insert query for each row in the product_category_data list
cursor.executemany(insert_query, product_category_data)

# Commit the changes to the database
conn.commit()

# Output the result
print(f"{cursor.rowcount} rows inserted successfully into product_category table.")

# Close the connection
cursor.close()
conn.close()
