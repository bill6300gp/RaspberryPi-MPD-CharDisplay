#! /bin/bash

echo "Install playerdisp script"
echo "-------------------------"

# Modify file path
locate=`pwd`
#echo "The scripts are in the path: $locate"
if [ -f $locate/playerdisp ]; then
	sed -i "s|{absolute_path}|$locate|g" playerdisp
fi
if [ -f $locate/playerdisp.service ]; then
	sed -i "s|{absolute_path}|$locate|g" playerdisp.service
fi

# Check Libraries
echo "Check Libraries:"
tmp=`python2 -m smbus |& grep -q 'No module named' && echo 0 || echo 1`
count=0
if [ $tmp -eq 1 ]; then
	echo -e "[\033[0;32m OK \033[0m] python smbus module has been installed."
	count=$(($count+1))
else
	echo -e "[\033[0;31mFail\033[0m] without python smbus module."
fi
tmp=`python2 -m RPi.GPIO |& grep -q 'No module named' && echo 0 || echo 1`
if [ $tmp -eq 1 ]; then
	echo -e "[\033[0;32m OK \033[0m] RPi.GPIO package has been installed."
	count=$(($count+1))
else
	tmp=`python2 -m RPi.GPIO.__init__ |& grep -q 'No module named' && echo 0 || echo 1`
	if [ $tmp -eq 1 ]; then
		echo -e "[\033[0;32m OK \033[0m] RPi.GPIO package has been installed."
		count=$(($count+1))
	else
		echo -e "[\033[0;31mFail\033[0m] without RPi.GPIO package."
	fi
fi
echo "-----------------------------------------------"

# Install and run
mps=`uname -n`
if [ "$mps" == "volumio" ]; then
	echo -e "Music Player System is \033[0;33mVolumio\033[0m."
	if [ -f /etc/init.d/playerdisp ]; then
		echo "playerdisp file has been upload."
	else
		echo "Installing the playerdisp..."
		sudo cp playerdisp /etc/init.d/
		sudo chmod 755 /etc/init.d/playerdisp
		sudo update-rc.d playerdisp defaults
	fi

	PID=`ps -ef | grep show.py | grep -v grep | awk '{print $2}'`
	if [ -z $PID ]; then
		if [ $count -eq 2 ]; then
			sudo /etc/init.d/playerdisp start
		fi
	#else
	#	echo "playerdisp has run already."
	fi
elif [ "$mps" == "runeaudio" ]; then
	echo -e "Music Player System is \033[0;33mRuneAudio\033[0m."
	tmp=`systemctl status playerdisp |& grep -q 'No such file' && echo 0 || echo 1`
	if [ $tmp -eq 0 ]; then
		echo "install playerdisp script..."
		chmod 755 playerdisp
		cp playerdisp.service /usr/lib/systemd/system/
		systemctl daemon-reload
		systemctl enable playerdisp
	else
		echo "playerdisp has been installed already."
	fi

	stat=`systemctl status playerdisp |& grep -q 'inactive' && echo 0 || echo 1`
	if [ $stat -eq 0 ]; then
		if [ $count -eq 2 ]; then
			echo "Start playerdisp..."
			systemctl start playerdisp
		fi
	#else
	#	echo "playerdisp has run already."
	fi
else
	echo "Unknow system. Stopped installing!"
fi


