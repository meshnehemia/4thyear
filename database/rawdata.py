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
cursor.execute("SET @min = 1")
cursor.execute("SET @max = 113")

product_category_data = [
    (1, 199.99, 'Feature 1 Description'),
    (2, 249.99, 'Feature 2 Description'),
    (3, 189.99, 'Feature 3 Description'),
    (4, 229.99, 'Feature 4 Description'),
    (5, 299.99, 'Feature 5 Description'),
    (6, 159.99, 'Feature 6 Description'),
    (7, 299.99, 'Feature 7 Description'),
    (8, 199.99, 'Feature 8 Description'),
    (9, 229.99, 'Feature 9 Description'),
    (10, 179.99, 'Feature 10 Description'),
    (11, 269.99, 'Feature 11 Description'),
    (12, 249.99, 'Feature 12 Description'),
    (13, 199.99, 'Feature 13 Description'),
    (14, 299.99, 'Feature 14 Description'),
    (15, 249.99, 'Feature 15 Description'),
    (16, 189.99, 'Feature 16 Description'),
    (17, 179.99, 'Feature 17 Description'),
    (18, 249.99, 'Feature 18 Description'),
    (19, 269.99, 'Feature 19 Description'),
    (20, 239.99, 'Feature 20 Description'),
    (21, 219.99, 'Feature 21 Description'),
    (22, 249.99, 'Feature 22 Description'),
    (23, 199.99, 'Feature 23 Description'),
    (24, 299.99, 'Feature 24 Description'),
    (25, 229.99, 'Feature 25 Description'),
    (26, 219.99, 'Feature 26 Description'),
    (27, 279.99, 'Feature 27 Description'),
    (28, 259.99, 'Feature 28 Description'),
    (29, 299.99, 'Feature 29 Description'),
    (30, 249.99, 'Feature 30 Description'),
    (31, 219.99, 'Feature 31 Description'),
    (32, 179.99, 'Feature 32 Description'),
    (33, 269.99, 'Feature 33 Description'),
    (34, 239.99, 'Feature 34 Description'),
    (35, 219.99, 'Feature 35 Description'),
    (36, 259.99, 'Feature 36 Description'),
    (37, 199.99, 'Feature 37 Description'),
    (38, 249.99, 'Feature 38 Description'),
    (39, 279.99, 'Feature 39 Description'),
    (40, 299.99, 'Feature 40 Description'),
    (41, 269.99, 'Feature 41 Description'),
    (42, 249.99, 'Feature 42 Description'),
    (43, 229.99, 'Feature 43 Description'),
    (44, 219.99, 'Feature 44 Description'),
    (45, 239.99, 'Feature 45 Description'),
    (46, 199.99, 'Feature 46 Description'),
    (47, 249.99, 'Feature 47 Description'),
    (48, 229.99, 'Feature 48 Description'),
    (49, 249.99, 'Feature 49 Description'),
    (50, 269.99, 'Feature 50 Description')
]

# SQL query to insert data into 'product_category' table
insert_query = "INSERT INTO featured (product_id, new_price, feature_description) VALUES (%s, %s, %s)"

# Execute the insert query for each row in the product_category_data list
cursor.executemany(insert_query, product_category_data)

# Commit the changes to the database
conn.commit()

# Output the result
print(f"{cursor.rowcount} rows inserted successfully into product_category table.")

# Close the connection
cursor.close()
conn.close()
