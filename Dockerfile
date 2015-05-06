FROM ubuntu:14.04

ENV PROJ_DIR /usr/local/geofencing-demo

# Base packages
RUN apt-get update
RUN apt-get install -y python3 libzmq3-dev python3-zmq python3-pip

RUN pip3 install msgpack-python nose
RUN pip3 install jsonschema 

RUN pip3 install gpxpy
# Install pre 0.10 Node because zmq package needs it
# Node compiler needs python2.x
RUN apt-get install -y python wget build-essential
RUN wget http://nodejs.org/dist/v0.10.30/node-v0.10.30.tar.gz
RUN tar -xvf node-v0.10.30.tar.gz
RUN cd node-v0.10.30 && ./configure && make && make install
RUN npm install -g gulp

# Must install node dependencies before changing
# sym link to python3
#RUN cd /usr/local/geofencing-demo && npm install

RUN rm /usr/bin/python
RUN ln -s /usr/bin/python3 /usr/bin/python


