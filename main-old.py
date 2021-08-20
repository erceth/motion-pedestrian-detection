import cv2
import sys
import numpy as np
import imutils
from imutils.object_detection import non_max_suppression
import os

index = sys.argv[1]
height = int(sys.argv[2])
width = int(sys.argv[3])
minPixelSize = int(sys.argv[4])
motion_delta_thresh = int(sys.argv[5])
motionPaddingCutoutPercent = float(sys.argv[6])
cutOutHeightLimit = int(sys.argv[7])
checkNLargestObjects = int(sys.argv[8])
windowStride = int(sys.argv[9])
hogPadding = int(sys.argv[10])
hogScale = float(sys.argv[11])
hogHitThreshold = int(sys.argv[12])
nonMaxSuppressionThreshold = float(sys.argv[13])
writeOutput = int(sys.argv[14])
imshow = int(sys.argv[15])

avg = None

hog = cv2.HOGDescriptor()
hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

while True:
  try:
    raw_data = sys.stdin.buffer.read(width*height*3)

    frame = np.frombuffer(raw_data, dtype=np.uint8)
    frame = frame.reshape((height, width, 3))
    transparent = np.zeros((height, width, 4), dtype=np.uint8)
    
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)
    if avg is None:
      print("[INFO] starting background model...")
      avg = gray.copy().astype("float")
      continue
    # accumulate the weighted average between the current frame and
    # previous frames, then compute the difference between the current
    # frame and running average
    cv2.accumulateWeighted(gray, avg, 0.5)
    frameDelta = cv2.absdiff(gray, cv2.convertScaleAbs(avg))

    thresh = cv2.threshold(frameDelta, motion_delta_thresh, 255, cv2.THRESH_BINARY)[1]
    thresh = cv2.dilate(thresh, None, iterations=2)
    cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    

    if len(cnts) <= 0:
      continue

    cntsSorted = sorted(cnts, key=cv2.contourArea, reverse=True)
    
    for c in cntsSorted[:checkNLargestObjects]:
      # if the contour is too small, ignore it
      if cv2.contourArea(c) < minPixelSize:
        continue
      (x, y, w, h) = cv2.boundingRect(c)
      paddingWidth = w * motionPaddingCutoutPercent
      paddingHeight = h * motionPaddingCutoutPercent
      padX1 = int(max(0, x - paddingWidth))
      padY1 = int(max(0, y - paddingHeight))
      padX2 = int(min(width, x + w + paddingWidth))
      padY2 = int(min(height, y + h + paddingHeight))

      cutOut = frame[padY1:padY2, padX1:padX2]
      if imshow:
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0,255,0)) # draw motion detection in green
        cv2.rectangle(frame, (padX1, padY1), (padX2, padY2), (255,0,0)) # draw padded cutout in blue

      if w > 100 and h > 100:
        ratio = 1
        resizedCutOut = cutOut
        if resizedCutOut.shape[0] > cutOutHeightLimit:

          ratio = cutOutHeightLimit / resizedCutOut.shape[0]
          dim = (int(resizedCutOut.shape[1] * ratio), cutOutHeightLimit)
          resizedCutOut = cv2.resize(cutOut, dim, interpolation=cv2.INTER_AREA)

        (rects, weights) = hog.detectMultiScale(resizedCutOut, winStride=(windowStride,windowStride), padding=(hogPadding, hogPadding), scale=hogScale, hitThreshold=hogHitThreshold)

        # unshrink, back to cutOut
        rects = np.array([[int(x/ratio), int(y/ratio), int(x/ratio + w/ratio), int(y/ratio + h/ratio)] for (x, y, w, h) in rects])
        pick = non_max_suppression(rects, probs=None, overlapThresh=nonMaxSuppressionThreshold)
        if len(pick):
          # print('ped detect #:', len(pick), flush=True)
          for (xA, yA, xB, yB) in pick:
            # translate cutout measurements to main frame
            # cv2.rectangle(frame, (padX1 + xA, padY1 + yA), (padX1 + xB, padY1 + yB), (0, 0, 255), 2)
            cv2.rectangle(transparent, (padX1 + xA, padY1 + yA), (padX1 + xB, padY1 + yB), (0, 255, 255, 255), 3)
        print(len(pick), flush=True)
    if imshow:
      cv2.imshow("Security Feed", frame)
      cv2.imshow("transparent", transparent)
      cv2.waitKey(1)
    if writeOutput:
      cv2.imwrite(f"output-detect{index}.tmp.png", transparent)
      os.rename(f'output-detect{index}.tmp.png', f'output-detect{index}.png') # makes write atomic
    
    
  except cv2.error as e:
    print('python exception', e, flush=True)
    continue