import mysql.connector
from mysql.connector import errorcode
from datetime import datetime, timedelta
from database import connect

# Function to get the total sales for the past 7 days
def get_sales_past_7_days():
        conn = connect()
        cursor = conn.cursor()
        current_date = datetime.today()
        sales_last_7_days = []
        days_labels = []
        for i in range(7):
            day_date = current_date - timedelta(days=i)
            day_str = day_date.strftime('%Y-%m-%d')  # Format the date as 'YYYY-MM-DD'
            
            # Query to fetch the total sales for the current day
            query = """
                SELECT SUM(amount_bought) 
                FROM sales 
                WHERE DATE(sale_date) = %s;
            """
            cursor.execute(query, (day_str,))
            result = cursor.fetchone()
            
            # If there are no sales for the day, the result will be None, so set it to 0
            total_sales = result[0] if result[0] is not None else 0
            
            # Append the total sales for the day to the sales_last_7_days array
            sales_last_7_days.append(total_sales)
            days_labels.append((current_date - timedelta(days=i)).strftime('%A'))  # Day name (e.g., "Monday")

        # Reverse the order of the data to make today's sales last
        sales_last_7_days.reverse()
        days_labels.reverse()

        # Format the data for the chart
        chart_data = {
            'labels': days_labels,
            'datasets': [{
                'label': 'Total Sales for the Past 7 Days',
                'data': sales_last_7_days,
                'borderColor': '#42a5f5',
                'backgroundColor': 'rgba(66, 165, 245, 0.2)',
                'fill': True
            }]
        }

        return chart_data


def get_sales_online_vs_instore():
        conn = connect()
        cursor = conn.cursor()
        current_date = datetime.today()
        # Initialize sales data for Online and In-Store
        online_sales = 0
        instore_sales = 0

        # Loop through the past 7 days and calculate the sales for each type
        for i in range(7):
            day_date = current_date - timedelta(days=i)
            day_str = day_date.strftime('%Y-%m-%d')

            # Query for Online Sales
            online_query = """
                SELECT SUM(amount_bought)
                FROM sales
                WHERE DATE(sale_date) = %s AND sale_type = 'Online';
            """
            cursor.execute(online_query, (day_str,))
            online_result = cursor.fetchone()
            online_sales += online_result[0] if online_result[0] is not None else 0

            # Query for In-Store Sales
            instore_query = """
                SELECT SUM(amount_bought)
                FROM sales
                WHERE DATE(sale_date) = %s AND sale_type = 'In-Store';
            """
            cursor.execute(instore_query, (day_str,))
            instore_result = cursor.fetchone()
            instore_sales += instore_result[0] if instore_result[0] is not None else 0

        # Prepare the data in a format suitable for the front-end chart
        sales_data = {
            'labels': ['Online', 'In-Store'],
            'datasets': [{
                'data': [online_sales, instore_sales],
                'backgroundColor': ['#f44336', '#4caf50']
            }]
        }

        return sales_data


def get_sales_last_8_hours():
        conn = connect()
        cursor = conn.cursor()
        current_time = datetime.now()

        # Prepare the list for hourly sales data (initialize to 0 for 8 hours)
        online_sales_per_hour = [0] * 8
        instore_sales_per_hour = [0] * 8

        # Loop through the past 8 hours and calculate the sales for each type
        for i in range(8):
            hour_time = current_time - timedelta(hours=i)
            hour_str = hour_time.strftime('%Y-%m-%d %H:00:00')

            # Query for Online Sales
            online_query = """
                SELECT SUM(amount_bought)
                FROM sales
                WHERE sale_date BETWEEN %s AND %s AND sale_type = 'Online';
            """
            next_hour_time = hour_time + timedelta(hours=1)
            cursor.execute(online_query, (hour_str, next_hour_time.strftime('%Y-%m-%d %H:00:00')))
            online_result = cursor.fetchone()
            online_sales_per_hour[i] = online_result[0] if online_result[0] is not None else 0

            # Query for In-Store Sales
            instore_query = """
                SELECT SUM(amount_bought)
                FROM sales
                WHERE sale_date BETWEEN %s AND %s AND sale_type = 'In-Store';
            """
            cursor.execute(instore_query, (hour_str, next_hour_time.strftime('%Y-%m-%d %H:00:00')))
            instore_result = cursor.fetchone()
            instore_sales_per_hour[i] = instore_result[0] if instore_result[0] is not None else 0

        # Reverse the data so the latest hour appears last
        online_sales_per_hour.reverse()
        instore_sales_per_hour.reverse()

        # Prepare the labels and datasets
        sales_data = {
            'labels': [f"{(current_time - timedelta(hours=i)).strftime('%I%p')}" for i in range(8)][::-1],  # Reverse the labels
            'datasets': [{
                'label': 'Online Sales',
                'data': online_sales_per_hour,
                'backgroundColor': '#42a5f5',
                'stack': 'stack1'
            }, {
                'label': 'On-Shelf Sales',
                'data': instore_sales_per_hour,
                'backgroundColor': '#66bb6a',
                'stack': 'stack1'
            }]
        }

        return sales_data

