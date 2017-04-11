#!/usr/bin/python
import smbus
from time import sleep
import logging

# LCD Commands
# ---------------------------------------------------------------------------
LCD_CLEARDISPLAY       =0x01
LCD_RETURNHOME         =0x02
LCD_ENTRYMODESET       =0x04
LCD_DISPLAYCONTROL     =0x08
LCD_CURSORSHIFT        =0x10
LCD_FUNCTIONSET        =0x20
LCD_SETCGRAMADDR       =0x40
LCD_SETDDRAMADDR       =0x80
# ** SSD1311: entended command
LCD_EXTENDEDFUNCTIONSET=0x08

# flags for display entry mode (_displaymode)
# ---------------------------------------------------------------------------
LCD_ENTRYRIGHT         =0x00
LCD_ENTRYLEFT          =0x02
LCD_ENTRYSHIFTINCREMENT=0x01
LCD_ENTRYSHIFTDECREMENT=0x00

# flags for display on/off and cursor control (_displaycontrol)
# ---------------------------------------------------------------------------
LCD_DISPLAYON          =0x04
LCD_DISPLAYOFF         =0x00
LCD_CURSORON           =0x02
LCD_CURSOROFF          =0x00
LCD_BLINKON            =0x01
LCD_BLINKOFF           =0x00

# flags for display/cursor shift
# ---------------------------------------------------------------------------
LCD_DISPLAYMOVE        =0x08
LCD_CURSORMOVE         =0x00
LCD_MOVERIGHT          =0x04
LCD_MOVELEFT           =0x00

# flags for function set
# ---------------------------------------------------------------------------
# ** Disp: LCM
LCD_8BITMODE           =0x10
LCD_4BITMODE           =0x00
LCD_2LINE              =0x08
LCD_1LINE              =0x00
LCD_5x10DOTS           =0x04
LCD_5x8DOTS            =0x00
# ** Disp: SSD1311
#          flags for function set , RE=0 (_displayfunction)
LCD_2OR4LINE           =0x08    #N=1 (POR)
LCD_1OR3LINE           =0x00    #N=0
LCD_EXTENSIONREGISTERON=0x02    # RE: extension register for extension command
LCD_DOUBLEHEIGHTON     =0x04    #DH=1
LCD_DOUBLEHEIGHTOFF    =0x00    #DH=0 (POR)

# flags for extended function set	(_extenddisplayfunction)
LCD_6DOTS              =0x04
LCD_5DOTS              =0x00
LCD_INVERTCURSORON     =0x02
LCD_3OR4LINE           =0x01    #NW=1
LCD_1OR2LINE           =0x00    #NW=0

# flags for function set , RE=1	(_displayfunctionRE)
LCD_REVERSEDISPLAYON   =0x01    #REV=1
LCD_REVERSEDISPLAYOFF  =0x00    #REV=0

#PCF8574T/PCF8574AT Pin Layout
Pin_RS = 0x01  #Pin P0
Pin_RW = 0x02  #Pin P1
Pin_EN = 0x04  #Pin P2
Pin_BL = 0x08  #Pin P3
Pin_D4 = 0x10  #Pin P4
Pin_D5 = 0x20  #Pin P5
Pin_D6 = 0x40  #Pin P6
Pin_D7 = 0x80  #Pin P7


