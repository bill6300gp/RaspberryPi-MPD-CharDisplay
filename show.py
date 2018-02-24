#!/usr/bin/python
import subprocess
from time import sleep
from lib.Display import DISPLAY
from lib.ButtonEncoder import ButtonEncoder

font_CGRAM=[
  0x00, 0x08, 0x0C, 0x0E, 0x0C, 0x08, 0x00, 0x00,  # Play
  0x00, 0x0A, 0x0A, 0x0A, 0x0A, 0x0A, 0x00, 0x00,  # Pause
  0x00, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F, 0x00, 0x00,  # Stop
  0x03, 0x02, 0x02, 0x02, 0x03, 0x00, 0x00, 0x00,  # AirPlay -L
  0x1F, 0x00, 0x00, 0x00, 0x04, 0x0E, 0x1F, 0x00,  # AirPlay
  0x18, 0x08, 0x08, 0x08, 0x18, 0x00, 0x00, 0x00,  # AirPlay -R
  0x04, 0x06, 0x05, 0x05, 0x0D, 0x1C, 0x18, 0x00,  # MARK MUSIC1
  0x04, 0x06, 0x05, 0x05, 0x0D, 0x14, 0x18, 0x00   # MARK MUSIC2
]

FONT_PLAY   =0x00
FONT_PAUSE  =0x01
FONT_STOP   =0x02
FONT_AIRPLAY=[0x03, 0x04, 0x05]
FONT_MUSIC1 =0x06
FONT_MUSIC2 =0x07

ENABLE_SLEEP  =True
ENABLE_POWERSW=True
ENABLE_ENCODER=False

Pin_POWERSW   =4

Display_stat  =0
Display_title =0
Display_update=0x00
Display_shift1=0
Display_shift2=0
Standby_count =0
Order_stat    =0
Order_update  =0
Order_operate =0
Order_exit    =0
Order_shutdown=0
mode_shutdown =0

Player_name =" "
Player_ip   =" "
Player_stat =0
Player_error=0x00

Audio_radioname=" "
Audio_airplayip=" "
Audio_time     =[0]*2
Audio_length   =[0]*2
Audio_sample   =0

# Get System Info
def getIpAddress():
  global Display_update
  global Player_ip
  global Player_error

#  s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#  _tmp=socket.inet_ntoa(fcntl.ioctl(
#    s.fileno(),
#    0x8915,
#    struct.pack('256s', ifname[:15])
#  )[20:24]).split('.')
#  for i in range(0,len(_tmp),1):
#    if Player_ip[i]!=int(_tmp[i]):
#      Player_ip[i]=int(_tmp[i])
#      count=count+1
  _tmp=Player_ip
  try:
    Player_ip=subprocess.check_output(["hostname", "-I"]).split('\n')[0].split()[0]
  except:
    Player_ip="0.0.0.0"
    Player_error|=0x01

  if len(Player_ip)!=len(_tmp) or Player_ip!=_tmp:
    Display_update|=0x02
    DISP.sendDebugInfo('IP address: '+Player_ip,1)

def getPlayerName(method=1):
  global Display_update
  global Player_name
  
  if method==1:
    _tmp =subprocess.check_output(["cat", "/etc/shairport-sync.conf"]).split('\"')[1]
  else:
    file =open('/etc/hostname', 'r')
    _tmp =file.readline()
    file.close()
  if Player_name!=_tmp:
    Player_name=_tmp
    Display_update=Display_update|0x01
    DISP.sendDebugInfo('Player name: '+Player_name,1)

