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
    users = """CREATE TABLE IF NOT EXISTS users (
        user_id INT AUTO_INCREMENT PRIMARY KEY,
        email VARCHAR(255) NOT NULL UNIQUE,
        phone_number VARCHAR(15),
        user_name VARCHAR(50) NOT NULL UNIQUE,
        password VARCHAR(255) NOT NULL,
        full_name VARCHAR(255) NOT NULL,
        face_id BLOB NOT NULL  -- Store image as BLOB
    );"""

    cursor.execute(users)
    print("Table 'users' created successfully.")


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

    cart ="""CREATE TABLE IF NOT EXISTS Cart (
    cart_id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    user_id INT NOT NULL,
    date_created DATETIME DEFAULT CURRENT_TIMESTAMP,
    number_of_items INT NOT NULL,
    FOREIGN KEY (product_id) REFERENCES Products(product_id),
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
    );
    """
    cursor.execute(cart)
    print("Table cart created successfully.")

    transact= '''CREATE TABLE IF NOT EXISTS tinitiation (
    user_id INT NOT NULL,
    status VARCHAR(255) NOT NULL,
    PRIMARY KEY (user_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
    );'''
    cursor.execute(transact)
    print("Table transact created successfully.")


    contact = '''CREATE TABLE IF NOT EXISTS contact_form (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    subject VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );'''
    cursor.execute(contact)
    print("Table contact created successfully.")
    
except mysql.connector.Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        print("Something is wrong with your user name or password")
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
        print("Database does not exist")
    else:
        print(err)
