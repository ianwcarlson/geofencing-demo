import urllib.request
from pykml import parser
import pdb
import os
import sys
import time
import 
from Sets import Set
scriptDir=os.path.dirname(os.path.realpath(__file__))
sys.path.append(scriptDir)
sys.path.append(os.path.join(scriptDir,'..','lib','python-zeromq-pubsub','src'))
import timeApiKey

UPDATE_INTERVAL_SECS = 3
TIME_BUFFER = 30
REMOTE_DATA_URL = "http://data.cabq.gov/transit/realtime/route/route790.kml"
TOTAL_SECS_IN_DAY = 24*60*60 

class AbqBusLocationInterface():
	def __init__(self, processName=None, fullConfigPath=None):		
		#gpsInterfaceNode = processNode.ProcessNode(fullConfigPath, processName)
		done = False
		epochStamp = self._getCurrentUtcTime()
		self.adjustedSeedTime = epochStamp - 30
		self.seedTimeTuple = time.gmtime(self.adjustedSeedTime)
		seedTimeString = 'SeedTime: ' + str(timeTuple.tm_hour) + ':' + \
			str(timeTuple.tm_min) + ':' + str(timeTuple.tm_sec)
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

				documentChildren = kmlDoc.Document.getchildren()



				for item in documentChildren:
					itemTag = item.tag
					if (itemTag.find('Placemark') != -1):
						routeName = item.name
						masterDict[routeName] = []

						tableItems = item.description.table.getchildren()
						for tableItem in tableItems:
							if (tableItem.td == 'Msg Time'):
								timeItems = tableItem.getchildren()
								routeTime = timeItems[1]

						routeLocation = item.Point.coordinates
						masterDict[routeName].append

						print ('Route: ' + str(routeName) + \
							' Time: ' + str(routeTime) + \
							' Location: ' + routeLocation)

				if (kmlDoc != None):
				#	gpsDataMsg = {
					# 	'latitude': point.latitude,
					# 	'longitude': point.longitude,
					# 	'altitude': point.elevation				
					# }
					# gpsInterfaceNode.send('gpsData', gpsDataMsg)
					# gpsInterfaceNode.log(logLevel=0, message=gpsDataMsg)
					time.sleep(UPDATE_INTERVAL_SECS)

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
			self.masterDict[item] = []

	def parseHumanTime(self, timeStamp):
		'''
		:param timeStamp: time in human readable <hour>:<min>:<sec>
		'''
		hour = -1
		minute = -1
		sec = -1
		if (len(timeStamp) < 10):
			gpsInterfaceNode.log(logLevel=3, message="Invalid time stamp")
		else:
			firstIndex = timeStamp.find(':') 
			if (firstIndex != -1):
				hour = timeStamp[0:firstIndex]
				if (timeStamp.find('PM'):
					hour += 12
				secondIndex = timeStamp.find(':', firstIndex) 
				if (secondIndex != -1):
					minute = timeStamp[firstIndex+1, secondIndex]
					thirdIndex = timeStamp.find(' ', secondIndex)
					if (thirdIndex != -1):
						sec = timeStamp[secondIndex+1, thirdIndex]

		print (hour + ':' + minute + ':' + sec)
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

	def orderAndWindowTime

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
