"""
.. module:: RealTimeGpsSequencer
    :synopsis: Subscribes to non-interpolated GPS data, interpolates
    the data to achieve 1 second time resolution, and replays 
    interpolated data in real-time
"""

import urllib.request
import pdb
import os
import sys
import time
import json
import numpy as np
import math
scriptDir=os.path.dirname(os.path.realpath(__file__))
sys.path.append(scriptDir)
sys.path.append(os.path.join(scriptDir,'..','lib','python-zeromq-pubsub','src'))
import processNode

TIME_INCREMENT = 1
MAX_TIMEOUT = 30
NUM_TIME_INTERVAL = 13
SECONDS_IN_DAY = 86400

class RealTimeGpsSequencer():
	def __init__(self, processName=None, fullConfigPath=None):		
		self.gpsInterfaceNode = processNode.ProcessNode(fullConfigPath, processName)
		self.prevMasterList = []
		self.interpDict = {}
		self.internalCounter = 0

	def run(self):
		"""
		Interpolates GPS points and sends them along in real-time 
		"""
		done = False
		while(not(done)):
			responseListDict = self.gpsInterfaceNode.receive()
			for itemDict in responseListDict:
				topic = itemDict['topic']
				if (topic == 'proc'):
					if (itemDict['contents']['action'] == 'stop'):
						done = True
						break
				elif(topic == 'gpsData'):	
					masterList = itemDict['contents']
					if (len(self.prevMasterList) != 0):
						self.interpolateAllValues(masterList)
					else:
						self.initializeInternalCounter(masterList)

					self.prevMasterList = masterList

			self.playbackInterpGps()		
			time.sleep(TIME_INCREMENT)
			if (self.internalCounter > SECONDS_IN_DAY):
				self.internalCounter = 0
			else:				
				self.internalCounter += TIME_INCREMENT
			self.gpsInterfaceNode.log(logLevel=0, message='internalCount: ' + str(self.internalCounter))

	def initializeInternalCounter(self, masterList):
		'''
		Initializes the internal counter to whatever the current time of day is 
		in seconds.  Buffers the initial value to ensure non of the timeStamps 
		coming in get skipped.
		'''
		self.internalCounter = SECONDS_IN_DAY
		for item in masterList:
			if (item['timeStamp'] < self.internalCounter):
				self.internalCounter = item['timeStamp'] - NUM_TIME_INTERVAL

	def playbackInterpGps(self):
		'''
		<vehicleID>:{
			<route>: number,
			<timeStampList>: list of numbers,
			<latList>: list of latitude numbers,
			<longList>: list of longitude numbers
		}
		'''
		masterList = []
		for key, value in self.interpDict.items():
			foundIdx = len(value['timeStampList']) - 1
			for idx in range(foundIdx + 1):
				if (value['timeStampList'][idx] >= self.internalCounter):
					interpDict = {
						'vehicleID': key,
						'route': value['route'],
						'timeStamp': value['timeStampList'][idx],
						'latitude': value['latList'][idx],
						'longitude': value['longList'][idx]
					}
					
					self.gpsInterfaceNode.send('interpGpsData', interpDict)
					masterList.append({
						'latitude': interpDict['latitude'], 
						'longitude': interpDict['longitude']
					})
					foundIdx = idx
					break

			value['timeStampList'] = value['timeStampList'][foundIdx+1:]
			value['latList'] = value['latList'][foundIdx+1:]
			value['longList'] = value['longList'][foundIdx+1:]

		self.gpsInterfaceNode.send('interpMasterGpsData', masterList)

	def interpolateAllValues(self, newMasterList):
		'''
		Interpolates the latitude and longitude values separately using
		linear interpolation and stuffs the results into a dictionary that
		uses the vehicle ID as a key.
		'''
		interpList = []
		for item in newMasterList:
			for prevItem in self.prevMasterList:
				if (prevItem['vehicleID'] == item['vehicleID']):
					timeStampList = self.calcXList(prevItem['timeStamp'],
						item['timeStamp'], item['timeStamp'] - prevItem['timeStamp'])
					latList = self.simpleLinearInterpolation(timeStampList,
						prevItem['timeStamp'], item['timeStamp'],
						prevItem['latitude'], item['latitude'])
					longList = self.simpleLinearInterpolation(timeStampList,
						prevItem['timeStamp'], item['timeStamp'],
						prevItem['longitude'], item['longitude'])
					itemID = item['vehicleID']
					if (itemID not in self.interpDict):
						self.interpDict[itemID] = {
							'route': item['route'],
							'timeStampList': [],
							'latList': [],
							'longList': []
						}
					self.interpDict[itemID]['timeStampList'] += timeStampList.tolist()
					self.interpDict[itemID]['latList'] += latList
					self.interpDict[itemID]['longList'] += longList
					break

		return interpList

	def calcXList(self, x1, x2, numXInterval):
		'''
		Returns a vector of equally spaced time stamps
		'''
		return np.linspace(x1, x2, num=numXInterval)

	def simpleLinearInterpolation(self, xInterp, x1, x2, y1, y2):
		'''
		Interpolation using Numpy's library call
		'''
		yArray = np.array((y1, y2), dtype=np.float32)
		xArray = np.array((x1, x2), dtype=np.float32)

		yInterp = np.interp(xInterp, xArray, yArray)

		return yInterp.tolist()

if __name__ == '__main__':
	gpsInterface = RealTimeGpsSequencer(sys.argv[1], sys.argv[2])

gpsInterface.run()