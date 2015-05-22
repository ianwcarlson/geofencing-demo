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

UPDATE_INTERVAL_SECS = 1
TIME_BUFFER = 30
REMOTE_DATA_URL = "http://data.cabq.gov/transit/realtime/route/route790.kml"
TOTAL_SECS_IN_DAY = 24*60*60 

def getTimeKey(inDict):
	return inDict['timeStamp']

class AbqBusLocationInterface():
	def __init__(self, processName=None, fullConfigPath=None):		
		self.gpsInterfaceNode = processNode.ProcessNode(fullConfigPath, processName)
		self.done = False
		# epochStamp = self._getCurrentUtcTime()
		# self.adjustedSeedTime = epochStamp - 30
		# self.seedTimeTuple = time.gmtime(self.adjustedSeedTime)
		# seedTimeString = 'SeedTime: ' + str(self.seedTimeTuple.tm_hour) + ':' + \
		# 	str(self.seedTimeTuple.tm_min) + ':' + str(self.seedTimeTuple.tm_sec)
		self.masterList = []
		self.prevMasterList = []

	def run (self):
		while(not(self.done)):
			kmlString = ''
			kmlDoc = None
			try:
				kmlString = urllib.request.urlopen(REMOTE_DATA_URL).read()
			except:
				print ("Unable to download remote data")
				self.gpsInterfaceNode.log(logLevel=3, message="Unable to download remote data")

			fixedString = kmlString.decode('utf8', 'replace')
			if (kmlString != ''):
				try:
					kmlDoc = parser.fromstring(fixedString.encode())
				except:
					self.gpsInterfaceNode.log(logLevel=3, message="Unable to parse remote data")

				if (kmlDoc != None):
					documentChildren = kmlDoc.Document.getchildren()
					# validRoutes = self.findValidRoutes(documentChildren)
					# self.initializeMasterDict(validRoutes)
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
						# print ('something new')
						self.sendMsgs()
						self.gpsInterfaceNode.log(logLevel=0, message=self.masterList)
						
					self.prevMasterList = self.masterList
					self.masterList = []

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

	def sendMsgs(self):
		self.gpsInterfaceNode.send('gpsData', self.masterList)

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

gpsInterface.run()