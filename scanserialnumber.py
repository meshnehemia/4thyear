import cv2
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"  # Windows example
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Could not open webcam.")
    exit()
words_to_check = ["1224132614281530", "mine","project proposal 2024"]
while True:
    ret, frame = cap.read()
    if ret:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        text = pytesseract.image_to_string(gray)
        cv2.imshow("Real-Time Text Detection", frame)
        print('words in the file  : ', text )
        found_words = []
        for word in words_to_check:
            if word.lower() in text.lower():
                found_words.append(word)
        if found_words:
            print("Yes, words found:", found_words)
        else:
            print("Words not found")
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
cap.release()
cv2.destroyAllWindows()
