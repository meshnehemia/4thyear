from flask import Flask, render_template, send_file , Response
from facedetection import gen_frames
import io
import mysql.connector
from mysql.connector import errorcode

app = Flask(__name__)
#categories fetch 
#connect to database
def connect():
    try:
        conn = mysql.connector.connect(
            host="127.0.0.1",  # e.g., 'localhost' or '127.0.0.1'
            user="root",  # your MySQL username
            password="",  # your MySQL password
            database="supermarket"  # your database name
        )
        return conn
    except mysql.connector.Error as err:
        return None

# Function to fetch categories and their appearance counts
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

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(debug=True)
