#!/usr/bin/python
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
  #parts setup
  __SWtype=0  # 1=Button, 2=Encoder+Switch
  __PinSW =0
  __PinA  =0
  __PinB  =0
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
    # ButtonEncoder(SWtype, pullLevel, PinSW, PinA, PinB)
    # ** SWtype: 1=Button, 2=Encoder
    #    [Usage] ButtonEncoder(1, pullLevel, PinSW)
    #            ButtonEncoder(2, pullLevel, PinSW, PinA, PinB)
    # ** pull: Internal pull up/down resistor: UP, DOWN >> default: UP
    # ** Pin suggestion : 04(Pin-07), 17(Pin-11), 27(Pin-13), 22(Pin-15), 05(Pin-29), 06(Pin-31), 13(Pin-33), 26(Pin-37),
    #    BCM no.(Pin no.) 23(Pin-16), 24(Pin-18), 25(Pin-22), 12(Pin-32)
    if type==1 or type==2:
      self.__SWtype=type

      GPIO.setmode(GPIO.BCM)
      GPIO.setwarnings(False)
      if self.__SWtype==1 and (len(vartuple)==1 and isinstance(vartuple[0], int)):
        self.__PinSW=vartuple[0]
        if pull.upper().find('UP')>=0:
          GPIO.setup(self.__PinSW, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        if pull.upper().find('DOWN')>=0:
          GPIO.setup(self.__PinSW, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
      elif self.__SWtype==2 and (len(vartuple)==3 and isinstance(vartuple[0], int) and isinstance(vartuple[1], int) and isinstance(vartuple[2], int)):
        self.__PinSW=vartuple[0]
        self.__PinA =vartuple[1]
        self.__PinB =vartuple[2]
        if pull.upper().find('UP')>=0:
          GPIO.setup(self.__PinSW, GPIO.IN, pull_up_down=GPIO.PUD_UP)
          GPIO.setup(self.__PinA , GPIO.IN, pull_up_down=GPIO.PUD_UP)
          GPIO.setup(self.__PinB , GPIO.IN, pull_up_down=GPIO.PUD_UP)
        if pull.upper().find('DOWN')>=0:
          GPIO.setup(self.__PinSW, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
          GPIO.setup(self.__PinA , GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
          GPIO.setup(self.__PinB , GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
      else:
        self.__SWtype=0
        return None

  def __del__(self):
    GPIO.cleanup()

  def eventBegin(self, callback, object=0, edge='BOTH'):
    # eventBegin(callback)
    # eventBegin(callback, object, edge)
    # ** callback: call function when Interrupt
    # ** object: set Interrupt pin: 1=Button, 2=Encoder  >> default: 0(all)
    # ** edge: set edge detection: RISING, FALLING, BOTH >> default: BOTH
    #          Encoder don't have "BOTH" mode, it will be changed to "FALLING" mode
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
      elif edge.upper().find('FALLING')>=0 or edge.upper().find('BOTH')>=0:
        GPIO.add_event_detect(self.__PinA , GPIO.FALLING, callback=self.eventEncoder, bouncetime=20)
        self.__eventStatus|=0x08

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
    return result

  #Interrupt event
  def eventButton(self, pin):
    timepoint=time.time()
    count=0
    access=True

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

    if Button==True:
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
    #timepoint=time.time()
    count0=0
    count1=0
    rotate=0
    access=True

    time.sleep(0.001)
    while access:
      if GPIO.input(self.__PinA)!=GPIO.input(self.__PinB):
        if rotate==2 and count1<=10:
          rotate=1
          count0=0
        else:
          if rotate==0:
            rotate=1
          count0+=1
      else:
        if rotate==1 and count0<=10:
          rotate=2
          count1=0
        else:
          if rotate==0:
            rotate=2
          count1+=1

      if count1>=20:
        access=False

    #timeLastEncoder=0.0
    #count2Encoder  =0.0
    if rotate==0:
      self.Callback(self.Unknow     )
      #print "Rotate Encoder: Unknow."
    elif rotate==1:
      self.Callback(self.Encoder_CW )
      #print "Rotate Encoder: clockwise."
    elif rotate==2:
      self.Callback(self.Encoder_CCW)
      #print "Rotate Encoder: counter-clockwise."

