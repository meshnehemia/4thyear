from flask import Flask, render_template, send_file, Response, jsonify, request, redirect, url_for, session
from facedetection import gen_frames, detect_face , genandface
from deepface import DeepFace
from datetime import datetime
import io
import cv2
from transactionemails import generate_order_receipt
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"  
import base64
import numpy as np
import cv2
import hashlib
from database import connect
import pymysql
import os
import json
from emailsending import sendEmail
from mpesa import send_mpesa_payment
from past7daysales import get_sales_past_7_days , get_sales_online_vs_instore,get_sales_last_8_hours,get_total_sales_per_week,get_top_sold_products, monthlyprofit,get_order_status_data
from dateutil.relativedelta import relativedelta
from datetime import timedelta
from worker import mytasks,completedtasks,completedorders,availableorders,availabletasks,assignedorders,assignedtasks,assigntask,completetask

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)  # Required for session
  # needed for flash messages

def categories():
    conn = connect()
    if conn is None:
        return []
    
    try:
        cursor = conn.cursor()
        query = '''
            SELECT d.category_name, COUNT(c.category_id) AS appearance_count, d.category_id
            FROM categories c
            JOIN d_categories d ON c.category_id = d.category_id
            GROUP BY d.category_id, d.category_name, d.category_cover;
        '''
        cursor.execute(query)
        result = cursor.fetchall()
        print(result)
    finally:
        conn.close()

    return result

# Context processor to inject categories data globally into all templates
@app.context_processor
def show_categories():
    return {'categories': categories()}


#convert blob to image 
# Route to serve category cover images
@app.route('/category_cover/<int:category_id>')
def category_cover(category_id):
    conn = connect()  # Your DB connection function
    if conn is None:
        return "Could not connect to database", 500

    try:
        cursor = conn.cursor()
        query = '''SELECT category_cover FROM d_categories WHERE category_id = %s'''
        cursor.execute(query, (category_id,))
        result = cursor.fetchone()

        if result and result[0]:
            # Assuming result[0] is a BLOB field containing the image
            image_data = result[0]
            # Return image as a response
            return send_file(io.BytesIO(image_data), mimetype='image/jpeg')
        else:
            return "No image found", 404

    finally:
        conn.close()


#top advertisement section starts 
def topadvertised():
    conn = connect()
    if conn is None:
        return "could not connect to database", 500
    try:
        cursor = conn.cursor()
        query = '''SELECT p.product_name, p.description, p.price, d.product_id,
           d.new_price, d.type_of_offer FROM products p 
           JOIN Discounts d ON p.product_id = d.product_id'''
        cursor.execute(query)
        result = cursor.fetchall()
        return result
    finally:
        conn.close()

# Route to serve category cover images
@app.route('/productsphoto/<int:product_id>')
def productsphoto(product_id):
    conn = connect()  # Your DB connection function
    if conn is None:
        return "Could not connect to database", 500

    try:
        cursor = conn.cursor()
        query = '''SELECT cover_photo FROM products WHERE product_id = %s'''
        cursor.execute(query, (product_id,))
        result = cursor.fetchone()

        if result and result[0]:
            # Assuming result[0] is a BLOB field containing the image
            image_data = result[0]
            # Return image as a response
            return send_file(io.BytesIO(image_data), mimetype='image/jpeg')
        else:
            return "No image found", 404

    finally:
        conn.close()

@app.context_processor
def show_topadvertised():
    return {'advertised': topadvertised()}


@app.route('/api/products', methods=['GET'])
def get_products():
    conn = connect()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT product_id AS id, product_name AS name, description, price FROM products")
    products = cursor.fetchall()

    for product in products:
        product['image']= url_for('productsphoto', product_id=product['id'])
        # Add oldPrice dynamically or leave it None
        product['oldPrice'] = None  # Old price is optional or calculated as needed
        product['rating'] = round(3.5 + (5.0 - 3.5) * (cursor.rowcount / 10), 1)  # Example random rating for demo

    return jsonify(products)


# featured products 
def featured():
    conn = connect()
    if conn is None:
        return "could not connect to database", 500
    try:
        cursor = conn.cursor()
        query = '''SELECT p.product_name, p.description, p.price, f.product_id,
           f.new_price, f.feature_description FROM products p 
           JOIN featured f ON p.product_id = f.product_id'''
        cursor.execute(query)
        result = cursor.fetchall()
        return result
    finally:
        conn.close()

@app.context_processor
def feature():
    return {'featured': featured()}

@app.route('/')
def home():
    session['user_id'] = 6
    session['username'] = "user_name"
    session['full_name'] = "full_name"
    session['email'] = "meshnehemia7@gmail.com"
    session['phone_number'] = 254757316903
    session['transact'] = "not verified";
    return render_template('index.html')

def calculate_total_cost(carts):
    if 'user_id' in session:
        total_cost = 0 
        for cart in carts:
            quantity = cart[6]
            prices = [cart[3]] 
            if cart[4]:
                prices.append(cart[4])
            if cart[5]:
                prices.append(cart[5])
            best_price = min(prices)
            total_cost += quantity * best_price
        return total_cost
    else:
        return

@app.context_processor   
def cartcount():
    if 'user_id' in session:
        conn = connect()
        cursor = conn.cursor()
        
        # Pass session['user_id'] as a tuple
        cursor.execute('SELECT COUNT(*) FROM cart WHERE user_id = %s', (session['user_id'],))
        
        result = cursor.fetchone()
        total_items = result[0] if result[0] is not None else 0
        return {'number_of_cart_items': total_items}
    
    return {'number_of_cart_items': 0}



def carts():
    if 'user_id' in session:
        user_id = session['user_id']
        db = connect()
        cursor = db.cursor()
        query = """
        SELECT 
            c.cart_id,
            p.product_name,
            p.product_id,
            p.price,
            f.new_price AS featured_price,
            d.new_price AS discount_price,
            c.number_of_items,
            c.date_created
        FROM 
            Cart c
        JOIN 
            Products p ON c.product_id = p.product_id
        LEFT JOIN 
            Featured f ON p.product_id = f.product_id
        LEFT JOIN 
            Discounts d ON p.product_id = d.product_id
        WHERE 
            c.user_id = %s
        """
        cursor.execute(query, (user_id,))
        user_carts = cursor.fetchall()
        cursor.close()
        return user_carts
    else: 
        return


@app.route('/cart')
def cart():
    if 'user_id' in session:
        user_carts = carts()
        return render_template('cart.html', cart=user_carts, total = calculate_total_cost(user_carts))
    else:
        return render_template('cart.html')

@app.route('/paymentdetails')
def paymentdetails():
    item = carts()
    return render_template('paymentdetails.html', items = item, total = calculate_total_cost(item))

@app.route('/shop')
def shop():
    return render_template('shop.html')

@app.route('/contant')
def contact():
    return render_template('contact.html')

@app.route('/login')
def login():
    return render_template('signin.html')

