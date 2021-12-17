#import os
#os.environ["OPENCV_VIDEOIO_MSMF_ENABLE_HW_TRANSFORMS"] = "0"

import cv2
import numpy as np
from threading import Thread, Lock

import tkinter as tk
from tkinter import filedialog
import os
import time
import datetime
import csv
import sys, getopt
from datetime import datetime


class WebcamVideoStream:
	def __init__(self, src, savepath, strtimenow, width = 640, height = 480):
		"""
			inputs:
				src: the camera index
				savepath: path to save the camera frames
				width, height: video width and height
		"""
		self.camID = src
		self.savepath = savepath
		self.strtimenow = strtimenow 

		print("Init Camera" + str(self.camID) + "....")
		self.videoCap = cv2.VideoCapture(self.camID, cv2.CAP_DSHOW)
		self.width = width
		self.height = height
		self.videoCap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
		self.videoCap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

		self.frametime = time.time() - t_start
		(self.retval, self.frame) = self.videoCap.read()

		self.read_lock = Lock()
		
		# initial the flag for read and save frames
		self.started = False
		

	def start(self):
		if self.started:
			print('webCam' + str(self.camID) + " already started!")
			return None

		# read and save frame 
		self.started = True
		self.readsavethread = Thread(target = self.readsaveframe, args= ())
		self.readsavethread.start()

		return self

	def readsaveframe(self):
		""" continously read and save frame"""

		# prefix of file name for both .avi and .csv files
		filename_prefix = 'video' + '_' + self.strtimenow + "_camera" + str(self.camID)
		
		#####################
		# .avi output config.
		#####################
		filename_avi = filename_prefix + '.avi'
		fourcc = cv2.VideoWriter_fourcc(*'XVID')
		fps = 30.0 # framerate of the created video stream
		frameSize = (self.width, self.height)
		vout = cv2.VideoWriter(os.path.join(self.savepath, filename_avi), fourcc, fps, frameSize)

		# header of the .csv storing timestamp file
		timefields = ['frame#', 'timestamp']
		filename_timestamp = filename_prefix + '.csv'
		
		# preview name for showing frames
		previewName = 'camera' + str(self.camID)

		############################
		# start read and save frames
		############################
		with open(os.path.join(self.savepath, filename_timestamp), 'w', newline = '') as csvfile:
			fwriter = csv.writer(csvfile)
			fwriter.writerow(['all video timestamp based on same time 0'])
			fwriter.writerow(timefields) # write the head of timestamp csv file
			
			framei = -1
			while self.started:
				(grabbed, frame) = self.videoCap.read()

				frametime = time.time() - t_start
				framei += 1

				# write part
				vout.write(frame)
				fwriter.writerow([str(framei), frametime])

				# read lock 
				self.read_lock.acquire()
				self.frame, self.frametime = frame.copy(), frametime
				self.read_lock.release()

		vout.release()

	def getframe(self):
		self.read_lock.acquire()
		frame, frametime = self.frame.copy(), self.frametime
		self.read_lock.release()
		return frame

	def stop(self):
		self.started = False
		self.readsavethread.join()

	def __exit__(self, exc_type, exc_value, traceback):
		self.videoCap.release()


def help():
	print("usage:  multiCams.py [-h] [-n <nCams>]")
	print("Options:")
	print("-h 		show this help and exit")
	print("-n nCams  	input the number of the total web cameras")
	print("Examples:")
	print("python multiCams.py -n 3")
	sys.exit(2)


def multiCams(argv):

	# parse input arguments
	try:
		opts, args = getopt.getopt(argv, 'hn:')
	except getopt.GetoptError:
		help()

	for opt, arg in opts:
		if opt == '-h':
			help()
		elif opt == '-n':
			nCams = int(arg)


	# pop dialog for save path input
	tk.Tk().withdraw()
	savepath = filedialog.askdirectory(initialdir=os.getcwd(), title = 'Please select a save directory')


	# create nCams WebcamVideoStream instances
	wvStreams = []
	previewNames = []
	strtimenow = datetime.now().strftime('%Y%m%d-%H%M%S')
	for cami in range(nCams):
		wvStreams.append(WebcamVideoStream(src = cami, savepath=savepath, strtimenow = strtimenow))
		previewNames.append('webCam' + str(cami) + ', Press ESC to stop')
	
	# start read and save frame for all cameras
	for cami in range(nCams): 
		wvStreams[cami].start()

	print("vides are saved in " + savepath)
	while True:
		# frame show
		for cami in range(nCams):
			frame = wvStreams[cami].getframe()

			# add timestamp on the frame
			cv2.putText(frame, str(datetime.now().replace(microsecond=0)), 
				(30,30), cv2.FONT_HERSHEY_PLAIN, 1, (100,0,0),2, cv2.LINE_AA)
			
			cv2.imshow(previewNames[cami],frame)

		if cv2.waitKey(10) == 27: # exit pressing 'esc'
			break
	
	# stop reading and saving frame
	for cami in range(nCams): 
		wvStreams[cami].stop()
	cv2.destroyAllWindows()



if __name__ == "__main__":
	t_start = time.time() # global t_start
	multiCams(sys.argv[1:])
