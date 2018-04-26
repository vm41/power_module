from constants import *
import sys
import os
import time
import random
from socket import *
from threading import Thread
# importing the ADC class file
from ADC128D818 import *
# importing the Transformation file
from Conversion import *
#Mode selection
if MODE_SELECT == PROGRAM_MODE.PI:
    import smbus
if MODE_SELECT == PROGRAM_MODE.PC:
    import Adafruit_GPIO.FT232H as FT232H
if MODE_SELECT == PROGRAM_MODE.PI:
    i2c = smbus.SMBus(1)
if MODE_SELECT == PROGRAM_MODE.PC:
    FT232H.use_FT232H() # Temporarily disable FTDI serial drivers.
    ft232h = FT232H.FT232H() #Find the first FT232H device.
    i2c = FT232H.I2CDevice(ft232h, ADC_ADDRESS.MID_MID) # Create an I2C device at address.
class Measure(object):
    """Encapsulates all the necessary functions and attributes required for logging the current measurement:

    Attributes:
        __LEVEL_LIST: description
        LOG_MARK: description
        MARK_VALUE:
        LOG_EVENT:
        LOG_INFO:
        INFO_STRING:
        IS_LOGGING:
        FINISH_LOGGING:
        DUMP_FILE:
        SESSION_DIR:
        SESSION_DIR_INIT:
    Methods:
        open_session():
        dump(myStr):
    """





    def __init__(self, adc):#one can pass i2c address here
        '''
        Initilisation goes here
        '''
        self.LEVEL_LIST                = None
        self.LOG_MARK                  = False
        self.MARK_VALUE                = 0
        self.LOG_EVENT                 = False
        self.LOG_INFO                  = False
        self.INFO_STRING               = ""
        self.IS_LOGGING                = False
        self.FINISH_LOGGING            = None
        self.DUMP_FILE                 = None
        self.SESSION_DIR               = None
        self.SESSION_DIR_INIT          = "session_"
        self.VERBOS_AVERAGE_WINDOW     = 10
        self.DEV_ADDRESS               = 0x4a
        self.I2C_CONFIG                = 0xC3E3 #11000011 11100011 #OS=1 MUX=100,A0_GND  PGA=001,1/1 MODE=1,single. data rate 111, rest unchanged
        self.SENSOR_STEP               = 0.1 #100mv/A for the 20A sensor module (-20 to 20 Amps in about 4V)
        self.ADC_SCALE                 = 4.096/32768.0
        self.MUX_MULTIPLIER            = 4096 #bits [13-12]
        self.I2C_REG_CONF              = 0x01
        self.I2C_REG_CONV              = 0x00
        self.BUFF                      = 1024
        self.HOST                      = "127.0.0.1"
        self.i2c                       = None
        self.adc                       = adc
        if not os.path.exists(LOG_DIR):
            os.makedirs(LOG_DIR)
        # new addition
        # if MODE_SELECT == PROGRAM_MODE.PI:
        #     self.i2c = smbus.SMBus(1)
        # if MODE_SELECT == PROGRAM_MODE.PC:
        #     FT232H.use_FT232H() # Temporarily disable FTDI serial drivers.
        #     ft232h = FT232H.FT232H() #Find the first FT232H device.
        #     self.i2c = FT232H.I2CDevice(ft232h, ADC_ADDRESS.MID_MID) # Create an I2C device at address.
        ################
        ### redundant    
        # if MODE_SELECT==PROGRAM_MODE.HW:
        #     self.i2c = smbus.SMBus(1)
        # if MODE_SELECT==PROGRAM_MODE.HW_IN_THE_LOOP:
        #     FT232H.use_FT232H() # Temporarily disable FTDI serial drivers.
        #     ft232h = FT232H.FT232H() # Find the first FT232H device.
        #     self.i2c = FT232H.I2CDevice(ft232h, self.DEV_ADDRESS) # Create an I2C device at address.

    # ###########################################################################################
    def open_session(self):
        session_id=1
        while os.path.exists(LOG_DIR+"/"+self.SESSION_DIR_INIT+"%03d"%(session_id)):
            session_id+=1
        self.SESSION_DIR=self.SESSION_DIR_INIT+"%03d"%(session_id)
        os.makedirs(LOG_DIR+"/"+self.SESSION_DIR)
        self.DUMP_FILE = open(LOG_DIR+"/"+self.SESSION_DIR+"/dump.log","a")
        print self.SESSION_DIR

    # ###########################################################################################
    def dump(self, myStr):
        newStr = time.strftime("%Y_%m_%d_%H_%M_%S \t", time.localtime(time.time()))+myStr
        print newStr
        sys.stdout.flush()
        self.DUMP_FILE.write(newStr+"\n")
        self.DUMP_FILE.flush()

    ###########################################################################################
    def logging(self):
        time.sleep(0.1)
        self.dump("start of logging thread")
        channel=0
        count=0
        start_time=0
        finish_time=0
        start_time=time.time()
        last_time=start_time
        myFile_name = LOG_DIR+"/"+self.SESSION_DIR+"/log_"+time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime(start_time))+"_power.log"# creating new file under current session directory
        self.dump("openning file: %s"%(myFile_name))
        myFile=open(myFile_name,"a")
        myFile.write("#start time: %13.3f\t"%(start_time))
        myFile.write("\n")
        myFile.write(LOG_HEADER)
        myFile.write("\n")

        myBuffer=[]
        avg=[0.0]*self.adc.NUMBER_OF_CHANNELS
        while True:
            channel=channel+1
            if (channel>=self.adc.NUMBER_OF_CHANNELS):
                channel=0
            try:
                now=time.time()
                if (channel==0):
                    if (self.LOG_EVENT):
                        self.LOG_EVENT=False
                        myLine="%14.3f\t%d"%(now,EVENT_TYPE.EVENT)
                        myBuffer.append(myLine)
                        continue

                    if (self.LOG_MARK):
                        self.LOG_MARK=False
                        myLine="%14.3f\t%d\t%d"%(now,EVENT_TYPE.MARK,self.MARK_VALUE)
                        myBuffer.append(myLine)
                        continue

                    if (self.LOG_INFO):
                        self.LOG_INFO=False
                        myLine="%14.3f\t%d\t%s"%(now,EVENT_TYPE.INFO,self.INFO_STRING)
                        myBuffer.append(myLine)
                        continue

                    if (self.FINISH_LOGGING):
                        finish_time=now
                        myLine = "%14.3f: logged %d measurements. duration: %8.3f seconds. finishing up this log"%(now,count,finish_time-last_time)
                        self.dump(myLine)
                        for item in myBuffer:
                            myFile.write("%s\n" % item)
                        myFile.flush()
                        break

                if CHANNEL_SENSOR_MAP[channel] == SENSOR_TYPE.DISABLE:
                    continue

                # new line, reading adc channel value
                raw_reading = self.adc.read_channel(channel)

                #convert the readings if required
                sensorStep = Conversion()
                channel_data = sensorStep.convert(CHANNEL_SENSOR_MAP[channel], raw_reading)

                ################
                myLine="%14.3f"%(now)+"\t"+str(EVENT_TYPE.MEASUREMENT)+"\t"+"%d"%(channel)+"\t"+"%6.2f"%(channel_data)
                myBuffer.append(myLine)
                
                if (MODE_SELECT == PROGRAM_MODE.PC):
                    avg[channel]+=channel_data

                    if (VERBOS_AVERAGE_WINDOW > 0 and count % (self.adc.NUMBER_OF_CHANNELS * VERBOS_AVERAGE_WINDOW) == 0):
                        myStr = "\n--- Average over last " + str(VERBOS_AVERAGE_WINDOW) + " measurements ---\n"
                        for i in range(0, self.adc.NUMBER_OF_CHANNELS):
                            myStr += "channel " + str(i) + " " + str(avg[i] / VERBOS_AVERAGE_WINDOW) + "\n"
                        self.dump(myStr)
                        avg = [0.0] * self.adc.NUMBER_OF_CHANNELS

                count+=1
                if (count>=LOG_BUFF_COUNT):
                    finish_time=now
                    myLine = "%14.3f: logged %d measurements. duration: %8.3f seconds"%(now,count,finish_time-last_time)
                    self.dump(myLine)
                    for item in myBuffer:
                        myFile.write("%s\n" % item)
                    myFile.flush()
                    myBuffer=[]
                    last_time=finish_time
                    count=0

            except Exception as e:
                self.dump("some error in logging process, passing this loop: "+str(e))
                pass

        self.dump("end of logging thread here. (won't reach)")


