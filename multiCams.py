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

class WebcamVideoStream:
	def __init__(self, src, savepath, width = 640, height = 480):
		"""
			inputs:
				src: the camera index
				savepath: path to save the camera frames
				width, height: video width and height
		"""
		self.camID = src
		self.savepath = savepath

		self.videoCap = cv2.VideoCapture(self.camID)
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

		#####################
		# .avi output config.
		#####################
		outname = 'webCam' + str(self.camID) + '.avi'
		fourcc = cv2.VideoWriter_fourcc(*'XVID')
		fps = 30.0 # framerate of the created video stream
		frameSize = (self.width, self.height)
		out = cv2.VideoWriter(os.path.join(self.savepath,outname), fourcc, fps, frameSize)

		# header of the .csv storing timestamp file
		timefields = ['frame#', 'timestamp']
		filename_timestamp = 'webCam' + str(self.camID) + '.csv'
		# preview name for showing frames
		previewName = 'camera' + str(self.camID)

		############################
		# start read and save frames
		############################
		with open(os.path.join(self.savepath, filename_timestamp), 'w', newline = '') as csvfile:
			writer = csv.writer(csvfile)
			writer.writerow(['all video timestamp based on same time 0'])
			writer.writerow(timefields) # write the head of timestamp csv file
			
			framei = -1
			while self.started:
				(grabbed, frame) = self.videoCap.read()

				frametime = time.time() - t_start
				framei += 1

				# write part
				out.write(frame)
				writer.writerow([str(framei), frametime])

				# read lock 
				self.read_lock.acquire()
				self.frame, self.frametime = frame.copy(), frametime
				self.read_lock.release()

		out.release()

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

def multiCams(argv):

	# parse input arguments
	try:
		opts, args = getopt.getopt(argv, 'hn:')
	except getopt.GetoptError:
		print('Usage: multiCams.py -n <nCams>')
		print('nCams is the total camera number')
		sys.exit(2)

	for opt, arg in opts:
		if opt == '-h':
			print('multiCams.py -nCams <nCams>')
		elif opt == '-n':
			nCams = int(arg)


	# pop dialog for save path input
	tk.Tk().withdraw()
	savepath = filedialog.askdirectory(initialdir=os.getcwd(), title = 'Please select a save directory')


	# create nCams WebcamVideoStream instances
	wvStreams = []
	previewNames = []
	for cami in range(nCams):
		wvStreams.append(WebcamVideoStream(src = cami, savepath=savepath))
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
			cv2.putText(frame, str(datetime.datetime.now().replace(microsecond=0)), 
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
