import urllib.request
import pdb
import os
import sys
import time
import json
scriptDir=os.path.dirname(os.path.realpath(__file__))
sys.path.append(scriptDir)
sys.path.append(os.path.join(scriptDir,'..','lib','python-zeromq-pubsub','src'))
import processNode
import timeApiKey

TIME_INCREMENT = 1
MAX_TIMEOUT = 30

class RealTimeGpsSequencer():
	def __init__(self, processName=None, fullConfigPath=None):		
		self.gpsInterfaceNode = processNode.ProcessNode(fullConfigPath, processName)

	def run(self):
		"""
		Main run function receives GPS data chunks and sends them out when their
		timestamps occur
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
				elif(topic == 'rawGpsData'):	
					self.masterDict = itemDict['contents']
					self.masterTime = self.findMinTime(self.masterDict)
					timeout = MAX_TIMEOUT
					while(not(self.checkIfAllMessagesSent()) and timeout != 0):
						self.sendCurrentMsg()
						self.masterTime += TIME_INCREMENT
						time.sleep(TIME_INCREMENT)
						timeout -= TIME_INCREMENT

	def findMinTime(self, masterDict):
		minTimesList = []
		for key, value in masterDict.items():
			minTimesList.append(value[0]['timeStamp'])

		minTimesList.sort()
		return minTimesList[0]

	def sendCurrentMsg(self):
		for key, value in self.masterDict.items():
			currentRouteDict = value[0]
			if (currentRouteDict['timeStamp'] == self.masterTime):
				gpsData = {
					'id': key,
					'latitude': currentRouteDict['lat'],
					'longitude': currentRouteDict['lng'],
					'timeStamp': currentRouteDict['timeStamp']
				}
				self.gpsInterfaceNode.send('gpsData', gpsData)
				print ('gpsData: ' + str(gpsData))
				value.pop(0)

	def checkIfAllMessagesSent(self):
		allSent = True
		for key, value in self.masterDict.items():
			if (value != []):
				allSent = False 
				break

		return allSent

if __name__ == '__main__':
	gpsInterface = RealTimeGpsSequencer(sys.argv[1], sys.argv[2])

gpsInterface.run()