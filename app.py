from flask import Flask, render_template, send_file, Response, jsonify, request, flash, redirect, url_for
from facedetection import gen_frames,detect_face
from datetime import datetime
import io
import base64
import numpy as np
import cv2
import hashlib
import mysql.connector
from database import connect
from mysql.connector import errorcode
from flask_sqlalchemy import SQLAlchemy
import pymysql
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

app = Flask(__name__)
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

@app.route('/cart')
def cart():
    return render_template('cart.html')

@app.route('/paymentdetails')
def paymentdetails():
    return render_template('paymentdetails.html')

@app.route('/shop')
def shop():
    return render_template('shop.html')

@app.route('/productdetails')
def details():
    return render_template('detail.html')

@app.route('/contant')
def contact():
    return render_template('contact.html')

@app.route('/login')
def login():
    return render_template('signin.html')

@app.route('/signup')
def signup():
    return render_template('signup.html') 
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


if __name__ == '__main__':
    app.run(debug=True)
