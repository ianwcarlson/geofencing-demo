#!/bin/bash
# This script assumes the repo has already been cloned
# 
# Check if boot2docker and/or docker installed
REPONAME="geofencing-demo"
DOCKERIMAGETAG=":0.0.5"
DOCKERIMAGE="ianwcarlson/"$REPONAME$DOCKERIMAGETAG
REPOMOUNTPATH="/usr/local/"$REPONAME
DOCKERPATH=$(/usr/bin/which docker)
BOOT2DOCKERPATH=$(/usr/bin/which boot2docker)
SCRIPTDIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
echo $BOOT2DOCKERPATH
if [ "$BOOT2DOCKERPATH" ] || [ "$DOCKERPATH" ]; then
	if [ "$BOOT2DOCKERPATH" ]; then
		boot2docker start
	fi
	docker pull $DOCKERIMAGE
	docker run --rm -it -v $SCRIPTDIR:$REPOMOUNTPATH $DOCKERIMAGE /bin/bash $REPOMOUNTPATH/installDependencies.sh $REPOMOUNTPATH
else
	echo "Docker not installed, exiting..." 
	exit 1
fi

echo "Sucessfully installed package dependencies"
exit 0