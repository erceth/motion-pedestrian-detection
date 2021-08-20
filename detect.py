import cv2
import os
import imutils
from imutils.object_detection import non_max_suppression
import numpy as np

class Detect:
  def __init__(self, height, width):
    self.avg = None
    self.transparent = np.zeros((height, width, 4), dtype=np.uint8)
    self.hog = cv2.HOGDescriptor()
    self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

  def processFrame(self, frame, index,imshow,writeOutput,height,width,minPixelSize,motionDeltaThreshold,motionPaddingCutoutPercent,cutOutHeightLimit,checkNLargestObjects,windowStride,hogPadding,hogScale,hogHitThreshold,nonMaxSuppressionThreshold):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)
    self.transparent = np.zeros((height, width, 4), dtype=np.uint8)
    if self.avg is None:
      print("[INFO] starting background model...")
      self.avg = gray.copy().astype("float")
    # accumulate the weighted average between the current frame and
    # previous frames, then compute the difference between the current
    # frame and running average
    cv2.accumulateWeighted(gray, self.avg, 0.5)
    frameDelta = cv2.absdiff(gray, cv2.convertScaleAbs(self.avg))

    thresh = cv2.threshold(frameDelta, motionDeltaThreshold, 255, cv2.THRESH_BINARY)[1]
    thresh = cv2.dilate(thresh, None, iterations=2)
    cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)

    cntsSorted = sorted(cnts, key=cv2.contourArea, reverse=True)

    for c in cntsSorted[:checkNLargestObjects]:
      # if the contour is too small, ignore it
      if cv2.contourArea(c) < minPixelSize:
        break
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

        (rects, weights) = self.hog.detectMultiScale(resizedCutOut, winStride=(windowStride,windowStride), padding=(hogPadding, hogPadding), scale=hogScale, hitThreshold=hogHitThreshold)

        # unshrink, back to cutOut
        rects = np.array([[int(x/ratio), int(y/ratio), int(x/ratio + w/ratio), int(y/ratio + h/ratio)] for (x, y, w, h) in rects])
        pick = non_max_suppression(rects, probs=None, overlapThresh=nonMaxSuppressionThreshold)
        if len(pick):
          for (xA, yA, xB, yB) in pick:
            # translate cutout measurements to main frame
            cv2.rectangle(self.transparent, (padX1 + xA, padY1 + yA), (padX1 + xB, padY1 + yB), (0, 255, 255, 255), 3)
            if imshow:
              cv2.rectangle(frame, (padX1 + xA, padY1 + yA), (padX1 + xB, padY1 + yB), (0, 255, 255, 255), 2)

        print(len(pick), flush=True)

    if writeOutput:
      self.write(index, self.transparent)

    if imshow:
      self.paint(frame, self.transparent)

  def paint(self, frame, transparent):
    cv2.imshow("Security Feed", frame)
    # cv2.imshow("transparent", transparent)
    cv2.waitKey(1)

  def write(self, index, transparent):
    cv2.imwrite(f"output-detect{index}.tmp.png", transparent)
    os.rename(f'output-detect{index}.tmp.png', f'output-detect{index}.png') # makes write atomic
        
    

