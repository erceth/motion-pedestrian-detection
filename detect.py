import cv2
import os
import imutils
from imutils.object_detection import non_max_suppression
import numpy as np

class Detect:
  def __init__(self, index,height,width,minPixelSize,motionDeltaThreshold,motionPaddingCutoutPercent,cutOutHeightLimit,checkNLargestObjects,windowStride,hogPadding,hogScale,hogHitThreshold,nonMaxSuppressionThreshold,imshow,writeOutput,writeTransparentOutput):
    self.index = index
    self.height = height
    self.width = width
    self.minPixelSize = minPixelSize
    self.motionDeltaThreshold = motionDeltaThreshold
    self.motionPaddingCutoutPercent = motionPaddingCutoutPercent
    self.cutOutHeightLimit = cutOutHeightLimit
    self.checkNLargestObjects = checkNLargestObjects
    self.windowStride = windowStride
    self.hogPadding = hogPadding
    self.hogScale = hogScale
    self.hogHitThreshold = hogHitThreshold
    self.nonMaxSuppressionThreshold = nonMaxSuppressionThreshold
    self.imshow = imshow
    self.writeOutput = writeOutput
    self.writeTransparentOutput = writeTransparentOutput
    self.avg = None
    self.transparent = np.zeros((height, width, 4), dtype=np.uint8)
    self.hog = cv2.HOGDescriptor()
    self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

  def processFrame(self, frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)

    self.transparent = np.zeros((self.height, self.width, 4), dtype=np.uint8)
    if self.avg is None:
      print("[INFO] starting background model...")
      self.avg = gray.copy().astype("float")
    # accumulate the weighted average between the current frame and
    # previous frames, then compute the difference between the current
    # frame and running average
    cv2.accumulateWeighted(gray, self.avg, 0.5)
    frameDelta = cv2.absdiff(gray, cv2.convertScaleAbs(self.avg))

    thresh = cv2.threshold(frameDelta, self.motionDeltaThreshold, 255, cv2.THRESH_BINARY)[1]
    thresh = cv2.dilate(thresh, None, iterations=2)
    cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)

    cntsSorted = sorted(cnts, key=cv2.contourArea, reverse=True)

    for c in cntsSorted[:self.checkNLargestObjects]:
      # if the contour is too small, ignore it
      if cv2.contourArea(c) < self.minPixelSize:
        break
      (x, y, w, h) = cv2.boundingRect(c)
      paddingWidth = w * self.motionPaddingCutoutPercent
      paddingHeight = h * self.motionPaddingCutoutPercent
      padX1 = int(max(0, x - paddingWidth))
      padY1 = int(max(0, y - paddingHeight))
      padX2 = int(min(self.width, x + w + paddingWidth))
      padY2 = int(min(self.height, y + h + paddingHeight))

      cutOut = frame[padY1:padY2, padX1:padX2]
      if self.imshow == 1 or self.writeOutput == 1:
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0,255,0), 2) # draw motion detection in green
        cv2.rectangle(frame, (padX1, padY1), (padX2, padY2), (255,0,0), 2) # draw padded cutout in blue

      if w > 100 and h > 100:
        ratio = 1
        resizedCutOut = cutOut
        if resizedCutOut.shape[0] > self.cutOutHeightLimit:

          ratio = self.cutOutHeightLimit / resizedCutOut.shape[0]
          dim = (int(resizedCutOut.shape[1] * ratio), self.cutOutHeightLimit)
          resizedCutOut = cv2.resize(cutOut, dim, interpolation=cv2.INTER_AREA)

        (rects, weights) = self.hog.detectMultiScale(resizedCutOut, winStride=(self.windowStride,self.windowStride), padding=(self.hogPadding, self.hogPadding), scale=self.hogScale, hitThreshold=self.hogHitThreshold)

        # unshrink, back to cutOut
        rects = np.array([[int(x/ratio), int(y/ratio), int(x/ratio + w/ratio), int(y/ratio + h/ratio)] for (x, y, w, h) in rects])
        pick = non_max_suppression(rects, probs=None, overlapThresh=self.nonMaxSuppressionThreshold)
        if len(pick):
          for (xA, yA, xB, yB) in pick:
            # translate cutout measurements to main frame
            cv2.rectangle(self.transparent, (padX1 + xA, padY1 + yA), (padX1 + xB, padY1 + yB), (0, 255, 255, 255), 2)
            cv2.rectangle(frame, (padX1 + xA, padY1 + yA), (padX1 + xB, padY1 + yB), (0, 255, 255, 255), 2)

        print(len(pick), flush=True)

    if self.imshow == 1:
      self.show(frame, self.transparent)

    if self.writeOutput == 1:
      self.write(frame, f'output{self.index}')

    if self.writeTransparentOutput == 1:
      self.write(self.transparent, f'output-detect{self.index}')

    

  def show(self, frame, transparent):
    cv2.imshow("Security Feed", frame)
    # cv2.imshow("transparent", transparent)
    cv2.waitKey(1)

  def write(self, image, filename):
    cv2.imwrite(f"{filename}.tmp.png", image)
    os.rename(f'{filename}.tmp.png', f'{filename}.png') # makes write atomic
