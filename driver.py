import json
from operator import itemgetter
import subprocess
import detect
import numpy as np

f = open('config.json',)

config = json.load(f)
f.close

pythonPath,imshow,writeOutput,writeTransparentOutput = itemgetter('pythonPath','imshow','writeOutput','writeTransparentOutput')(config['general'])
ip,path = itemgetter('ip','path')(config['cameras'][0])
detectFps,height,width,minPixelSize,motionDeltaThreshold,motionPaddingCutoutPercent,cutOutHeightLimit,checkNLargestObjects,windowStride,hogPadding,hogScale,hogHitThreshold,nonMaxSuppressionThreshold = itemgetter('detectFps','height','width','minPixelSize','motionDeltaThreshold','motionPaddingCutoutPercent','cutOutHeightLimit','checkNLargestObjects','windowStride','hogPadding','hogScale','hogHitThreshold','nonMaxSuppressionThreshold')(config['cameras'][0]['detectParameters'])
index = 0
detector = detect.Detect(index,height,width,minPixelSize,motionDeltaThreshold,motionPaddingCutoutPercent,cutOutHeightLimit,checkNLargestObjects,windowStride,hogPadding,hogScale,hogHitThreshold,nonMaxSuppressionThreshold,imshow,writeOutput,writeTransparentOutput)

streamInput = f'rtsp://{ip}{path}'

command = ['ffmpeg', '-i', streamInput, '-f', 'image2pipe', '-vf', f'fps={detectFps}', '-pix_fmt', 'bgr24', '-vcodec', 'rawvideo', '-an', 'pipe:1']
stringCommand = ' '.join(command)
print('ffmpeg arguments:', stringCommand)

p1 = subprocess.Popen(command, stdout=subprocess.PIPE)

while True:
  raw_frame = p1.stdout.read(width*height*3)
  if len(raw_frame) != (width*height*3):
    print('Error reading frame!!!')  # Break the loop in case of an error (too few bytes were read).
    break
  # Convert the bytes read into a NumPy array, and reshape it to video frame dimensions
  frame = np.fromstring(raw_frame, np.uint8)
  frame = frame.reshape((height, width, 3))

  detector.processFrame(frame)
