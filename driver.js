const { spawn } = require('child_process');
const config = require('./config.json')

const {
  pythonPath, 
  writeOutput,
  imshow
} = config.general;

const cam = config.cameras[0];
const {
  detectFps,
  height,
  width,
  minPixelSize,
  motionDeltaThreshold,
  motionPaddingCutoutPercent,
  cutOutHeightLimit,
  checkNLargestObjects,
  windowStride,
  hogPadding,
  hogScale,
  hogHitThreshold,
  nonMaxSuppressionThreshold,
} = cam.detectParameters;

const streamInput = cam.input ? cam.input : `rtsp://${cam.ip}${cam.path}`;

const command = ['-i', streamInput, '-f', 'image2pipe', '-vf', `fps=${detectFps}`, '-pix_fmt', 'bgr24', '-vcodec', 'rawvideo', '-an', 'pipe:1'];

if (cam.input) {
  command.unshift('-re')
}

const stringCommand = command.join(' ');
console.log('ffmpeg arguments:', stringCommand);

const ffmpegSpawn = spawn('ffmpeg', command);

const detectSpawn = spawn(pythonPath, ['detect-wrapper.py',
  0,
  height,
  width,
  minPixelSize,
  motionDeltaThreshold,
  motionPaddingCutoutPercent,
  cutOutHeightLimit,
  checkNLargestObjects,
  windowStride,
  hogPadding,
  hogScale,
  hogHitThreshold,
  nonMaxSuppressionThreshold,
  writeOutput,
  imshow
]);

ffmpegSpawn.stdout.on('data', (data) => {
  detectSpawn.stdin.write(data);
})
ffmpegSpawn.stderr.on('data', (data) => {
  console.log('ffmpegSpawn:stderr', String(data));
})

detectSpawn.stdout.on('data', (data) => {
  console.log('detectSpawn:stdout', String(data));
})

detectSpawn.stderr.on('data', (data) => {
  console.log('detectSpawn:stderr', String(data));
})
