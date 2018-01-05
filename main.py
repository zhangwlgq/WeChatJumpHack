import os
import cv2
import numpy as np
import math
import time
import random

PADDING = 3
NUM = 0
DEBUG = False
INTERVAL = 3

def getImage():
	os.system("adb shell screencap -p /sdcard/screenshot.png")
	os.system("adb pull /sdcard/screenshot.png ./")
	return cv2.imread("screenshot.png")

def sendPress(t):
	os.system("adb shell input swipe %d %d %d %d %d" %(
		100*random.random(),
		100*random.random(),
		100*random.random(),
		100*random.random(),
		t))

def getStartPointRaw(rawImg):
	height, width, _ = rawImg.shape
	startPoint = [0, 0]
	for h in range(height / 6, height * 5 / 6):
		for w in range(width):
			if all(rawImg[h, w] == [95, 55, 56]) and h > startPoint[0]:
				startPoint = [h, w]
	return startPoint

def getStartPoint(rawImg, templatePath="template.png"):
	templateImg = cv2.imread(templatePath, 0)
	grayImg = cv2.cvtColor(rawImg, cv2.COLOR_BGR2GRAY)
	result = cv2.matchTemplate(grayImg, templateImg, cv2.TM_CCOEFF_NORMED)
	maxLoc = cv2.minMaxLoc(result)[-2]
	height = 182 + maxLoc[1]
	width = 44 + maxLoc[0]
	return [height, width]

def angle2radian(angle):
	return angle * 3.1415926 / 180.

def getSobelEdge(img):
	x = cv2.Sobel(img, cv2.CV_16S, 1, 0)
	y = cv2.Sobel(img, cv2.CV_16S, 0, 1)
	absX = cv2.convertScaleAbs(x)
	absY = cv2.convertScaleAbs(y)
	edgeImg = cv2.addWeighted(absX, 0.5, absY, 0.5, 0)
	_, edgeImg = cv2.threshold(edgeImg, 5, 255, cv2.THRESH_BINARY)
	return edgeImg

def getCannyEdge(img):
	edgeImg = cv2.Canny(img, 50, 200)
	return edgeImg	

def getEndPoint(rawImg, startPoint):
	global NUM
	grayImg = cv2.cvtColor(rawImg, cv2.COLOR_BGR2GRAY)
	sobelImg = getSobelEdge(grayImg)
	cannyImg = getCannyEdge(grayImg)
	height, width = sobelImg.shape


	topPoint = [startPoint[0], 0.]
	sameHeightNum = 0
	for h in range(height/6, startPoint[0]):
		for w in range(width):
			if w in range(startPoint[1] - 50, startPoint[1] + 50):
				continue
			if sobelImg[h, w] == 255:
				if h < topPoint[0]:
					sameHeightNum = 1
					topPoint = [h, w]
				elif h == topPoint[0]:
					topPoint[1] *= sameHeightNum
					sameHeightNum += 1.
					topPoint[1] = (topPoint[1] + w) / sameHeightNum
		if topPoint[0] != startPoint[0]:
			break
	topPoint[1] = int(topPoint[1])

	centerPoint = None
	for h in range(topPoint[0], topPoint[0] + height/6):
		if all(rawImg[h, topPoint[1]] == [245, 245, 245]):
			print "Combo!!!!!"
			centerPoint = [h+10, topPoint[1]]
			break

	if not centerPoint:
		rightPoint = None
		leftPoint = None
		h, w = topPoint
		i = 0.
		while True:
			i += 1
			h = topPoint[0] + int(i * math.sin(angle2radian(30.2))) + PADDING
			w = topPoint[1] - int(i * math.cos(angle2radian(30.2)))
			if cannyImg[h, w] == 255:
				rightPoint = [h, topPoint[1] + int(i * math.cos(angle2radian(30.2)))]
				leftPoint = [h, w]
				break
		centerPoint = [(rightPoint[0] + leftPoint[0]) / 2, (rightPoint[1] + leftPoint[1]) / 2]

	if DEBUG:
		points = [startPoint, centerPoint, topPoint]
		print points
		for point in points:
			rawImg[point[0], point[1]] = [0, 0, 255]
		cv2.imwrite("log/points%d.png" %NUM, rawImg)
		cv2.imwrite("log/canny%d.png" %NUM, cannyImg)
		cv2.imwrite("log/sobel%d.png" %NUM, sobelImg)

	NUM += 1
	return centerPoint

def main():
	lastTime = time.time()
	while True:
		if time.time() - lastTime > INTERVAL:
			image = getImage()
			startPoint = getStartPoint(image)
			startPointRaw = getStartPointRaw(image)
			if abs(startPoint[0] - startPointRaw[0]) > 180 or abs(startPoint[1] - startPointRaw[1]) > 80:
				startPoint = startPointRaw
				print "template match error!"
			endPoint = getEndPoint(image, startPoint)
			length = math.sqrt(math.pow(startPoint[0] - endPoint[0], 2) + math.pow(startPoint[1] - endPoint[1], 2))
			sendPress(length*1.295)
			lastTime = time.time()
		else:
			time.sleep(1.0)

if __name__ == "__main__":
	main()