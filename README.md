
# RaspberryPi-MPD-CharDisplay

A Python project of the Raspberry Pi to control character LCD or OLED(SSD1311 controller) module via I2C protocol with button events. It can be used to display hostname, IP address, and some MPD infomation.

---

## Preparation

### Hardware and System

   **Raspberry pi:** B+, 2B, or 3B
   </br>
   **Display units:** Character LCD *(via PCF8574)* or OLED *(with SSD1311 controller)* module of 20x02 or 16x02 via I2C protocol
   </br>
   **Operating system:** Volumio 2, RuneAudio
   </br>
   **Python2 library requirements:** smbus, RPi.GPIO

## Installation

1. Install essential Python2 libraries(see Appendix-1).

2. Check I2C Character module LCD address and number of cols

   Open 'show.py' and go to Line-40

      `Display_addr  =0x27`
      `Display_cols  =16`

### For Volumio2

1. Copy and upload the files to /home/volumio/ or other folder

2. Edit 'playerdisp' file path(if necessary): check absolute path of show.py

   find and modify it, and there are 2 locations have to modify.
 
      `{absolute_path}/show.py &`

      *Note: The '{absolute_path}' will be modified by runing setup.sh automatically. But you can also modify manually.
   
3. Let the setup.sh executable

   `sudo chmod 755 setup.sh`
   
4. Let main script will be run when system startup

   `./setup.sh`
   
   *Note: If the essential Python2 libraries are OK, the script will run automatically when finishing the setup.sh.
   
### For RuneAudio

1. Copy and upload the files to /root/ or other folder

2. Edit 'playerdisp' and 'playerdisp.service' file path(if necessary)

   - Edit 'playerdisp': check absolute path of show.py

      find and modify it, and there are 2 locations have to modify.

         `{absolute_path}/show.py &`

   - Edit 'playerdisp.service': check absolute path of playerdisp

      find and modify it, and there are 2 locations have to modify.

         `{absolute_path}/playerdisp`

         *Note: The '{absolute_path}' will be modified by runing setup.sh automatically. But you can also modify manually.
   
3. Let the setup.sh executable

   `chmod 755 setup.sh`
   
4. Let main script will be run when system startup

   `./setup.sh`
   
   *Note: If the essential Python2 libraries are OK, the script will run automatically when finishing the setup.sh.

---

## *Appendix-1: Installation Guide of Python2 Library*

### For Volumio2

0. Compatibility test for following code

   [Version 2.368 (18-02-2018)](https://volumio.org/get-started/ "Volumio >> Download") - OK
   </br>
   Version 2.129 (07-03-2017) - OK
   </br>
   Version 2.118 (07-03-2017) - OK
   </br>
   Version 2.114 (03-03-2017) - OK

1. Update the local database of apt-get

   `sudo apt-get update`

2. Install smbus

   `sudo apt-get install python-smbus`

3. Install RPi.GPIO

   `sudo apt-get install python-rpi.gpio`

### For RuneAudio

0. Compatibility test for following code

   [Version 0.4 beta](http://www.runeaudio.com/forum/runeaudio-0-4-beta-for-raspberry-pi2-3-t4434.html "Forum >> Development and Support >> Raspberry Pi >> RuneAudio 0.4-beta for Raspberry Pi2/3") - OK

1. Extend partition to use unused space on the SD card

   - Use fdisk to modify the partition

      `fdisk /dev/mmcblk0`
      
      *The detailed guidelines please see the [official website](http://www.runeaudio.com/documentation/troubleshooting/extend-partition-sd/ "RuneAudio documentation >> Troubleshooting >> Extend a partition")*

   - Reboot the system, then use following script to resize the filesystem

      `resize2fs /dev/mmcblk0p2`

2. Update the local database

   `pacman -Syy`

3. Install 'python2-pip' and 'gcc'

   `pacman -S python2-pip`
   </br>
   `pacman -S gcc`

3. Install 'smbus' module

   - Edit '/boot/config.txt': find following script and remove **#** mark

      `#...param=i2c_arm=on`

   - Edit '/boot/cmdline.txt': add following script in the end
   
      `bcm2708.vc_i2c_override=1`
   
   - Edit '/etc/modules-load.d/raspberrypi.conf': add following two lines script
      
      `i2c-bcm2708`
      </br>
      `i2c-dev`
   
      *Note: If 'raspberrypi.conf' isn't exist, please create it.*
      
   - Reboot the system, then install 'i2c-tools'
   
      `pacman -S i2c-tools`
   
4. install 'RPi.GPIO' module

   - Download RPi.GPIO package by git or wget
   
   - Unzip the package
   
      `tar -xvf RPi.GPIO-*.tar.gz`
      
   - Install it
   
      `cd RPi.GPIO-*`
      </br>
      `python2 setup.py install`