class I2C_DISP:
  __bus = smbus.SMBus(1)

  #I2C Slave Address
  #PCF8574T     : 0x20~0x27
  #PCF8574AT    : 0x38~0x3F
  #SSD1311(OLED): 0x3C~0x3D
  __address = 0x00

  #Disp_mode
  #LCM(4bits) : 0
  #OLED(4bits): 1
  #OLED(I2C)  : 2
  __Disp_mode = 0
  
  __backlightStsMask = 0x00 # LCM: backlight

  ##==================##
  ##  Basic Function  ##
  ##==================##
  def __init__(self, address, disp=0):
    self.__address  = address
    self.__Disp_mode= disp
    self.__bus.write_byte(self.__address,self.__backlightStsMask)

  def sendCommand(self, command):
    if self.__Disp_mode == 2:
      self.__bus.write_byte_data(self.__address,0x80,command)
    else:
      self.pulseEN( (command & 0xF0) | self.__backlightStsMask)
      self.pulseEN( ((command << 4) & 0xF0) | self.__backlightStsMask)

  def sendData(self, data):
    if self.__Disp_mode == 2:
      self.__bus.write_byte_data(self.__address,0x40,data)
    else:
      self.pulseEN( (data & 0xF0) | Pin_RS | self.__backlightStsMask)
      self.pulseEN( ((data << 4) & 0xF0) | Pin_RS | self.__backlightStsMask)

  def pulseEN(self, data):
    self.__bus.write_byte(self.__address,data | Pin_EN)
    self.__bus.write_byte(self.__address,data & ~Pin_EN)

  def createChar(self, location, charmap):
    location &= 0x7
    self.sendCommand(0x40|(location<<3))
    sleep(0.1)

    if len(charmap) >= 8:
      for i in range(0, 8, 1):
        self.sendData(charmap[i])
        #delayMicroseconds(40);

  def uploadCGRAM(self, count, charmap):
    self.sendCommand(0x40)
    sleep(0.1)

    if count >= 8: count=8
    if count > 0 and len(charmap) >= 8*count:
      for i in range(0, count*8, 1):
        self.sendData(charmap[i])
        #delayMicroseconds(40);

  def setBacklight(self, state):
    if self.__Disp_mode==0 and state==1:
      self.__backlightStsMask=Pin_BL
    else:
      self.__backlightStsMask=0x00
    self.__bus.write_byte(self.__address,self.__backlightStsMask)

#================
#  Display
#================
class DISPLAY(I2C_DISP):
  #System State Variable
  #__backlightStsMask = 0x00 # LCM: backlight
  __displayfunction  = 0x00 # LCM: 5x10/5x8 DOTS, 4/8 BITMODE, 1/2 LINE
                            # SSD1131:[RE=0, SD=0] N(2,4/1,3 LINE), DH(DoubleHeight); Enter RE(0->1)
  __displaycontrol   = 0x00 # Base control command: LCD on/off, blink, cursor
  __displaymode      = 0x00 # Text entry mode to the LCD
#  # SSD1131 Extra state
#  __extenddisplayfunction = 0x00
#  __displayfunctionRE     = 0x00
  
  __cols=20
  __rows=4
  __row_offsets = [0x00, 0x40, 0x14, 0x54]
  __disp_mode=0
  __cgram_num=0
  def __init__(self, address=0x00, cols=20, rows=4, disp=0, cgram=[None]):
    self.__cols     = cols
    self.__rows     = rows
    self.__disp_mode= disp

    self.begin_debuginfo()
    if address!=0x00:
      if self.__disp_mode==0:
        if (address>=0x20 and address<=0x27) or (address>=0x38 and address<=0x3F):
          self.Disp_Device=I2C_DISP(address, 0)
          self.begin_lcd()
          self.logger.info('Display(4bit-LCD) ready...')
      elif self.__disp_mode==1:
        if (address>=0x20 and address<=0x27) or (address>=0x38 and address<=0x3F):
          self.Disp_Device=I2C_DISP(address, 1)
          self.begin_oled()
          self.logger.info('Display(4bit-OLED) ready...')
      elif self.__disp_mode==2:
        if address==0x3C or address==0x3D:
          self.Disp_Device=I2C_DISP(address, 2)
          self.begin_oled()
          self.logger.info('Display(I2C-OLED) ready...')
      else:
        self.logger.error('Invalid display type!')
        return None

      if len(cgram)>=8:
        self.__cgram_num=len(cgram)/8
        if self.__cgram_num>8:
          self.__cgram_num=8
        self.noDisplay()
        self.Disp_Device.uploadCGRAM(self.__cgram_num,cgram)
        self.display()

      if self.__disp_mode == 0:
        self.__displayfunction = (LCD_4BITMODE | LCD_1LINE | LCD_5x8DOTS)
      else:
        self.__displayfunction = (LCD_2OR4LINE | LCD_DOUBLEHEIGHTOFF)