@app.route('/signing', methods=['POST'])
def signing():
    data = request.get_json()  # Get JSON data from the request
    email = data.get('email')
    password = data.get('password')
    captured_image_data = data.get('captured_image_data')

    if not email or not password or not captured_image_data:
        return jsonify({"message": "Please fill out all fields."}), 400

    # Use SELECT query to check if the email exists in the database
    connection = connect()
    cursor = connection.cursor()
    cursor.execute("SELECT user_id, password,user_name, face_id,full_name , email, phone_number FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()

    if not user:
        return jsonify({"message": "Email not found."}), 404

    user_id, stored_password,user_name, stored_face_image,full_name ,em, phone_number = user

    if hashlib.sha256(password.encode()).hexdigest() != stored_password:
        subject = "unknown person"
        message = """
                        Hello,
                        We noticed a new login attempt to your account. 
                        If this was you, try to change password. 
                        However, if you do not recognize this attempt or suspect any unauthorized access, 
                        we strongly recommend that you change your password immediately for security purposes.
                        Your security is important to us. 
                        If you have any concerns, please don't hesitate to contact our support team.
                        Best regards,
                        Intelligent Supermarket Management Security Team
                        """
              
        sendEmail(email,subject, message);
        return jsonify({"message": "Incorrect password."}), 401

    # Decode the captured image (base64 to binary)
    try:
        image_data = base64.b64decode(captured_image_data.split(',')[1])  # Remove the data URL prefix
        nparr = np.frombuffer(image_data, np.uint8)  # Convert byte data to numpy array
        captured_image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)  # Decode into an image format OpenCV can handle
    except Exception as e:
        subject = "unknown person"
        message = """
                        Hello,
                        We noticed a new login attempt to your account. 
                        If this was you, no further action is required. 
                        However, if you do not recognize this attempt or suspect any unauthorized access, 
                        we strongly recommend that you change your password immediately for security purposes.
                        Your security is important to us. 
                        If you have any concerns, please don't hesitate to contact our support team.
                        Best regards,
                        Intelligent Supermarket Management Security Team
                        """
              
        sendEmail(email,subject, message);
        return jsonify({"message": "try again!"}), 500

    # Check if the user has a stored face image in the database
    if not stored_face_image:
        subject = "unknown person"
        message = """
                        Hello,
                        We noticed a new login attempt to your account. 
                        Either you, or someone who may look like you and has access to your password,
                        has tried to log in. If this was you, no further action is required. 
                        However, if you do not recognize this attempt or suspect any unauthorized access, 
                        we strongly recommend that you change your password immediately for security purposes.
                        Your security is important to us. 
                        If you have any concerns, please don't hesitate to contact our support team.
                        Best regards,
                        Intelligent Supermarket Management Security Team
                        """
              
        sendEmail(email,subject, message);
        return jsonify({"message": "No face image found for this user."}), 404

    try:
        # Decode stored face image from BLOB and convert to numpy array
        stored_face_image = np.frombuffer(stored_face_image, np.uint8)
        stored_face_image = cv2.imdecode(stored_face_image, cv2.IMREAD_COLOR)

        # Use DeepFace to compare the captured image with the stored face image
        result = DeepFace.verify(captured_image, stored_face_image)

        # Check the result for face match
        if result["verified"]:
            session['user_id'] = user_id
            session['username'] = user_name
            session['full_name'] = full_name
            session['email'] = email
            session['phone_number'] = phone_number
            session['transact'] = "not verified";
            subject = "account accessed successfully"
            message = """
            Hello,
            We noticed a new login to your account just now.
            Either you, or someone who resembles you and has your password, has accessed the system.
            If this was you, there's no need to worry! However, 
            if you do not recognize this activity or suspect any unauthorized access,
            we recommend you immediately change your password for security purposes.
            Stay safe and feel free to contact our support if you need any assistance.
            Best regards,
            intelligent supermarkt management Security Team
            """
            sendEmail(email,subject, message);

            return jsonify({"message": "Login successful.","user_id": session['user_id'], "username": session['username']}), 200
        else:
            subject = "unknown person"
            message = """
                        Hello,
                        We noticed a new login attempt to your account. 
                        Either you, or someone who may look like you and has access to your password,
                        has tried to log in. If this was you, no further action is required. 
                        However, if you do not recognize this attempt or suspect any unauthorized access, 
                        we strongly recommend that you change your password immediately for security purposes.
                        Your security is important to us. 
                        If you have any concerns, please don't hesitate to contact our support team.
                        Best regards,
                        Intelligent Supermarket Management Security Team
                        """
              
            sendEmail(email,subject, message);
            return jsonify({"message": "Face does not match."}), 403
    except Exception as e:
        session['user_id'] = user_id
        session['username'] = user_name
        session['full_name'] = full_name
        session['email'] = email
        session['phone_number'] = phone_number
        session['transact'] = "not verified";
        subject = "account accessed successfully"
        message = """
                        Hello,
                        We noticed a new login attempt to your account. 
                        Either you, or someone who may look like you and has access to your password,
                        has tried to log in. If this was you, no further action is required. 
                        However, if you do not recognize this attempt or suspect any unauthorized access, 
                        we strongly recommend that you change your password immediately for security purposes.
                        Your security is important to us. 
                        If you have any concerns, please don't hesitate to contact our support team.
                        Best regards,
                        Intelligent Supermarket Management Security Team
                        """
              
        sendEmail(email,subject, message);
        return jsonify({"message": "Login successful.","user_id": session['user_id'], "username": session['username']}), 200
@app.route('/signup')
def signup():
    return render_template('signup.html') 

@app.route('/sendotp', methods=['POST'])
def send_otp():
    data = request.get_json()  # Getting the data sent from frontend
    otp_received = data.get('otp')
    email = data.get('email')  # If you want the email too
    subject = "confirm email for supermarket management system"
    message = f"""
    Dear User,

    Your OTP code for email confirmation process is: {otp_received}

    This OTP is valid for the next 10 minutes. If you did not request this, please ignore this email.

    Best regards,
    Intelligent Supermarket Security Team
    """
    # Print the OTP to verify it has been received correctly
    sendEmail(email,subject,message)
    
    # Send a response back to the frontend
    return jsonify({'status': 'success', 'message': f'OTP {otp_received} received'}), 200

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('user_id', None)
    return redirect(url_for('home'))
 # Render the registration form
@app.route('/register', methods=['POST'])
def register():
        try:
            data = request.get_json()

        # Extract form data
            full_name = data.get('full_name')
            phone_number = data.get('phone_number')
            email = data.get('email')
            username = data.get('username')
            password = data.get('password')
            # Hash password

            hashed_password = hashlib.sha256(password.encode()).hexdigest()

            # Get the captured face image (BLOB)
            
            face_image = data.get('captured_image_data')  # This will be the face captured by the user
        
            face_data = None
            if face_image:
                # Remove base64 header (data:image/jpeg;base64,)
                face_image_base64 = face_image.split(',')[1]  # Get the base64 part after the comma
                # Decode the base64 string to binary data
                face_data = base64.b64decode(face_image_base64)


            # Establish MySQL connection using pymysql
            try:
                connection = connect()
                with connection.cursor() as cursor:
                    # SQL insert statement
                    insert_query = """
                        INSERT INTO users (email, phone_number, user_name, password, full_name, face_id)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """
                    # Execute the insert query with the data
                    cursor.execute(insert_query, (email, phone_number, username, hashed_password, full_name, face_data))
                    # Commit the changes to the database
                    connection.commit()
                return jsonify({'message': 'saved sucessfully'})
            except pymysql.MySQLError as e:
                print(f"Error: {e}")
                return jsonify({'message': 'f"Error: {e}"'})
            finally:
                if connection:
                    connection.close()
        except Exception as e:
            return jsonify({'message': f'Error: {str(e)}'}), 400
