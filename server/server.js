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

app.use(express.static(pathToLeafletDraw));
app.use(express.static(pathToLeafletSmooth));
app.use(express.static(pathToClient));

io.on('connection', function(socket){
	socket.on('newPolygonPoints', function(newPolygonPoints){			
		processNode.send('newPolygonPoints', newPolygonPoints);
	});
});

http.listen(3698, function(){
  console.log('listening on *:3698');
});	

pointInPolygon = false;
processNode.onReceive(function(err, topic, message){
	switch (topic){
		case ('pointInPolygon'):
			if (message['contents'] != pointInPolygon){
				io.emit('pointInPolygon', message['contents']);
				pointInPolygon = message['contents'];	
			}
			break;
		case ('gpsData'):
			io.emit('newGpsPoint', message['contents']);
			break;
		default:
			console.log('unrecognized topic');
	}
});	