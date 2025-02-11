import cv2
import numpy as np
from scipy.spatial import distance as dist
import facedetection as fc
import database as db
import numpy as np
from deepface import DeepFace
# Initialize the camera
cap = cv2.VideoCapture(0)

# A list to hold trackers for each object
trackers = []
objects = []  # List to store objects with their names, prices, and trackers

# Number of frames before an object is considered "sold" if not detected
max_missed_frames = 5

# Function to calculate the Euclidean distance between two points
def calculate_distance(p1, p2):
    return dist.euclidean(p1, p2)

# Function to select a new object
def select_new_object(frame):
    initBB = cv2.selectROI("Object Tracking", frame, fromCenter=False, showCrosshair=True)

    if initBB and initBB != (0, 0, 0, 0):
        name = input("Enter the name of the object: ")
        price = input("Enter the price of the object: ")

        tracker = cv2.TrackerCSRT_create()  # Create a new tracker
        tracker.init(frame, initBB)  # Initialize it with the selected bounding box
        trackers.append(tracker)  # Add the tracker to the list

        centroid = (initBB[0] + initBB[2] // 2, initBB[1] + initBB[3] // 2)

        objects.append({
            'name': name,
            'price': price,
            'tracker': tracker,
            'initBB': initBB,
            'prev_centroid': centroid,
            'current_centroid': centroid,
            'sold': False,  # Flag to indicate if the item has been sold
            'returned': False,  # Flag to indicate if the item has returned
            'missed_frames': 0  # To count the number of missed frames
        })

while True:
    ret, frame = cap.read()
    if not ret:
        break
    # Assuming `frame` is the image where the face is being detected
    if fc.detect_face(frame):
        connection = db.connect()
        cursor = connection.cursor()

        # Get all user faces from the database (user_id and face image)
        cursor.execute("SELECT user_id, face_id FROM users")
        stored_faces = cursor.fetchall()

        # Use DeepFace to extract faces from the frame
        detected_faces = DeepFace.extract_faces(frame, detector_backend='opencv', enforce_detection=False)
        
        for face in detected_faces:
            # Get facial area coordinates from the detected face
            x, y, w, h = face['facial_area']['x'], face['facial_area']['y'], face['facial_area']['w'], face['facial_area']['h']

            # Extract the face region from the frame for comparison
            captured_image = frame[y:y+h, x:x+w]

            # Variable to hold the match result
            recognized = False
            name = "Not Recognized"

            # Loop through stored faces in the database to compare each
            for user_id, face_id in stored_faces:
                # Check if face_id is BLOB or path to image
                if isinstance(face_id, bytes):  # Handle BLOB data (if the image is stored as a BLOB)
                    stored_face_image = np.frombuffer(face_id, np.uint8)  # Convert BLOB to numpy array
                    stored_face_image = cv2.imdecode(stored_face_image, cv2.IMREAD_COLOR)  # Decode image

                    try:
                        # Perform face verification between the captured face and stored face
                        result = DeepFace.verify(captured_image, stored_face_image)

                        if result['verified']:
                            name = f"User {user_id}"
                            recognized = True
                            break  # If a match is found, stop checking further

                    except Exception as e:
                        print(f"Error verifying face for user {user_id}: {e}")

                else:  # If face_id is a path to the image
                    stored_image_path = face_id  # Modify this according to your database storage logic
                    try:
                        # Perform face verification between the captured and stored face
                        result = DeepFace.verify(captured_image, stored_image_path)

                        if result['verified']:
                            name = f"User {user_id}"
                            recognized = True
                            break  # If a match is found, stop checking further

                    except Exception as e:
                        print(f"Error verifying face for user {user_id}: {e}")

            # Draw rectangle around the detected face and display the name
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)  # Green rectangle
            cv2.putText(frame, name, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
    else:
        print("No faces detected.")
    for i, obj in enumerate(objects):
        # If object is already sold and not returned, skip it
        if obj['sold'] and not obj['returned']:
            for face in detected_faces:
                # Get facial area coordinates from the detected face
                x, y, w, h = face['facial_area']['x'], face['facial_area']['y'], face['facial_area']['w'], face['facial_area']['h']

                # Draw rectangle around the detected face
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                # Extract the face region from the frame for comparison
                captured_image = frame[y:y+h, x:x+w]

                # Perform face verification between the captured and stored face
                result = DeepFace.verify(captured_image, stored_face_image)
            break

        # Update each tracker
        success, newbox = obj['tracker'].update(frame)

        if success:
            (x, y, w, h) = [int(v) for v in newbox]

            # Update the current centroid
            obj['current_centroid'] = (x + w // 2, y + h // 2)

            # Draw the bounding box
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # Display the name, price, and location of the object
            cv2.putText(frame, f"{obj['name']} (${obj['price']})", (x, y - 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.putText(frame, f"Location: ({x}, {y})", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            # Calculate the distance moved if the previous centroid exists
            if obj['prev_centroid'] is not None:
                distance_moved = calculate_distance(obj['prev_centroid'], obj['current_centroid'])
                cv2.putText(frame, f"Moved: {distance_moved:.2f} px", (x, y + h + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

            # Update the previous centroid
            obj['prev_centroid'] = obj['current_centroid']

            # If the object was marked as "sold" but has reappeared, mark it as "returned"
            if obj['sold']:
                obj['returned'] = True
                obj['sold'] = False  # Reset the sold flag
                obj['missed_frames'] = 0  # Reset missed frames counter
                print(f"Object '{obj['name']}' has returned!")
                cv2.putText(frame, f"{obj['name']} is RETURNED", (50, 50 + i * 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        else:
            # Tracker failed to find the object, increment missed frames
            obj['missed_frames'] += 1

            # If the object has been missed for too long, mark it as sold
            if obj['missed_frames'] >= max_missed_frames and not obj['sold']:
                obj['sold'] = True
                obj['returned'] = False  # Reset returned flag
                print(f"Object '{obj['name']}' is sold (out of frame).")
                cv2.putText(frame, f"{obj['name']} is SOLD", (50, 50 + i * 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

    # Display the instructions to select new objects
    cv2.putText(frame, "Press 's' to select new object", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(frame, "Press 'q' to quit", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    # Display the frame
    cv2.imshow("Object Tracking", frame)

    key = cv2.waitKey(1) & 0xFF

    if key == ord('s'):  # Press 's' to select new objects
        select_new_object(frame)

    elif key == ord('q'):  # Press 'q' to quit
        break

# Release the camera and close all windows
cap.release()
cv2.destroyAllWindows()
