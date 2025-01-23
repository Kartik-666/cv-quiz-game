import cv2
import cvzone
from cvzone.HandTrackingModule import HandDetector
import csv
import time

# Initialize HandDetector
detector = HandDetector(maxHands=1, detectionCon=0.8)

# Open webcam
cap = cv2.VideoCapture(0)
cap.set(3, 1280)  # Set width
cap.set(4, 720)   # Set height

# Class for MCQs
class MCQ:
    def __init__(self, data):
        self.question = data[0]
        self.op1 = data[1]
        self.op2 = data[2]
        self.op3 = data[3]
        self.op4 = data[4]
        self.ans = int(data[5])
        self.userAns = None  # User's answer
    
    def update(self, cursor, bboxs):
        for x, bbox in enumerate(bboxs):
            x1, y1, x2, y2 = bbox
            if x1 < cursor[0] < x2 and y1 < cursor[1] < y2:
                self.userAns = x + 1
                cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), cv2.FILLED)

# Load MCQs from CSV
pathCSV = "mcqs.csv"
with open(pathCSV, newline='\n') as f:
    reader = csv.reader(f)
    dataAll = list(reader)[1:]

# Initialize MCQ objects
mcqList = [MCQ(q) for q in dataAll]
print("Total MCQ Objects Created:", len(mcqList))

# Variables for question tracking
qNo = 0
qTotal = len(mcqList)
quizStarted = False  # Flag to check if the quiz has started
quizCompleted = False  # Flag to check if the quiz is completed

# Main Loop
while True:
    success, img = cap.read()
    if not success:
        print("Failed to capture frame from webcam")
        break
    img = cv2.flip(img, 1)
    # Detect hands
    hands, img = detector.findHands(img)

    if not quizStarted and not quizCompleted:
        # Show "Start Quiz" button
        img, startButton = cvzone.putTextRect(img, "Start Quiz", [500, 300], 2, 2, offset=50, border=5)

        # Check if hand clicks the "Start Quiz" button
        if hands:
            lmList = hands[0]['lmList']  # Get landmarks
            cursor = lmList[8][:2]  # Index fingertip position
            x1, y1, x2, y2 = startButton
            if x1 < cursor[0] < x2 and y1 < cursor[1] < y2:
                quizStarted = True  # Start the quiz
                time.sleep(0.4)  # Delay to avoid immediate interaction

    elif quizStarted and not quizCompleted:
        if qNo < qTotal:
            mcq = mcqList[qNo]

            # Display question and options
            img, bboxQ = cvzone.putTextRect(img, mcq.question, [100, 100], 2, 2, offset=50, border=5)
            img, bbox1 = cvzone.putTextRect(img, mcq.op1, [100, 250], 2, 2, offset=50, border=5)
            img, bbox2 = cvzone.putTextRect(img, mcq.op2, [400, 250], 2, 2, offset=50, border=5)
            img, bbox3 = cvzone.putTextRect(img, mcq.op3, [100, 400], 2, 2, offset=50, border=5)
            img, bbox4 = cvzone.putTextRect(img, mcq.op4, [400, 400], 2, 2, offset=50, border=5)

            # Check for hand actions
            if hands:
                lmList = hands[0]['lmList']  # Get landmarks
                cursor = lmList[8][:2]  # Index fingertip position (x, y only)
                length, info, _ = detector.findDistance(lmList[8][:2], lmList[12][:2])  # Unpack three return values
                if length < 35:
                    mcq.update(cursor, [bbox1, bbox2, bbox3, bbox4])
                    if mcq.userAns is not None:
                        print("User Answer:", mcq.userAns)
                        time.sleep(0.3)
                        qNo += 1
        else:
            quizCompleted = True
            quizStarted = False

    if quizCompleted:
        # Calculate Score
        score = 0
        for mcq in mcqList:
            if mcq.ans == mcq.userAns:
                score += 1
        score = round((score / qTotal) * 100, 2)

        # Display Completion and Restart Button
        img, _ = cvzone.putTextRect(img, "Quiz Completed", [250, 300], 2, 2, offset=50, border=5)
        img, _ = cvzone.putTextRect(img, f'Your Score: {score}%', [700, 300], 2, 2, offset=50, border=5)
        img, restartButton = cvzone.putTextRect(img, "Restart", [500, 500], 2, 2, offset=50, border=5)

        # Check if hand clicks the "Restart" button
        if hands:
            lmList = hands[0]['lmList']  # Get landmarks
            cursor = lmList[8][:2]  # Index fingertip position
            x1, y1, x2, y2 = restartButton
            if x1 < cursor[0] < x2 and y1 < cursor[1] < y2:
                # Reset variables
                qNo = 0
                for mcq in mcqList:
                    mcq.userAns = None
                quizCompleted = False
                time.sleep(0.4)

    # Draw Progress Bar if the quiz is ongoing
    if quizStarted:
        barValue = 150 + (950 // qTotal) * qNo
        cv2.rectangle(img, (150, 600), (barValue, 650), (0, 255, 0), cv2.FILLED)
        cv2.rectangle(img, (150, 600), (1100, 650), (255, 0, 255), 5)
        img, _ = cvzone.putTextRect(img, f'{round((qNo / qTotal) * 100)}%', [1130, 635], 2, 2, offset=16)

    # Show the frame
    cv2.imshow("Img", img)

    # Exit on pressing ' '
    if cv2.waitKey(1) & 0xFF == ord(' '):
        break

cv2.destroyAllWindows()