#        self.__extenddisplayfunction    = LCD_5DOTS       #FW=0
#        if self.__rows <= 2:
#          self.__extenddisplayfunction |= LCD_1OR2LINE    #NW=0
#        else:
#          self.__extenddisplayfunction |= LCD_3OR4LINE    #NW=1
#      self.__displayfunctionRE = (self.__displayfunction & 0xF8)  #clear last 3 bits
      self.__displaycontrol    = (LCD_DISPLAYON | LCD_CURSOROFF | LCD_BLINKOFF)
      self.__displaymode       = (LCD_ENTRYLEFT | LCD_ENTRYSHIFTDECREMENT)
    else:
      self.logger.error('Invalid I2C address!')

  def initDisp(self, cgram=[None]):
    if self.__disp_mode==0:
      self.begin_lcd()
    else:
      self.begin_oled()

    if len(cgram)>=8:
      self.__cgram_num=len(cgram)/8
      if self.__cgram_num>8:
        self.__cgram_num=8
      self.noDisplay()
      self.Disp_Device.uploadCGRAM(self.__cgram_num,cgram)
      self.display()

  def begin_lcd(self):
    if self.__disp_mode==0:
      self.Disp_Device.sendCommand(0x33)       #
      sleep(0.001)
      self.Disp_Device.sendCommand(0x33)       #
      self.Disp_Device.sendCommand(0x33)       #
      self.Disp_Device.sendCommand(0x32)       # Set 4bit
      self.Disp_Device.sendCommand(0x28)       # Set Function Set: LCD_2LINE, LCD_5x8DOTS, LCD_4BITMODE
      self.Disp_Device.sendCommand(0x06)       # Set Entry Mode: LCD_ENTRYLEFT
      self.Disp_Device.sendCommand(0x08)       # Set Sleep Mode On
      self.Disp_Device.sendCommand(0x01)       # Clear Display
      self.Disp_Device.sendCommand(0x80)       # Set DDRAM Address to 0x80 (line 1 start)
      sleep(0.1)
      self.Disp_Device.sendCommand(0x0C)       # Turn on Display
      self.Disp_Device.setBacklight(1)

  def begin_oled(self):
    if self.__disp_mode==1 or self.__disp_mode==2:
      self.Disp_Device.sendCommand(0x08)
      self.Disp_Device.sendCommand(0x28)
      self.Disp_Device.sendCommand(0x06)
      sleep(0.01)
      self.Disp_Device.sendCommand(0x0C)
