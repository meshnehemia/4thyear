from flask import jsonify, request
from PIL import Image
from database import connect
from flask import jsonify
from datetime import datetime

def mytasks():
    conn = connect()
    cursor = conn.cursor()
    worker_id = 1
    query_tasks = """
    SELECT 
        (SELECT COUNT(*) FROM list_of_tasks WHERE status = 'completed' AND staff_id = %s) AS completed_tasks,
        (SELECT COUNT(*) FROM list_of_tasks WHERE status = 'pending' AND staff_id = %s) AS pending_tasks,
        (SELECT COUNT(*) FROM list_of_tasks WHERE status = 'assigned' AND staff_id = %s) AS assigned_tasks
    """
    cursor.execute(query_tasks, (worker_id,worker_id,worker_id))

    task_counts = cursor.fetchone()

    # Query for orders
    query_orders = """
    SELECT 
        (SELECT COUNT(*) FROM orders WHERE status = 'completed' AND assigned_worker =%s) AS completed_orders,
        (SELECT COUNT(*) FROM orders WHERE status = 'pending' AND assigned_worker = %s) AS pending_orders,
        (SELECT COUNT(*) FROM orders WHERE status = 'assigned' AND assigned_worker = %s) AS assigned_orders
    """
    cursor.execute(query_orders,(worker_id,worker_id,worker_id))
    order_counts = cursor.fetchone()

    # Return results as JSON
    result = {
        'tasks': {
            'completed': task_counts[0] + order_counts[0],
            'pending': task_counts[1] + order_counts[1],
            'assigned': task_counts[2] + order_counts[2]
        }
    }

    return result
# def available_tasks():
#     tasks = mongo.db.tasks.find({"status": "available"})
#     return dumps(tasks), 200

# # Route to get assigned tasks for a worker
# def assigned_tasks():
#     worker_id = request.args.get('workerId')
#     tasks = mongo.db.tasks.find({"workerId": worker_id, "status": "assigned"})
#     return dumps(tasks), 200

# # Route to mark a task as completed
# def mark_task_done():
#     data = request.json
#     task_id = data.get('taskId')
#     mongo.db.tasks.update_one({"taskId": task_id}, {"$set": {"status": "completed"}})
#     return jsonify({"message": "Task marked as completed"}), 200

# def process_payment():
#     data = request.json
#     email = data.get('email')
#     phone = data.get('phone')
#     video_data = data.get('videoData')
#     image_data = base64.b64decode(video_data.split(',')[1])
#     image = Image.open(io.BytesIO(image_data))
#     image.save('video_frame.jpg')
#     processed_text = f"Processed video for email: {email}, phone: {phone}"
#     return jsonify({"message": processed_text}), 200

def completedtasks():
    staff_id = 1
    conn = connect()
    cursor = conn.cursor()
    query_with_staff = "SELECT * FROM list_of_tasks WHERE status = 'completed'  AND staff_id = %s"
    query_without_staff = "SELECT * FROM list_of_tasks t  JOIN staff s ON t.staff_id = s.staff_id WHERE t.status = 'completed' AND s.staff_id != %s"
    
    # Execute queries
    cursor.execute(query_with_staff, (staff_id,))
    results_with_staff = cursor.fetchall()
    
    cursor.execute(query_without_staff, (staff_id,))
    results_without_staff = cursor.fetchall()
    
    # Get the counts
    count_with_staff = len(results_with_staff)
    count_without_staff = len(results_without_staff)
    
    # Close the connection
    conn.close()
    
    return {
        "with_staff": results_with_staff,
        "without_staff": results_without_staff,
        "count_with_staff": count_with_staff,
        "count_without_staff": count_without_staff
    }

def completedorders():
    assigned_worker = 2
    conn = connect()
    cursor = conn.cursor()
    query_with_worker = """
        SELECT o.*, u.user_name as username, u.email as email, 
               u.phone_number AS phonenumber, u.full_name AS name
        FROM orders o
        JOIN users u ON o.client_id = u.user_id
        WHERE o.status = 'completed' AND o.assigned_worker = %s
    """

    # Query for orders without the specified assigned worker
    query_without_worker = """
        SELECT o.*, u.user_name as username, u.email as email, 
               u.phone_number AS phonenumber, u.full_name AS name
               ,st.*
        FROM orders o
        JOIN users u ON o.client_id = u.user_id
        Join staff st ON o.assigned_worker = st.staff_id
        WHERE o.status = 'completed' AND o.assigned_worker != %s
    """
    
    cursor.execute(query_with_worker, (assigned_worker,))
    orders_with_worker = cursor.fetchall()
    
    cursor.execute(query_without_worker,(assigned_worker,))
    orders_without_worker = cursor.fetchall()

    # Fetch orders without assigned worker (if no worker assigned)
    cursor.execute(query_without_worker,(assigned_worker,))
    orders_without_worker = cursor.fetchall()

    orders_with_worker = [dict(zip([column[0] for column in cursor.description], order)) for order in orders_with_worker]
    orders_without_worker = [dict(zip([column[0] for column in cursor.description], order)) for order in orders_without_worker]

    for order in orders_with_worker:
        order_id = order['order_id']  # Assuming order_id is in the first column of the result
        order['order_info'] = orderdetails(order_id)
    
    for order in orders_without_worker:
        order_id = order['order_id']  # Assuming order_id is in the first column of the result
        order['order_info'] = orderdetails(order_id)

    count_with_worker = len(orders_with_worker)
    count_without_worker = len(orders_without_worker)


    # Close the database connection
    conn.close()
    return {
        "orders_with_worker": orders_with_worker,
        "orders_without_worker": orders_without_worker,
        "count_with_worker": count_with_worker,
        "count_without_worker": count_without_worker
    }