def getAudioCardinfo():
  global Card_id
  global Card_name
  global Card_device
  global Card_subdevice
  global Card_active

  try:
    _info=subprocess.check_output(["aplay", "-l"])
    n=_info.count("card")
    Card_id=[None]*n
    Card_name=[None]*n
    Card_device=[None]*n
    Card_subdevice=[None]*n
    Card_active=-1

    start=0
    for i in range(0,n,1):
      locate=_info.find("card", start)
      if locate>=0:
        Card_id[i]=_info[locate+5]
        path="/proc/asound/card"+Card_id[i]+"/id"
        Card_name[i]=subprocess.check_output(["cat", path]).split('\n')[0]
        start=locate
      locate=_info.find("device", start)
      if locate>=0:
        Card_device[i]=_info[locate+7]
        start=locate
      locate=_info.find("Subdevices", start)
      if locate>=0:
        Card_subdevice[i]=_info[locate+14]
        start=locate
        if _info[locate+12]<_info[locate+14]:
          Card_active=i
      #print "Card{:s}({:s}) -  Device{:s}: {:s}".format(Card_id[i], Card_name[i], Card_device[i], Card_subdevice[i])
  except:
    Card_active=-1
    Player_error|=0x02

def getAudioOutputCard():
  if Card_active>=0:
    path="/proc/asound/card"+Card_id[Card_active]+"/pcm"+Card_device[Card_active]+"p/sub0/status"
    _tmp=subprocess.check_output(["cat", path])
    if _tmp.find("RUNNING")>=0:
      DISP.sendDebugInfo('Active sound card: Card'+Card_id[Card_active]+', device'+Card_device[Card_active],1)
      print "Active sound card: Card"+Card_id[Card_active]+", device"+Card_device[Card_active]+" >> Running!"

def getAirPlayCpu(num=1):
  value=[0.0]*num
  _pid=subprocess.check_output(["pidof", "shairport-sync"]).split('\n')[0]
  _tmp=subprocess.check_output(["top", "-b", "-p", _pid, "-n", str(num), "-d", "0.1"])
  for i in range(0,num,1):
    value[i]=float(_tmp.split('\n')[7+9*i].split()[8])
  return sum(value)/num

def getMPDCpu(num=1):
  value=[0.0]*num
  _pid=subprocess.check_output(["pidof", "mpd"]).split('\n')[0]
  _tmp=subprocess.check_output(["top", "-b", "-p", _pid, "-n", str(num), "-d", "0.1"])
  for i in range(0,num,1):
    value[i]=float(_tmp.split('\n')[7+9*i].split()[8])
  return sum(value)/num

#
def getAirPlayState():
  global Display_update
  global Player_stat
  global Player_error
  global Audio_airplayip
  count=0

  try:
    _tmp=subprocess.check_output(["sudo", "netstat", "-npt"])
  except:
    _tmp=None
    Player_error|=0x04
    return 0

  if _tmp.find("shairport")>=0:
    Player_stat=7
    _stat=_tmp.split('\n')
    for i in range(2,len(_stat),1):
      if _stat[i].find("shairport")>=0:
        if _stat[i].split()[5]=="ESTABLISHED":
          _ip=Audio_airplayip
          Audio_airplayip=_stat[i].split()[4].split(':')[0]
        if _ip!=Audio_airplayip:
          Display_update=Display_update|0x80
        return 1
  return 0
  #

def getMPDState():
  global Display_update
  global Player_stat
  global Player_error
  global Audio_time
  global Audio_length
  global Audio_radioname
  old_time=Audio_time[0]*60+Audio_time[1]
  old_length=Audio_length[0]*60+Audio_length[1]
  old_radioname=Audio_radioname

  try:
    _stat=subprocess.check_output(["mpc"])
  except:
    _stat=None
    Player_error|=0x08
    return 0

  if _stat.find("playing")>=0:
    Player_stat=1
  elif _stat.find("paused")>=0:
    Player_stat=2
  else:
    return 0

  _tmp=_stat.split('\n')[1].split()[2]
  Audio_time[0]=int(_tmp.split('/')[0].split(':')[0])
  Audio_time[1]=int(_tmp.split('/')[0].split(':')[1])
  Audio_length[0]=int(_tmp.split('/')[1].split(':')[0])
  Audio_length[1]=int(_tmp.split('/')[1].split(':')[1])
  if old_time!=Audio_time[0]*60+Audio_time[1]:
    Display_update=Display_update|0x10
  if old_length!=Audio_length[0]*60+Audio_length[1]:
    Display_update=Display_update|0x20
  if _stat.split('\n')[0].find("source=youtube")>=0:
    Player_stat=Player_stat+2
  elif (Audio_length[0]*60+Audio_length[1])==0:
    Player_stat=Player_stat+4
    Audio_radioname=_stat.split('\n')[0].split(': ')[0]
    if len(old_radioname)!=len(Audio_radioname) or old_radioname!=Audio_radioname:
      Display_update=Display_update|0x40