# The following is for SSD1311
#      self.Disp_Device.sendCommand(0x2A)      # ***** Set "RE"=1, "IS"=0  00101010B
#      self.Disp_Device.sendCommand(0x71)      # [010] Function Selection A  [71h] (IS = X, RE = 1, SD=0), 2bajty
#      self.Disp_Device.sendData(0x5C)         # [010] 0x5C set Vdd
#      self.Disp_Device.sendCommand(0x28)      # ***** Set "RE"=0, "IS"=0  00101000B
#
#      self.Disp_Device.sendCommand(0x08)      # [000] Set Sleep Mode On
#      self.Disp_Device.sendCommand(0x2A)      # ***** Set "RE"=1, "IS"=0  00101010B
#      self.Disp_Device.sendCommand(0x79)      # ***** Set "SD"=1(when "RE"=1)
#
#      self.Disp_Device.sendCommand(0xD5)      # [011] Set Display Clock Divide Ratio/ Oscillator Frequency (D5h
#      self.Disp_Device.sendCommand(0x70)      #
#      self.Disp_Device.sendCommand(0x78)      # ***** Set "SD"=0(when "RE"=1)
#
#      if(self.__rows >= 3):                   # [010] Set 5-dot,
#        self.Disp_Device.sendCommand(0x09)    #   |   Set 3 or 4 line(0x09)
#      else:                                   #   |
#        self.Disp_Device.sendCommand(0x08)    #   |   Set 1 or 2 line(0x08)
#      self.Disp_Device.sendCommand(0x06)      # [010] Set Com0-->Com31  Seg99-->Seg0
#      sleep(5)
#
#      # **** Set OLED Characterization
#      self.Disp_Device.sendCommand(0x2A)      # ***** Set "RE"=1
#
#      # **** CGROM/CGRAM Management
#      self.Disp_Device.sendCommand(0x72)      # [010] Set ROM:
#      self.Disp_Device.sendData(0x00)         #   |   Set ROM A and 8 CGRAM
#      #self.Disp_Device.sendData(0x05)        #   |   Set ROM B and 8 CGRAM
#
#      self.Disp_Device.sendCommand(0x79)      # ***** Set "SD"=1(when "RE"=1)
#      self.Disp_Device.sendCommand(0xDA)      # [011] Set Seg Pins HW Config:
#      self.Disp_Device.sendCommand(0x10)      #   |
#
#      self.Disp_Device.sendCommand(0x81)      # [011] Set Contrast:
#      self.Disp_Device.sendCommand(0xFF)      #   |
#
#      self.Disp_Device.sendCommand(0xDB)      # [011] Set VCOM deselect level:
#      self.Disp_Device.sendCommand(0x30)      #   |   VCC x 0.83
#      sleep(0.01)
#
#      self.Disp_Device.sendCommand(0xDC)      # [011] Set gpio - turn EN for 15V generator on:
#      self.Disp_Device.sendCommand(0x03)      #   |
#
#      self.Disp_Device.sendCommand(0x78)      # ***** Set "SD"=0(when "RE"=1)
#      self.Disp_Device.sendCommand(0x28)      # ***** Set "RE"=0, "IS"=0
#
#      #self.Disp_Device.sendCommand(0x05)     # [000] Set Entry Mode
#      self.Disp_Device.sendCommand(0x06)      # [000] Set Entry Mode
#
#      self.Disp_Device.sendCommand(0x08)      # [000] Set Sleep Mode On
#      self.Disp_Device.sendCommand(0x01)      # [000] Clear Display
#      self.Disp_Device.sendCommand(0x80)      # [000] Set DDRAM Address to 0x80 (line 1 start)
#      sleep(0.01)
#      self.Disp_Device.sendCommand(0x0C)      # [000] Turn on Display

  def begin_debuginfo(self):
    self.logger = logging.getLogger('displaylog')
    self.hdlr = logging.FileHandler('/tmp/display.log')
    self.formatter = logging.Formatter('%(asctime)s | [%(levelname)s] %(message)s','%Y/%m/%d %H:%M:%S')
    self.hdlr.setFormatter(self.formatter)

    self.logger.addHandler(self.hdlr) 
    self.logger.setLevel(logging.DEBUG)
    self.logger.info('-- Start to store display controlled message --')

  def sendDebugInfo(self, arg, level=1):
    # sendDebugInfo(string, level)
    # ** level 0=DEBUG
    #          1=INFO(default)
    #          2=WARNING
    #          3=ERROR
    #          4=CRITICAL
    if isinstance(arg, str):
      if level==0:
        self.logger.debug(arg)
      elif level==1:
        self.logger.info(arg)
      elif level==2:
        self.logger.warning(arg)
      elif level==3:
        self.logger.error(arg)
      elif level==4:
        self.logger.critical(arg)

  ##====================##
  ##  Display Function  ##
  ##====================##

  def clear(self):
    # clear display, set cursor position to zero
    self.Disp_Device.sendCommand(LCD_CLEARDISPLAY)
    sleep(0.002)
    self.logger.info('Control: Clear')

  def home(self):
    # set cursor position to zero
    self.Disp_Device.sendCommand(LCD_RETURNHOME)

  def setCursor(self, col, row):
    if row > self.__rows:
      row = self.__rows-1
    self.Disp_Device.sendCommand(0x80 | (col + self.__row_offsets[row]))
  # This will 'right justify' text from the cursor
  def autoscroll(self):
    self.__displaymode |= LCD_ENTRYSHIFTINCREMENT
    self.Disp_Device.sendCommand(LCD_ENTRYMODESET | self.__displaymode)
  # This will 'left justify' text from the cursor
  def noAutoscroll(self):
    self.__displaymode &= ~LCD_ENTRYSHIFTINCREMENT
    self.Disp_Device.sendCommand(LCD_ENTRYMODESET | self.__displaymode)
  # This is for text that flows Left to Right
  def leftToRight(self): 
    self.__displaymode |= LCD_ENTRYLEFT
    self.Disp_Device.sendCommand(LCD_ENTRYMODESET | self.__displaymode)
  # This is for text that flows Right to Left
  def rightToLeft(self):
    self.__displaymode &= ~LCD_ENTRYLEFT
    self.Disp_Device.sendCommand(LCD_ENTRYMODESET | self.__displaymode)

  ##===========================##
  ##  Display on/off Function  ##
  ##     __displaycontrol      ##
  ##     __backlightStsMask    ##
  ##===========================##
  #Turn on Display
  def display(self):
    self.__displaycontrol |= LCD_DISPLAYON
    self.Disp_Device.sendCommand(LCD_DISPLAYCONTROL | self.__displaycontrol)
    #sendCommand(0x0C)			# **** Turn on
    self.logger.info('Control: Turn display on')

  #Turn off Display
  def noDisplay(self):
    self.__displaycontrol &= ~LCD_DISPLAYON
    self.Disp_Device.sendCommand(LCD_DISPLAYCONTROL | self.__displaycontrol)
    #sendCommand(0x08)			# **** Turn Off
    self.logger.info('Control: Turn display off')

  def on(self):
    self.display()
    self.clear()
    self.backlight()

  def off(self):
    self.noBacklight()
    self.noDisplay()
  #Turn on Backlight(No need for OLED module)
  def backlight(self):
    if self.__disp_mode!=1 and self.__disp_mode!=2:
      self.Disp_Device.setBacklight(1)
      self.logger.info('Control: Light backlight on')
  #Turn off Backlight(No need for OLED module)
  def noBacklight(self):
    if self.__disp_mode!=1 and self.__disp_mode!=2:
      self.Disp_Device.setBacklight(0)
      self.logger.info('Control: Light backlight off')

  ##==========================##
  ##  Display Tools Function  ##
  ##     __displaycontrol     ##
  ##==========================##
  #Display Cursor
  def cursor(self):
    self.__displaycontrol |= LCD_CURSORON
    self.Disp_Device.sendCommand(LCD_DISPLAYCONTROL | self.__displaycontrol)
    self.logger.info('Control: Turn cursor on')
  #Don't Display Cursor
  def noCursor(self):
    self.__displaycontrol &= ~LCD_CURSORON
    self.Disp_Device.sendCommand(LCD_DISPLAYCONTROL | self.__displaycontrol)
    self.logger.info('Control: Turn cursor off')
  #Display Invert Cursor
  def blink(self):
    self.__displaycontrol |= LCD_BLINKON
    self.Disp_Device.sendCommand(LCD_DISPLAYCONTROL | self.__displaycontrol)
    self.logger.info('Control: Turn invert cursor on')
  #Don't Display Invert Cursor
  def noBlink(self):
    self.__displaycontrol &= ~LCD_BLINKON
    self.Disp_Device.sendCommand(LCD_DISPLAYCONTROL | self.__displaycontrol)
    self.logger.info('Control: Turn invert cursor off')

  ##===================================##
  ##  Display(SSD1311) Tools Function  ##
  ##===================================##
