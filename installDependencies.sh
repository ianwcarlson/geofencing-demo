#!/bin/bash
# This script assumes the repo has already been cloned and it's being
# run in a Docker container so no need to reset sym links
# 
PROJECTROOTPATH=$1
echo $PROJECTROOTPATH
/bin/rm /usr/bin/python
/bin/ln -s /usr/bin/python2 /usr/bin/python
if [ $PROJECTROOTPATH ]; then
#	/usr/bin/cd $PROJECTROOTPATH
	npm install $PROJECTROOTPATH
	cd $PROJECTROOTPATH && bower install -s -q --allow-root $PROJECTROOTPATH
else
	echo "Need to pass in the project root as the first parameter"
	exit 1
fi
exit 0