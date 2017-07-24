#!/usr/bin/python2
# -------------------------------------------------------
# File name  : ButtonEncoder.py
# Version    : 1.1
# Release    : 2017.07.22
# Author     :
# Description: The library of button switch or incremental
#               encoder for Raspberry Pi.
# -------------------------------------------------------
import time
import RPi.GPIO as GPIO
#sudo apt-get install rpi.gpio

class ButtonEncoder:
  #Define Event Code
  Unknow     =0
  Button_Up  =1
  Button_Down=2
  Encoder_CW =3
  Encoder_CCW=4
  #Event Status
  __eventStatus=0x00
  #Units setup
  __SWtype=0    # 1=Button, 2=Incremental Encoder+Switch
  __PinSW =0
  __PinA  =0
  __PinB  =0
  __Nlevel=True # Normal level. Maybe it depends on GPIO's pull-up and pull-down setting
  #Encoder Bounce Error Debug
  __EncoderDeError =True
  __statLastEncoder=0
  # ** Example: Define GPIO inputs (BCM)
  #    PowerSW  =  4  # Pin 07
  #    EncoderA = 17  # Pin 11
  #    EncoderB = 27  # Pin 13
  #    EncoderSW= 22  # Pin 15
  # Time count
  timeLastSW     =0.0
  timeLastEncoder=0.0
  countdSW       =0.0
  count2SW       =0.0
  count2Encoder  =0.0
  __timeSWdown   =0.0
  
  def __init__(self, type=0, pull='UP', *vartuple):
    # ButtonEncoder(SWtype, pullLevel, PinSW)
    # ButtonEncoder(SWtype, pullLevel, PinSW, PinA, PinB)
    # ** SWtype: 1=Button, 2=Incremental Encoder
    #    [Usage] ButtonEncoder(1, pullLevel, PinSW)
    #            ButtonEncoder(2, pullLevel, [PinSW, PinA, PinB])
    #            ButtonEncoder(2, pullLevel, PinSW, PinA, PinB)
    # ** pull: Internal pull up/down resistor: UP, DOWN >> default: UP
    # ** Pin suggestion : 04(Pin-07), 17(Pin-11), 27(Pin-13), 22(Pin-15), 05(Pin-29), 06(Pin-31), 13(Pin-33), 26(Pin-37),
    #    BCM no.(Pin no.) 23(Pin-16), 24(Pin-18), 25(Pin-22), 12(Pin-32)
    #                     * Pin=0 to skip GPIO setup, but avoid setting PinA=0 and PinB=0 when SWtype is Encoder!
    if type==1 or type==2:
      self.__SWtype=type

      GPIO.setmode(GPIO.BCM)
      GPIO.setwarnings(False)
      if self.__SWtype==1 and (len(vartuple)==1 and isinstance(vartuple[0], int)):
        self.__PinSW=vartuple[0]
        if pull.upper().find('UP')>=0:
          GPIO.setup(self.__PinSW, GPIO.IN, pull_up_down=GPIO.PUD_UP)
          self.__Nlevel=True
        if pull.upper().find('DOWN')>=0:
          GPIO.setup(self.__PinSW, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
          self.__Nlevel=False
      elif self.__SWtype==2:
        if len(vartuple)==1 and (isinstance(vartuple[0], list) and len(vartuple[0])==3 and isinstance(vartuple[0][0], int) and isinstance(vartuple[0][1], int) and isinstance(vartuple[0][2], int)):
          self.__PinSW=vartuple[0][0]
          self.__PinA =vartuple[0][1]
          self.__PinB =vartuple[0][2]
        elif len(vartuple)==3 and (isinstance(vartuple[0], int) and isinstance(vartuple[1], int) and isinstance(vartuple[2], int)): 
          self.__PinSW=vartuple[0]
          self.__PinA =vartuple[1]
          self.__PinB =vartuple[2]
        else:
          self.__SWtype=0
          return None

        if pull.upper().find('UP')>=0:
          if self.__PinSW!=0:
            GPIO.setup(self.__PinSW, GPIO.IN, pull_up_down=GPIO.PUD_UP)
          if self.__PinA !=0:
            GPIO.setup(self.__PinA , GPIO.IN, pull_up_down=GPIO.PUD_UP)
          if self.__PinB !=0:
            GPIO.setup(self.__PinB , GPIO.IN, pull_up_down=GPIO.PUD_UP)
          self.__Nlevel=True
        if pull.upper().find('DOWN')>=0:
          if self.__PinSW!=0:
            GPIO.setup(self.__PinSW, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
          if self.__PinA !=0:
            GPIO.setup(self.__PinA , GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
          if self.__PinB !=0:
            GPIO.setup(self.__PinB , GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
          self.__Nlevel=False
      else:
        self.__SWtype=0
        return None

  def __del__(self):
    GPIO.cleanup()

  def setEncoderDeError(self, mode=1):
    # setEncoderDeError(mode)
    # ** mode: 0=Disable, 1=Enable >> default: Enable
    if self.__SWtype==2:
      if mode==1:
        self.__EncoderDeError=True
      else:
        self.__EncoderDeError=False
  
  def getEncoderDeError(self):
    # getEncoderDeError()
    # ** respond: 1=Enable, 2=Disable or Switch unit
    if self.__SWtype==2 and self.__EncoderDeError==True:
      return 1
    else:
      return 0
  
  def eventBegin(self, callback, object=0, edge='BOTH'):
    # eventBegin(callback)
    # eventBegin(callback, object, edge)
    # ** callback: call function when Interrupt
    # ** object: set Interrupt pin: 1=Button, 2=Encoder  >> default: 0(all)
    # ** edge: set edge detection: RISING, FALLING, BOTH >> default: BOTH
    self.Callback=callback

    if object==0 and ((self.__SWtype==1 and self.__eventStatus&0x03!=0x00) or (self.__SWtype==2 and self.__eventStatus&0x0F!=0x00)):
      self.eventEnd(0)
    elif object==1 and self.__eventStatus&0x03!=0x00:
      self.eventEnd(1)
    elif object==2 and (self.__SWtype==2 and self.__eventStatus&0x0C!=0x00):
      self.eventEnd(2)

    if object==0 or object==1:
      if edge.upper().find('RISING')>=0:
        GPIO.add_event_detect(self.__PinSW, GPIO.RISING, callback=self.eventButton, bouncetime=40)
        self.__eventStatus|=0x01
      elif edge.upper().find('FALLING')>=0:
        GPIO.add_event_detect(self.__PinSW, GPIO.FALLING, callback=self.eventButton, bouncetime=40)
        self.__eventStatus|=0x02
      elif edge.upper().find('BOTH')>=0:
        GPIO.add_event_detect(self.__PinSW, GPIO.BOTH, callback=self.eventButton, bouncetime=40)
        self.__eventStatus|=0x03
    if (object==0 or object==2) and self.__SWtype==2:
      if edge.upper().find('RISING')>=0:
        GPIO.add_event_detect(self.__PinA , GPIO.RISING, callback=self.eventEncoder, bouncetime=20)
        self.__eventStatus|=0x04
      elif edge.upper().find('FALLING')>=0:
        GPIO.add_event_detect(self.__PinA , GPIO.FALLING, callback=self.eventEncoder, bouncetime=20)
        self.__eventStatus|=0x08
      elif edge.upper().find('BOTH')>=0:
        GPIO.add_event_detect(self.__PinA , GPIO.BOTH, callback=self.eventEncoder, bouncetime=20)
        self.__eventStatus|=0x0C

  def eventEnd(self, object=0):
    # eventEnd()
    # eventEnd(object)
    # ** object: set Interrupt pin: 1=Button, 2=Encoder  >> default: 0(all)
    if self.__eventStatus!=0x00:
      if (object==0 or object==1) and self.__eventStatus&0x03!=0x00:
        GPIO.remove_event_detect(self.PinSW)
        self.__eventStatus&=0xFC
      if (object==0 or object==2) and self.__eventStatus&0x0C!=0x00:
        GPIO.remove_event_detect(self.PinA )
        self.__eventStatus&=0xF3

  def eventCheck(self, object=0):
    # eventCheck()
    # eventCheck(object)
    # ** object : set Interrupt pin: 1=Button, 2=Encoder  >> default: 0(all)
    # ** respond: mn (m=Encoder; n=Switch.)
    #      value: 0=None, 1=Rising, 2=Falling, 3=Both
    result=0
    if self.__eventStatus&0x0F!=0x00:
      if object==0 or object==1:
        if self.__eventStatus&0x03==0x01:
          result+=1
        elif self.__eventStatus&0x03==0x02:
          result+=2
        elif self.__eventStatus&0x03==0x03:
          result+=3
      if (object==0 or object==2) and self.__SWtype==2:
        if self.__eventStatus&0x0C==0x04:
          result+=10
        elif self.__eventStatus&0x0C==0x08:
          result+=20
        elif self.__eventStatus&0x0C==0x0C:
          result+=30
    return result

  ## Interrupt Event
  def eventButton(self, pin):
    timepoint=time.time()
    count=0
    access=True

    # Switch debounce
    time.sleep(0.005)
    Button=GPIO.input(self.__PinSW)  
    while access:
      if Button==GPIO.input(self.__PinSW):
        count+=1
      else:
        count=0
        Button=GPIO.input(self.__PinSW)
      if count>=10:
        access=False

    # Analysis action
    if Button==self.__Nlevel:
    #if Button==True
      if self.__eventStatus&0x03==0x01:
        if self.timeLastSW!=0.0:
          self.count2SW=timepoint-self.timeLastSW
        else:
          self.count2SW=0.0
        self.timeLastSW=timepoint
      elif self.__eventStatus&0x03==0x03:
        if self.__timeSWdown!=0.0:
          self.countdSW=timepoint-self.__timeSWdown
        else:
          self.countdSW=0.0
        self.__timeSWdown=0.0
      #Callback function
      if self.__eventStatus&0x01==0x01:
        self.Callback(self.Button_Up  )
        #print "Push up Power Switch - {:.3f}".format(timepoint)
        #if self.countdSW!=0.0:
        #  print "Push timer: {:.3f}s".format(self.countdSW)    
    else:
      if self.__eventStatus&0x02==0x02:
        if self.timeLastSW!=0.0:
          self.count2SW=timepoint-self.timeLastSW
        else:
          self.count2SW=0.0
        self.timeLastSW=timepoint
      if self.__eventStatus&0x03==0x03:
        self.__timeSWdown=timepoint
      #Callback function
      if self.__eventStatus&0x02==0x02:
        self.Callback(self.Button_Down)
        #print "Push down Power Switch - {:.3f}".format(timepoint)

  def eventEncoder(self, pin):
    timepoint=time.time()
    count0=0
    count1=0
    rotate=0
    access=True

    # Encoder debounce
    time.sleep(0.001)
    while access:
      if GPIO.input(self.__PinA)!=GPIO.input(self.__PinB):
        if rotate==2 and count1<=15:
          rotate=1
          count0=0
        else:
          if rotate==0:
            rotate=1
          count0+=1
      else:
        if rotate==1 and count0<=15:
          rotate=2
          count1=0
        else:
          if rotate==0:
            rotate=2
          count1+=1

      if count1>=20:
        access=False

    # Analysis action
    if rotate==0:
      self.__statLastEncoder=0
      self.Callback(self.Unknow     )
      #print "Rotate Encoder: Unknow."
    else:
      if self.timeLastEncoder!=0.0:
        _tmp=timepoint-self.timeLastEncoder
        if self.__EncoderDeError==True and self.__statLastEncoder!=rotate and (self.count2Encoder>=0.2 or self.count2Encoder<=0.06) and _tmp<=0.04:
          print "Encoder Bounce Error Debug detected!"
          return None
        else:
          self.count2Encoder=_tmp
      else:
        self.count2Encoder=0.0
      self.timeLastEncoder=timepoint
      self.__statLastEncoder=rotate

      if rotate==1:
        self.Callback(self.Encoder_CW )
        #print "Rotate Encoder: clockwise."
      elif rotate==2:
        self.Callback(self.Encoder_CCW)
        #print "Rotate Encoder: counter-clockwise."