@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/transactionfeed')
def transactionfeed():
    return Response(genandface(session['user_id']), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/capture_image', methods=['POST'])
def capture_image():
    try:
        # Get the image from the POST request
        data = request.get_json()
        image_data = data['image']

        # Convert the base64 string to an image
        image_data = image_data.split(",")[1]  # Remove 'data:image/jpeg;base64,' part
        image_bytes = base64.b64decode(image_data)
        np_arr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        # Create a unique filename for each captured image
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        image_filename = f'captured_image_{timestamp}.jpg'

        # Save the captured image to a file
        cv2.imwrite(image_filename, img)

        if detect_face(img):
            return jsonify({'message': 'face detected continue to register','image': image_filename})

        return jsonify({'message': 'no face detected', 'image': image_filename}), 401

    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 405



@app.route('/transact')
def transaction():
    return render_template('transactions.html')

@app.route('/shelfpayment', methods=['POST'])
def shelf_payment():
    data = request.json
    if 'phoneNumber' not in data:
        return jsonify({"success": False, "message": "Phone number is missing"}), 400

    phone_number = data['phoneNumber']
    result = send_mpesa_payment(phone_number)
    if result["status"] == "success":
        return jsonify({"success": True, "message": result["message"]}), 200
    else:
        return jsonify({"success": False, "message": "Payment failed"}), 500

@app.route('/transactionverification', methods=['POST'])
def transaction_verification():
    data = request.get_json()
    otp = data.get('otp')
    email = session['email']
    user_id = session['user_id']
    if otp:
        generate_order_receipt(email , user_id,otp)
        print(f"OTP to send: {user_id}")
        return jsonify({'success': True})
    else:
        return jsonify({'success': False}), 400

@app.route('/verify')
def face_recognized():
    select_query = """
    SELECT status FROM tinitiation WHERE user_id = %s;
    """
    conn = connect()
    cursor = conn.cursor()
    cursor.execute(select_query, (session['user_id'],))
    result = cursor.fetchone()
    if result is None:
        return jsonify({"verified": "not verified"}), 404
    else:
        delete_query = "DELETE FROM tinitiation WHERE user_id = %s"
        cursor.execute(delete_query, (session['user_id'],))
        conn.commit()
        return jsonify({"verified": result}), 200
    
@app.route('/rcart', methods=['POST'])
def reducecart():
        data = request.get_json() 
        conn = connect()
        cursor = conn.cursor()
        select_query = "SELECT number_of_items FROM cart WHERE user_id = %s AND product_id = %s"
        cursor.execute(select_query, (session['user_id'], data))
        result = cursor.fetchone()

        if result is None:
            return jsonify({"message": "Item not found in the cart"}), 404
        
        current_quantity = result[0]
        if current_quantity <= 1:
            return jsonify({"message": "the minimum product allowed is 1 "}), 400
        
        new_quantity = current_quantity - 1
        if new_quantity < 1:
            new_quantity = 1
        update_query = "UPDATE cart SET number_of_items = %s WHERE user_id = %s AND product_id = %s"
        cursor.execute(update_query, (new_quantity, session['user_id'], data))
        conn.commit()
        return jsonify({"message": "updated successfully "}), 200

@app.route('/acart', methods=['POST'])
def addcart():
        data = request.get_json() 
        conn = connect()
        cursor = conn.cursor()
        select_query = "SELECT number_of_items FROM cart WHERE user_id = %s AND product_id = %s"
        cursor.execute(select_query, (session['user_id'], data))
        result = cursor.fetchone()

        if result is None:
            insert = "INSERT INTO cart (user_id, product_id, number_of_items) VALUES (%s, %s, %s)"
            cursor.execute(insert,(session['user_id'],data,1))
            conn.commit()
            return jsonify({"message": "Item added successful"}), 404
        
        current_quantity = result[0]
        new_quantity = current_quantity + 1
        update_query = "UPDATE cart SET number_of_items = %s WHERE user_id = %s AND product_id = %s"
        cursor.execute(update_query, (new_quantity, session['user_id'], data))
        conn.commit()
        return jsonify({"message": "updated successfully "}), 200

@app.route('/deletep', methods=['POST'])
def deletecart():
        data = request.get_json() 
        conn = connect()
        cursor = conn.cursor()
        delete_query = "DELETE FROM cart WHERE user_id = %s AND product_id = %s"
        print(session['user_id'])
        print(data)
        print(cursor.execute(delete_query, (session['user_id'], data)))
        conn.commit()
        return jsonify({"message": "deleted successfully "}), 200

@app.route('/sendmessage', methods=['POST'])
def insert_contact_form():
    try:
        conn = connect()
        data = request.get_json()
        full_name = data['full_name']
        email = data['email']
        subject = data['subject']
        message = data['message']
        status = "sent"
        insert_query = """
        INSERT INTO contact_form (full_name, email, subject, message,status)
        VALUES (%s, %s, %s, %s, %s)
        """
        cursor = conn.cursor()
        cursor.execute(insert_query, (full_name, email, subject, message, status))
        conn.commit() 
        return jsonify({"message": "message sent successully"}), 201

    except Exception as e:
        return jsonify({"message": str(e)}), 500

@app.route('/moreinformation/<int:product_id>')
def productdetails(product_id):

    conn = connect()  # Assuming connect() function exists to get DB connection
    try:
        cursor = conn.cursor()
        query = '''
           SELECT p.product_name, p.description, p.price, p.product_id,
            f.new_price, f.feature_description
            FROM products p
            LEFT JOIN featured f ON p.product_id = f.product_id
            WHERE p.product_id = %s
        '''
        cursor.execute(query, (product_id,))
        product_item = cursor.fetchone()
        images_query = '''
            SELECT image_data FROM ProductImages WHERE product_id = %s;
        '''
        cursor.execute(images_query, (product_id,))
        images = cursor.fetchall()

        if not images:
            images_query = '''
            SELECT cover_photo FROM Products WHERE product_id = %s;
            '''
            cursor.execute(images_query, (product_id,))
            images = cursor.fetchall()
            images_list = [base64.b64encode(image[0]).decode('utf-8') for image in images]
            return render_template('detail.html', product=product_item, images=images_list)
        images_list = [base64.b64encode(image[0]).decode('utf-8') for image in images]

        return render_template('detail.html', product=product_item, images=images_list)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/scan')
def scanproducts():
    return render_template('onother.html')


@app.route('/dashboardAdmin')
def dashboard():
    monthly_data = monthlyprofit()
    return render_template('dashboard.html', salesonlinevsstore=get_sales_online_vs_instore(), past8hrssales= get_sales_last_8_hours(), weekly = get_total_sales_per_week(), topsold= get_top_sold_products(), monthly_profits=monthly_data['monthly_profits'], months=monthly_data['months'])

@app.route('/get_order_status')
def get_order_status():
    order_status_data = get_order_status_data()  # e.g., {'pending': 300, 'completed': 450, 'assigned': 250}
    
    return jsonify(order_status_data)


@app.route('/salesperweek')
def salesperweek():
    return get_sales_past_7_days()

@app.route('/productlists')
def productlist():
    db = connect()  # Connect to the database
    cursor = db.cursor(dictionary=True)  # Use dictionary cursor to return results as dictionaries

    # Query to get all products, their prices (base, feature, and advertised), and their categories
    query = """
    SELECT p.product_id, p.product_name, p.description, p.price,
           f.new_price AS featured_price, 
           d.new_price AS advertised_price, 
           c.category_id, dc.category_name
    FROM products p
    LEFT JOIN featured f ON p.product_id = f.product_id
    LEFT JOIN discounts d ON p.product_id = d.product_id
    LEFT JOIN categories c ON p.product_id = c.product_id
    LEFT JOIN d_categories dc ON c.category_id = dc.category_id
    """

    cursor.execute(query)
    products = cursor.fetchall()  # Fetch all the product data

    # Process the results to include 'nil' for missing prices and category information
    for product in products:
        if product['featured_price'] is None:
            product['featured_price'] = 'nil'  # Set 'nil' if no featured price
        if product['advertised_price'] is None:
            product['advertised_price'] = 'nil'  # Set 'nil' if no advertised price
        if product['category_name'] is None:
            product['category_name'] = 'Uncategorized'  # Set 'Uncategorized' if no category assigned

    # Retrieve all categories for the category dropdown in the modal
    cursor.execute("SELECT category_id, category_name FROM d_categories")
    categories = cursor.fetchall()

    return render_template('products.html', products=products, categories=categories)

@app.route('/addproduct')
def addproduct():
    return render_template('addproduct.html')

@app.route('/newuser')
def newuser():
    return render_template('newstaff.html')

@app.route('/wmanagement')
def worker_management():
    # Fetch workers from the database
    conn = connect()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM staff")
    workers = cursor.fetchall()

    # Fetch tasks
    cursor.execute("SELECT * FROM list_of_tasks")
    tasks = cursor.fetchall()

    conn.close()

    return render_template('workersmanagement.html', workers=workers, tasks=tasks)

@app.route('/add_task', methods=['POST'])
def add_task():
    data = request.json
    task_description = data.get('task_description')
    current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO list_of_tasks (task_description, status, staff_id)
        VALUES (%s, 'not assigned', NULL)
    """, (task_description,))

    conn.commit()
    conn.close()

    return jsonify({'message': 'Task added successfully'}), 201

@app.route('/assign_task', methods=['POST'])
def assign_task():
    data = request.json
    task_id = data.get('task_id')
    staff_id = data.get('staff_id')
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("UPDATE list_of_tasks SET staff_id = %s, status = 'assigned' WHERE task_id = %s", (staff_id, task_id))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Task assigned successfully'}), 200


@app.route('/wassign_task', methods=['POST'])
def wassign_task():
    data = request.json
    task_id = data.get('task_id')
    return assigntask(session['user_id'],task_id)

@app.route('/wcomplete', methods=['POST'])
def completetasks():
    data = request.json
    task_id = data.get('task_id')
    return completetask(task_id)

# Fetch worker payment details
@app.route('/worker_payment_details', methods=['GET'])
def worker_payment_details():
    conn = connect()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT s.staff_id, s.name_of_staff, p.monthly_payment, p.payment_date 
        FROM staff s 
        JOIN payment p ON s.staff_id = p.staff_id
    """)
    payments = cursor.fetchall()

    conn.close()

    return jsonify(payments)

