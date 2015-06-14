# geofencing-demo

This app polls the open Albuquerque bus tracking data and displays the bus
locations in real-time.  The source data only updates every 13-15 seconds so interpolation is used to get 1 second update rate.  The user can draw a polygon on the map and it will change its color to green if any bus is located within the polygon.  The polygon will change to red if there is no bus contained within.  Currently, only one polygon is supported, but it can be deleted and redrawn.  

The ZeroMQ framework (Python) is used to publish/subscribe messages to/from
each micro service that's running server side via IPC.  A node server utilizes the ZeroMQ framework to communicate to server-side services, but also uses websockets (via socket.io library) to communicate with the client.  All the processes run asychronously.  

A network configuration file expressed in JSON syntax configures the network topology and publish/subscribe details.  

# Installation

- Install [boot2docker](https://docs.docker.com/installation/mac/)
- Install [Git](http://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
- Clone this repo and included submodules `git clone --recursive https://github.com/ianwcarlson/geofencing-demo`
- Run install script `./installMacLinux.sh` (This will start boot2docker.  Ensure ensure environment variables are getting set in shell properly. Scripts 
do not shut down virtual box. Currently untested on Linux host)
- Run everything `./run.sh`
- Open browser to <boot2docker IP>:3698