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
import serial
import serial.tools.list_ports

class WebcamVideoStream:
	def __init__(self, src, savepath, strtimenow, width = 640, height = 480):
		"""
			inputs:
				src: the camera index
				savepath: path to save the camera frames
				width, height: video width and height
		"""
		self.camID = src # camID start from 0
		self.savepath = savepath
		self.strtimenow = strtimenow 

		print("Init camera-" + str(self.camID + 1) + "....")
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
			print('Camera-' + str(self.camID + 1) + " already started!")
			return None

		# read and save frame 
		self.started = True
		self.readsavethread = Thread(target = self.readsaveframe, args= ())
		self.readsavethread.start()

		return self

	def readsaveframe(self):
		""" continously read and save frame"""

		# prefix of file name for both .avi and .csv files
		filename_prefix = 'v' + '-' + self.strtimenow + "-camera" + '-' + str(self.camID + 1)
		
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
		filename_timestamp = filename_prefix + '-timestamp.csv'
		

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

class SerialPortIO8:
	def __init__(self, savefile):
		IO8Name = ""
		for d, p, i in serial.tools.list_ports.grep("COM[0-9]*"):
			ser = serial.Serial(port = d, baudrate = 115200, timeout=1, write_timeout=1)
			ser.write(b'Z')
			s = ser.readline().strip().decode('UTF-8')
			ser.close()
			if("V" in s):
				IO8Name = d
				break
		
		if IO8Name is "":
			self.serial = None
			self.TimestampFile = ""
			self.started = False
			print("Can not find Serial Port for IO8 Module.")
			return

		self.serial = serial.Serial(port = IO8Name, baudrate = 115200, timeout=1, write_timeout=1)
		self.TimestampFile = savefile
		self.started = False
		print("create SerialPortIO8 for " + IO8Name  + "!")


	def Locate_serialPortIO8():		
		IO8Name = ""
		for d, p, i in serial.tools.list_ports.grep("COM[0-9]*"):
			ser = serial.Serial(port = d, baudrate = 115200, timeout=1, write_timeout=1)
			ser.write(b'Z')
			s = ser.readline().strip().decode('UTF-8')
			ser.close()
			if("V" in s):
				IO8Name = d
				break
		
		return IO8Name


	def start(self):
		if self.started:
			print("port IO8 already started!")
			return None

		# read and save frame 
		self.started = True
		self.savePressedthread = Thread(target = self.savePressed, args= ())
		self.savePressedthread.start()

		return self


	def savePressed(self):
		""" continously monitor the startpad state and save only the press timestamp"""
		
		# identify idle and pressed bit
		print("Don't press the startpad to identify the idle state")
		self.serial.write(b'A')
		s = self.serial.readline().strip().decode('UTF-8')
		idlebit = s
		print("touchpad idle bit = " + s)
		if(idlebit=="0"):
			pressbit = "1"
		else:
			pressbit = "0"

		print("Identifying Startpad Idle State is done!")


		# monitor and save the press 
		timefields = ['pressed#', 'timestamp'] # header of the .csv storing timestamp file
		with open(self.TimestampFile, 'w', newline = '') as csvfile:
			fwriter = csv.writer(csvfile)
			fwriter.writerow(['all timestamp based on same time 0'])
			fwriter.writerow(timefields) # write the head of timestamp csv file
			
			pressi = 0
			prebit = ""
			while self.started:
				self.serial.write(b'A')
				s = self.serial.readline().strip().decode('UTF-8')
				pressedtime = time.time() - t_start
				if(prebit == idlebit and s == pressbit):
					pressi += 1
					fwriter.writerow([str(pressi), pressedtime])
				prebit = s

	def stop(self):
		self.started = False
		self.savePressedthread.join()

	def __exit__(self, exc_type, exc_value, traceback):
		if (self.IO8serial is not None) and self.IO8serial.is_open:
			self.IO8serial.close()


def help():
	print("usage:  multiCams.py [-h] [-n <nCams>] [--IO8Exist <existLabel>]")
	print("\n")
	print("Options:")
	print("-h, --help 			show this help and exit")
	print("-n, --nCams <cameraNum>		input the number of the total web cameras")
	print("--IO8Exist <existLabel>  	IO8 exist (y) or not (n), default is n")
	print("\n")

	print("Examples:")
	print("python multiCams.py -n 3 --IO8Exist y")
	
	sys.exit(2)


def multiCams(argv):

	# parse input arguments
	try:
		opts, args = getopt.getopt(argv, 'n:e:h:', ["nCams =", "IO8Exist =", "help ="])
	except getopt.GetoptError:
		help()

	IO8Exist = False
	for opt, arg in opts:
		if  opt in ['-n', '--nCams ']:
			nCams = int(arg)
			
		elif opt in ['-e', '--IO8Exist ']:
			x = str(arg)
			if x == 'y':
				IO8Exist = True

		elif opt in ['-h', '--help ']:
			help()


	# pop dialog for save path input
	tk.Tk().withdraw()
	savepath = filedialog.askdirectory(initialdir=os.getcwd(), title = 'Please select a save directory')

	strtimenow = datetime.now().strftime('%Y%m%d-%H%M%S')

	# Create SerialPortIO8 instance
	if IO8Exist:
		IO8savefile = os.path.join(savepath, "v-" + strtimenow + "-startpad-timestamp.csv")
		serIO8 = SerialPortIO8(savefile = IO8savefile)
		if serIO8.serial is None:
			return
		serIO8.start()

	# create nCams WebcamVideoStream instances
	wvStreams = []
	previewNames = []	
	for cami in range(nCams):
		wvStreams.append(WebcamVideoStream(src = cami, savepath=savepath, strtimenow = strtimenow))
		previewNames.append('camera-' + str(cami + 1) + ', Press ESC to stop')
	
	# start read and save frame for all cameras
	for cami in range(nCams): 
		wvStreams[cami].start()


	print("vides/timestamp are saved in " + savepath)
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

	if IO8Exist:
		serIO8.stop()



if __name__ == "__main__":
	t_start = time.time() # global t_start
	multiCams(sys.argv[1:])