@app.route('/worker_stats', methods=['GET'])
def worker_stats():
    conn = connect()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM staff')
    total_workers = cursor.fetchone()[0] 
    cursor.execute('SELECT COUNT(*) FROM staff WHERE status = "active"')
    active_workers = cursor.fetchone()[0] 
    cursor.execute('SELECT COUNT(*) FROM staff WHERE status = "inactive"')
    inactive_workers = cursor.fetchone()[0] 
    conn.close()
    return jsonify({
        'totalWorkers': total_workers,
        'activeWorkers': active_workers,
        'inactiveWorkers': inactive_workers
    })

@app.route('/tasks', methods=['GET'])
def get_tasks():
    conn = connect()
    cursor = conn.cursor()  # No dictionary=True here
    cursor.execute('SELECT * FROM list_of_tasks where status = "not assigned"')
    tasks = cursor.fetchall()
    conn.close()

    # Using tuple indexing to extract task_id and task_description
    task_list = [{'task_id': task[0], 'task_description': task[1]} for task in tasks]  # Adjust the indices as necessary
    return jsonify(task_list)

@app.route('/workers', methods=['GET'])
def get_workers():
    conn = connect()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM staff')
    workers = cursor.fetchall()
    conn.close()
    worker_list = [{'staff_id': worker[0], 'name_of_staff': worker[1]} for worker in workers]
    return jsonify(worker_list)

@app.route('/api/task_list', methods=['GET'])
def task_list():
    conn = connect()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM list_of_tasks')
    tasks = cursor.fetchall()
    conn.close()
    task_list = [{'task_id': task[0],
                  'task_description': task[1],
                  'status': task[2],
                  'created': task[4],
                  'completed':task[5],
                  'assigned_worker': getworkername(task[3])} for task in tasks]
    return jsonify(task_list)
def getworkername(staff_id):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute('SELECT name_of_staff FROM staff where staff_id = %s', (staff_id,))
    name = cursor.fetchone()
    return name[0] if name else "No worker assigned"

@app.route('/api/mark_task_completed/<int:task_id>', methods=['POST'])
def mark_task_completed(task_id):
    conn = connect()
    completion_date = datetime.now()
    cursor = conn.cursor()
    cursor.execute('UPDATE list_of_tasks SET status = "completed", date_completed = %s  WHERE task_id = %s', (completion_date,task_id))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Task marked as completed'})


@app.route('/api/staff_details', methods=['GET'])
def staff_details():
    conn = connect()
    cursor = conn.cursor()

    # Query to get all staff details along with the number of tasks they completed, salary, and level
    cursor.execute("""
        SELECT s.staff_id, s.name_of_staff, s.date_employed, 
               COUNT(t.task_id) AS tasks_completed, s.status, 
               s.level, p.payment_per_level AS salary 
        FROM staff s
        LEFT JOIN list_of_tasks t ON s.staff_id = t.staff_id AND t.status = 'completed'
        LEFT JOIN payment_amount p ON s.level = p.level
        GROUP BY s.staff_id
    """)
    staff = cursor.fetchall()
    
    # Prepare the data in the response format
    staff_list = [{
        'staff_id': staff_member[0],
        'name_of_staff': staff_member[1],
        'date_employed': staff_member[2],
        'tasks_completed': staff_member[3],
        'status': staff_member[4],
        'level': staff_member[5],
        'salary': staff_member[6],
    } for staff_member in staff]

    conn.close()
    return jsonify(staff_list)


@app.route('/fire_staff', methods=['POST'])
def fire_staff():
    data = request.json
    staff_id = data.get('staff_id')

    conn = connect()
    cursor = conn.cursor()

    # Fetch current level and status of the staff member
    cursor.execute("SELECT level, status FROM staff WHERE staff_id = %s", (staff_id,))
    staff = cursor.fetchone()

    if staff and staff[1] != 'fired':  # Only proceed if the staff is not already fired
        # Set status to 'fired' and level to 'Junior-fired'
        cursor.execute("UPDATE staff SET status = 'fired', level = CONCAT(level, '-fired') WHERE staff_id = %s", (staff_id,))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Staff member fired successfully'}), 200
    else:
        return jsonify({'message': 'Staff member is already fired'}), 400

@app.route('/promote_staff', methods=['POST'])
def promote_staff():
    data = request.json
    staff_id = data.get('staff_id')

    conn = connect()
    cursor = conn.cursor()

    # Fetch current level and status
    cursor.execute("SELECT level, status FROM staff WHERE staff_id = %s", (staff_id,))
    staff = cursor.fetchone()
    print(staff)
    print(staff_id)
    if staff:
        current_level = staff[0]
        current_status = staff[1]
        print(staff_id)
        # If the staff member is fired, reemploy them at their last level (before '-fired')
        if current_status == 'fired':
            original_level = current_level.split('-')[0]  # Remove '-fired' suffix
            cursor.execute("UPDATE staff SET status = 'active', level = %s WHERE staff_id = %s", (original_level, staff_id))
            conn.commit()
            conn.close()
            return jsonify({'message': f'Staff member reemployed to their original level: {original_level}'}), 200
    
        # Define possible levels and promotion logic
        levels = ['Junior', 'Senior', 'Manager', 'Director', 'CEO']
        if current_level in levels:
            current_index = levels.index(current_level)
            if current_index < len(levels) - 1:
                new_level = levels[current_index + 1]
                cursor.execute("UPDATE staff SET level = %s WHERE staff_id = %s", (new_level, staff_id))
                conn.commit()
                conn.close()
                return jsonify({'message': f'Staff member promoted to {new_level}'}), 200
            else:
                return jsonify({'message': 'This staff member is at the highest level'}), 400
    return jsonify({'message': 'Staff member not found!!'}), 404

@app.route('/api/staff_payment_details', methods=['GET'])
def staff_payment_details():
    conn = connect()
    cursor = conn.cursor()

    # Fetch staff payment details
    cursor.execute("""
        SELECT s.staff_id, 
       s.name_of_staff, 
       pa.payment_per_level, 
       s.date_employed,
       COALESCE(SUM(p.monthly_payment), 0) as total_paid,
       MAX(p.payment_date) as latest_payment
        FROM staff s
        LEFT JOIN payment p ON s.staff_id = p.staff_id
        LEFT JOIN payment_amount pa ON pa.level = s.level
        GROUP BY s.staff_id;
    """)
    staff_members = cursor.fetchall()
    conn.close()
    current_date = datetime.now()
    staff_details = []

    for staff in staff_members:
        staff_id, name_of_staff, salary, date_employed, total_paid, latest_payment = staff

        # Calculate the days remaining to the end of the current month
        end_of_month = (current_date.replace(day=1) + relativedelta(months=1)) - timedelta(seconds=1)
        days_remaining = (end_of_month - current_date).days

        staff_details.append({
            'staff_id': staff_id,
            'name_of_staff': name_of_staff,
            'salary': salary,
            'total_paid': total_paid,
            'latest_payment': latest_payment,
            'days_remaining': days_remaining
        })
    return jsonify(staff_details)

@app.route('/demote_staff', methods=['POST'])
def demote_staff():
    data = request.json
    staff_id = data.get('staff_id')

    conn = connect()
    cursor = conn.cursor()

    # Fetch current level and status
    cursor.execute("SELECT level, status FROM staff WHERE staff_id = %s", (staff_id,))
    staff = cursor.fetchone()

    if staff:
        current_level = staff[0]
        current_status = staff[1]

        # If staff is fired, demotion is not allowed
        if current_status == 'fired':
            return jsonify({'message': 'This staff member is fired and cannot be demoted'}), 400

        # Define possible levels and demotion logic
        levels = ['Junior', 'Senior', 'Manager', 'Director', 'CEO']
        if current_level in levels:
            current_index = levels.index(current_level)
            if current_index > 0:
                new_level = levels[current_index - 1]
                cursor.execute("UPDATE staff SET level = %s WHERE staff_id = %s", (new_level, staff_id))
                conn.commit()
                conn.close()
                return jsonify({'message': f'Staff member demoted to {new_level}'}), 200
            else:
                return jsonify({'message': 'This staff member is at the lowest level'}), 400
    return jsonify({'message': 'Staff member not found'}), 404


