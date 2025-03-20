import mysql.connector
from mysql.connector import errorcode
conn= ''
# Establish connection to MySQL
try:
    conn = mysql.connector.connect(
        host="127.0.0.1",         # e.g., 'localhost' or '127.0.0.1'
        user="root",              # your MySQL username
        password="",              # your MySQL password
        database="supermarket"    # your database name
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
    print("Table created featured successfully.")

    cart ="""CREATE TABLE IF NOT EXISTS Cart (
    cart_id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    user_id INT NOT NULL,
    date_created DATETIME DEFAULT CURRENT_TIMESTAMP,
    number_of_items INT NOT NULL,
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
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


    product_images = '''CREATE TABLE IF NOT EXISTS ProductImages (
    image_id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT,
    image_data BLOB NOT NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
        );
    '''
    cursor.execute(product_images)
    print("Table PRODUCT IMAGES CREATED  created successfully.")

    staff = '''CREATE TABLE IF NOT EXISTS staff (
    staff_id SERIAL PRIMARY KEY,  -- Auto-incrementing primary key for each staff member
    name_of_staff VARCHAR(100) NOT NULL,  -- Name of the staff member
    phone_number VARCHAR(15) NOT NULL,    -- Phone number
    email_address VARCHAR(100) UNIQUE NOT NULL,  -- Unique email address, required
    level VARCHAR(50),                    -- Staff's level (e.g., junior, senior, manager
    date_employed DATE DEFAULT CURRENT_DATE,  -- Automatically set employment date to current date if not provided
    status VARCHAR(50) DEFAULT 'active',      -- Employment status, default is 'active'
    id_number VARCHAR(20) UNIQUE NOT NULL   -- Unique identification number for the staff member
);
'''
    cursor.execute(staff)
    print("Table staff CREATED  created successfully.")


    sales = '''CREATE TABLE IF NOT EXISTS sales (
        sale_id INT AUTO_INCREMENT PRIMARY KEY,
        product_id INT NOT NULL,
        client_id INT,
        sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        sale_type VARCHAR(50),
        amount_bought DECIMAL(10, 2),
        profit_made DECIMAL(10, 2),
        FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE,
        FOREIGN KEY (client_id) REFERENCES users(user_id) ON DELETE NO ACTION
    );
    '''
    cursor.execute(sales)
    print("Table 'sales' created successfully.")

    orders ='''CREATE TABLE IF NOT EXISTS orders (
    order_id INT AUTO_INCREMENT PRIMARY KEY,
    client_id INT NOT NULL,
    date_placed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) NOT NULL,
    assigned_worker BIGINT UNSIGNED,
    FOREIGN KEY (client_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_worker) REFERENCES staff(staff_id)
);
'''

    cursor.execute(orders)
    print("Table 'orders' created successfully.")


    tasks='''CREATE TABLE IF NOT EXISTS list_of_tasks (
    task_id INT AUTO_INCREMENT PRIMARY KEY,  -- Unique identifier for each task
    task_description TEXT NOT NULL,          -- Description of the task
    status ENUM('not assigned', 'assigned', 'completed') DEFAULT 'not assigned',  -- Task status with default value 'not assigned'
    staff_id BIGINT UNSIGNED,                            -- Foreign key referencing the staff member assigned to the task
    date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- Automatically sets the date when the task is created
    date_completed TIMESTAMP NULL,           -- Date when the task is completed, nullable
    FOREIGN KEY (staff_id) REFERENCES staff(staff_id)  -- Foreign key linking to the staff table
);
'''
    cursor.execute(tasks)
    print("Table 'tasks' created successfully.")


    payments = '''CREATE TABLE IF NOT EXISTS payment (
    payment_id INT AUTO_INCREMENT PRIMARY KEY,  -- Auto-incrementing primary key for each payment
    staff_id BIGINT UNSIGNED NOT NULL,          -- Foreign key referencing the staff member
    monthly_payment DECIMAL(10, 2) NOT NULL,    -- The payment amount for the staff member
    payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- Timestamp of when the payment is recorded
    FOREIGN KEY (staff_id) REFERENCES staff(staff_id)  -- Foreign key linking to the staff table
);


'''
    cursor.execute(payments)
    print("Table 'payments' created successfully.")


    pay ='''CREATE TABLE IF NOT EXISTS payment_amount (
    level_id INT AUTO_INCREMENT PRIMARY KEY,  -- Unique identifier for each level payment record
    level VARCHAR(50) NOT NULL,               -- Staff level (e.g., junior, senior, manager)
    payment_per_level DECIMAL(10, 2) NOT NULL  -- Payment amount associated with the level
);
'''
    cursor.execute(pay)
    print("Table 'pay' created successfully.")


    ordersales = '''CREATE TABLE IF NOT EXISTS ordersales (
    order_sales_id INT AUTO_INCREMENT PRIMARY KEY,  -- Unique ID for each record in ordersales
    order_id INT,                                   -- Foreign key referencing orders table
    product_id INT,                                 -- Foreign key referencing products table
    cost DECIMAL(10, 2),                            -- Cost of the product
    number_of_items INT,                            -- Number of items sold
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,   -- Foreign key relation with orders table
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE  -- Foreign key relation with products table
);
'''

#     changemodel = '''ALTER TABLE orders ADD COLUMN assigned_worker VARCHAR(255);
# '''
#     cursor.execute(changemodel)
#     conn.commit()
    print("Table 'orders' altered successfully.")
    cursor.execute(ordersales)
    print("Table 'ordersales' created successfully.")

    availableitems ='''CREATE TABLE IF NOT EXISTS availableItemNumber (
    product_id INT,
    number_of_items INT NOT NULL,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
);
'''

    cursor.execute(availableitems)
    print("table availabe items created sucessfully")

    orderself = '''CREATE TABLE IF NOT EXISTS selforders (
    staff_id BIGINT UNSIGNED NOT NULL,
    product_id INT NOT NULL,
    number_of_items INT NOT NULL,
    FOREIGN KEY (staff_id) REFERENCES staff(staff_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
);
'''


    derivery = '''CREATE TABLE derivery_details (
    derivery_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone_number VARCHAR(15) NOT NULL,
    station VARCHAR(100) NOT NULL,
    address VARCHAR(255) NOT NULL,
    house_details VARCHAR(255),
    delivery_type VARCHAR(100) NOT NULL,
    payment_method VARCHAR(100) NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    derivery_status VARCHAR(50) NOT NULL DEFAULT 'NOT DELIVERED', -- New column for delivery status
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);
'''
    cursor.execute(derivery)
    print("table derivery created")
    cursor.execute(orderself)
    print("table orderself successfully created")
except mysql.connector.Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        print("Something is wrong with your user name or password")
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
        print("Database does not exist")
    else:
        print(err)
