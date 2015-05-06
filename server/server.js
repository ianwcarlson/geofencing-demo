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

app.use(express.static(__dirname + '../bower_compenents/leaflet.draw/dist'));

io.on('connection', function(socket){
	socket.on('newPolygonPoints', function(newPolygonPoints){			
		processNode.send(['newPolygonPoints', newMsg]);
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