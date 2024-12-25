import mysql.connector
from mysql.connector import errorcode
conn= ''
# Establish connection to MySQL
try:
    conn = mysql.connector.connect(
        host="127.0.0.1",         # e.g., 'localhost' or '127.0.0.1'
        user="root",     # your MySQL username
        password="", # your MySQL password
        database="supermarket"  # your database name
    )
    
    cursor = conn.cursor()

    # SQL query to create the 'products' table
    create_table_query = """
    CREATE TABLE IF NOT EXISTS products (
        product_id INT AUTO_INCREMENT PRIMARY KEY,
        product_name VARCHAR(255) NOT NULL,
        description TEXT,
        price DECIMAL(10, 2),
        cover_photo BLOB
    );
    """
    
    # Execute the query to create the table
    cursor.execute(create_table_query)
    print("Table 'products' created successfully.")


    create_table_query = '''
        CREATE TABLE IF NOT EXISTS d_categories (
            category_id INT AUTO_INCREMENT PRIMARY KEY,
            category_name VARCHAR(255) NOT NULL,
            category_cover BLOB 
        );
        '''
    cursor.execute(create_table_query)
    print("Table created successfully.")

    create_categories_table_query = """
    CREATE TABLE IF NOT EXISTS categories (
    product_id INT,
    category_id INT,
    FOREIGN KEY (product_id) REFERENCES products(product_id) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE,
    FOREIGN KEY (category_id) REFERENCES d_categories(category_id) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE  );

    """
    cursor.execute(create_categories_table_query)
    print("Tables 'products' and 'categories' created successfully.")


    create_table='''CREATE TABLE IF NOT EXISTS Discounts (
    product_id INT,                             
    new_price DECIMAL(10, 2) NOT NULL,         
    type_of_offer VARCHAR(255) NOT NULL,
    FOREIGN KEY (product_id) REFERENCES products(product_id)  ON DELETE CASCADE 
        ON UPDATE CASCADE
    );'''
    cursor.execute(create_table)
    print("Table created successfully.")


    feature = '''CREATE TABLE  IF NOT EXISTS featured(
    product_id INT,
    new_price DECIMAL(10, 2),
    feature_description VARCHAR(255),
    FOREIGN KEY (product_id)
        REFERENCES products (product_id)
        ON DELETE CASCADE
    );'''
    cursor.execute(feature)
    print("Table created successfully.")

    
    
except mysql.connector.Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        print("Something is wrong with your user name or password")
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
        print("Database does not exist")
    else:
        print(err)
