# SETUP
## Package Setup
This repo is currently working with **raspberry pi 3 model B** with **Python 3.5** and a **Logitech webcam**
* First install the *fswebcam package* (you can check [this tutorial](https://www.raspberrypi.org/documentation/usage/webcams/)) with 
`sudo apt-get install fswebcam`, check if the cam is working correctly by running `fswebcam image.jpg` (use `eog image.jpg` to view the image throught ssh)
* Then follow [this tutorial](https://www.pyimagesearch.com/2016/04/18/install-guide-raspberry-pi-3-raspbian-jessie-opencv-3/)
To install **OpenCV** for raspberry pi (changing python3.4 to python3.5)
* Then install the **scikit-image** package by running `sudo apt-get install python-skimage` followed by `pip install scikit-image` (be sure to be in the correct virtual enviroment using python3.5)
* Install [telegram-python-bot](https://github.com/python-telegram-bot/python-telegram-bot) with `pip install python-telegram-bot --upgrade`
* Install image utils with `sudo pip install imutils`

## Final Setup
* Edit file **token_psw.txt**, insert your token and password after the *=*

# HOW TO USE

To start the bot simply use
`pyhton main.py`
If you want to run it even when you close the ssh connection use
`nohup python main.py &`

## Avaiable telgram commands
* /start - strat the bot and provide the password (you get only one chanche to type the correct one)
* /photo - get a snapshot from the camera and send it trhought telegram 
* /video seconds - you can usit with or without the parameter *seconds* and it will send you a gif of form the camera (default duration 5 seconds)
* /flags - you can dis/enable the notification from the movement detection 




# USEFUL LINKS
## Opencv 
### API
* https://docs.opencv.org/2.4/modules/highgui/doc/reading_and_writing_images_and_video.html
* https://docs.opencv.org/3.0-beta/doc/py_tutorials/py_gui/py_video_display/py_video_display.html#display-video

### CAPTURE VIDEO
* http://answers.opencv.org/question/128081/python-frame-grabbing-from-ip-camera-and-process-in-a-different-thread/

### Image similarity comparison
* https://ece.uwaterloo.ca/~z70wang/publications/ssim.pdf

### Motion detection
* https://www.pyimagesearch.com/2015/05/25/basic-motion-detection-and-tracking-with-python-and-opencv/

## With telegram
* https://github.com/meinside/telegram-bot-opencv


# TODO

## Raspberry
- [ ] cron job to start the bot at 8 

## General
- [X] Get token and psw from file
- [ ] Get Classifier path from home direcotry
- [ ] Save images/videos with format *video-user_id.extension*
- [X] use Cam_shotter to get video
- [ ] Fix while score, exit when no difference are detected anymore
- [ ] Stop/start cam_motion class by flag value
- [X] reorganize prints
- [ ] create profiling function
- [ ] implement a logger

## Telegram
- [X] fix mp4 video on telegram mobile
- [ ] Command to stop bot execution
- [X] Make custom inline keyboard to set flags
- [X] User friendly motion detection notification
- [X] Send caption with image
- [X] Command to reset ground image


### Movement detection
- [X] Nofity when movement is detected 
- [X] Enable/disable notification
- [X] Send different image
- [X] Send different video
- [X] Detect face in image change
- [X] Draw rectangle around face
- [X] Find something faster than SSIM -> MSE
- [X] Get face photo
- [X] Denoise photo
- [X] Wait after cam is opened
- [ ] Reste ground image programmaticly
- [ ] Take frames for video from are_different
- [ ] Find out if background has changed (sum of image mean < threshold)
- [ ] find a confidence method for faces in video 
- [ ] detect movement direction (right,left)
- [ ] detect movement direction (incoming, outcoming)
- [ ] Classify person

# Issues

## Telegram gif not showing up on mobile
### Issue
Using 
> codec= cv2.VideoWriter_fourcc(*'MP4V')
out = cv2.VideoWriter(video_name, codec, fps,(640,480))
out.write(frame)


Generate a .mp4 video with is shown as a *gif* in telegram. While the desktop version has no problem viewing it the mobile version 
displays a blank file wich can be seen only by downloading the .mp4.

While generating the file *OpenCv* yelds the following warning
> OpenCV: FFMPEG: tag 0x5634504d/'MP4V' is not supported with codec id 13 and format 'mp4 / MP4 (MPEG-4 Part 14)'
OpenCV: FFMPEG: fallback to use tag 0x00000020/' ???'


### Tried Fixes
* Changing the resolution from *640,480* to any other resolution brings telegram to recognize the file as a video (not gif), but it still does not show up in the mobile version
* Changing the file extension to *.mp4v* does not work 
* Changing codec to _cv2.VideoWriter_fourcc(*'MPEG')_ does not show gif on desktop too
* Using **isColor=False** does not work

### Solutions
* Changing codec to _cv2.VideoWriter_fourcc(*'avc1')_ and extension to **.mov** sends a file (not a gif) which can be viewd both by the desktop and the mobile version of telegram
* Final solution: Removed the codec calss and used **0x00000021** instead (with **.mp4** extension), found (here)[https://devtalk.nvidia.com/default/topic/1029451/-python-what-is-the-four-characters-fourcc-code-for-mp4-encoding-on-tx2/]

## Video difference is laggy 
### Issue
The video difference is send when a difference in frame is detected, this detection is time costly thus writing a frame to the video object too slowly.
This brings to a laggy gif file.
GRAY SCALING takes 0.01 seconds
SSIM takes about 0.5 seconds for every image, while gray scale takes 0.01 seconds
PSNR takes 0.04 seconds for every image

### Tried Fixes
* Remove *sleep(1/self.fps)* from while loop...not working
* Remove face detection...not working

### Solution
* Taking the frames in the Cam_shotter class resolved the issue

### Issue 
If you are having an error like:
> VIDEOIO ERROR: V4L: index 0 is not correct!

Change the **cam_idx** in Cam_shotter to the correct one for your raspberry pi

### Warning

Encountered when the cam_movement class first start to compute difference between images
>python3.5/site-packages/skimage/measure/simple_metrics.py:142: RuntimeWarning: divide by zero encountered in double_scalars
  return 10 * np.log10((data_range ** 2) / err)

When the cam_shotter class compl

### Issue
Using the *haarcascades/haarcascade_frontalface_alt.xml* with *CascadeClassifier* yelds a great number of false-positive

### Solution 
Changing to *haarcascades/haarcascade_frontalface_alt_tree.xml* resolved the issue


# Infos

## Image difference


| Algorithm        | Time taken in seconds| Suggested range |
| -------------    |:-------------:       |  -----:         |
| GRAY SCALING     | 0.01                 |                 |
| SSIM             | 0.5                  | x  <   0.75     |
| PSNR             | 0.03                 | x  <   30       |
| NRMSE            | 0.035                | x  >   0.3      |
| MSE              | 0.025                | x  > 500       |

## Image difference log

### MSE
* Change in shadow with value 3919
* It does not detect image far away persons
* Switched to PSNR

## PSNR
* Way more sensible than MSE (in a good way)
* Not so sensitive to shadow changes
* Change detected with score 24, while there was none 
* Is triggered when camera auto adjust brightness
* In bright places it becomes very sensitive -> the use of an *equalizeHist* seems to resolve the problem
* No good in poor light condition

## SSIM
* Using gaussian_weights=True -> time increases to 0.7 seconds

### Passing to  cv2.absdiff