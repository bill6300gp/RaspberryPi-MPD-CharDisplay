#!/usr/bin/python2
import subprocess
import socket
import fcntl
import struct

class PlayerStat:
  # Define System Code
  Unknow   =0
  Volumio  =1
  RuneAudio=2
  # Define Player Status Code
  StandBy      =10
  PlaylistPlay =11
  PlaylistPause=12
  YouTubePlay  =13
  YouTubePause =14
  WebRadioPlay =15
  WebRadioPause=16
  AirPlay      =17
  MiniDLNA     =18
  # System Status
  SystemLogger =0
  SystemType   =0
  SystemIPeth0 ="0.0.0.0"
  SystemIPwlan0="0.0.0.0"
  SystemAPSSID =" "
  AirPlayCIP   ="0.0.0.0"
  NameHost     =" "
  NameAirPlay  =" "
  NameUPmP     =" "
  NameRadio    =" "
  NameTitle    =" "
  # Player Status
  PlayerStatus =0
  AudioOutput  =0
  AudioTime    =[0]*2
  AudioLength  =[0]*2
  AudioChannels=0
  AudioSample  =0
  QueueNumber  =0
  QueueTotal   =0
  PlayerVolume =0
  PlayerMute   =0
  PlayerRepeat =False
  PlayerRandom =False
  PlayerSingle =False
  PlayerConsume=False
  
  # Actived Sound Card
  __CardActive=-1
  __CardAPath="/proc/asound/"
  InfoUpdate=0x00
  InfoError =0x00

  def __init__(self, logger=None):
    if logger!=None:
      self.__Logger=logger
      self.__Logger('PlayStat >> \033[33moperating\033[0m...',1)
      self.SystemLogger=1
    self.checkSystem()
    self.getSystemInfo()

  def getSystemInfo(self):
    if self.SystemType==self.Unknow:
      self.checkSystem()
    self.getIpAddress('eth0')
    self.getIpAddress('wlan0')
    self.getHostName()
    self.getAirPlayName()
    self.getUPmPName()

