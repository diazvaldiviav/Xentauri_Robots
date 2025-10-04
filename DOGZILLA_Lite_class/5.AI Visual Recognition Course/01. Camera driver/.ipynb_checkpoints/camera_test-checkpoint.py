import cv2


# For webcam input:
cap=cv2.VideoCapture(0)
cap.set(3,320)
cap.set(4,240)

while cap.isOpened():
  ret, frame = cap.read()
  if not ret:
      print("Can not receive frame (stream end?). Exiting...")
      break
  cv2.imshow("image1",frame)

  if cv2.waitKey(5) & 0xFF == 27:
    break
cap.release()