#      print "Radio name: "+old_radioname+" > "+Audio_radioname

  return 1

def getAudioSample():
  global Display_update
  global Audio_sample
  old_sample=Audio_sample

  getAudioCardinfo()
  if Card_active>=0:
    path="/proc/asound/card"+Card_id[Card_active]+"/pcm"+Card_device[Card_active]+"p/sub0/hw_params"
    _info=subprocess.check_output(["cat", path])

    if _info.find("closed")>=0:
      DISP.sendDebugInfo('Audio card status: Closed',2)
#      print "Output: Closed"
      if old_sample!=0:
        Audio_sample=0
        Display_update=Display_update|0x08
    else:
      tmp=_info.find("rate:")
      Audio_sample=0
      for i in range(tmp+6,tmp+12,1):
        if _info[i]==' ':
          continue
        if ord(_info[i])>=0x30 and ord(_info[i])<=0x39:
          Audio_sample=Audio_sample*10+int(_info[i])
        else:
          if Audio_sample>0:
            break
      if old_sample!=Audio_sample:
        Display_update=Display_update|0x08
        DISP.sendDebugInfo('Audio card status: {:.1f}kHz'.format(float(Audio_sample)/1000),1)
#        print "Format: {:.1f}kHz".format(float(Audio_sample)/1000)
  else:
    if old_sample!=0:
      DISP.sendDebugInfo('Audio card status: Closed',2)
#      print "Output: Closed"
      Audio_sample=0
      Display_update=Display_update|0x08

def getState():
  global Display_update
  global Standby_count
  global Player_stat
  #global Audio_sample

  old_stat=Player_stat
  Player_stat=0
  if getAirPlayState()==0:
    getMPDState()

  getAudioSample()
  #if Player_stat==1 or Player_stat==3 or Player_stat==5 or Player_stat==7:
  if Player_stat%2==1:
    Standby_count=0
  else:
    if ENABLE_SLEEP==True:
      Standby_count=Standby_count+1
    #Audio_sample=0

  if old_stat!=Player_stat:
    Display_update=Display_update|0x04

    if Player_stat==1:
      if old_stat!=2:
        DISP.sendDebugInfo('Player status: playing Playlist',1)
#      print "Playing | Playlist: {:d}:{:02d}".format(Audio_length[0],Audio_length[1])
    elif Player_stat==2:
        DISP.sendDebugInfo('Player status: paused Playlist',1)
#      print "Paused | Playlist: {:d}:{:02d}".format(Audio_length[0],Audio_length[1])
    elif Player_stat==3:
      if old_stat!=4:
        DISP.sendDebugInfo('Player status: playing YouTube Stream',1)
#      print "Playing | YouTubr"
    elif Player_stat==4:
        DISP.sendDebugInfo('Player status: paused YouTube Stream',1)
#      print "Paused | YouTube"
    elif Player_stat==5:
      if old_stat!=6:
        DISP.sendDebugInfo('Player status: playing Web Radio',1)
#      print "Playing | Web Radio: "+Audio_radioname
    elif Player_stat==6:
        DISP.sendDebugInfo('Player status: paused Web Radio',1)
#      print "Paused | Web Radio: "+Audio_radioname
    elif Player_stat==7:
      DISP.sendDebugInfo('Player status: AirPlay('+Audio_airplayip+')',1)
#      print "AirPlay: "+Audio_airplayip
    else:
      DISP.sendDebugInfo('Player status: Standby...',1)
#      print "Standby..."    

##=================##
##  Order Program  ##
##=================##

