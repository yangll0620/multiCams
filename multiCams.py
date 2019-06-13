import cv2
import numpy as numpy
import threading

class camThread(threading.Thread):
	def __init__(self, previewName, camID):
		threading.Thread.__init__(self)
		self.previewName = previewName
		self.camID = camID

	def run(self):
		print("Starting " + self.previewName)
		camPreview(self.previewName, self.camID)

def camPreview(previewName, camID):
	cv2.namedWindow(previewName)
	cam = cv2.VideoCapture(camID)
	print(cam)
	
	# Define the codec and create VideoWriter object
	fourcc = cv2.VideoWriter_fourcc('M','P','E','G')
	out = cv2.VideoWriter(previewName + '.avi',fourcc, 20.0, (640,480))

	if cam.isOpened(): # try to get the first frame
		rval, frame = cam.read()
	else:
		rval = False
		print(previewName + 'is not opened')

	while rval:
		# write the frame
		out.write(frame)
		
		# show the fram
		cv2.imshow(previewName, frame)

		rval, frame = cam.read()
		if cv2.waitKey(10) == 27: # exit on 'Esc'
			break
	
	# release the resources
	cam.release()
	out.release()
#	cv2.destoryWindows(previewName)



thread0 = camThread("Camera 1", 0)
thread0.start()
thread1 = camThread("Camera 2", 1)
thread1.start()
thread2 = camThread("Camera 3", 2)
thread2.start()



# nCams = 3
# # for i in range(nCams):
# # 	thread = camThread("Camera" + str(i+1), 0)
# # 	thread.start()
