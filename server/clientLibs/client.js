var socket = io();

var osmUrl = 'http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
	osmAttrib = '&copy; <a href="http://openstreetmap.org/copyright">OpenStreetMap</a> contributors',
	osm = L.tileLayer(osmUrl, {maxZoom: 18, attribution: osmAttrib}),
	map = new L.Map('map', {
		layers: [osm], 
		center: new L.LatLng(35.08444, -106.6505556), 
		zoom: 15,
		zoomAnimation: false,
		fadeAnimation: false,
		markerZoomAnimation: false
	});

var userMarker = null;
var vehicleMarkerIDArray = [];

socket.on('newGpsPoint', function(newGpsPoint){
	var latlngPoint = new L.LatLng(newGpsPoint.latitude, newGpsPoint.longitude);
	var marker = getVehicleMarker(newGpsPoint.vehicleID);
	if (marker === null){
		vehicleMarker = new L.SmoothMarkerTransition(latlngPoint, map, {
			traverseTime: 1000,
			markerID: newGpsPoint.vehicleID
		});
		vehicleMarkerIDArray.push(vehicleMarker);
		vehicleMarker.addTo(map);
		//userMarker = new L.Marker(latlngPoint);
		//userMarker.addTo(map);
		// map.setView(latlngPoint, 15);
	} else {
		marker.transition(latlngPoint);
		//userMarker.setLatLng(latlngPoint);
	}
});

function getVehicleMarker(vehicleID){
	var marker = null;
	var arrayLength = vehicleMarkerIDArray.length;
	for (var i=0; i<arrayLength; i++){
		if (vehicleMarkerIDArray[i].getMarkerID() === vehicleID){
			marker = vehicleMarkerIDArray[i];
			break;
		}
	}
	return marker;
}

var drawnItems = new L.FeatureGroup();
map.addLayer(drawnItems);

var drawControl = new L.Control.Draw({
	draw: {
		position: 'topleft',
		polygon: {
			title: 'Draw a sexy polygon!',
			allowIntersection: false,
			drawError: {
				color: '#b00b00',
				timeout: 1000
			},
			shapeOptions: {
				color: '#CC3300'
			},
			showArea: true
		},
		polyline: false,
		circle: false,
		marker: false,
		rectangle: false
	},
	edit: {
		featureGroup: drawnItems
	}
});
map.addControl(drawControl);

map.on('draw:created', function (e) {
	var type = e.layerType,
		layer = e.layer;

	if (type === 'polygon') {
		var latlngs = layer.getLatLngs();
		notifyServerPolygonPoints(latlngs);
	}

	drawnItems.addLayer(layer);
});
map.on('draw:edited', function(e){
	var layers = e.layers;
	layers.eachLayer(function (layer) {
		var latlngs = layer.getLatLngs();
		notifyServerPolygonPoints(latlngs);
	});			
});
map.on('draw:deleted', function(e){
	var layers = e.layers;
	layers.eachLayer(function (layer) {
		var latlngs = [];
		notifyServerPolygonPoints(latlngs);
	});	
});
function notifyServerPolygonPoints(latlngs){
	console.log('new lat longs: ', latlngs);
	socket.emit('newPolygonPoints', latlngs);
}

function changeColorOfPolygon(newColor){
	var elems = document.getElementsByTagName('path');
	elems[0].setAttribute('stroke', newColor);
	elems[0].setAttribute('fill', newColor);
}

socket.on('pointInPolygon', function(isPointInPolygon){
	console.log('new is point in polygon: ', isPointInPolygon);
	if (isPointInPolygon){
		changeColorOfPolygon('#336600');
	} else {
		changeColorOfPolygon('#CC3300');		
	}
});