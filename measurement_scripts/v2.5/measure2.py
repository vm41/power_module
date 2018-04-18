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
from Transformation import *
#Mode selection
if MODE_SELECT==PROGRAM_MODE.HW:
    import smbus
if MODE_SELECT==PROGRAM_MODE.HW_IN_THE_LOOP:
    import Adafruit_GPIO.FT232H as FT232H

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
        if MODE_SELECT == PROGRAM_MODE.PI:
            self.i2c = smbus.SMBus(1)
        if MODE_SELECT == PROGRAM_MODE.PC:
            FT232H.use_FT232H() # Temporarily disable FTDI serial drivers.
            ft232h = FT232H.FT232H() #Find the first FT232H device.
            self.i2c = FT232H.I2CDevice(ft232h, ADC_ADDRESS.MID_MID) # Create an I2C device at address.
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

    # # ###########################################################################################
    def i2c_write(self, reg, val):
        reverse = (val%256)*256 + (val/256) #reformatting the responses for byte order:  0xAaBb => 0xBbAa
        if MODE_SELECT==PROGRAM_MODE.HW:
            self.i2c.write_word_data(self.DEV_ADDRESS, reg, reverse)
        if MODE_SELECT==PROGRAM_MODE.HW_IN_THE_LOOP:
            self.i2c.write16(reg,reverse)
        if MODE_SELECT==PROGRAM_MODE.SW_IN_THE_LOOP:
            time.sleep(0.1)
            pass
    # # ###########################################################################################
    def i2c_wait_to_read(self):
        if MODE_SELECT==PROGRAM_MODE.HW:
            time.sleep(0.010)
            while (self.i2c_read(self.I2C_REG_CONF)<32768):
                pass
        if MODE_SELECT==PROGRAM_MODE.HW_IN_THE_LOOP:
            time.sleep(0.010)
            while (self.i2c_read(self.I2C_REG_CONF)<32768):
                pass
        if MODE_SELECT==PROGRAM_MODE.SW_IN_THE_LOOP:
            pass

    ############################################################################################
    def i2c_read(self, reg):
        if MODE_SELECT==PROGRAM_MODE.HW:
            reverse=self.i2c.read_word_data(self.DEV_ADDRESS,reg)
        if MODE_SELECT==PROGRAM_MODE.HW_IN_THE_LOOP:
            reverse=self.i2c.readU16(reg)
        if MODE_SELECT==PROGRAM_MODE.SW_IN_THE_LOOP:
            time.sleep(0.001)
            reverse=random.uniform(3.0,3.5)/self.ADC_SCALE  # this is an example value which relates to around 3-4V
            reverse = (reverse%256)*256 + (reverse/256) #reformatting the responses for byte order:  0xAaBb => 0xBbAa

        result = (reverse%256)*256 + (reverse/256) #reformatting the responses for byte order:  0xAaBb => 0xBbAa
        return result

    ###########################################################################################
    def calibrate(self):
        self.dump("calibrating sensors, motors should not be running...")
        if MODE_SELECT==PROGRAM_MODE.SW_IN_THE_LOOP:
            self.LEVEL_LIST=[VDD/2.0]*NUMBER_OF_CHANNELS
            self.dump("SW_IN_THE_LOOP detected, calibrating all motors with default value: %.3f"%(VDD/2.0))
        else:
            self.LEVEL_LIST=[None]*NUMBER_OF_CHANNELS
            try:
                for channel in range(NUMBER_OF_CHANNELS):
                    calibrate_sum = 0.0
                    for sample in range(CALIBRATE_SAMPLES):
                        value=self.I2C_CONFIG
                        value+=channel*self.MUX_MULTIPLIER
                        self.i2c_write(self.I2C_REG_CONF, value)
                        self.i2c_wait_to_read()
                        value=self.i2c_read(self.I2C_REG_CONV)
                        voltage=value * self.ADC_SCALE
                        calibrate_sum += voltage

                    self.LEVEL_LIST[channel] = calibrate_sum / CALIBRATE_SAMPLES
                    self.dump("channel %d calibrated with %d samples: %.3f"%(channel, CALIBRATE_SAMPLES, self.LEVEL_LIST[channel]))
                self.dump("calibration successful")
            except:
                self.dump("calibration failed, using default value=%.3f for all channels, results might not be correct"%(VDD/2.0))
                for channel in range(NUMBER_OF_CHANNELS):
                    self.LEVEL_LIST[channel]=VDD/2.0

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
        avg=[0.0]*NUMBER_OF_CHANNELS
        while True:
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
                        # new line
                        self.adc.stop()
                        break

                # new line, reading adc channel value
                current = self.adc.read_channel(channel)
                #create the Transformation object
                sensorStep = Transformation(1)
                current = sensorStep.transform(current)
                ##

                ### redundant################
                #value=self.I2C_CONFIG
                #value+=channel*self.MUX_MULTIPLIER
                #self.i2c_write(self.I2C_REG_CONF,value)
                #self.i2c_wait_to_read()
                #value=self.i2c_read(self.I2C_REG_CONV)
                #voltage=value * self.ADC_SCALE
                #current = (voltage - self.LEVEL_LIST[channel]) / self.SENSOR_STEP
                #if current<0:   # no negative value
                #    current = 0
                ################
                myLine="%14.3f"%(now)+"\t"+str(EVENT_TYPE.MEASUREMENT)+"\t"+"%d"%(channel)+"\t"+"%6.2f"%(current)
                myBuffer.append(myLine)
                if MODE_SELECT == PROGRAM_MODE.PC:
                    avg[channel]+=current
                # if MODE_SELECT==PROGRAM_MODE.HW_IN_THE_LOOP:
                #     avg[channel]+=current

                channel=channel+1
                if (channel>=NUMBER_OF_CHANNELS):
                    channel=0

                count+=1
                if(channel >= self.adc.NUMBER_OF_CHANNELS):# my be 4, or 8
                    channel = 0

                            if (MODE_SELECT == PROGRAM_MODE.PC and VERBOS_AVERAGE_WINDOW > 0 and count % (self.adc.NUMBER_OF_CHANNELS * VERBOS_AVERAGE_WINDOW) == 0):
                    myStr = "\n--- Average over last " + str(VERBOS_AVERAGE_WINDOW) + " measurements ---\n"
                    for i in range(0, self.adc.NUMBER_OF_CHANNELS):
                        myStr += "channel " + str(i) + " " + str(avg[i] / VERBOS_AVERAGE_WINDOW) + "\n"
                    self.dump(myStr)
                    avg = [0.0] * self.adc.NUMBER_OF_CHANNELS
                # if MODE_SELECT==PROGRAM_MODE.HW_IN_THE_LOOP and self.VERBOS_AVERAGE_WINDOW>0 and count%(NUMBER_OF_CHANNELS*self.VERBOS_AVERAGE_WINDOW)==0:
                #     myStr = "--- Average over last " + str(self.VERBOS_AVERAGE_WINDOW) + " measurements ---\n"
                #     for i in range(NUMBER_OF_CHANNELS):
                #         myStr += "channel "+str(i)+" " + str(avg[i]/self.VERBOS_AVERAGE_WINDOW) + "\n"
                #     self.dump(myStr)
                #     avg=[0.0] * NUMBER_OF_CHANNELS


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

    # new entries
    #intialize the ADC to 8 single ended inputs, external VREF, continuous  #sampling and no masked channels or interrupts
    #sampling and no masked channels or interrupts
    adc.initialize(ADC_MODE.MODE_1, ADC_VREF.EXT, ADC_RATE.CONTINUOUS, 0, 0)

    #Setting the limits for each channel from 0 to vref
    for c in range(0, adc.NUMBER_OF_CHANNELS):
        adc.initialize_limit(c, ADC_LIMIT.HIGH, 0x80)
        adc.initialize_limit(c, ADC_LIMIT.LOW, 0)

    #Start the ADC
    adc.start()
    #Here is where channels would be calibrated
    #call adc.calibrate(channel) for each channel that has an initial input
    #voltage of 0, e.g the motors are initially off so their current
    #consumption is 0 while the PI wil already be drawing current and therefore
    #cant be calibrated to account fo a zero input response
    adc.calibrate(0)
    adc.calibrate(1)
    adc.calibrate(3)
    adc.calibrate(4)
    adc.calibrate(5)
    adc.calibrate(6)
    adc.calibrate(7)
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
         