def get_total_sales_per_week():
        conn = connect()
        cursor = conn.cursor()

        current_date = datetime.now()
        weekly_sales_online = []
        weekly_sales_instore = []
        week_labels = []

        # Loop through the last 4 weeks (current week is last)
        for i in range(4):
            # Calculate the start of the week (Monday) for the current week and the previous ones
            # Get the current week's start (Monday) and end (Sunday)
            week_start = current_date - timedelta(days=current_date.weekday()) - timedelta(weeks=i)
            week_end = week_start + timedelta(days=6)  # Sunday of the same week

            # Query for Online Sales in the week range
            online_query = """
                SELECT SUM(amount_bought)
                FROM sales
                WHERE sale_date BETWEEN %s AND %s AND sale_type = 'Online';
            """
            cursor.execute(online_query, (week_start, week_end))
            online_sales = cursor.fetchone()
            weekly_sales_online.append(online_sales[0] if online_sales[0] else 0)

            # Query for In-Store Sales in the week range
            instore_query = """
                SELECT SUM(amount_bought)
                FROM sales
                WHERE sale_date BETWEEN %s AND %s AND sale_type = 'In-Store';
            """
            cursor.execute(instore_query, (week_start, week_end))
            instore_sales = cursor.fetchone()
            weekly_sales_instore.append(instore_sales[0] if instore_sales[0] else 0)

            # Add Week Labels (starting from Week 1)
            week_labels.append(f"Week {i+1}")

        # Reverse the lists to have the current week as the last
        weekly_sales_online.reverse()
        weekly_sales_instore.reverse()
        week_labels.reverse()

        # Calculate total sales per week
        total_sales_per_week = [online + instore for online, instore in zip(weekly_sales_online, weekly_sales_instore)]

        # Prepare the dataset for the chart
        weekly_sales_data = {
            'labels': week_labels,  # Week 1 to Week 4 labels (current week last)
            'datasets': [
                {
                    'label': 'Online Sales',
                    'data': weekly_sales_online,
                    'backgroundColor': '#42a5f5'
                },
                {
                    'label': 'On-Shelf Sales',
                    'data': weekly_sales_instore,
                    'backgroundColor': '#66bb6a'
                },
                {
                    'label': 'Total Sales',
                    'data': total_sales_per_week,
                    'backgroundColor': '#ffeb3b'  # Yellow for total sales
                }
            ]
        }

        return weekly_sales_data

def get_top_sold_products():
        conn = connect()
        cursor = conn.cursor()

        cursor = conn.cursor()

        query = """
            SELECT p.product_name,
                   COUNT(s.sale_id) AS number_of_occurrences,
                   SUM(s.amount_bought) AS total_sales,
                   SUM(s.profit_made) AS total_profit
            FROM sales s
            JOIN products p ON s.product_id = p.product_id
            WHERE s.sale_date >= CURDATE() - INTERVAL 30 DAY
            GROUP BY s.product_id
            ORDER BY total_sales DESC
            LIMIT 10;
        """
        cursor.execute(query)
        results = cursor.fetchall()

        top_sold_products = []
        for row in results:
            top_sold_products.append({
                'product_name': row[0],
                'number_of_occurrences': row[1],
                'total_sales': row[2],
                'total_profit': row[3]
            })

        return top_sold_products

def monthlyprofit():
    conn = connect()
    cursor = conn.cursor()
    current_month = datetime.now().month
    current_year = datetime.now().year

    # Query to get the total profits for each of the last 12 months starting from February of the last year
    query = '''
        SELECT 
            MONTH(sale_date) AS month, 
            YEAR(sale_date) AS year, 
            SUM(profit_made) AS total_profit
        FROM sales
        WHERE sale_date >= CURDATE() - INTERVAL 1 YEAR
        GROUP BY YEAR(sale_date), MONTH(sale_date)
        ORDER BY YEAR(sale_date) DESC, MONTH(sale_date) DESC
    '''
    cursor.execute(query)
    results = cursor.fetchall()

    # Prepare data for chart
    monthly_profits = [0] * 12  # List to store profit for each month
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    # Loop through the result and store profit for each month
    for row in results:
        month = row[0] - 1  # Adjust the month to 0-based index (Jan = 0, Feb = 1, ...)
        monthly_profits[month] = row[2]  # Store the profit for that month

    # Re-arranging to start from February of the previous year to the current month (January of current year)
    if current_month == 1:
        months_reversed = months[1:] + months[:1]  # Starts from February and adds January at the end
        monthly_profits_reversed = monthly_profits[1:] + monthly_profits[:1]
    else:
        months_reversed = months[current_month:] + months[:current_month]
        monthly_profits_reversed = monthly_profits[current_month:] + monthly_profits[:current_month]

    # Current month profit (for January, it should return the profit for January)
    current_month_profit = monthly_profits_reversed[current_month - 1]

    # Return the formatted data
    return {
        "monthly_profits": monthly_profits_reversed,
        "current_month_profit": current_month_profit,
        "months": months_reversed,
    }


def get_order_status_data():
    conn = connect()
    cursor = conn.cursor()
    query = """
    SELECT 
        SUM(CASE WHEN status = 'Pending' THEN 1 ELSE 0 END) AS pending,
        SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) AS completed,
        SUM(CASE WHEN status = 'Assigned' THEN 1 ELSE 0 END) AS assigned
    FROM orders;
    """

    cursor.execute(query)
    result = cursor.fetchone()
    print(result[0],result[1],result[2])

    return {
        'pending': result[0],
        'completed': result[1],
        'assigned': result[2]
    }