#Set entension register (RE) bit
#  def setRE(self):
#    self.__displayfunction |= LCD_EXTENSIONREGISTERON
#    self.Disp_Device.sendCommand(LCD_FUNCTIONSET | self.__displayfunction)
#    #                                  0x20      |          0x02
#    #sendCommand(0x2A)  # set RE to 1
#Set entension register (RE) bit
#  def clearRE(self):
#    self.__displayfunction &= ~LCD_EXTENSIONREGISTERON
#    self.Disp_Device.sendCommand(LCD_FUNCTIONSET | self.__displayfunction)	#2A
#    #sendCommand(0x28)  # clear RE
#def cursorInvert():
  #Set OLED Command set
  #sendCommand(0x2A)
#  setRE()
#  self.__extenddisplayfunction |= LCD_INVERTCURSORON
#  self.Disp_Device.sendCommand(LCD_EXTENDEDFUNCTIONSET | self.__extenddisplayfunction)
#  clearRE()
  #sendCommand(0x28)
#black/white inverting of cursor
#def noCursorInvert():
  #Set OLED Command set
  #sendCommand(0x2A)
#  setRE()
#  self.__extenddisplayfunction &= ~LCD_INVERTCURSORON
#  self.Disp_Device.sendCommand(LCD_EXTENDEDFUNCTIONSET | self.__extenddisplayfunction)
#  clearRE()
  #sendCommand(0x28)

