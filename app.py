from flask import Flask, render_template

app = Flask(__name__)

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