def checkOrder():
  global Display_stat
  global Display_update
  global Order_stat
  global Order_operate
  global Order_exit
  global Order_shutdown

  if subprocess.check_output(["ls", "/tmp/"]).count("displayorder")>0:
    _tmp=subprocess.check_output(["cat", "/tmp/displayorder"])
    subprocess.call(["sudo", "rm", "/tmp/displayorder"])
    if _tmp.find("stop")>=0:
      DISP.sendDebugInfo('Order: stop!',2)
      Order_exit    =1
      Order_shutdown=1
    elif _tmp.find("restart")>=0:
      DISP.sendDebugInfo('Order: restart!',2)
      Order_exit    =1
    elif _tmp.find("initdisplay")>=0:
      reinitDisplay()
      Display_update=0xFF
      Display_stat=1
      updateDisplay()
    if Order_stat!=0 or Order_operate!=0:
      Order_stat   =0
      Order_operate=0

def shutdownSystem(mode=0):
  global mode_shutdown

  if mode==1:
    subprocess.call(["sudo", "shutdown", "-h", "+1"])
    mode_shutdown=1
    DISP.clear()
    DISP.sendString(' The system will go ',0,0)
    DISP.sendString('  down in 1 minute  ',0,1)
    sleep(5)
  elif mode==2:
    subprocess.call(["sudo", "shutdown", "-r", "+1"])
    mode_shutdown=2
    DISP.clear()
    DISP.sendString(' The system will    ',0,0)
    DISP.sendString(' reboot in 1 minute ',0,1)
    sleep(5)
  else:
    subprocess.call(["sudo", "shutdown", "-c"])
    mode_shutdown=0

def reinitDisplay():
  DISP.sendDebugInfo('Order: re-init display!',2)
  DISP.initDisp(font_CGRAM)

def restartAirPlay():
  subprocess.call(["sudo", "service", "shairport-sync", "restart"])

##================##
##  Main Program  ##
##================##
def checkI2Cdevice(addr):
  i=int((addr&0xF0)>>4)+1
  j=int(addr&0x0F)+1
  _tmp=subprocess.check_output(["i2cdetect", "-y", "1"]).split('\n')[i].split()[j]
  if _tmp=="--":
    print "The I2C device(0x{:2x}) not found.".format(addr)
    return 0
  else:
    return 1

