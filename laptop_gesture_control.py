import cv2
import mediapipe as mp
import socket

# --- NETWORK CONFIGURATION ---
ESP32_IP = "192.168.15.206" 
ESP32_PORT = 4210

# Initialize UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
print(f"Wireless UDP Socket initialized. Sending commands to {ESP32_IP}:{ESP32_PORT}")

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)
mp_draw = mp.solutions.drawing_utils

# Open Webcam
cap = cv2.VideoCapture(0)

# Track the last sent command to avoid spamming the network
last_command = ""

def classify_gesture(hand_landmarks):
    """
    Classifies hand gestures for Forward, Backward, Left, Right, and Stop.
    """
    lm = hand_landmarks.landmark
    
    # Fingertip check
    index_extended = lm[8].y < lm[6].y
    middle_extended = lm[12].y < lm[10].y
    ring_extended = lm[16].y < lm[14].y
    pinky_extended = lm[20].y < lm[18].y
    
    thumb_extended = lm[4].x > lm[3].x
    fingers_up = sum([index_extended, middle_extended, ring_extended, pinky_extended])

    # 1. Stop ('S'): 5 fingers open
    if fingers_up >= 4:
        return 'S', "Stop / Hold (5 Fingers)"
    
    # 2. Backward ('B'): Fist (0 fingers up)
    elif fingers_up == 0:
        return 'B', "Backward (Fist)"
    
    # 3. Single Finger Pointing Logic (Forward, Left, Right)
    index_tip = lm[8]
    index_mcp = lm[5]

    dx = index_tip.x - index_mcp.x
    dy = index_tip.y - index_mcp.y

    # Check whether the movement is primarily vertical or horizontal
    if abs(dy) > abs(dx):
        if dy < -0.05:
            return 'F', "Forward (Point Up)"
        elif dy > 0.05:
            return 'B', "Backward (Point Down)"
    else:
        # Note: Because OpenCV video is flipped horizontally, 
        # pointing towards your left on screen commands Left ('L')
        if dx < -0.05:
            return 'L', "Left (Point Left)"
        elif dx > 0.05:
            return 'R', "Right (Point Right)"

    return 'S', "Hold / Stop (Default)"

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        print("Ignoring empty camera frame.")
        continue

    # Flip frame horizontally for a selfie-view display and convert to RGB for MediaPipe
    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    results = hands.process(rgb_frame)
    
    command = 'S'
    gesture_name = "Stop"

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            command, gesture_name = classify_gesture(hand_landmarks)

    # Send UDP packet only when the command changes
    if command != last_command:
        sock.sendto(command.encode('utf-8'), (ESP32_IP, ESP32_PORT))
        print(f"Wireless Command Sent: {command} ({gesture_name})")
        last_command = command

    # Display feedback on the live video window
    cv2.putText(frame, f"Command: {command} ({gesture_name})", (10, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

    cv2.imshow("ESP32 Gesture Controller", frame)

    # Press 'q' to exit the loop
    if cv2.waitKey(1) & 0xFF == ord('q'):
        cap.release()
        cv2.destroyAllWindows()
        break
