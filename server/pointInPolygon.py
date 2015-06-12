"""
.. module:: pointInPolygon
    :synopsis: ray casting algorithm, currently doesn't detect right on
    boundaries.  Refer to http://www.ariel.com.au/a/python-point-int-poly.html
    and http://geospatialpython.com/2011/08/point-in-polygon-2-on-line.html
    for more info.  Just needed a quick implementation to demonstrate
    the architecture
"""
import os
import sys
import time
scriptDir=os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(scriptDir,'..','lib','python-zeromq-pubsub','src'))
import processNode

class PointInAPolygon():
    def __init__(self, processName, fullConfigPath):
        self.polygonDict = {}
        self.pointInPolygonNode = processNode.ProcessNode(fullConfigPath, processName)

    def run(self):
        """
        Main run function receives gpsData, processes them, and sends them to
        subscribers.  This function manages the data structure that contains
        a unique id string and a list of vertices for user-drawn polygon.  When
        a new GPS point comes in the its location is tested against the provided
        polygon vertices.
        """
        done = False
        while(not(done)):
            responseListDict = self.pointInPolygonNode.receive()
            for itemDict in responseListDict:
                topic = itemDict['topic']
                contents = itemDict['contents']
                if (topic == 'proc'):
                    if (contents['action'] == 'stop'):
                        done = True
                        break
                elif(topic == 'interpMasterGpsData'):
                    gpsDataList = contents
                    isInside = False

                    for userID, listOfPolygonPoints in self.polygonDict.items():
                        for gpsCoordinatesDict in gpsDataList:
                            isInside = self.pointInsidePolygon(gpsCoordinatesDict['latitude'], 
                                gpsCoordinatesDict['longitude'], listOfPolygonPoints)
                            if (isInside):
                                break

                        logMsg = 'Inside' if (isInside) else 'Outside'
                        self.pointInPolygonNode.log(logLevel=0, message=logMsg)
                        self.pointInPolygonNode.send('pointInPolygon', {
                            'id': userID,
                            'isInside': isInside
                        })
                elif(topic == 'newPolygonPoints'):
                    self.pointInPolygonNode.log(logLevel=0, message=contents)
                    userID = contents['id']
                    if (not(userID in self.polygonDict)):
                        self.polygonDict[userID] = []
                    newPolygonPoints = contents['newPolygonPoints']
                    listOfTuples = self.convertDictsToTuples(newPolygonPoints)
                    self.polygonDict[userID] = listOfTuples

                elif(topic == 'deletePolygonPoints'):
                    userID = contents['id']
                    try:
                        self.polygonDict.pop(userID, None)
                    except:
                        self.pointInPolygonNode.log(logLevel=2, \
                            message="user ID key not found in polygon structure")

            time.sleep(0.01)

    @staticmethod
    def convertDictsToTuples(listOfDicts):
        '''
        Convert to list of tuples
        :param listOfDicts
        :type listOfDicts: list of dictionaries
        :returns: list of dictionaries
        '''
        listOfTuples = []
        for dictItem in listOfDicts:
            listOfTuples.append((dictItem['lat'],dictItem['lng']))

        return listOfTuples

    @staticmethod
    def pointInsidePolygon(x,y,poly):
        '''
        Find point inside of polygon
        :param x: latitude of test point
        :type x: float
        :param y: longitude of test point
        :type y: float
        :param poly: list of latitude/longitude pairs
        :type poly: list of tuple pairs
        :returns: boolean
        '''

        n = len(poly)
        inside =False
        if (n != 0):
            p1x,p1y = poly[0]
            for i in range(n+1):
                p2x,p2y = poly[i % n]
                if y > min(p1y,p2y):
                    if y <= max(p1y,p2y):
                        if x <= max(p1x,p2x):
                            if p1y != p2y:
                                xinters = (y-p1y)*(p2x-p1x)/(p2y-p1y)+p1x
                            if p1x == p2x or x <= xinters:
                                inside = not inside
                p1x,p1y = p2x,p2y

        return inside

if __name__ == '__main__':
    pointInAPolygon = PointInAPolygon(sys.argv[1], sys.argv[2])
    pointInAPolygon.run()