def updateDisplay():
  global Display_title
  global Display_update
  global Display_shift1
  global Display_shift2
  
  if Display_stat==0:
    Display_update=0x00
    return 0
  else:
    if Display_update&0x01==0x01 and Player_name is not None:
      if len(Player_name)<=13:
        DISP.sendString('{:{space}{align}{width}s}'.format(Player_name,space=' ',align='^',width=13),0,0)
      else:
        DISP.sendString('{:{space}{align}{width}s}'.format(Player_name[0:13],space=' ',align='<',width=13),0,0)
      Display_shift1=0
      Display_title=0
    elif Display_update&0x02==0x02:
      if Player_stat==0:
        if len(Player_ip)<=11:
          DISP.sendString('{:{space}{align}{width}s}'.format(Player_ip,space=' ',align='^',width=11),9,1)
        else:
          DISP.sendString('{:{space}{align}{width}s}'.format(Player_ip[0:11],space=' ',align='<',width=11),9,1)
        Display_shift2=0
      else:
        if len(Player_ip)<=13:
          DISP.sendString('{:{space}{align}{width}s}'.format(Player_ip,space=' ',align='^',width=13),0,0)
        else:
          DISP.sendString('{:{space}{align}{width}s}'.format(Player_ip[0:13],space=' ',align='<',width=13),0,0)
        Display_shift1=0
        Display_title=1
    if Display_update&0x04==0x04:
      DISP.printCGRam(FONT_MUSIC1,13,0)
      if Player_stat>=1 and Player_stat<=4:
        if Player_stat==1 or Player_stat==2:
          DISP.sendString("Playlist",0,1)
        elif Player_stat==3 or Player_stat==4:
          DISP.sendString("YouTube ",0,1)

        if Player_stat%2==1:
          DISP.printCGRam(FONT_PLAY,8,1)
        else:
          DISP.printCGRam(FONT_PAUSE,8,1)

        if Audio_length[0]<10:
          DISP.sendString(" {:d}:{:02d}/{:d}:{:02d} ".format(Audio_time[0],Audio_time[1],Audio_length[0],Audio_length[1]))
        elif Audio_length[0]<100:
          DISP.sendString("{:02d}:{:02d}/{:02d}:{:02d}".format(Audio_time[0],Audio_time[1],Audio_length[0],Audio_length[1]))
      elif Player_stat==5 or Player_stat==6:
        DISP.sendString("WebRadio",0,1)
        if Player_stat%2==1:
          DISP.printCGRam(FONT_PLAY,8,1)
        else:
          DISP.printCGRam(FONT_PAUSE,8,1)
        if len(Audio_radioname)<=11:
          DISP.sendString('{:{space}{align}{width}s}'.format(Audio_radioname,space=' ',align='^',width=11),9,1)
        else:
          DISP.sendString('{:{space}{align}{width}s}'.format(Audio_radioname[0:11],space=' ',align='<',width=11),9,1)
        Display_shift2=0
      elif Player_stat==7:
        DISP.sendString("AirPlay",0,1)
        DISP.printCGRam(FONT_AIRPLAY,7,1)
        DISP.sendString('{:{space}{align}{width}s}'.format(Audio_airplayip[0:10],space=' ',align='<',width=10),10,1)
        Display_shift2=0
      else:
        DISP.sendString("Standby ",0,1)
        DISP.printCGRam(FONT_STOP)
        if len(Player_ip)<=11:
          DISP.sendString('{:{space}{align}{width}s}'.format(Player_ip,space=' ',align='^',width=11),9,1)
        else:
          DISP.sendString('{:{space}{align}{width}s}'.format(Player_ip[0:11],space=' ',align='<',width=11),9,1)
        Display_shift2=0
      if Audio_sample!=0:
        DISP.sendString("{:5.1f}K".format(float(Audio_sample)/1000),14,0)
      else:
        DISP.sendString("Closed",14,0)
    else:
      if Display_update&0x08==0x08:
        if Audio_sample!=0:
          DISP.sendString("{:5.1f}K".format(float(Audio_sample)/1000),14,0)
        else:
          DISP.sendString("Closed",14,0)
      if Display_update&0x10==0x10 and (Player_stat>=1 and Player_stat<=4):
        DISP.sendString("{:2d}:{:02d}".format(Audio_time[0],Audio_time[1]),9,1)
      if Display_update&0x20==0x20 and (Player_stat>=1 and Player_stat<=4):
        DISP.sendString("{:d}:{:02d}".format(Audio_length[0],Audio_length[1]),15,1)
      if Display_update&0x40==0x40 and (Player_stat==5 or Player_stat==6):
        if len(Audio_radioname)<=11:
          DISP.sendString('{:{space}{align}{width}s}'.format(Audio_radioname,space=' ',align='^',width=11),9,1)
        else:
          DISP.sendString('{:{space}{align}{width}s}'.format(Audio_radioname[0:11],space=' ',align='<',width=11),9,1)
        Display_shift2=0
      if Display_update&0x80==0x80 and Player_stat==7:
        DISP.sendString('{:{space}{align}{width}s}'.format(Audio_airplayip[0:10],space=' ',align='<',width=10),10,1)
        Display_shift2=0

    Display_update=0x00
    return 1

