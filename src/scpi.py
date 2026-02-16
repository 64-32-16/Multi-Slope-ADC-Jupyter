import time, socket

class SCPIInst:
  def __init__(self, ip, port):
    self.ip = ip
    self.port = port
    self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.socket.connect((ip, port))
    #self.socket.settimeout(1) # Sekunden 

  def send(self, cmd):
    cmd = cmd+"\n"
    self.socket.sendall(cmd.encode())  
    
  # TODO Read Funktion verbessern und timeout einführen
  def read(self):
    result = "NO_RESULT"
    try:
      raw = self.socket.recv(1024)
      result = raw.decode()
    except:
        print( "No Result");
    return result;
  
  def wait(self, delay= 0.1):
    time.sleep(delay)    
    
  # Allgemeine SCPI Funktionen  
  # soll die Lesegeschwindigkeit verbessern  
  def setDisplayOn(self):
    self.send("DISP ON")
  
  def setDisplayOff(self):
    self.send("DISP OFF")    


#---------------------------------------------------------------------
# DMM6500
#---------------------------------------------------------------------
class DMM6500(SCPIInst):
  def __init__(self, ip, port):
    super().__init__(ip, port)


  def reset(self):
     self.send("*RST")

  def setRange( self, range="AUTO"):
    if str(range).upper() == "AUTO":
        self.send("SENS:VOLT:DC:RANG AUTO")
    else:
        self.send(f"SENS:VOLT:DC:RANG {range}")

  def setNPLC( self, nplc ):
    self.send(f"SENS:VOLT:DC:NPLC {nplc}")

  def setFunctionVoltDC(self):
    self.send("SENS:FUNC 'VOLT:DC'")


  def getVoltDC(self):
    self.send("READ?")  # trigger and return a single read
    return float(self.read())

  def getIdent(self):
    self.send("*IDN?")
    value = self.read()
    return value

  def setDisplayOff(self):
    self.send("DISPLAY:LIGHT:STATE OFF")

  def setDisplayOn(self):
    self.send("DISPLAY:LIGHT:STATE ON")

#---------------------------------------------------------------------
# A-SMU 100
#---------------------------------------------------------------------
class ASMU(SCPIInst):
  def __init__(self, ip, port):
    super().__init__(ip, port)

      
  def setPWM(self, value=0):
    self.send(":SET:PWM {0}".format(value))
    result = self.read()

  def getIdent(self):
    self.send("*IDN?")
    self.wait(0.5);
    value = self.read()
    return value

  def getVoltage(self):
    self.send(":READ?")
    self.wait(0.5);
    value = self.read()
    return float(value)
            
#---------------------------------------------------------------------
# Fluke8846
#---------------------------------------------------------------------
class Fluke8846(SCPIInst):
  def __init__(self, ip, port):
    super().__init__(ip, port)


  def getVoltDC(self, rng=1):
    self.send("MEAS:volt:dc? {0}".format(rng))
    self.wait()
    return float(self.read())

  def getCurrentDC(self, rng=0.1):
    self.send("MEAS:curr:dc? {0}".format(rng))
    self.wait()
    return float(self.read())
    

  
  def setDisplayText(self, text):
    self.send('DISP:TEXT "{0}"'.format(text))
  
  def getIdent(self):
    self.send("*IDN?")
    
    value = self.read()
    return value

    
    
  def setRemote(self):
     self.send("SYST:REM")
        
            
#---------------------------------------------------------------------
# DP832A Rigol
#---------------------------------------------------------------------
class DP832A(SCPIInst):
  def __init__(self, ip, port):
    super().__init__(ip, port)

  # CH  
  def selectChannel(self, ch):
    self.send(":INST CH{0}".format(ch))
        
  def setVoltage(self, ch, value):
    if( value > 10.0 ): 
        return

    self.send(":VOLT {0}".format(value))
    self.wait(0.2)
   
    
  def channelOn(self, ch):                
    self.send(":OUTP CH{0},ON".format(ch))
    

  def channelOff(self, ch):            
    self.send(":OUTP CH{0},OFF".format(ch))
    
  def getCurrent(self, ch):    
    self.send(":MEAS:CURR? CH{0}".format(ch))
   
    self.wait(0.2)
    value = self.read()
    return float(value)


#---------------------------------------------------------------------
# DAC100
#---------------------------------------------------------------------
class DAC100(SCPIInst):
  def __init__(self, ip, port):
    super().__init__(ip, port)

      
  def setDACA(self, value):

    self.send("SET:DAC:A {0}".format(value))
    self.wait(1.0)

  def setDACB(self, value):

    self.send("SET:DAC:B {0}".format(value))
    self.wait(1.0)

  def setVoltage(self, value):

    self.send("SET:VOLT {0}".format(value))
    self.wait(1.0)
    


#---------------------------------------------------------------------
# RedPitaty
#---------------------------------------------------------------------

class redpitaya:
  def __init__(self, ip, port):
    self.ip = ip
    self.port = port
    self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.socket.connect((ip, port))
    
  def getAverageState(self):
    cmd = "ACQ:AVG?"+"\r\n"
    self.socket.sendall(cmd.encode())
    raw = self.socket.recv(512)
    value = raw.decode().strip('{}\n\r')
    return value

  def getVoltage(self, ch):
    n=1
    cmd = "ACQ:START"+"\r\n"
    self.socket.sendall(cmd.encode())
    cmd = "ACQ:TRIG NOW"+"\r\n"
    self.socket.sendall(cmd.encode())
    
    cmd = "ACQ:SOUR{0}:DATA:LAT:N? {1}".format(ch,n)+"\r\n"
    self.socket.sendall(cmd.encode())  
    time.sleep(0.2) # TODO Eine bessere Lösung finden
    raw = self.socket.recv(512)
    value = raw.decode().strip('{}\n\r')
    return float(value)

    
  def getSocket(self):
    return self.socket
    
    
  def setOutToDC(self, ch):
    cmd = "SOUR{0}:FUNC PWM".format(ch)+"\r\n"
    self.socket.sendall(cmd.encode()) 
    cmd = "SOUR{0}:FREQ:FIX 100".format(ch)+"\r\n"
    self.socket.sendall(cmd.encode()) 
    cmd = "SOUR{0}:DCYC 1.0".format(ch)+"\r\n"
    self.socket.sendall(cmd.encode()) 
    cmd = "SOUR{0}:VOLT:OFFS 0.0".format(ch)+"\r\n"
    self.socket.sendall(cmd.encode()) 
    cmd = "SOUR{0}:VOLT 0.0".format(ch)+"\r\n"
    self.socket.sendall(cmd.encode()) 

  # ! Amplitude ist Strom abhänig !  
  def setOutAmplitude(self, ch, value):
    cmd = "SOUR{0}:VOLT {1}".format(ch, value)+"\r\n"
    self.socket.sendall(cmd.encode()) 
    
        
  def setOutOn(self, ch):
    cmd = "OUTPUT{0}:STATE ON".format(ch)+"\r\n"
    self.socket.sendall(cmd.encode()) 
    
#---------------------------------------------------------------------
# DP832A Rigol
#---------------------------------------------------------------------
    
    