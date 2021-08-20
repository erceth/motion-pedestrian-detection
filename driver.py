import json
from operator import itemgetter
import subprocess
import detect
import numpy as np

f = open('config.json',)

config = json.load(f)
f.close

pythonPath,writeOutput,imshow = itemgetter('pythonPath','writeOutput','imshow')(config['general'])
ip,path = itemgetter('ip','path')(config['cameras'][0])
detectFps,height,width,minPixelSize,motionDeltaThreshold,motionPaddingCutoutPercent,cutOutHeightLimit,checkNLargestObjects,windowStride,hogPadding,hogScale,hogHitThreshold,nonMaxSuppressionThreshold = itemgetter('detectFps','height','width','minPixelSize','motionDeltaThreshold','motionPaddingCutoutPercent','cutOutHeightLimit','checkNLargestObjects','windowStride','hogPadding','hogScale','hogHitThreshold','nonMaxSuppressionThreshold')(config['cameras'][0]['detectParameters'])
index = 0
detector = detect.Detect(height, width)

print(detectFps,height,width,minPixelSize)

streamInput = f'rtsp://{ip}{path}'

command1 = ['ffmpeg', '-i', streamInput, '-f', 'image2pipe', '-vf', f'fps={detectFps}', '-pix_fmt', 'bgr24', '-vcodec', 'rawvideo', '-an', 'pipe:1']
p1 = subprocess.Popen(command1, stdout=subprocess.PIPE)

while True:
  raw_frame = p1.stdout.read(width*height*3)
  if len(raw_frame) != (width*height*3):
    print('Error reading frame!!!')  # Break the loop in case of an error (too few bytes were read).
    break
  # Convert the bytes read into a NumPy array, and reshape it to video frame dimensions
  frame = np.fromstring(raw_frame, np.uint8)
  frame = frame.reshape((height, width, 3))

  detector.processFrame(frame, index,imshow,writeOutput,height,width,minPixelSize,motionDeltaThreshold,motionPaddingCutoutPercent,cutOutHeightLimit,checkNLargestObjects,windowStride,hogPadding,hogScale,hogHitThreshold,nonMaxSuppressionThreshold)