def shiftDisplay():
  global Display_shift1
  global Display_shift2

  if Display_title==0 and len(Player_name)>13:
    if Display_shift1>=len(Player_name)+11:
      Display_shift1=0
    else:
      Display_shift1+=1
    if Display_shift1>=len(Player_name):
      DISP.sendString('{:{space}{align}{width}s}'.format(Player_name[0:Display_shift1-len(Player_name)+1],space=' ',align='>',width=13),0,0)
    else:
      DISP.sendString('{:{space}{align}{width}s}'.format(Player_name[Display_shift1+0:Display_shift1+13],space=' ',align='<',width=13),0,0)
  elif Display_title==1 and len(Player_ip)>13:
    if Display_shift1>=len(Player_ip)+11:
      Display_shift1=0
    else:
      Display_shift1+=1
    if Display_shift1>=len(Player_ip):
      DISP.sendString('{:{space}{align}{width}s}'.format(Player_ip[0:Display_shift1-len(Player_ip)+1],space=' ',align='>',width=13),0,0)
    else:
      DISP.sendString('{:{space}{align}{width}s}'.format(Player_ip[Display_shift1+0:Display_shift1+13],space=' ',align='<',width=13),0,0)


  if Player_stat==5 or Player_stat==6:
    if Display_shift2>=len(Audio_radioname)+9:
      Display_shift2=0
    else:
      Display_shift2+=1
    if Display_shift2>=len(Audio_radioname):
      DISP.sendString('{:{space}{align}{width}s}'.format(Audio_radioname[0:Display_shift2-len(Audio_radioname)+1],space=' ',align='>',width=11),9,1)
    else:
      DISP.sendString('{:{space}{align}{width}s}'.format(Audio_radioname[Display_shift2+0:Display_shift2+11],space=' ',align='<',width=11),9,1)
  elif Player_stat==7:
    if Display_shift2>=len(Audio_airplayip)+8:
      Display_shift2=0
    else:
      Display_shift2+=1
    if Display_shift2>=len(Audio_airplayip):
      DISP.sendString('{:{space}{align}{width}s}'.format(Audio_airplayip[0:Display_shift2-len(Audio_airplayip)+1],space=' ',align='>',width=10),10,1)
    else:
      DISP.sendString('{:{space}{align}{width}s}'.format(Audio_airplayip[Display_shift2+0:Display_shift2+10],space=' ',align='<',width=10),10,1)
  elif Player_stat==0:
    if Display_shift2>=len(Player_ip)+9:
      Display_shift2=0
    else:
      Display_shift2+=1
    if Display_shift2>=len(Player_ip):
      DISP.sendString('{:{space}{align}{width}s}'.format(Player_ip[0:Display_shift2-len(Player_ip)+1],space=' ',align='>',width=11),9,1)
    else:
      DISP.sendString('{:{space}{align}{width}s}'.format(Player_ip[Display_shift2+0:Display_shift2+11],space=' ',align='<',width=11),9,1)

def orderDisplay():
  global Order_update

  if Order_stat==1:
    if mode_shutdown==1:
      DISP.sendString('to cancel shutdown? ',0,1)
    elif mode_shutdown==2:
      DISP.sendString('to cancel reboot?   ',0,1)
  elif  Order_stat==2:
    if mode_shutdown==0:
      DISP.sendString('to shutdown system? ',0,1)
  elif  Order_stat==3:
    if mode_shutdown==0:
      DISP.sendString('to reboot system?   ',0,1)
  elif  Order_stat==4:
    DISP.sendString('to initialize Disp? ',0,1)
  elif  Order_stat==5:
    DISP.sendString('to restart AirPlay? ',0,1)

  Order_update=0

def startup():
  global Player_error
  count_ready=0

  #_tmp=subprocess.check_output(["cat", "/tmp/display.log"])
  #if 
  DISP.on()
  DISP.sendString('The Volumio2 Player!',0,0)
  DISP.sendString(' Starting System... ',0,1)
  while True:
    Player_error=0x00
    getState()
    if Player_stat!=0 or (Player_stat==0 and Audio_sample!=0) or count_ready>=250:
      return 1
    elif Player_error==0x00:
      count_ready+=1
    else:
      count_ready=0

