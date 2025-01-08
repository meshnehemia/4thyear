import cv2
import numpy as np
from deepface import DeepFace
from database import connect
def gen_frames():
    cap = cv2.VideoCapture(0)  # Capture video from webcam
    while True:
        success, frame = cap.read()
        if not success:
            break
        else:
            # Perform face detection using DeepFace
            try:
                detected_faces = DeepFace.extract_faces(frame, detector_backend='opencv', enforce_detection=False)
                for face in detected_faces:
                    x, y, w, h = face['facial_area']['x'], face['facial_area']['y'], face['facial_area']['w'], face['facial_area']['h']
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)  # Draw rectangle around faces
            except Exception as e:
                print("No face detected:", e)

            # Encode frame and send it back
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    cap.release()

def detect_face(img):
    try:
        detected_faces = DeepFace.extract_faces(img, enforce_detection=True)
        if detected_faces is not None:
            return True
        else:
            return False
    except Exception as e:
        return False
    

def genandface(id):
    connection = connect()
    cursor = connection.cursor()
    cursor.execute("SELECT * from tinitiation where user_id = %s ",(id,))
    if cursor.fetchone():
        cursor.execute('DELETE FROM tinitiation where user_id  = %s',(id,))
        connection.commit();
    insert_query = """
    INSERT INTO tinitiation (user_id, status)
    VALUES (%s, %s);
    """
    cursor.execute("SELECT face_id FROM users WHERE user_id = %s", (id,))
    stored_face_image = cursor.fetchone()


    if not stored_face_image:
        print("No face image found for this user.")
        return None

    # Decode the stored face image (assumed to be stored as a BLOB)
    stored_face_image = np.frombuffer(stored_face_image[0], np.uint8)  # Extract BLOB data
    stored_face_image = cv2.imdecode(stored_face_image, cv2.IMREAD_COLOR)  # Decode into OpenCV image format

    cap = cv2.VideoCapture(0)  # Capture video from webcam
    while True:
        success, frame = cap.read()
        if not success:
            break

        try:
            # Perform face detection using DeepFace
            detected_faces = DeepFace.extract_faces(frame, detector_backend='opencv', enforce_detection=False)

            for face in detected_faces:
                # Get facial area coordinates from the detected face
                x, y, w, h = face['facial_area']['x'], face['facial_area']['y'], face['facial_area']['w'], face['facial_area']['h']

                # Draw rectangle around the detected face
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                # Extract the face region from the frame for comparison
                captured_image = frame[y:y+h, x:x+w]

                # Perform face verification between the captured and stored face
                result = DeepFace.verify(captured_image, stored_face_image)

                if result["verified"]:
                    cursor.execute(insert_query, (id, "verified"))
                    connection.commit()
                    print("Face matched.")
                    cap.release()  # Stop the video feed once matched
                    cv2.destroyAllWindows()
                    ret, buffer = cv2.imencode('.jpg', captured_image)
                    frame = buffer.tobytes()
                    yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
                    return 

        except Exception as e:
            print(f"Face detection/verification error: {e}")
        # Encode frame for streaming
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        # Yield the encoded frame as a response for MJPEG streaming
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    # Release the webcam and close all windows when done
    cap.release()
    cv2.destroyAllWindows()
