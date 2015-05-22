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
		var color = getIconColor(newGpsPoint.route)
		var icon = L.MakiMarkers.icon({icon: 'bus', color: color, size: "m"})
		vehicleMarker = new L.SmoothMarkerTransition(latlngPoint, map, {
			traverseTime: 1000,
			markerID: newGpsPoint.vehicleID,
			icon: icon
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

function getIconColor(route){
	color = '';
	switch(route){
		case('1'):
			color = '#EEDFCC';
			break;
		case('2'):
			color = '#8B8378';
			break;
		case('5'):
			color = '#76EEC6';
			break;
		case('6'):
			color = '#458B74';
			break;
		case('7'):
			color = '#C1CDCD';
			break;
		case('8'):
			color = '#838B8B';
			break;
		case('10'):
			color = '#EED5B7';	
			break;
		case('11'):
			color = '#8B7D6B';
			break;
		case('12'):
			color = '#0000FF';
			break;
		case('13'):
			color = '#00008B';
			break;
		case('16'):
			color = '#8A2BE2';
			break;
		case('31'):
			color = '#A52A2A';
			break;
		case('34'):
			color = '#FF4040';
			break;
		case('36'):
			color = '#DEB887';
			break;
		case('40'):
			color = '#8B7355';
			break;
		case('50'):
			color = '#98F5FF';
			break;
		case('51'):
			color = '#53868B';
			break;
		case('53'):
			color = '#66CD00';
			break;
		case('54'):
			color = '#458B00';
			break;
		case('66'):
			color = '#FF7F24';
			break;
		case('92'):
			color = '#CD661D';
			break;
		case('93'):
			color = '#8B4513';
			break;
		case('94'):
			color = '#FF7F50';
			break;
		case('96'):
			color = '#FF7256';
			break;
		case('97'):
			color = '#CD5B45';
			break;
		case('98'):
			color = '#8B3E2F';
			break;
		case('140'):
			color = '#6495ED';
			break;
		case('141'):
			color = '#CDC8B1';
			break;
		case('155'):
			color = '#8B8878';
			break;
		case('157'):
			color = '#DC143C';
			break;
		case('162'):
			color = '#00CDCD';
			break;
		case('198'):
			color = '#008B8B';
			break;	
		case('217'):
			color = '#FFB90F';
			break;
		case('222'):
			color = '#CD950C';
			break;
		case('250'):
			color = '#8B6508';
			break;
		case('251'):
			color = '#006400';
			break;
		case('551'):
			color = '#BDB76B';
			break;
		case('766'):
			color = '#A2CD5A';
			break;
		case('777'):
			color = '#6E8B3D';
			break;
		case('790'):
			color = '#8B0000';
			break;
		default:
			color = '#68228B';

	}
	return color;
}