def main():
  global Display_stat
  global Display_update
  global Standby_count
  global Order_stat
  global Order_update
  global Order_operate
  count_system=0
  count_title=0
  count_shift=0
  count_order=0

  Display_update=0xFF
  DISP.clear()
  Display_stat=1
  getPlayerName(1)
  getIpAddress()

  while True:
    if count_system>=10:
      getPlayerName(1)
      getIpAddress()
      count_system=0

    checkOrder()
    if Order_exit==1:
      if ENABLE_POWERSW==True:
        PowerSW.eventEnd()
      break

    getState()

    if Display_stat!=2 and Order_stat!=0:
      if Display_stat==0:
        DISP.on()
      Display_stat=2
      Order_update=1
      DISP.clear()
      DISP.sendString(' Press power button ',0,0)

    if Display_stat==1:
      if Display_update&0x02==0x02:
        count_title=0
      elif count_title>=30 and Display_title==1:
        Display_update|=0x01
        count_title=0

      if Display_update!=0x00:
        updateDisplay()
      else:
        if ENABLE_SLEEP==True and Standby_count>1000:
          DISP.sendDebugInfo('Display go into sleep mode',2)
          DISP.off()
          Display_stat=0
        else:
          if count_shift>=5 and ((Display_title==0 and len(Player_name)>13) or (Display_title==1 and len(Player_ip)>13) or ((Player_stat==5 or Player_stat==6) and len(Audio_radioname)>11) or Player_stat==7 or (Player_stat==0 and len(Player_ip)>11)):
            shiftDisplay()
            count_shift=0
    elif Display_stat==2:
      if Order_operate==1:
        if Order_stat==1:
          if mode_shutdown==1 or  mode_shutdown==2:
            shutdownSystem(0)
        elif Order_stat==2: 
          if mode_shutdown==0:
            shutdownSystem(1)
        elif Order_stat==3:
          if mode_shutdown==0:
            shutdownSystem(2)
        elif Order_stat==4: 
          reinitDisplay()
        elif Order_stat==5: 
          restartAirPlay()
        Order_stat=0
        Order_operate=0
      else:
        if Order_update==1:
          count_order=0
          orderDisplay()
      if count_order>=30:
        Order_stat=0
      if Order_stat==0:
        Standby_count=0
        Display_update=0xFF
        Display_stat=1
        updateDisplay()
      count_order+=1
    else:
      if Display_update!=0x00:
        DISP.sendDebugInfo('Display exit sleep mode',2)
        Standby_count=0
        Display_update=0xFF
        DISP.on()
        Display_stat=1
        updateDisplay()

    count_system+=1
    count_title+=1
    count_shift+=1

def eventPowerSW(code):
  global Order_stat
  global Order_update
  global Order_operate

  if code==ButtonEncoder.Button_Up:
    timer=PowerSW.countdSW
    if timer<=0.50:
      if Order_stat==0:
        if mode_shutdown==0:
          Order_stat=2
        else:
          Order_stat=1
        Order_update=1
      else:
        Order_operate=1
    elif timer>0.50 and timer<=3.50:
      if Order_stat==0 or Order_stat==1:
        Order_stat=4
      elif Order_stat==5:
        Order_stat=0
      else:
        Order_stat+=1
      if Order_stat!=0:
        Order_update=1

if __name__ == '__main__':
  try:
# PCF8574T LCD 20x04
#DISP=DISPLAY(0x27,20,4,0,font_CGRAM)
# PCF8574T OLED 20x04
#DISP=DISPLAY(0x27,20,4,1,font_CGRAM)
# I2C OLED 20x04
#DISP=DISPLAY(0x3C,20,4,2,font_CGRAM)
    if checkI2Cdevice(0x27)==1:
      if subprocess.check_output(["ls", "/tmp/"]).count("display.log")>0:
        DISP=DISPLAY(0x27,20,2,0,font_CGRAM)
      else:
        DISP=DISPLAY(0x27,20,2,0,font_CGRAM)
        startup()
      if ENABLE_POWERSW==True:
        PowerSW=ButtonEncoder(1, 'UP', Pin_POWERSW)
        PowerSW.eventBegin(eventPowerSW)
      main()
  except KeyboardInterrupt:
    pass
  except:
    pass
  finally:
    if Display_stat!=0:
      if Order_shutdown==1:
        DISP.clear()
        DISP.sendString(' System shut down!! ',0,0)
        sleep(1.5)
      DISP.clear()
      DISP.off()
      DISP.sendDebugInfo('Player displayer stop!',2)