#def reverseDisplay():
#  global _displayfunctionRE
  #sendCommand(0x2A);	# set RE to 1
  #Set OLED Command set
#  setRE()
  #sendCommand(0x2B)	# set RE to 1, REV to 1
#  self.__displayfunctionRE = (self.__displayfunction & 0xFA) | LCD_REVERSEDISPLAYON)
#  self.Disp_Device.sendCommand(LCD_FUNCTIONSET | self.__displayfunctionRE)
#  clearRE()
  #sendCommand(0x28)	# clear RE

#def noReverseDisplay():
#  global _displayfunctionRE
  #Set OLED Command set
#  setRE()
  #sendCommand(0x2A)	# set RE to 1
  #sendCommand(0x2A)	# set RE to 1
#  self.__displayfunctionRE = (self.__displayfunction & 0xFA)
#  self.Disp_Device.sendCommand(LCD_FUNCTIONSET | self.__displayfunctionRE)
#  clearRE()
  #sendCommand(0x28)	# clear RE
  ##==========================##
  ##  Display Print Function  ##
  ##==========================##
  
  def printCGRam(self, arg, *vartuple):
    # printCGRam(String)
    # printCGRam(String, col, row)
  
    if len(vartuple) == 2 and isinstance(vartuple[0], int) and isinstance(vartuple[0], int):
      col=vartuple[0]
      row=vartuple[1]
      self.setCursor(col, row)
  
    if self.__cgram_num!=0:
      if isinstance(arg, list):
        for i in range(0, len(arg), 1):
          if arg[i]>=0 and arg[i]<=self.__cgram_num:
            self.Disp_Device.sendData(arg[i])
      else:
        if arg>=0 and arg<=self.__cgram_num:
          self.Disp_Device.sendData(arg)
  
  def sendString(self, arg, *vartuple):
    # sendString(String)
    # sendString(String, col, row)
  
    if len(vartuple) == 2 and isinstance(vartuple[0], int) and isinstance(vartuple[0], int):
      col=vartuple[0]
      row=vartuple[1]
      self.setCursor(col, row)

    if isinstance(arg, str):
      for i in range(0, len(arg), 1):
        self.Disp_Device.sendData(ord(arg[i]))

  def sendStringAlign(self, arg, length=0, sp=' ', ali='LEFT', *vartuple):
    # sendStringAlign(String, length, space, align)		>> default: col=0, row=0
    # sendStringAlign(String, length, space, align, row)	>> default: col=0
    # sendStringAlign(String, length, space, align, col, row)
    # ** space: show symbol on empty char:				>> default: ' '
    # ** align: LEFT, CENTER, RIGHT						>> default: LEFT
    if len(vartuple) == 1 and isinstance(vartuple[0], int):
      col=0
      row=vartuple[0]
    elif len(vartuple) == 2 and isinstance(vartuple[0], int) and isinstance(vartuple[1], int):
      col=vartuple[0]
      row=vartuple[1]
    else:
      col=0
      row=0

    self.setCursor(col, row)

    if length == 0:
      length = len(arg)
  
    if isinstance(arg, str):
      if len(arg) >= length:
        self.sendString(str(arg))
      else:
        if ali.upper().find('LEFT')>=0:
          self.sendString('{:{space}{align}{width}s}'.format(arg,space=sp,align='<',width=length))
        if ali.upper().find('CENTER')>=0:
          self.sendString('{:{space}{align}{width}s}'.format(arg,space=sp,align='^',width=length))
        if ali.upper().find('RIGHT')>=0:
          self.sendString('{:{space}{align}{width}s}'.format(arg,space=sp,align='>',width=length))

  def sendHex(self, value, sign=0, *vartuple):
    # sendHex(value)
    # sendHex(value, sign)
    # sendHex(value, sign, col, row)
    # ** sign: 0: none, 1: 0x00
    if isinstance(value,list):
      Arr=1
    else:
      Arr=0

    if len(vartuple) == 2 and isinstance(vartuple[0], int) and isinstance(vartuple[1], int):
      col=vartuple[0]
      row=vartuple[1]
      self.setCursor(col, row)

    if Arr == 0:
      if sign == 0:
        self.sendString('{:X}'.format(int(value)))
      else:
        self.sendString('0x{:X}'.format(int(value)))
    else:
      if sign == 0:
        for i in range(0, len(arg), 1):
          self.sendString('{:X}'.format(int(value[i])))
          if i <= (len(arg)-1):
            self.sendString(' ')
      else:
        for i in range(0, len(arg), 1):
          self.sendString('0x{:X}'.format(int(value[i])))
        if i <= (len(arg)-1):
            self.sendString(' ')

  def sendInteger(self, value, *vartuple):
    # sendInteger(value)
    # sendInteger(value, length)
    # sendInteger(value, col, row)
    # sendInteger(value, length, col, row)
    NumberTypes = (int, long, float)

    try:
      if isinstance(value, complex):
        C_value=1
      else:
        C_value=0
    except NameError:
      # No support for complex numbers compiled
      C_value=0

    length=0
    if len(vartuple) == 1 and isinstance(vartuple[0], int):
      length=vartuple[0]
    elif len(vartuple) == 2 and isinstance(vartuple[0], int) and isinstance(vartuple[1], int):
      col=vartuple[0]
      row=vartuple[1]
      setCursor(col, row)
    elif len(vartuple) == 3 and isinstance(vartuple[0], int) and isinstance(vartuple[1], int) and isinstance(vartuple[2], int):
      length=vartuple[0]
      col=vartuple[1]
      row=vartuple[2]
      self.setCursor(col, row)

    if C_value == 1:
      self.sendString('{0:d} {1} {2:d}i'.format(int(value.real), '+-'[value.imag < 0], int(abs(value.imag))))
    elif isinstance(value, NumberTypes):
      if value<=pow(10,20):
        if length == 0:
          self.sendString('{:d}'.format(int(value)))
        else:
          self.sendString('{:{width}d}'.format(int(value),width=length))

  def sendFloat(self, value, *vartuple):
    # sendFloat(value)
    # sendFloat(value, precision)
    # sendFloat(value, col, row)
    # sendFloat(value, precision, col, row)
    NumberTypes = (int, float)

    try:
      if isinstance(value, complex):
        C_value=1
      else:
        C_value=0
    except NameError:
      # No support for complex numbers compiled
      C_value=0

    prec=3
    if len(vartuple) == 1 and isinstance(vartuple[0], int):
      prec=vartuple[0]
    elif len(vartuple) == 2 and isinstance(vartuple[0], int) and isinstance(vartuple[1], int):
      col=vartuple[0]
      row=vartuple[1]
      self.setCursor(col, row)
    elif len(vartuple) == 3 and isinstance(vartuple[0], int) and isinstance(vartuple[1], int) and isinstance(vartuple[2], int):
      prec=vartuple[0]
      col=vartuple[1]
      row=vartuple[2]
      self.setCursor(col, row)

    if C_value == 1:
      self.sendString('{0:f} {1} {2:f}i'.format(int(value.real), '+-'[value.imag < 0], int(abs(value.imag))))
    elif isinstance(value, long):
      self.sendString('{:.{prec}E}'.format(value, precision=prec))
    elif isinstance(value, NumberTypes):
      if value < pow(10,-3):
        self.sendString('{:.{prec}E}'.format(value, precision=prec))
      else:
        self.sendString('{:.{prec}f}'.format(float(value), precision=prec))
