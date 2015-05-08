import urllib.request
from pykml import parser
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

UPDATE_INTERVAL_SECS = 3
TIME_BUFFER = 30
REMOTE_DATA_URL = "http://data.cabq.gov/transit/realtime/route/route790.kml"
TOTAL_SECS_IN_DAY = 24*60*60 

def getTimeKey(inDict):
	return inDict['timeStamp']

class AbqBusLocationInterface():
	def __init__(self, processName=None, fullConfigPath=None):		
		gpsInterfaceNode = processNode.ProcessNode(fullConfigPath, processName)
		done = False
		epochStamp = self._getCurrentUtcTime()
		self.adjustedSeedTime = epochStamp - 30
		self.seedTimeTuple = time.gmtime(self.adjustedSeedTime)
		seedTimeString = 'SeedTime: ' + str(self.seedTimeTuple.tm_hour) + ':' + \
			str(self.seedTimeTuple.tm_min) + ':' + str(self.seedTimeTuple.tm_sec)
		print (seedTimeString)
		self.masterDict = {}

		while(not(done)):
			kmlString = ''
			kmlDoc = None
			try:
				kmlString = urllib.request.urlopen(REMOTE_DATA_URL).read()
			except HTTPError as err:
				print ("Unable to download remote data")
				gpsInterfaceNode.log(logLevel=3, message="Unable to download remote data")

			fixedString = kmlString.decode('utf8', 'replace')
			if (kmlString != ''):
				try:
					kmlDoc = parser.fromstring(fixedString.encode())
				except:
					gpsInterfaceNode.log(logLevel=3, message="Unable to parse remote data")

				if (kmlDoc != None):
					documentChildren = kmlDoc.Document.getchildren()
					validRoutes = self.findValidRoutes(documentChildren)
					self.initializeMasterDict(validRoutes)
					for item in documentChildren:
						itemTag = item.tag
						if (itemTag.find('Placemark') != -1):
							routeName = str(item.name)
							tableItems = item.description.table.getchildren()
							for tableItem in tableItems:
								if (tableItem.td == 'Msg Time'):
									timeItems = tableItem.getchildren()
									routeTime = self.convertTime(str(timeItems[1]))

							routeLocation = item.Point.coordinates
							valid, lat, lng = self.parseCoordinates(str(routeLocation))
							if (valid):
								self.masterDict[routeName].append({
									'timeStamp': routeTime,
									'lat': lat,
									'lng': lng
								})

							# print ('Route: ' + str(routeName) + \
							# 	' Time: ' + str(routeTime) + \
							# 	' Location: ' + routeLocation)
					self.orderMasterDict()
					self.removeInvalidTimeStamps()
					print ('self.masterDict: ' + str(self.masterDict))
					gpsInterfaceNode.send('gpsDataRaw', self.masterDict)
					gpsInterfaceNode.log(logLevel=0, message=self.masterDict)
					time.sleep(UPDATE_INTERVAL_SECS)

	def parseCoordinates(self, coordinatesString):
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

	def orderMasterDict(self):
		for key, value in self.masterDict.items():
			self.masterDict[key] = sorted(value, key=getTimeKey)

	def removeInvalidTimeStamps(self):
		for key, value in self.masterDict.items():
			matchTimeList = []
			idx = 0
			while(idx < len(value)):
				timeStamp = value[idx]['timeStamp']
				if timeStamp not in matchTimeList:
					matchTimeList.append(timeStamp)
				else:
					value.pop(idx)

				idx += 1

			matchTimeList.sort()

			# remove timestamps that are more than N seconds in the past
			# not sure why these datapoints are in there
			idx = 0
			while(idx < len(value)):
				timeStamp = value[idx]['timeStamp']
				if (timeStamp < matchTimeList[-1] - TIME_BUFFER):
					value.pop(idx)

				idx += 1

	def findValidRoutes(self, kmlDocChildren):
		validRoutes = []
		for item in kmlDocChildren:
			itemTag = item.tag
			if (itemTag.find('Placemark') != -1):
				validRoutes.append(item.name)

		return set(validRoutes)

	def initializeMasterDict(self, validRoutesSet):
		self.masterDict = {}
		for item in validRoutesSet:
			self.masterDict[str(item)] = []

	def convertTime(self, timeStamp):
		hour, minute, sec = self.parseHumanTime(timeStamp)
		return self.convertHumanToSecsInDay(hour, minute, sec)

	def parseHumanTime(self, timeStamp):
		'''
		:param timeStamp: time in human readable <hour>:<min>:<sec>
		'''
		hour = -1
		minute = -1
		sec = -1
		# pdb.set_trace()
		# if (len(timeStamp) < 10):
		# 	gpsInterfaceNode.log(logLevel=3, message="Invalid time stamp")
		# else:
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

		# print (str(hour) + ':' + str(minute) + ':' + str(sec))
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

	def _getCurrentUtcTime(self):
		epochStamp = 0
		url = 'http://api.timezonedb.com/?key=' + timeApiKey.key + \
		'&zone=America/Denver&format=json'		
		timeJson = urllib.request.urlopen(url).read()
		try:
			epochStamp = json.loads(timeJson.decode())['timestamp']
		except:
			gpsInterfaceNode.log(logLevel=3, message="Unable to get current MST time")

		return epochStamp

if __name__ == '__main__':
	if (len(sys.argv) == 3):
		gpsInterface = AbqBusLocationInterface(sys.argv[1], sys.argv[2])
	else:
		gpsInterface = AbqBusLocationInterface()
