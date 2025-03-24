from flask import session, jsonify, request
from database import connect

def init_derivery_routes(app):
    # Route to fetch deliveries
    @app.route('/deliveries', methods=['GET'])
    def get_deliveries():
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"error": "User not logged in"}), 401

        try:
            conn = connect()
            cursor = conn.cursor()
            query = """
            SELECT *
            FROM derivery_details 
            WHERE derivery_status = 'NOT DELIVERED' AND order_id IS NOT NULL
            """
            cursor.execute(query)
            deliveries = cursor.fetchall()
            conn.close()
            return jsonify(deliveries)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # Route to fetch "Requests Sent" (status = Request Sent)
    @app.route('/requests', methods=['GET'])
    def get_requests():
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"error": "User not logged in"}), 401

        try:
            conn = connect()
            cursor = conn.cursor()
            query = """
            SELECT *
            FROM derivery_details 
            WHERE derivery_status = 'REQUEST SENT' AND user_id = %s
            """
            cursor.execute(query, (user_id,))
            requests = cursor.fetchall()
            conn.close()
            return jsonify(requests)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # Route to fetch "Accepted Deliveries" (status = Accepted)
    @app.route('/accepted', methods=['GET'])
    def get_accepted():
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"error": "User not logged in"}), 401

        try:
            conn = connect()
            cursor = conn.cursor()
            query = """
            SELECT *
            FROM derivery_details 
            WHERE derivery_status = 'ACCEPTED' AND user_id = %s
            """
            cursor.execute(query, (user_id,))
            accepted_deliveries = cursor.fetchall()
            conn.close()
            return jsonify(accepted_deliveries)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # Route to fetch "Picked Packages" (status = Picked)
    @app.route('/picked', methods=['GET'])
    def get_picked():
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"error": "User not logged in"}), 401

        try:
            conn = connect()
            cursor = conn.cursor()
            query = """
            SELECT *
            FROM derivery_details 
            WHERE derivery_status = 'PICKED' AND user_id = %s
            """
            cursor.execute(query, (user_id,))
            picked_deliveries = cursor.fetchall()
            conn.close()
            return jsonify(picked_deliveries)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # Route to fetch "Delivered Packages" (status = Delivered)
    @app.route('/delivered', methods=['GET'])
    def get_delivered():
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"error": "User not logged in"}), 401

        try:
            conn = connect()
            cursor = conn.cursor()
            query = """
            SELECT *
            FROM derivery_details 
            WHERE derivery_status = 'DELIVERED' AND user_id = %s
            """
            cursor.execute(query, (user_id,))
            delivered_packages = cursor.fetchall()
            conn.close()
            return jsonify(delivered_packages)
        except Exception as e:
            return jsonify({"error": str(e)}), 500


    # Function to mark a package as delivered
    @app.route('/mark-status/<string:status>/<int:package_id>', methods=['POST'])
    def mark_status(status, package_id):
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"error": "User not logged in"}), 401

        try:
            conn = connect()
            cursor = conn.cursor()

            # Update the delivery status based on the status value passed
            update_query = """
            UPDATE derivery_details 
            SET derivery_status = %s 
            WHERE derivery_id = %s
            """
            cursor.execute(update_query, (status, package_id))
            conn.commit()
            conn.close()

            return jsonify({"message": f"Package status updated to {status}"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
            

    @app.route('/delivery-status-counts', methods=['GET'])
    def get_delivery_status_counts():
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"error": "User not logged in"}), 401

        try:
            conn = connect()
            cursor = conn.cursor()

            # Fetch count of "Requests Sent"
            query_requests = """
            SELECT COUNT(*) FROM derivery_details 
            WHERE derivery_status = 'REQUEST SENT' AND user_id = %s
            """
            cursor.execute(query_requests, (user_id,))
            total_requests_sent = cursor.fetchone()[0]

            # Fetch count of "Deliveries" (NOT DELIVERED)
            query_deliveries = """
            SELECT COUNT(*) FROM derivery_details 
            WHERE derivery_status = 'NOT DELIVERED' AND user_id = %s
            """
            cursor.execute(query_deliveries, (user_id,))
            total_deliveries = cursor.fetchone()[0]

            # Fetch count of "Accepted Deliveries"
            query_accepted = """
            SELECT COUNT(*) FROM derivery_details 
            WHERE derivery_status = 'ACCEPTED' AND user_id = %s
            """
            cursor.execute(query_accepted, (user_id,))
            total_accepted = cursor.fetchone()[0]

            # Fetch count of "Picked Deliveries"
            query_picked = """
            SELECT COUNT(*) FROM derivery_details 
            WHERE derivery_status = 'PICKED' AND user_id = %s
            """
            cursor.execute(query_picked, (user_id,))
            total_picked = cursor.fetchone()[0]

            conn.close()

            return jsonify({
                "totalRequestsSent": total_requests_sent,
                "totalDeliveries": total_deliveries,
                "totalAccepted": total_accepted,
                "totalPicked": total_picked
            }), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500