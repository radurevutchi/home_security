# USAGE
# python3 motion_detector.py


# import the necessary packages
from threading import Thread
from imutils.video import VideoStream
import datetime
import time
import imutils
import time
import cv2
import signal # catching ctrl c signals and properly ending camera capture
import sys
import os
import yagmail # sending email attachments with motion capture
from pytz import timezone # timezone for date setting


# FUNCTION TO SEND EMAIL WITH ATTACHMENT
def send_email(filename):

	RECEIVER = ["radurevutchi@gmail.com"]
	SUBJECT = "MOTION DETECTED"
	BODY = '{0:%B %d %Y %H:%M:%S}'.format(d.now(timezone(my_timezone)))
	FILENAME = filename



	yag = yagmail.SMTP("radurevutchi")
	yag.send(
	    to=RECEIVER,
	    subject=SUBJECT,
	    contents=BODY,
	    attachments=FILENAME,
	)


def beep(filename):
	os.system(filename)

# FUNCTION TO HANDLE CTRL C EXIT
def signal_handler(sig, frame):


	vs.stop()
	cv2.destroyAllWindows()
	print('Exited Successfully!')
	sys.exit(0)



# MAIN CODE


# Initial wait time (for user to move out of camera's way)
time.sleep(5)


# setting up signal handler
signal.signal(signal.SIGINT, signal_handler)


# setting up time and date tools
# change timezone here
my_timezone = "US/Eastern"
d = datetime.datetime


# starting video stream
vs = VideoStream(src=0, resolution=(1920,1080)).start()
time.sleep(2.0)


# units in seconds
local_save_freq = 1
background_freq = 60 # How often to refresh background
server_freq = 5 # How often to upload capture to server
email_freq = 60 * 5 # How often to send email
clear_local_freq = 30 # How often to clear up local images


# initialize the first frame in the video stream
firstFrame = None
local_save_timer = time.time()
background_time = time.time()
server_timer = time.time() - server_freq # Counter for uploading motion capture to server
email_timer = time.time() - email_freq # Counter for sending email attachment
clear_local_timer = time.time()





# loop over the frames of the video
while True:


	# grab the current frame and initialize the occupied/unoccupied
	# text
	frame = vs.read()
	frame = frame
	text = "Unoccupied"
	occupied = False



	# if the frame could not be grabbed, then we have reached the end
	# of the video
	if frame is None:
		break

	# resize the frame, convert it to grayscale, and blur it
	frame = imutils.resize(frame, width=1000)
	gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
	gray = cv2.GaussianBlur(gray, (21, 21), 0)




	# resets background every <background_freq> seconds
	# this deals with vibrations, changes in lighting, and false motion
	if time.time() - background_time > background_freq:
		firstFrame = None
		background_time = time.time()



	# if the first frame is None, initialize it
	if firstFrame is None:
		firstFrame = gray
		continue



	# compute the absolute difference between the current frame and
	# first frame
	frameDelta = cv2.absdiff(firstFrame, gray)
	thresh = cv2.threshold(frameDelta, 50, 255, cv2.THRESH_BINARY)[1] # modify threshold value to adjust noise

	# dilate the thresholded image to fill in holes, then find contours
	# on thresholded image
	thresh = cv2.dilate(thresh, None, iterations=2)
	cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
		cv2.CHAIN_APPROX_SIMPLE)
	cnts = imutils.grab_contours(cnts)


	# loop over the contours
	for c in cnts:
		# if the contour is too small, ignore it
		if cv2.contourArea(c) < 500:          # this is the min area
			continue

		# compute the bounding box for the contour, draw it on the frame,
		# and update the text
		(x, y, w, h) = cv2.boundingRect(c)
		cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
		text = "Occupied"
		occupied = True


	# clears local deposit of image captures every 30 seconds
	if time.time() - clear_local_timer > clear_local_freq:
		os.system("rm captures/*")
		clear_local_timer = time.time()

	img_filename = '{0:%B_%d_%Y_%H_%M_%S}'.format(d.now(timezone(my_timezone))) + '.jpg'

	# writes to local machine
	if time.time() - local_save_timer > 0.9:
		cv2.imwrite("captures/"+img_filename, frame)
		local_save_timer = time.time()


	# writes to external server

	if occupied and time.time() - server_timer > server_freq:
		scp_to_server = "scp -i "
		scp_to_server += "deep_learning_instance_1.pem "
		scp_to_server += "captures/" + img_filename + " "
		scp_to_server += "ubuntu@ec2-34-236-155-231.compute-1.amazonaws.com:/home/ubuntu/motion"
		copying = Thread(target=beep, args=[scp_to_server])
		copying.start()
		#os.system(scp_to_server)
		server_timer = time.time()


	# sends email with attachment
	if occupied and time.time() - email_timer > email_freq:
		cv2.imwrite(img_filename, frame)
		send_email(img_filename)
		email_timer = time.time()
		os.system("rm " + img_filename)



	# draw the text and timestamp on the frame
	cv2.putText(frame, "Room Status: {}".format(text), (10, 20),
		cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
	cv2.putText(frame, datetime.datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"),
		(10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)


	# show the frame and record if the user presses a key
	#cv2.imshow("Security Feed", frame)


	#cv2.imshow("Thresh", thresh)
	#cv2.imshow("Frame Delta", frameDelta)
	key = cv2.waitKey(1) & 0xFF

	# if the `q` key is pressed, break from the lop






# cleanup the camera and close any open windows
vs.stop()
cv2.destroyAllWindows()
