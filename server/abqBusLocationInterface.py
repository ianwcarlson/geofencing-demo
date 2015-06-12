import urllib.request
from pykml import parser
import pdb
import os
import sys
import time
import json
import math
scriptDir=os.path.dirname(os.path.realpath(__file__))
sys.path.append(scriptDir)
sys.path.append(os.path.join(scriptDir,'..','lib','python-zeromq-pubsub','src'))
import processNode

UPDATE_INTERVAL_SECS = 1
TIME_BUFFER = 30
REMOTE_DATA_URL = "http://data.cabq.gov/transit/realtime/route/allroutes.kml"
TOTAL_SECS_IN_DAY = 24*60*60 

class AbqBusLocationInterface():
	def __init__(self, processName=None, fullConfigPath=None):		
		self.gpsInterfaceNode = processNode.ProcessNode(fullConfigPath, processName)
		self.done = False
		self.masterList = []
		self.prevMasterList = []

	def run (self):
		'''
		Polls the public bus data that's in a KML format.  The data is then parsed 
		and stuffed into a data structure that's optimal to publish internally.  
		'''
		while(not(self.done)):
			kmlString = b''
			kmlDoc = None
			try:
				kmlString = urllib.request.urlopen(REMOTE_DATA_URL).read()
			except:
				self.gpsInterfaceNode.log(logLevel=3, message="Unable to download remote data")

			fixedString = kmlString.decode('utf8', 'replace')
			if (kmlString != b''):
				try:
					kmlDoc = parser.fromstring(fixedString.encode())
				except:
					self.gpsInterfaceNode.log(logLevel=3, message="Unable to parse remote data")

				if (kmlDoc != None):
					documentChildren = kmlDoc.Document.getchildren()
					for item in documentChildren:
						vehicleID = ''
						routeTime = ''
						routeName = ''
						lat = None
						lng = None
						itemTag = item.tag
						if (itemTag.find('Placemark') != -1):
							routeName = str(item.name)
							tableItems = item.description.table.getchildren()
							for tableItem in tableItems:
								tableChildren = tableItem.getchildren()
								if (tableItem.td == 'Vehicle #'):
									vehicleID = str(tableChildren[1])
								elif (tableItem.td == 'Msg Time'):
									routeTime = self.convertTime(str(tableChildren[1]))

							routeLocation = item.Point.coordinates
							valid, lat, lng = self.parseCoordinates(str(routeLocation))
							if (valid):
								self.masterList.append({
									'vehicleID': vehicleID,
									'route': routeName,
									'timeStamp': routeTime,
									'latitude': lat,
									'longitude': lng
								})

					if (len(self.prevMasterList) != 0 and self.prevMasterList != self.masterList):
						newIdx = 0
						filteredMasterList = self.masterList
						while(newIdx < len(filteredMasterList)):
							newItem = filteredMasterList[newIdx]
							vehicleFound = False
							for oldItem in self.prevMasterList:
								if (newItem['vehicleID'] == oldItem['vehicleID']):
									latList = [oldItem['latitude'], newItem['latitude']]
									longList = [oldItem['longitude'], newItem['longitude']]
									invalid = self.detectAndSanitizeGPSJumps(latList, longList)
									if (invalid):
										filteredMasterList.pop(newIdx)
									break

							newIdx += 1

						self.sendMsgs()
						self.gpsInterfaceNode.log(logLevel=0, message=filteredMasterList)
						
					self.prevMasterList = self.masterList
					self.masterList = []

					time.sleep(UPDATE_INTERVAL_SECS)

	def detectAndSanitizeGPSJumps(self, latList, longList):
		'''
		Checks to see if there are large GPS jumps and filter them out
		'''
		invalid = False
		for idx in range(len(latList) - 1):
			delta = self.calcRectDistanceKM(latList[idx], latList[idx+1], longList[idx], longList[idx+1])
			if (delta > 1):
				self.gpsInterfaceNode.log(logLevel=0, message="Large GPS jump detected: " + str(delta))
				invalid = True
				break

		return invalid

	def calcRectDistanceKM(self, lat1, lat2, long1, long2):
		'''
		Calculate distance using equirectangular approximation
		'''
		EARTHRADIUSKM = 6371
		x = (math.radians(long2 - long1)) * math.cos(math.radians((lat1+lat2)/2))
		y = math.radians(lat2 - lat1)
		d = math.sqrt(x*x + y*y) * EARTHRADIUSKM
		return d

	def parseCoordinates(self, coordinatesString):
		'''
		Custom little parser that converts the comma delimted latitude and 
		longitude coordinates into pythonic data
		'''
		validCoordinates = False
		lng = -360
		lat = -360
		firstIndex = coordinatesString.find(',')
		if (firstIndex != -1):
			lng = float(coordinatesString[0:firstIndex])
			lat = float(coordinatesString[firstIndex+1:])
			if (lat > -90 and lat < 90 and lng > -180 and lng < 180):
				validCoordinates = True

		return validCoordinates, lat, lng

	def sendMsgs(self):
		'''
		Wrapper for publishing/sending the parsed GPS data structure to 
		subscribers
		'''
		self.gpsInterfaceNode.send('gpsData', self.masterList)

	def convertTime(self, timeStamp):
		'''
		Converts human time to time of day (in seconds)
		'''
		hour, minute, sec = self.parseHumanTime(timeStamp)
		return self.convertHumanToSecsInDay(hour, minute, sec)

	def parseHumanTime(self, timeStamp):
		'''
		:param timeStamp: time in human readable <hour>:<min>:<sec>
		'''
		hour = -1
		minute = -1
		sec = -1
		firstIndex = -1
		firstIndex = timeStamp.find(':') 
		if (firstIndex != -1):
			hour = int(timeStamp[0:firstIndex])
			if (timeStamp.find('PM')):
				hour += 12
			secondIndex = timeStamp.find(':', firstIndex+1) 
			if (secondIndex != -1):
				minute = int(timeStamp[firstIndex+1: secondIndex])
				thirdIndex = timeStamp.find(' ', secondIndex+1)
				if (thirdIndex != -1):
					sec = int(timeStamp[secondIndex+1: thirdIndex])

		if (hour == -1 or minute == -1 or sec == -1):
			gpsInterfaceNode.log(logLevel=3, message="Unable to parse time stamp")

		return hour, minute, sec

	def convertHumanToSecsInDay(self, hour, minute, sec):
		'''
		Convert hours, minutes, seconds to total seconds elapsed during the day 
		'''
		return hour*3600 + minute*60 + sec

	def adjustTime(self, secsInDay):
		'''
		Need to calculate valid time window because there are garbage time stamps
		in the data and handle wrap condition
		'''
		newSecs = secsInDay - TIME_BUFFER
		if (newSecs < 0):
			newSecs = TOTAL_SECS_IN_DAY + newSecs

		return newSecs

if __name__ == '__main__':
	if (len(sys.argv) == 3):
		gpsInterface = AbqBusLocationInterface(sys.argv[1], sys.argv[2])
	else:
		gpsInterface = AbqBusLocationInterface()

gpsInterface.run()