#  def getPlayerStat(self):
#    if self.SystemType==self.Unknow:
#      self.checkSystem()
#    if self.__CardActive==-1:
#      self.getAudioCardInfo()

  def restartAirPlay(self):
    if self.SystemType==0:
      checkSystem()
    if self.SystemType==self.Volumio:
      subprocess.call(["sudo", "service", "shairport-sync", "restart"])
    elif self.SystemType==self.RuneAudio:
      subprocess.call(["systemctl", "restart", "shairport"])
    else:
      return None
    if self.SystemLogger==1:
      self.__Logger('\033[31mRestart\033[0m AirPlay(shairport) service',2)

  def restartUPmP(self):
    if self.SystemType==0:
      checkSystem()
    if self.SystemType==self.Volumio:
      return None
    elif self.SystemType==self.RuneAudio:
      subprocess.call(["systemctl", "restart", "upmpdcli"])
    else:
      return None
    if self.SystemLogger==1:
      self.__Logger('\033[31mRestart\033[0m UPnP/DLNA(upmpdcli) service',2)

  #=========================#
  #  Get player infomation  #
  #=========================#

  def checkSystem(self):
    try:
      _tmp=subprocess.check_output(["uname", "-n"])
      if self.SystemType!=_tmp:
        if _tmp.find("volumio")>=0:
          self.SystemType=self.Volumio
          if self.SystemLogger==1:
            self.__Logger('System   >> \033[33mVolumio\033[0m',1)
        elif _tmp.find("runeaudio")>=0:
          self.SystemType=self.RuneAudio
          if self.SystemLogger==1:
            self.__Logger('System   >> \033[33mRuneAudio\033[0m',1)
        else:
          self.SystemType=self.Unknow
          if self.SystemLogger==1:
            self.__Logger('System: \033[31mUnknow\033[0m',1)
    except:
      self.SystemType=self.Unknow
      if self.SystemLogger==1:
        self.__Logger('System: \033[31mUnknow\033[0m',1)

  def getIpAddress(self, ifname='eth0'):
    # getIpAddress('eth0')
    # getIpAddress('wlan0')
    try:
      s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
      _tmp=socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,
        struct.pack('256s', ifname[:15])
      )[20:24])
      #print "IP("+ifname+")="+_tmp

      if ifname=='wlan0':
        _oldAPSSID=self.SystemAPSSID
        _tmp1=subprocess.check_output(["iwconfig", "wlan0"]).split('\n')
        if _tmp1[0].find("ESSID")>=0 and _tmp1[1].find("Not-Associated")<0:
          self.SystemAPSSID=_tmp1[0].split()[3].split('\"')[1]
          #print "AP SSID: "+self.SystemAPSSID
        else:
          self.SystemAPSSID=" "
        if _oldAPSSID!=self.SystemAPSSID:
          if self.SystemLogger==1 and self.SystemAPSSID!=" ":
            self.__Logger('AP(wlan0) SSID: \033[33m{:s}\033[0m'.format(self.SystemAPSSID),1)
    except:
      _tmp="0.0.0.0"

    if ifname=='eth0' and self.SystemIPeth0!=_tmp:
      self.SystemIPeth0=_tmp
      self.InfoUpdate|=0x02
      if self.SystemLogger==1:
        if self.SystemIPeth0=="0.0.0.0":
          self.__Logger('IP(eth0) : \033[31m{:s}\033[0m'.format(self.SystemIPeth0),1)
        else:
          self.__Logger('IP(eth0) : \033[33m{:s}\033[0m'.format(self.SystemIPeth0),1)
    elif ifname=='wlan0' and self.SystemIPwlan0!=_tmp:
      self.SystemIPwlan0=_tmp
      self.InfoUpdate|=0x02
      if self.SystemLogger==1:
        if self.SystemIPwlan0=="0.0.0.0":
          self.__Logger('IP(wlan0): \033[31m{:s}\033[0m'.format(self.SystemIPwlan0),1)
        else:
          self.__Logger('IP(wlan0): \033[33m{:s}\033[0m'.format(self.SystemIPwlan0),1)

  def getHostName(self, method=0):
    # getHostName()
    # getHostName(method)
    # method=0: using 'hostname' command
    # method=1: read '/etc/hostname' file
    try:
      if method==0:
        _tmp=subprocess.check_output("hostname").split('\n')[0]
    except:
      file=open('/etc/hostname', 'r')
      _tmp=file.readline()
      file.close()

    if self.NameHost!=_tmp:
      self.NameHost=_tmp
      if self.SystemLogger==1:
        self.__Logger('Hostname : \033[33m{:s}\033[0m'.format(self.NameHost),1)

  def getAirPlayName(self):
    if self.SystemType==0:
      checkSystem()
    if self.SystemType==self.Volumio:
      _tmp=subprocess.check_output(["cat", "/etc/shairport-sync.conf"]).split('\"')[1]
    elif self.SystemType==self.RuneAudio:
      _stat=subprocess.check_output(["cat", "/usr/lib/systemd/system/shairport.service"]).split('\n')
      for i in range(2,len(_stat),1):
        if _stat[i].find("--name=")>=0:
          _tmp=_stat[i].split("\"")[1]
    if self.NameAirPlay!=_tmp:
      self.NameAirPlay=_tmp
      if self.SystemLogger==1:
        self.__Logger('AirPlay Name  : \033[33m{:s}\033[0m'.format(self.NameAirPlay),1)

  def getUPmPName(self):
    if self.SystemType==0:
      checkSystem()
    if self.SystemType==self.Volumio:
      _tmp=" "
    elif self.SystemType==self.RuneAudio:
      _stat=subprocess.check_output(["cat", "/usr/lib/systemd/system/upmpdcli.service"]).split('\n')
      for i in range(2,len(_stat),1):
        if _stat[i].find("-f")>=0:
          _tmp=_stat[i].split("\"")[1]
    if self.NameUPmP!=_tmp:
      self.NameUPmP=_tmp
      if self.SystemLogger==1:
        self.__Logger('UPnP/DLNA Name: \033[33m{:s}\033[0m'.format(self.NameUPmP),1)

  def getAudioCardInfo(self):
    try:
      _info=subprocess.check_output(["aplay", "-l"])
      n=_info.count("card")
      _CardId=[None]*n
      _CardName=[None]*n
      _CardDevice=[None]*n
      _CardSubdevice=[None]*n

      start=0
      for i in range(0,n,1):
        locate=_info.find("card", start)
        if locate>=0:
          _CardId[i]=_info[locate+5]
          path="/proc/asound/card"+_CardId[i]+"/id"
          _CardName[i]=subprocess.check_output(["cat", path]).split('\n')[0]
          start=locate
        locate=_info.find("device", start)
        if locate>=0:
          _CardDevice[i]=_info[locate+7]
          start=locate
        locate=_info.find("Subdevices", start)
        if locate>=0:
          _CardSubdevice[i]=_info[locate+14]
          start=locate
          if _info[locate+12]<_info[locate+14] and self.__CardActive!=i:
            self.__CardActive=i
            self.__CardAPath="/proc/asound/card"+_CardId[i]+"/pcm"+_CardDevice[i]+"p/sub0/"
            #print "Actived Sound Card: "+self.__CardAPath
            if self.SystemLogger==1:
              self.__Logger('Active sound card: Card'+_CardId[i]+'-device'+_CardDevice[i]+'('+_CardName[i]+')',1)
        #print "Card{:s}({:s}) -  Device{:s}: {:s}".format(_CardId[i], _CardName[i], _CardDevice[i], _CardSubdevice[i])
    except:
      self.InfoError|=0x02

  #=====================#
  #  Get player status  #
  #=====================#

  def getAudioOutputInfo(self):
    _oldChannels=self.AudioChannels
    _oldSample  =self.AudioSample

    if self.__CardActive==-1:
      self.getAudioCardInfo()
    if self.__CardActive>=0:
      path=self.__CardAPath+"hw_params"
      _info=subprocess.check_output(["cat", path])

      if _info.find("closed")>=0:
        #print "Output: Closed"
        if _oldSample!=0:
          if self.SystemLogger==1:
            self.__Logger('Audio card status: Closed',2)
          self.AudioChannels=0
          self.AudioSample  =0
          self.AudioOutput  =0
          self.InfoUpdate|=0x08
      else:
        self.AudioOutput  =1
        # Channels
        _tmp=_info.find("channels:")
        self.AudioChannels=0
        if ord(_info[_tmp+10])>=0x30 and ord(_info[_tmp+10])<=0x39:
          self.AudioChannels=int(_info[_tmp+10])
        else:
          self.AudioChannels=0
        if _oldChannels!=self.AudioChannels:
          self.InfoUpdate|=0x08
          if self.SystemLogger==1:
            self.__Logger('Audio card channels: {:d}'.format(self.AudioChannels),1)
        # Sample rate
        _tmp=_info.find("rate:")
        self.AudioSample  =0
        for i in range(_tmp+6,_tmp+12,1):
          if _info[i]==' ':
            continue
          if ord(_info[i])>=0x30 and ord(_info[i])<=0x39:
            self.AudioSample=self.AudioSample*10+int(_info[i])
          else:
            if self.AudioSample>0:
              break
        if _oldSample!=self.AudioSample:
          self.InfoUpdate|=0x08
          if self.SystemLogger==1:
            self.__Logger('Audio card status: {:.1f}kHz'.format(float(self.AudioSample)/1000),1)

  def getMPDSetting(self):
    _oldVolume =self.PlayerVolume
    _oldRepeat =self.PlayerRepeat
    _oldRandom =self.PlayerRandom
    _oldSingle =self.PlayerSingle
    _oldConsume=self.PlayerConsume

    try:
      _stat=subprocess.check_output(["mpc"])
    except:
      self.InfoError|=0x08
      return 0

    # Volume
    _locate=_stat.find("volume:")
    self.PlayerVolume=0
    for i in range(_locate+7,_locate+10,1):
      if _stat[i]==' ':
        continue
      if ord(_stat[i])>=0x30 and ord(_stat[i])<=0x39:
        self.PlayerVolume=self.PlayerVolume*10+int(_stat[i])
      else:
        if self.PlayerVolume>0:
          break
    if _oldVolume!=self.PlayerVolume:
      self.InfoUpdate|=0x08
      if self.SystemLogger==1:
        if self.PlayerMute==True and self.PlayerVolume==0:
          self.__Logger('Volume = MUTE',1)
        else:
          self.__Logger('Volume ={:3d}%'.format(self.PlayerVolume),1)
    # Repeat
    _locate=_stat.find("repeat:")
    self.PlayerRepeat=False
    if _stat[_locate+8]=='o':
      if _stat[_locate+9]=='n':
        self.PlayerRepeat=True
      elif _stat[_locate+9]=='f' and _stat[_locate+10]=='f':
        self.PlayerRepeat=False
    if _oldRepeat!=self.PlayerRepeat:
      self.InfoUpdate|=0x08
      if self.SystemLogger==1:
        if self.PlayerRepeat==True:
          self.__Logger('Repeat : On',1)
        else:
          self.__Logger('Repeat : Off',1)
    # Random
    _locate=_stat.find("random:")
    self.PlayerRandom=False
    if _stat[_locate+8]=='o':
      if _stat[_locate+9]=='n':
        self.PlayerRandom=True
      elif _stat[_locate+9]=='f' and _stat[_locate+10]=='f':
        self.PlayerRandom=False
    if _oldRandom!=self.PlayerRandom:
      self.InfoUpdate|=0x08
      if self.SystemLogger==1:
        if self.PlayerRandom==True:
          self.__Logger('Random : On',1)
        else:
          self.__Logger('Random : Off',1)
    # Single
    _locate=_stat.find("single:")
    self.PlayerSingle=False
    if _stat[_locate+8]=='o':
      if _stat[_locate+9]=='n':
        self.PlayerSingle=True
      elif _stat[_locate+9]=='f' and _stat[_locate+10]=='f':
        self.PlayerSingle=False
    if _oldSingle!=self.PlayerSingle:
      self.InfoUpdate|=0x08
      if self.SystemLogger==1:
        if self.PlayerSingle==True:
          self.__Logger('Single : On',1)
        else:
          self.__Logger('Single : Off',1)
    # Consume
    _locate=_stat.find("consume:")
    self.PlayerConsume=False
    if _stat[_locate+9]=='o':
      if _stat[_locate+10]=='n':
        self.PlayerConsume=True
      elif _stat[_locate+10]=='f' and _stat[_locate+11]=='f':
        self.PlayerConsume=False
    if _oldSingle!=self.PlayerConsume:
      self.InfoUpdate|=0x08
      if self.SystemLogger==1:
        if self.PlayerConsume==True:
          self.__Logger('Consume: On',1)
        else:
          self.__Logger('Consume: Off',1)

  def getMPDState(self):
    _oldTime     =self.AudioTime[0]*60+self.AudioTime[1]
    _oldLength   =self.AudioLength[0]*60+self.AudioLength[1]
    _oldNameTitle=self.NameTitle
    _oldNameRadio=self.NameRadio
    _oldQNumber  =self.QueueNumber
    _oldQTotal   =self.QueueTotal

    try:
      _stat=subprocess.check_output(["mpc"])
    except:
      self.InfoError|=0x08
      return 0

    # Play/Paused
    if _stat.find("playing")>=0:
      self.PlayerStatus=11
      #print "Status: playing"
    elif _stat.find("paused")>=0:
      self.PlayerStatus=12
      #print "Status: paused"
    else:
      return 0

    # Track Number
    _tmp=_stat.split('\n')[1].split()[1].split('#')[1].split('/')
    self.QueueNumber=int(_tmp[0])
    self.QueueTotal =int(_tmp[1])
    print "Track no.{:d} of {:d}".format(self.QueueNumber, self.QueueTotal)

    # Music Time/Length
    _tmp=_stat.split('\n')[1].split()[2].split('/')
    self.AudioTime[0]=int(_tmp[0].split(':')[0])
    self.AudioTime[1]=int(_tmp[0].split(':')[1])
    self.AudioLength[0]=int(_tmp[1].split(':')[0])
    self.AudioLength[1]=int(_tmp[1].split(':')[1])
    if _oldTime!=self.AudioTime[0]*60+self.AudioTime[1]:
      self.InfoUpdate|=0x10
    if _oldLength!=self.AudioLength[0]*60+self.AudioLength[1]:
      self.InfoUpdate|=0x20
    print "Time  ={:02d}:{:02d}".format(self.AudioTime[0], self.AudioTime[1])
    print "Length={:02d}:{:02d}".format(self.AudioLength[0], self.AudioLength[1])

    # Track title
    self.NameTitle=_stat.split('\n')[0]
    print "Song: "+self.NameTitle
    # Check source is youTube or webRadio
    if _stat.split('\n')[0].find("source=youtube")>=0:
      self.PlayerStatus=self.PlayerStatus+2
    elif (self.AudioLength[0]*60+self.AudioLength[1])==0:
      self.PlayerStatus=self.PlayerStatus+4
      self.NameRadio=_stat.split('\n')[0].split(': ')[0]
      if _oldNameRadio!=self.NameRadio:
        self.InfoUpdate|=0x40

    return self.PlayerStatus

  def getAirPlayState(self):
    try:
      _tmp=subprocess.check_output(["sudo", "netstat", "-npt"])
      if _tmp.find("shairport")>=0:
        self.PlayerStatus=self.AirPlay
        _stat=_tmp.split('\n')
        for i in range(2,len(_stat),1):
          if _stat[i].find("shairport")>=0:
            if _stat[i].split()[5]=="ESTABLISHED":
              _oldCIP=self.AirPlayCIP
              self.AirPlayCIP=_stat[i].split()[4].split(':')[0]
            if _oldCIP!=self.AirPlayCIP:
              self.InfoUpdate|=0x80
            return 1
      else:
        return 0
    except:
      self.InfoError|=0x04
      return 0

  def getPlayerState(self):
    _oldStat=self.PlayerStatus

    # Check sound card output
    self.getAudioOutputInfo()
    self.getMPDSetting()
    # Get Player status
    self.PlayerStatus=0
    if self.AudioOutput!=0:
      if self.getAirPlayState()==0:
        self.getMPDState()

    if _oldStat!=self.PlayerStatus:
      self.InfoUpdate|=0x04

      if self.SystemLogger==1:
        if self.PlayerStatus==self.PlaylistPlay:
          if _oldStat!=self.PlaylistPause:
            self.__Logger('Player status: playing Playlist',1)
        elif self.PlayerStatus==self.PlaylistPause:
          self.__Logger('Player status: paused Playlist',1)
        elif self.PlayerStatus==self.YouTubePlay:
          if old_stat!=self.YouTubePause:
            self.__Logger('Player status: playing YouTube Stream',1)
        elif self.PlayerStatus==self.YouTubePause:
          self.__Logger('Player status: paused YouTube Stream',1)
        elif self.PlayerStatus==self.WebRadioPlay:
          if _oldStat!=self.WebRadioPause:
            self.__Logger('Player status: playing Web Radio',1)
        elif self.PlayerStatus==self.WebRadioPause:
          self.__Logger('Player status: paused Web Radio',1)
        elif self.PlayerStatus==self.AirPlay:
          self.__Logger('Player status: AirPlay('+self.AirPlayCIP+')',1)
        else:
          self.__Logger('Player status: Standby...',1)

  #=====================#
  #  Set player status  #
  #=====================#
'''
  def setVolumeUp(self, value=1):
    if self.SystemType==0:
      checkSystem()
    if self.PlayerMute==0 and self.PlayerVolume<100:
      if self.SystemType==self.Volumio:
        return None
      elif self.SystemType==self.RuneAudio and self.PlayerVolume!=100:
        subprocess.call(["mpc", "volume", "+{:d}".format(value)])

  def setVolumeDown(self, value=1):
    if self.SystemType==0:
      checkSystem()
    if self.PlayerMute==0 and self.PlayerVolume>0:
      if self.SystemType==self.Volumio:
        return None
      elif self.SystemType==self.RuneAudio:
        subprocess.call(["mpc", "volume", "-{:d}".format(value)])

  def setVolumeMute(self):
    if self.SystemType==0:
      checkSystem()
    if self.SystemType==self.Volumio:
      return None
    elif self.SystemType==self.RuneAudio:
      if self.PlayerMute==0 and self.PlayerVolume>0:
        self.PlayerMute=self.PlayerVolume
        subprocess.call(["mpc", "volume", "0"])
      elif self.PlayerMute!=0:
        subprocess.call(["mpc", "volume", "{:d}".format(self.PlayerMute)])

'''
