# geofencing-demo
Real-time mapping demonstration using ZeroMQ and websockets

(Work in progress)

# Installation

- Install [boot2docker](https://docs.docker.com/installation/mac/)
- Install [Git](http://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
- Clone this repo and included submodules `git clone --recursive https://github.com/ianwcarlson/geofencing-demo`
- Run install script `./installMacLinux.sh` (This will start boot2docker.  Ensure ensure environment variables are getting set in shell properly.  Currently untested on Linux host)
- Run everything `./run.sh`
- Open browser to <boot2docker IP>:3698