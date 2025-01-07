from flask import Flask, render_template, send_file, Response, jsonify, request, redirect, url_for, session
from facedetection import gen_frames, detect_face , genandface
from deepface import DeepFace
from datetime import datetime
import io
import base64
import numpy as np
import cv2
import hashlib
from database import connect
import pymysql
import os
import json
from past7daysales import get_sales_past_7_days , get_sales_online_vs_instore,get_sales_last_8_hours,get_total_sales_per_week,get_top_sold_products, monthlyprofit,get_order_status_data

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
        return jsonify({"message": "Incorrect password."}), 401

    # Decode the captured image (base64 to binary)
    try:
        image_data = base64.b64decode(captured_image_data.split(',')[1])  # Remove the data URL prefix
        nparr = np.frombuffer(image_data, np.uint8)  # Convert byte data to numpy array
        captured_image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)  # Decode into an image format OpenCV can handle
    except Exception as e:
        return jsonify({"message": "Error processing image."}), 500

    # Check if the user has a stored face image in the database
    if not stored_face_image:
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
            session['email'] = em
            session['phone_number'] = phone_number
            session['transact'] = "not verified";
            return jsonify({"message": "Login successful.","user_id": session['user_id'], "username": session['username']}), 200
        else:
            return jsonify({"message": "Face does not match."}), 403
    except Exception as e:
        return jsonify({"message": "Error comparing faces."}), 500
@app.route('/signup')
def signup():
    return render_template('signup.html') 

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
    session['user_id'] = 1;
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

        return jsonify({'message': 'no face detected', 'image': image_filename}), 400

    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 400



@app.route('/transact')
def transaction():
    return render_template('transactions.html')

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
        session['user_id']=6;
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
def manageworkers():
    return render_template('workersmanagement.html')

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


if __name__ == '__main__':
    app.run(debug=True)
