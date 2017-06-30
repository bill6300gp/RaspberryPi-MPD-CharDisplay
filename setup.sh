#! /bin/bash

if [ -f /etc/init.d/playerdisp ]; then
  echo "playerdisp file has been upload."
else
  echo "Installing the playerdisp..."
  sudo cp playerdisp /etc/init.d/
  sudo chmod 755 /etc/init.d/playerdisp
  sudo update-rc.d playerdisp defaults
fi

tmp=`python2 -m smbus |& grep -q 'No module named' && echo 0 || echo 1`
if [ $tmp -eq 1 ]; then
  echo "smbus module has been installed."
else
  echo "Installing python-smbus module..."
  sudo apt-get update
  sudo apt-get install python-smbus
fi

tmp=` python2 -m RPi.GPIO.__init__ |& grep -q 'No module named' && echo 0 || echo 1`
if [ $tmp -eq 1 ]; then
  echo "RPi.GPIO package has been installed."
else
  echo "Installing rpi.gpio package..."
  sudo apt-get install rpi.gpio
fi

PID=`ps -ef | grep show.py | grep -v grep | awk '{print $2}'`
if [ -z $PID ]; then
  sudo /etc/init.d/playerdisp start
else
  echo "playerdisp has run already."
fi
