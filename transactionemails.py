from database import connect
from emailsendingHtml import sendEmail
def generate_order_receipt(email,user_id,otp):
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
            return "No items in cart to generate a receipt", 400

        # Step 2: Build the HTML table for the receipt
        html_content = """
            <html>
            <head>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        background-color: #F9F9F9;
                    }
                    .header {
                        background-color: #0047AB; /* Navy Blue */
                        color: white;
                        padding: 10px;
                        text-align: center;
                        font-size: 26px;
                        font-weight: bold;
                    }
                    h2 {
                        color: #FBBF24; /* Vibrant Yellow */
                    }
                    p {
                        font-size: 16px;
                        color: #333;
                    }
                    .receipt-table {
                        width: 100%;
                        border-collapse: collapse;
                        margin-top: 20px;
                        background-color: #FFFFFF;
                        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                    }
                    .receipt-table th {
                        background-color: #0047AB; /* Navy Blue */
                        color: white;
                        padding: 12px;
                    }
                    .receipt-table td {
                        padding: 10px;
                        border: 1px solid #DDD;
                    }
                    .receipt-table tr:nth-child(even) {
                        background-color: #F3F4F6; /* Light grey for alternating rows */
                    }
                    .receipt-table tr:hover {
                        background-color: #E2E8F0; /* Slight hover effect */
                    }
                    .footer {
                        margin-top: 20px;
                        text-align: center;
                        font-size: 14px;
                        color: #777;
                    }
                    .total-row {
                        background-color: #FBBF24; /* Yellow for the total row */
                        color: #0047AB; /* Dark Blue text */
                        font-weight: bold;
                    }
                </style>
            </head>
            <body>
                <div class="header">Intelligent Supermarket Management System</div>
                <h2>Order Receipt</h2>
                <p>Thank you for trusting us. We received your purchase request. Please enter the code: <strong>""" +otp + """</strong>.</p>

                <table class="receipt-table">
                    <tr>
                        <th>Product Name</th>
                        <th>Quantity</th>
                        <th>Unit Price</th>
                        <th>Total Cost</th>
                    </tr>
            """

        total_cost = 0

        # Step 3: Loop through the cart items and build the table rows
        for item in cart_items:
            product_id = item[0]
            number_of_items = item[1]

            # Get product name and price from Products table
            query_product = '''SELECT product_name, price FROM Products WHERE product_id = %s'''
            cursor.execute(query_product, (product_id,))
            product = cursor.fetchone()
            product_name = product[0]
            unit_price = float(product[1])
            item_total = unit_price * float(number_of_items)

            # Add the product to the HTML table
            html_content += f"""
                <tr>
                    <td>{product_name}</td>
                    <td>{number_of_items}</td>
                    <td>${unit_price:.2f}</td>
                    <td>${item_total:.2f}</td>
                </tr>
            """

            total_cost += item_total

        # Step 4: Add the total cost to the table
        html_content += f"""
                <tr class="total-row">
                    <td colspan="3" style="text-align: right;">Total</td>
                    <td>ksh {total_cost:.2f}</td>
                </tr>
            </table>

            <div class="footer">
                Intelligent Supermarket Management System | &copy; 2025 All rights reserved
            </div>
        </body>
        </html>
        """
        sendEmail(email, "purchase confirmation",html_content)
        # Return the HTML content as the order receipt
        return True

    except Exception as e:
        conn.rollback()  # Rollback in case of error
        print(str(e))
        return "Error generating receipt", 500
    finally:
        conn.close()
    