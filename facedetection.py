import cv2
from deepface import DeepFace
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