@app.route('/api/orders', methods=['GET'])
def get_orders():
    try:
        conn = connect()
        cursor = conn.cursor()

        # Query to get all orders
        cursor.execute('''
            SELECT 
                o.order_id, o.client_id, o.date_placed, o.status,o.assigned_worker
            FROM orders o
        ''')

        orders = cursor.fetchall()

        response = {
            'orders': []
        }

        for order in orders:
            order_id, client_id, date_placed, status , worker= order
            response['orders'].append({
                'order_id': order_id,
                'client_id': get_user_email(client_id),
                'date_placed': date_placed.strftime('%Y-%m-%d %H:%M:%S'),
                'status': status,
                'status_class': get_status_class(status),
                'assigned_worker': get_staffname(worker) # Assuming no workers assigned yet
            })

        cursor.close()
        conn.close()

        return jsonify(response), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Helper function to map order status to CSS classes
def get_status_class(status):
    if status == 'Pending':
        return 'status-pending'
    elif status == 'Completed':
        return 'status-completed'
    elif status == 'Assigned':
        return 'status-assigned'
    else:
        return 'status-unknown'


@app.route('/api/orders/<int:order_id>/assign', methods=['POST'])
def assign_worker(order_id):
    try:
        worker_id = request.json.get('worker')
        conn = connect()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE orders
            SET assigned_worker = %s, status = "assigned"
            WHERE order_id = %s
        ''', (worker_id, order_id))

        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({'success': True}), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/wassignorder', methods=['POST'])
def assignorders():
    data = request.json
    order_id = data.get('task_id')
    worker_id = session['user_id']
    try:
        conn = connect()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE orders
            SET assigned_worker = %s, status = "assigned"
            WHERE order_id = %s
        ''', (worker_id, order_id))

        conn.commit()

        cursor.close()
        conn.close()
        return jsonify({'success': True}), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/wcompleteorder', methods=['POST'])