def orderdetails(order_id):
    conn = connect()
    cursor = conn.cursor()
    query = """
        SELECT 
            o.*,  
            oi.number_of_items,
            (oi.cost * oi.number_of_items) AS producttotal,
            p.*
        FROM orders o
        JOIN ordersales oi ON o.order_id = oi.order_id
        JOIN products p ON oi.product_id = p.product_id
        WHERE o.order_id = %s;
    """
    cursor.execute(query, (order_id,))
    order_details = cursor.fetchall()
    total_sum = sum(float(item[6]) for item in order_details)
    conn.close()
    return {
        "order_details": order_details,
        "total_sum": total_sum
    }


def availableorders():
    conn = connect()
    cursor = conn.cursor()
    # Query for orders without the specified assigned worker
    tasks = """
        SELECT o.*, u.user_name as username, u.email as email, 
               u.phone_number AS phonenumber, u.full_name AS name
        FROM orders o
        JOIN users u ON o.client_id = u.user_id
        WHERE o.status = 'pending' or o.status = 'Pending'
    """

    cursor.execute(tasks)
    orders = cursor.fetchall()
    available_orders = [dict(zip([column[0] for column in cursor.description], order)) for order in orders]

    for order in available_orders:
        order_id = order['order_id']  # Assuming order_id is in the first column of the result
        order['order_info'] = orderdetails(order_id)

    count_available_orders = len(available_orders)


    # Close the database connection
    conn.close()
    return {
        "available_counts": count_available_orders,
        "available_orders": available_orders
    }

def availabletasks():
    conn = connect()
    cursor = conn.cursor()
    availabletasks = "SELECT * FROM list_of_tasks WHERE status = 'not assigned'"
    
    # Execute queries
    cursor.execute(availabletasks)
    availabletasks = cursor.fetchall()

    # Get the counts
    counts_of_orders = len(availabletasks)
    
    # Close the connection
    conn.close()
    
    return {
        "availabletasks": availabletasks,
        "counts_of_orders": counts_of_orders,
    }

def assignedorders():
    staff_id = 1
    conn = connect()
    cursor = conn.cursor()
    # Query for orders without the specified assigned worker
    tasks = """
         SELECT o.*, u.user_name as username, u.email as email, 
               u.phone_number AS phonenumber, u.full_name AS name
        FROM orders o
        JOIN users u ON o.client_id = u.user_id
        WHERE o.status = 'assigned' AND o.assigned_worker = %s
    """

    cursor.execute(tasks,(staff_id,))
    orders = cursor.fetchall()
    available_orders = [dict(zip([column[0] for column in cursor.description], order)) for order in orders]

    for order in available_orders:
        order_id = order['order_id']  # Assuming order_id is in the first column of the result
        order['order_info'] = orderdetails(order_id)

    count_available_orders = len(available_orders)


    # Close the database connection
    conn.close()
    return {
        "available_counts": count_available_orders,
        "available_orders": available_orders
    }

def assignedtasks():
    staff_id = 1
    conn = connect()
    cursor = conn.cursor()
    availabletasks = "SELECT * FROM list_of_tasks WHERE status = 'assigned' and staff_id = %s"
    
    # Execute queries
    cursor.execute(availabletasks, (staff_id,))
    availabletasks = cursor.fetchall()

    # Get the counts
    counts_of_orders = len(availabletasks)
    
    # Close the connection
    conn.close()
    
    return {
        "availabletasks": availabletasks,
        "counts_of_orders": counts_of_orders,
    }

def assigntask(task_id):
    staff_id = 1
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("UPDATE list_of_tasks SET staff_id = %s, status = 'assigned' WHERE task_id = %s", (staff_id, task_id))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Task assigned successfully'}), 200

def completetask(task_id):
    date = datetime.now()
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("UPDATE list_of_tasks SET date_completed = %s, status = 'completed' WHERE task_id = %s", (date, task_id))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Task completed successfully'}), 200