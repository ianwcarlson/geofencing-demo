/**
 * Main Node.js/Express server.  Provides static file serving to client.
 * Uses Socket.io websocket API to send JSON objects back and forth with the 
 * client.  Also uses ZeroMQ wrapper to import the server-side network config
 * and publish JSON objects to subscribers
 */

var express = require('express');
var app = express();
var http = require('http').Server(app);
var io = require('socket.io')(http);
var scriptDir = process.cwd();
var path = require('path');
__dirname = path.dirname(module.filename);
var nameOfProcess = process.argv[2];
var pathToNetworkConfig = process.argv[3];

var pathToLib = path.join(__dirname,'..','lib','python-zeromq-pubsub',
	'src','processNode.js');

var processNode = require(pathToLib)(pathToNetworkConfig, 
	nameOfProcess, 0);

app.get('/', function(req, res){
  res.sendFile(__dirname + '/index.html');
});

var pathToLeafletDraw = path.join(__dirname,'clientLibs',
	'leaflet.draw','dist');
var pathToLeafletSmooth = path.join(__dirname,'clientLibs',
	'Leaflet.SmoothMarkerTransition','src');
var pathToClient = path.join(__dirname,'clientLibs');
var pathToMarkers = path.join(__dirname,'clientLibs',
	'Leaflet.MakiMarkers');

app.use(express.static(pathToLeafletDraw));
app.use(express.static(pathToLeafletSmooth));
app.use(express.static(pathToClient));
app.use(express.static(pathToMarkers));

var pointInPolygon = {};

io.on('connection', function(socket){
	pointInPolygon[socket.id] = false;
	socket.on('newPolygonPoints', function(newPolygonPoints){
		var objectToSend = {'id': socket.id, 'newPolygonPoints': newPolygonPoints};			
		processNode.send('newPolygonPoints', objectToSend);
	});
	socket.on('disconnect', function(){
		processNode.send('deletePolygonPoints', {'id': socket.id});
		delete pointInPolygon[socket.id]
	});
});

http.listen(3698, function(){
  console.log('listening on *:3698');
});	

processNode.onReceive(function(err, topic, message){
	switch (topic){
		case ('pointInPolygon'):
			var socketID = message.contents.id;
			var isInside = message.contents.isInside; 
			if (typeof(pointInPolygon[socketID]) !== undefined && 
				isInside != pointInPolygon[socketID]){
				io.to(socketID).emit('pointInPolygon', isInside);
				pointInPolygon[socketID] = isInside;
			}
			break;
		case ('interpGpsData'):
			io.emit('newGpsPoint', message['contents']);
			break;
		default:
			console.log('unrecognized topic');
	}
});	