def completeorder():
    data = request.json
    order_id = data.get('task_id')

    try:
        conn = connect()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE orders
            SET status = "completed"
            WHERE order_id = %s
        ''', (order_id,))

        conn.commit()

        cursor.close()
        conn.close()
        return jsonify({'success': True}), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500




def get_user_email(user_id):
    try:
        conn = connect()  # Your database connection function
        cursor = conn.cursor()

        # Query to get the email for a specific user ID
        cursor.execute('''
            SELECT email 
            FROM users 
            WHERE user_id = %s
        ''', (user_id,))

        result = cursor.fetchone()

        cursor.close()
        conn.close()

        if result:
            return result[0]  # Return the email
        else:
            return None  # User ID not found

    except Exception as e:
        print(f"Error: {e}")
        return None

def get_staffname(staff_id):
    try:
        conn = connect()  # Your database connection function
        cursor = conn.cursor()

        # Query to get the email for a specific user ID
        cursor.execute('''
            SELECT name_of_staff 
            FROM staff 
            WHERE staff_id = %s
        ''', (staff_id,))

        result = cursor.fetchone()

        cursor.close()
        conn.close()

        if result:
            return result[0]  # Return the email
        else:
            return None  # User ID not found

    except Exception as e:
        print(f"Error: {e}")
        return None

@app.route('/placeorder',methods=['POST'])
def place_order():
    send_mpesa_payment(session['phone_number'])
    user_id = session['user_id']
    conn = connect()
    if conn is None:
        return "Could not connect to the database", 500
    try:
        cursor = conn.cursor()

        # Step 1: Get all products from the user's cart
        query_cart = '''SELECT product_id, number_of_items FROM Cart WHERE user_id = %s'''
        cursor.execute(query_cart, (user_id,))
        cart_items = cursor.fetchall()  # This gets all the products in the user's cart

        if not cart_items:
            return "No items in cart to place an order", 400

        # Step 2: Insert into the orders table with 'assigned_worker' as NULL and status as 'Pending'
        query_order = '''INSERT INTO orders (client_id, status, assigned_worker)
                         VALUES (%s, 'Pending', NULL)'''
        cursor.execute(query_order, (user_id,))
        order_id = cursor.lastrowid  # Get the last inserted order_id

        # Step 3: For each item in the cart, insert into the ordersales and sales tables
        for item in cart_items:
            product_id = item[0]
            number_of_items = item[1]

            # Get product price from Products table to calculate total cost
            query_product = '''SELECT price FROM Products WHERE product_id = %s'''
            cursor.execute(query_product, (product_id,))
            product = cursor.fetchone()
            cost = float(product[0]) * float(number_of_items)

            # Insert into ordersales
            query_ordersales = '''INSERT INTO ordersales (order_id, product_id, cost, number_of_items)
                                  VALUES (%s, %s, %s, %s)'''
            cursor.execute(query_ordersales, (order_id, product_id, cost, number_of_items))

            # Insert into sales table (optional, if you want to track individual product sales)
            query_sales = '''INSERT INTO sales (product_id, client_id, sale_type, amount_bought, profit_made)
                             VALUES (%s, %s, 'online', %s, %s)'''
            profit_made = cost * 0.1  # Assuming a 10% profit margin, adjust as necessary
            cursor.execute(query_sales, (product_id, user_id, cost, profit_made))
            reduce(product_id)

        # Step 4: Clear the user's cart
        query_clear_cart = '''DELETE FROM Cart WHERE user_id = %s'''
        cursor.execute(query_clear_cart, (user_id,))

        # Commit all the changes
        conn.commit()

        print("Order placed successfully!")
        return redirect(url_for('home'))

    except Exception as e:
        conn.rollback()  # In case of error, rollback the transaction
        print(str(e))
        return "Error placing order", 500
    finally:
        conn.close()
@app.route('/self_sales_orders', methods=['POST'])
def process_self_order():
    staff_id = session['user_id']  # Get the staff_id from the session
    if not staff_id:
        return jsonify({"error": "Staff ID not found in session"}), 400

    conn = connect()
    if conn is None:
        return jsonify({"error": "Could not connect to the database"}), 500

    try:
        cursor = conn.cursor()

        # Step 1: Fetch the self-orders for this staff member
        query_self_orders = '''SELECT product_id, number_of_items FROM selforders WHERE staff_id = %s'''
        cursor.execute(query_self_orders, (staff_id,))
        self_orders = cursor.fetchall()

        if not self_orders:
            return jsonify({"error": "No self-orders found for this staff member"}), 400

        # Step 2: For each self-order, insert into the 'sales' table with 'on-Store' as sale_type
        for order in self_orders:
            product_id = order[0]
            number_of_items = order[1]

            # Get product price from the Products table to calculate total cost
            query_product = '''SELECT price FROM Products WHERE product_id = %s'''
            cursor.execute(query_product, (product_id,))
            product = cursor.fetchone()

            if product is None:
                return jsonify({"error": f"Product with ID {product_id} not found"}), 400

            cost = float(product[0]) * float(number_of_items)

            # Insert into sales table for 'on-Store' type
            query_sales = '''INSERT INTO sales (product_id, client_id, sale_type, amount_bought, profit_made)
                             VALUES (%s, %s, 'In-Store', %s, %s)'''
            profit_made = cost * 0.1  # Assuming a 10% profit margin
            cursor.execute(query_sales, (product_id, staff_id, cost, profit_made))
            reduce(product_id)

        # Step 3: Remove the self-orders from the 'selforders' table
        query_remove_self_orders = '''DELETE FROM selforders WHERE staff_id = %s'''
        cursor.execute(query_remove_self_orders, (staff_id,))

        # Step 4: Add a task indicating the self-order has been processed
        query_add_task = '''INSERT INTO list_of_tasks (task_description, status, staff_id, date_completed)
                    VALUES (%s, 'completed', %s, NOW())'''
        task_description = f'Self-order processing completed for staff ID {staff_id}.'
        cursor.execute(query_add_task, (task_description, staff_id))

        # Commit all changes
        conn.commit()

        print(f"Self-order processed successfully for staff ID {staff_id}.")
        return jsonify({"message": "Self-order processed successfully"}), 200

    except Exception as e:
        conn.rollback()  # Rollback in case of error
        print(f"Error processing self-order for staff ID {staff_id}: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/ordersmanagement')
def listoforders():
    return render_template('listoforders.html')

@app.route('/addcategory')
def newcategory():
    return render_template('newcategory.html')

@app.route('/saveproduct', methods=['POST'])
def saveproduct():
    try:
        serial_number = request.form['serial_number']
        product_name = request.form['product_name']
        description = request.form['description']
        price = request.form['price']
        
        # Handle cover photo upload
        cover_photo = request.files['cover_photo']
        if cover_photo and cover_photo.filename != '':
            photo_data = cover_photo.read()  # Read binary data of the file

            # Insert product data into the database
            db = connect()
            cursor = db.cursor()

            insert_query = '''
            INSERT INTO products (product_id,product_name, description, price, cover_photo)
            VALUES (%s, %s, %s, %s, %s)
            '''
            cursor.execute(insert_query, (serial_number,product_name, description, price, photo_data))
            db.commit()
            cursor.close()
            db.close()

            return jsonify({'success': True, 'message': 'Product has been added successfully!'})
        else:
            return jsonify({'success': False, 'message': 'Cover photo is required!'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/save_category', methods=['POST'])
def save_category():
    try:
        category_name = request.form['product_name']  # Get category name from form
        # Handle cover photo upload
        cover_photo = request.files['cover_photo']
        
        if cover_photo and cover_photo.filename != '':
            photo_data = cover_photo.read()  # Read binary data of the file

            # Insert category data into the database
            db = connect()
            cursor = db.cursor()

            insert_query = '''
            INSERT INTO d_categories (category_name, category_cover)
            VALUES (%s, %s)
            '''
            cursor.execute(insert_query, (category_name, photo_data))
            db.commit()
            cursor.close()
            db.close()

            return jsonify({'success': True, 'message': 'Category has been added successfully!'})
        else:
            return jsonify({'success': False, 'message': 'Cover photo is required!'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


def save_feature(product_id, new_price, feature_description):
    db = connect()
    cursor = db.cursor()

    try:
        # Step 1: Check if product_id exists in the featured table
        check_query = "SELECT product_id FROM featured WHERE product_id = %s"
        cursor.execute(check_query, (product_id,))
        result = cursor.fetchone()  # If product_id exists, result will not be None

        if result:  # If product_id exists, update the record
            update_query = """
            UPDATE featured
            SET new_price = %s, feature_description = %s
            WHERE product_id = %s
            """
            cursor.execute(update_query, (new_price, feature_description, product_id))
        else:  # If product_id does not exist, insert a new record
            insert_query = """
            INSERT INTO featured (product_id, new_price, feature_description)
            VALUES (%s, %s, %s)
            """
            cursor.execute(insert_query, (product_id, new_price, feature_description))

        # Commit the transaction
        db.commit()

    except Exception as e:
        db.rollback()  # Rollback in case of error
        raise e

    finally:
        cursor.close()
        db.close()


def save_advertisement(product_id, new_price, offer_type):
    db = connect()
    cursor = db.cursor()

    try:
        # Step 1: Check if product_id exists in the discounts table
        check_query = "SELECT product_id FROM discounts WHERE product_id = %s"
        cursor.execute(check_query, (product_id,))
        result = cursor.fetchone()  # If product_id exists, result will not be None
        
        if result:  # If product_id exists, update the record
            update_query = """
            UPDATE discounts
            SET new_price = %s, type_of_offer = %s
            WHERE product_id = %s
            """
            cursor.execute(update_query, (new_price, offer_type, product_id))
        else:  # If product_id does not exist, insert a new record
            insert_query = """
            INSERT INTO discounts (product_id, new_price, type_of_offer)
            VALUES (%s, %s, %s)
            """
            cursor.execute(insert_query, (product_id, new_price, offer_type))

        # Commit the transaction
        db.commit()

    except Exception as e:
        db.rollback()  # Rollback in case of error
        raise e

    finally:
        cursor.close()
        db.close()


def save_category(product_id, category_id):
    db = connect()
    cursor = db.cursor()

    try:
        # Step 1: Check if product_id exists in the table
        check_query = "SELECT product_id FROM categories WHERE product_id = %s"
        cursor.execute(check_query, (product_id,))
        result = cursor.fetchone()  # If product_id exists, result will not be None
        
        if result:  # Product already exists, so we update
            update_query = """
            UPDATE categories
            SET category_id = %s
            WHERE product_id = %s
            """
            cursor.execute(update_query, (category_id, product_id))
        else:  # Product doesn't exist, so we insert a new record
            insert_query = """
            INSERT INTO categories (product_id, category_id)
            VALUES (%s, %s)
            """
            cursor.execute(insert_query, (product_id, category_id))

        # Commit the transaction after executing the query
        db.commit()

    except Exception as e:
        db.rollback()  # Rollback in case of error
        raise e

    finally:
        cursor.close()
        db.close()


@app.route('/save-category', methods=['POST'])
def save_category_route():
    try:
        data = request.get_json()
        product_id = data['product_id']
        category_id = data['category_id']
        save_category(product_id, category_id)
        return jsonify({'success': True}), 200
    except Exception as e:
        print(str(e))
        return jsonify({'success': False, 'error': str(e)}), 300

@app.route('/save-advertisement', methods=['POST'])
def save_advertisement_route():
    try:
        data = request.get_json()
        product_id = data['product_id']
        new_price = data['advertised_price']
        offer_type = data['offer_type']
        
        save_advertisement(product_id, new_price, offer_type)
        return jsonify({'success': True}), 200
    except Exception as e:
        print(str(e))
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/save-feature', methods=['POST'])
def save_feature_route():
    try:
        data = request.get_json()
        product_id = data['product_id']
        new_price = data['feature_price']
        feature_description = data['feature_description']
        
        save_feature(product_id, new_price, feature_description)
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/editproduct/<int:product_id>', methods=['POST'])
def edit_product(product_id):
      # Get form data
    product_name = request.form.get('product_name')
    product_price = request.form.get('product_price')
    product_description = request.form.get('product_description')
    product_cover = request.files.get('product_cover')  # Get file from the form
    
    # Convert the image to blob and save it to the database
    cover_image_blob = None
    if product_cover:
        cover_image_blob = product_cover.read()  # Read image as binary (BLOB)
    
    try:
        # Connect to the database
        connection = connect()
        with connection.cursor() as cursor:
            # SQL query to update the product, including BLOB data for the image
            sql = """
            UPDATE products
            SET product_name = %s, price = %s, description = %s, cover_photo = %s
            WHERE product_id = %s
            """
            cursor.execute(sql, (product_name, product_price, product_description, cover_image_blob, product_id))
            connection.commit()
        
        return jsonify({'success': True, 'message': 'Product updated successfully!'})
    
    except Exception as e:
        print(str(e))
        return jsonify({'success': False, 'message': str(e)})
    
    finally:
        connection.close()

# Route to delete a product
@app.route('/deleteproduct/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    try:
        # Connect to the database
        connection = connect()
        with connection.cursor() as cursor:
            # SQL query to delete the product
            sql = "DELETE FROM products WHERE product_id = %s"
            cursor.execute(sql, (product_id,))
            connection.commit()
        
        return jsonify({'success': True, 'message': 'Product deleted successfully!'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    
    finally:
        connection.close()


def add_staff(data):
    try:
        conn = connect()
        cursor = conn.cursor()

        # Check if the email exists in the 'users' table
        email = data['email_address']
        cursor.execute("SELECT user_id FROM users WHERE email = %s", (email,))
        result = cursor.fetchone()

        if result:
            # If email exists, get the user_id
            user_id = result[0]

            # Check if the user_id already exists in the 'staff' table
            cursor.execute("SELECT staff_id FROM staff WHERE staff_id = %s", (user_id,))
            staff_result = cursor.fetchone()

            if staff_result:
                # If staff_id already exists, return an error message
                return {"status": "error", "message": "Staff member already exists."}

            # If the staff_id doesn't exist, insert the new staff member
            insert_query = """
            INSERT INTO staff (staff_id, name_of_staff, phone_number, email_address, level, date_employed, status, id_number)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, (
                user_id,
                data['name_of_staff'],
                data['phone_number'],
                data['email_address'],
                data['level'],
                data['date_employed'],
                data['status'],
                data['id_number']
            ))
            conn.commit()
            return {"status": "success", "message": "Staff member added successfully."}

        else:
            # Email does not exist
            return {"status": "error", "message": "Email not found. Please register on the platform first."}

    finally:
        if conn:
            conn.close()


@app.route("/add_staff", methods=["POST"])
def add_staff_route():
    data = request.get_json()
    response = add_staff(data)
    return jsonify(response)

@app.route("/myorders")
def myorders():
    user_id = session.get('user_id')  # Assuming user is logged in and you have user_id stored in the session

    if not user_id:
        return "Please log in to view your orders.", 401  # Redirect to login if not authenticated

    try:
    # Ensure the database connection works
        conn = connect()
        cursor = conn.cursor(dictionary=True)
        query = """
        SELECT o.order_id, o.status, o.date_placed, os.cost, os.number_of_items, p.product_name, p.product_id,p.description
        FROM orders o
        JOIN ordersales os ON o.order_id = os.order_id
        JOIN products p ON os.product_id = p.product_id
        WHERE o.client_id = %s
        """
        # Fetch the orders
        cursor.execute(query, (user_id,))
        orders = cursor.fetchall()
        # print("Fetched Orders:", orders)  # Debug output
        
        # Group and format orders
        grouped_orders = {}
        for order in orders:
            order_id = order['order_id']
            if order_id not in grouped_orders:
                grouped_orders[order_id] = {
                    'status': order['status'],
                    'date_placed': order['date_placed'].strftime('%Y-%m-%d %H:%M:%S'),
                    'items': []
                }
            grouped_orders[order_id]['items'].append({
                'product_name': order['product_name'],
                'id':order['product_id'],
                'description':order['description'],
                'cost': float(order['cost']),
                'number_of_items': order['number_of_items']
            })

        # Check the type and structure of grouped_orders
        # print(f"Type of grouped_orders: {type(grouped_orders)}")
        # for key, value in grouped_orders.items():
            # print(f"Order ID: {key}, Order Info: {value}")

        return render_template('myorders.html', orders=grouped_orders)
        
    except Exception as err:
        print(f"Error: {err}")
        return f"Error fetching orders: {err}", 500



@app.route("/workersdaskboard")
def listoftasks():
    tasks = mytasks(session['user_id'])
    return render_template('workers.html', tasks= tasks['tasks'],completetasks= completedtasks(session['user_id']) ,completedorders=completedorders(session['user_id']), availableorders=availableorders(),availabletasks=availabletasks(),assignedorders=assignedorders(session['user_id']),assignedtasks=assignedtasks(session['user_id']))



@app.route('/get_work_data', methods=['GET'])
def get_work_data():
    # Check if worker_id is in the session (example hardcoded)
    worker_id = session['user_id']  # You can replace this with session['worker_id'] if using sessions
    conn = connect()
    cursor = conn.cursor(dictionary=True)
    
    # Query for tasks completed, pending, and assigned in the past 7 hours
    now = datetime.now()
    past_7_hours = now - timedelta(hours=7)
    
    # Query for tasks
    query_tasks = """
    SELECT HOUR(date_completed) as hour, COUNT(*) AS count, status 
    FROM list_of_tasks 
    WHERE staff_id = %s AND date_completed >= %s
    GROUP BY hour, status
    """
    cursor.execute(query_tasks, (worker_id, past_7_hours))
    task_data = cursor.fetchall()

    # Initialize hourly data for tasks
    hourly_data = {}

    for record in task_data:
        hour = record['hour']
        count = record['count']
        status = record['status']

        if hour not in hourly_data:
            hourly_data[hour] = {'tasks': 0}

        # Update the task count for the corresponding hour
        hourly_data[hour]['tasks'] += count

    # Fill missing hours with 0 tasks
    for hour in range(now.hour - 6, now.hour + 1):
        if hour not in hourly_data:
            hourly_data[hour] = {'tasks': 0}
    
    # Return the tasks data as JSON
    return jsonify(hourly_data)

def get_all_products():
    conn = connect()
    cursor = conn.cursor(dictionary=True)  # Get results as dictionaries
    query = "SELECT product_id, product_name, description, price FROM products"
    cursor.execute(query)
    return cursor.fetchall()

@app.route('/process_frame', methods=['POST'])
def process_frame():
    results = get_all_products()
    try:
        # Check if the request has image data
        if 'image' not in request.json:
            return jsonify({'error': 'No image data provided'}), 400
        
        data = request.get_json()
        img_data = data.get('image')

        # Decode the base64 string
        img_data = img_data.split(',')[1]  # Remove the base64 prefix (data:image/jpeg;base64, ...)
        img_bytes = base64.b64decode(img_data)
        img_array = np.frombuffer(img_bytes, dtype=np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

        if img is None:
            return jsonify({'error': 'Image processing failed'}), 500

        # Convert the image to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Use Tesseract to extract text from the image
        text = pytesseract.image_to_string(gray)
        product_ids_to_check = [str(product['product_id']) for product in results]
        print(text)
        for product_id in product_ids_to_check:
            # found= [product_id in text.lower()]
            # print(text)
            # print(product_id)
            # print(found)
            if product_id in text.lower():
                product = next((p for p in results if str(p['product_id']) == product_id), None)
                if product:
                    result = insert_selforder(session['staff_id'], product['product_id'], 1)
                    return jsonify({'found_products': product['product_name'] + " " + result}), 200
        # Return the found product names as a JSON response
        return jsonify({'found_products': ''})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/checkSerialNumber', methods=['GET'])
def check_serial_number():
    session['staff_id'] = session['user_id'];
    # Get the serial number from the query parameters
    serial_number = request.args.get('serial_number')

    if not serial_number:
        return jsonify({'error': 'Serial number not provided'}), 400  # Return error if serial number is missing

    # Convert serial_number to integer to match product_id type in the data
    try:
        serial_number = int(serial_number)
    except ValueError:
        return jsonify({'error': 'Invalid serial number format'}), 400  # Return error if serial number is invalid

    # Search for the product with matching product_id
    product = next((p for p in get_all_products() if p['product_id'] == serial_number), None)

    if product:
        result = insert_selforder(session['staff_id'], product['product_id'], 1)
        return jsonify({'product': product['product_name'] + " " + result}), 200  # Return the product if found
    else:
        return jsonify({'error': 'Product not found'}), 404  # Return error if no product is found
@app.route('/updateNumber', methods=['GET'])
def insert_or_update_item():
    product_id = request.args.get('product_id')
    number_of_items = request.args.get('number_of_items')

    try:
        conn = connect()
        cursor = conn.cursor()

        # First, check if the product already exists
        check_query = "SELECT * FROM availableItemNumber WHERE product_id = %s"
        cursor.execute(check_query, (product_id,))
        existing_item = cursor.fetchone()

        if existing_item:
            # If the item exists, update the item count
            update_query = """
            UPDATE availableItemNumber 
            SET number_of_items = %s 
            WHERE product_id = %s;
            """
            cursor.execute(update_query, (number_of_items, product_id))
            print(f"Product ID {product_id} updated with {number_of_items} items.")
        else:
            # If the item does not exist, insert the new item
            insert_query = """
            INSERT INTO availableItemNumber (product_id, number_of_items) 
            VALUES (%s, %s);
            """
            cursor.execute(insert_query, (product_id, number_of_items))
            print(f"Product ID {product_id} inserted with {number_of_items} items.")

        # Commit the changes
        conn.commit()
        return jsonify({"status": "success", "message": "Item count updated successfully."})

    except Exception as error:
        print(f"Failed to insert or update record: {error}")
        return jsonify({"status": "error", "message": "Failed to update item count."})

    finally:
        # Close the cursor and connection
        if conn.is_connected():
            cursor.close()
            conn.close()


def get_item_count(product_id):
    connection = connect()
    cursor = connection.cursor()
    query = "SELECT number_of_items FROM availableItemNumber WHERE product_id = %s"
    cursor.execute(query, (product_id,))
    result = cursor.fetchone()
    cursor.close()
    connection.close()
    if result:
        return result[0]
    return 0 

@app.route('/get_item_count/<int:product_id>', methods=['GET'])
def get_item_count_route(product_id):
    item_count = get_item_count(product_id)
    return jsonify({'number_of_items': item_count})


def insert_selforder(staff_id, product_id, number_of_items):
    try:
        # Establish a database connection
        conn = connect()
        cursor = conn.cursor()

        # First, check if the combination of staff_id and product_id exists
        check_query = """
        SELECT * FROM selforders WHERE staff_id = %s AND product_id = %s
        """
        cursor.execute(check_query, (staff_id, product_id))
        result = cursor.fetchone()

        if result:
            update_query = """
            UPDATE selforders 
            SET number_of_items = number_of_items + 1
            WHERE staff_id = %s AND product_id = %s
            """
            values = (staff_id, product_id)

            # Execute the query
            cursor.execute(update_query, values)
            conn.commit()
            return "updated by adding 1"
        else:
            # If not found, insert the new order
            insert_query = """
            INSERT INTO selforders (staff_id, product_id, number_of_items)
            VALUES (%s, %s, %s)
            """
            cursor.execute(insert_query, (staff_id, product_id, number_of_items))
            conn.commit()  # Commit the changes to the database

            return "Order added successfully."

    except Exception as error:
        return "Failed to add or check record."

    finally:
        # Close the cursor and connection
        if conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/collectselfpurchase', methods=['GET'])
def check():
    return retrieve_products_for_staff(session['user_id'])
def retrieve_products_for_staff(staff_id):
    try:
        conn = connect()  # Establish database connection
        cursor = conn.cursor(dictionary=True)  # Use dictionary=True for results as dictionaries

        # Step 1: Get product IDs for the given staff_id from selforders
        select_product_ids_query = """
        SELECT product_id 
        FROM selforders
        WHERE staff_id = %s
        """
        cursor.execute(select_product_ids_query, (staff_id,))
        product_ids = cursor.fetchall()
        if not product_ids:
            return {"status": "not_found", "message": "No products found for the given staff."}
        product_ids_list = [row['product_id'] for row in product_ids]

        # Step 2: Use the product IDs to retrieve product details from the Cart, Products, Featured, and Discounts tables
        select_product_details_query = """
                SELECT 
                    p.product_name,
                    p.product_id,
                    p.price,
                    f.new_price AS featured_price,
                    d.new_price AS discount_price,
                    s.number_of_items
                FROM 
                    selforders s
                JOIN 
                    Products p ON s.product_id = p.product_id
                LEFT JOIN 
                    Featured f ON p.product_id = f.product_id
                LEFT JOIN 
                    Discounts d ON p.product_id = d.product_id
                WHERE 
                    s.product_id IN (%s)
            """ % ','.join(['%s'] * len(product_ids_list))
            # Dynamically bind multiple product_ids
        
        cursor.execute(select_product_details_query, product_ids_list)
        products = cursor.fetchall()  # Fetch all product details

        if not products:
            return {"status": "not_found", "message": "No product details found for the given staff."}
        
        return {"status": "success", "data": products}

    except Exception as error:
        print(f"Failed to retrieve products: {error}")
        return {"status": "error", "message": "Failed to retrieve product details."}

    finally:
        # Close the cursor and connection
        if conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/deleteselfproduct', methods=['POST'])
def delete_self_product():
    # Get the staff_id from session
    staff_id = session['user_id']
    conn = connect()
    # Get the product_id from the request
    data = request.get_json()
    product_id = data.get('product_id')

    if not staff_id or not product_id:
        return jsonify({'status': 'error', 'message': 'Missing staff or product ID'}), 400

    try:
        # Assuming you have a function to remove a product for a specific staff member
        cursor = conn.cursor()
        delete_query = """
            DELETE FROM selforders
            WHERE staff_id = %s AND product_id = %s
        """
        cursor.execute(delete_query, (staff_id, product_id))
        conn.commit()

        # Check if the product was actually deleted
        if cursor.rowcount == 0:
            return jsonify({'status': 'error', 'message': 'Product not found or already deleted'}), 404

        return jsonify({'status': 'success', 'message': 'Product deleted successfully'})

    except Exception as e:
        # Handle any errors that may occur during the deletion process
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/updateQuantity', methods=['POST'])
def update_quantity():
    data = request.get_json()
    conn = connect()
    product_id = data.get('product_id')
    number_of_items = data.get('number_of_items')
    staff_id = session['user_id']  # Assuming staff_id is stored in session

    if not product_id or number_of_items is None or not staff_id:
        return jsonify({'status': 'error', 'message': 'Missing product ID, quantity, or staff ID'}), 400

    try:
        # Assuming you have a database connection
        cursor = conn.cursor()
        update_query = """
            UPDATE selforders
            SET number_of_items = %s
            WHERE product_id = %s
            AND staff_id = %s
        """
        cursor.execute(update_query, (number_of_items, product_id, staff_id))
        conn.commit()

        return jsonify({'status': 'success', 'message': 'Quantity updated successfully'})

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    

def reduce(product_id):
    try:
        conn = connect()
        cursor = conn.cursor()

        # Check the current number of items
        check_query = """
        SELECT number_of_items
        FROM availableItemNumber
        WHERE product_id = %s;
        """
        cursor.execute(check_query, (product_id,))
        current_item = cursor.fetchone()

        if current_item is None:
            # If the product doesn't exist, return an error message
            return jsonify({"status": "error", "message": "Product not found."})

        # Get the current number of items
        number_of_items = current_item[0]

        if number_of_items > 0:
            # Reduce the item count by 1
            update_query = """
            UPDATE availableItemNumber
            SET number_of_items = number_of_items - 1
            WHERE product_id = %s;
            """
            cursor.execute(update_query, (product_id,))
            conn.commit()
            return jsonify({"status": "success", "message": "Item reduced by one."})

        else:
            # If the number of items is already 0, return an error message
            return jsonify({"status": "error", "message": "No more items available."})

    except Exception as error:
        print(f"Failed to reduce item count: {error}")
        return jsonify({"status": "error", "message": "Failed to reduce item count."})

    finally:
        # Close the cursor and connection
        if conn.is_connected():
            cursor.close()
            conn.close()
            
@app.route('/derivery', methods=['POST'])
def save_or_update_delivery():
    data = request.json  # Receiving JSON data from the front end
    user_id = session['user_id']  # Assuming user_id is in the session
    full_name = data.get('full_name')
    email = data.get('email')
    phone_number = data.get('phone_number')
    station = data.get('station')
    address = data.get('address')
    house_details = data.get('house_details')
    delivery_type = data.get('delivery_type')
    payment_method = data.get('payment_method')
    total_amount = data.get('total_amount')  # Ensure this value is provided

    try:
        # Establish the database connection
        conn = connect()  # Adjust this function to connect to your MySQL database
        cursor = conn.cursor()

        # Check if delivery details for this user already exist
        check_query = "SELECT derivery_id FROM derivery_details WHERE user_id = %s"
        cursor.execute(check_query, (user_id,))
        result = cursor.fetchone()

        if result:
            # If the details exist, update the record (without changing delivery status)
            update_query = """
            UPDATE derivery_details
            SET full_name = %s, email = %s, phone_number = %s, station = %s, 
                address = %s, house_details = %s, delivery_type = %s, payment_method = %s, total_amount = %s
            WHERE user_id = %s
            """
            values = (full_name, email, phone_number, station, address, house_details, delivery_type, payment_method, total_amount, user_id)
            cursor.execute(update_query, values)
            conn.commit()
            message = "Delivery details updated successfully!"

        else:
            # Insert new record if no details exist
            insert_query = """
            INSERT INTO derivery_details (user_id, full_name, email, phone_number, station, address, house_details, delivery_type, payment_method, total_amount, derivery_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'NOT DELIVERED')
            """
            values = (user_id, full_name, email, phone_number, station, address, house_details, delivery_type, payment_method, total_amount)
            cursor.execute(insert_query, values)
            conn.commit()
            message = "Delivery details saved successfully!"

        # Close the cursor and connection
        cursor.close()
        conn.close()

        # Return success message
        return jsonify({"message": message}), 200

    except Exception as err:
        # Handle errors and return the error message as a JSON response
        print(err)
        return jsonify({"error": str(err)}), 500


if __name__ == '__main__':
    app.run(debug=True)


