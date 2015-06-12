#!/bin/bash
SCRIPTDIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
docker run --rm -it -v $SCRIPTDIR:/usr/local/geofencing-demo \
	-p 3698:3698 ianwcarlson/geofencing-demo:0.0.5 \
	python3 /usr/local/geofencing-demo/server/main.py