if __name__ == '__main__':
    #create the ADC object
    adc = ADC128D818(i2c, ADC_ADDRESS.MID_MID)

    #intialize the ADC to 8 single ended inputs, external VREF, continuous  #sampling and no masked channels or interrupts
    #sampling and no masked channels or interrupts
    channels_to_measure = []
    for ch in range(adc.NUMBER_OF_CHANNELS):
        if (CHANNEL_SENSOR_MAP[ch] != SENSOR_TYPE.DISABLE):
            channels_to_measure.append(ch)

    print "Channels to measure:", channels_to_measure

    adc.initialize(ADC_MODE.MODE_1, ADC_VREF.EXT, ADC_RATE.CONTINUOUS, channels_to_measure, 0)

    #Here is where channels would be calibrated
    #call adc.calibrate(channel) for each channel that has an initial input
    #voltage of 0, e.g the motors are initially off so their current
    #consumption is 0 while the PI wil already be drawing current and therefore
    #cant be calibrated to account fo a zero input response
    for ch in channels_to_measure:
        if (CHANNEL_SENSOR_MAP[ch] == SENSOR_TYPE.HALL) or
           (CHANNEL_SENSOR_MAP[ch] == SENSOR_TYPE.SHUNT):
            adc.calibrate(ch)
    ##########################
    currentServer = Measure(adc)#instanciating the class object
    currentServer.open_session()
    currentServer.dump("--------------------------------------")
    currentServer.dump("STARTED PROGRAM")
    currentServer.dump("Writing logs to folder: %s"%(LOG_DIR+"/"+currentServer.SESSION_DIR))
    currentServer.dump("Make sure your constant.py file is set. MODE_SELECT, VDD, and LOG_DIR are important for logging")
    currentServer.dump("Currently these values are: %d, %5.3f, %s"%(MODE_SELECT, VDD, LOG_DIR))

    
    ADDR = (currentServer.HOST,PWR_PORT)
    serversock=socket(AF_INET,SOCK_STREAM)
    serversock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    serversock.bind(ADDR)
    serversock.listen(5)

    # currentServer.calibrate()

    currentServer.dump("waiting for the client to connect")
    clientsock, add = serversock.accept()
    currentServer.dump("client connected")
    while True:
        try: 
            currentServer.dump("waiting for a command from client")
            data=clientsock.recv(currentServer.BUFF)
            if data=="":
                currentServer.dump("there seems to be something wrong with the socket, accepting another socket")
                clientsock, add = serversock.accept()
                currentServer.open_session()
                currentServer.dump("--------------------------------------")
                currentServer.dump("RESTARTING SESSION")
                currentServer.dump("writing logs to folder: %s"%(LOG_DIR+"/"+currentServer.SESSION_DIR))
                currentServer.dump("client connected")
                continue
            currentServer.dump("data received from client:" + repr(data))
            for command in data.split(PACKET_END):
                if command=="":
                    continue
                currentServer.dump("the number for command is: %d"%(int(command[0].encode("hex"),16)))
                if int(command[0].encode("hex"),16)==PWR_Command.PWR_START and currentServer.IS_LOGGING==False:
                    currentServer.LOG_EVENT = False
                    currentServer.LOG_MARK = False
                    currentServer.FINISH_LOGGING = False
                    currentServer.LOG_INFO = False
                    currentServer.INFO_STRING = ""
                    currentServer.IS_LOGGING=True
                    myThread=Thread(target=currentServer.logging)
                    myThread.start()
                    currentServer.dump("logging thread started from main thread")
                    continue

                if int(command[0].encode("hex"),16)==PWR_Command.PWR_STOP and currentServer.IS_LOGGING==True:
                    currentServer.dump("client wants to finish logging")
                    currentServer.FINISH_LOGGING=True
                    myThread.join()
                    currentServer.IS_LOGGING=False
                    currentServer.dump("child thread is done, this session is finished")

                if int(command[0].encode("hex"),16)==PWR_Command.PWR_EVENT and currentServer.IS_LOGGING==True:
                    currentServer.dump("client wants to record an event")
                    while(currentServer.LOG_EVENT):
                        pass
                    currentServer.LOG_EVENT=True

                if int(command[0].encode("hex"),16)==PWR_Command.PWR_MARK and currentServer.IS_LOGGING==True:
                    currentServer.dump("client wants to make a numbered mark")
                    while(currentServer.LOG_MARK):
                        pass
                    currentServer.MARK_VALUE=int(command[1:].encode("hex"), 16)
                    currentServer.dump("Mark is: %d"%(currentServer.MARK_VALUE))
                    currentServer.LOG_MARK=True

                if int(command[0].encode("hex"),16)==PWR_Command.PWR_INFO and currentServer.IS_LOGGING==True:
                    currentServer.dump("client has some info to log")
                    while(currentServer.LOG_INFO):
                        pass
                    currentServer.INFO_STRING=command[1:].decode('utf-8')
                    currentServer.dump("Info is: %s"%(currentServer.INFO_STRING))
                    currentServer.LOG_INFO=True

        except KeyboardInterrupt:
            currentServer.dump("interrupted by user, waiting for logging to finish")
            if currentServer.IS_LOGGING==True:
                currentServer.FINISH_LOGGING=True
                myThread.join()
                currentServer.dump("child thread done")
            currentServer.dump("now exiting program")
            time.sleep(1.0)
            exit()
