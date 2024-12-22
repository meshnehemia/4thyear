from flask import Flask, render_template
import mysql.connector
from mysql.connector import errorcode

app = Flask(__name__)

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

# Route to serve category cover images
@app.route('/category_cover/<int:category_id>')
def category_cover(category_id):
    print("testinh")
    return "testing"
    conn = connect()
    if conn is None:
        return "Database connection failed", 500

    try:
        cursor = conn.cursor()
        query = '''
            SELECT category_cover FROM d_categories WHERE category_id = %s
        '''
        cursor.execute(query, (category_id,))
        result = cursor.fetchone()
        if result:
            return "my name"
            return send_file(BytesIO(result[0]), mimetype='image/jpeg')  # Adjust mimetype if necessary
        else:
            return "Image not found", 404
    finally:
        conn.close()

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

if __name__ == '__main__':
    app.run(debug=True)
