from constants import *
import sys
import os
import time
import random
from socket import *
from threading import Thread

if MODE_SELECT==PROGRAM_MODE.HW:
    import smbus
if MODE_SELECT==PROGRAM_MODE.HW_IN_THE_LOOP:
    import Adafruit_GPIO.FT232H as FT232H

global LEVEL_LIST
global LOG_MARK
global MARK_VALUE
global LOG_EVENT
global LOG_INFO
global INFO_STRING
global IS_LOGGING
global FINISH_LOGGING
global DUMP_FILE
global SESSION_DIR
global SESSION_DIR_INIT

SESSION_DIR_INIT="session_"
VERBOS_AVERAGE_WINDOW = 10

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)


LOG_MARK        = False
LOG_EVENT       = False
MARK_VALUE      = 0
IS_LOGGING      = False
LOG_INFO        = False
INFO_STRING     = ""

DEV_ADDRESS     = 0x4a
I2C_CONFIG      = 0xC3E3 #11000011 11100011 #OS=1 MUX=100,A0_GND  PGA=001,1/1 MODE=1,single. data rate 111, rest unchanged
SENSOR_STEP     = 0.1 #100mv/A for the 20A sensor module (-20 to 20 Amps in about 4V)
ADC_SCALE       = 4.096/32768.0
MUX_MULTIPLIER  = 4096 #bits [13-12]
I2C_REG_CONF    = 0x01
I2C_REG_CONV    = 0x00

BUFF            = 1024
HOST            = "127.0.0.1"


if MODE_SELECT==PROGRAM_MODE.HW:
    i2c = smbus.SMBus(1)
if MODE_SELECT==PROGRAM_MODE.HW_IN_THE_LOOP:
    FT232H.use_FT232H() # Temporarily disable FTDI serial drivers.
    ft232h = FT232H.FT232H() # Find the first FT232H device.
    i2c = FT232H.I2CDevice(ft232h, DEV_ADDRESS) # Create an I2C device at address.

###########################################################################################
def open_session():
    global DUMP_FILE
    global SESSION_DIR
    global SESSION_DIR_INIT

    session_id=1
    while os.path.exists(LOG_DIR+"/"+SESSION_DIR_INIT+"%03d"%(session_id)):
        session_id+=1
    SESSION_DIR=SESSION_DIR_INIT+"%03d"%(session_id)
    os.makedirs(LOG_DIR+"/"+SESSION_DIR)
    DUMP_FILE = open(LOG_DIR+"/"+SESSION_DIR+"/dump.log","a")

###########################################################################################
def dump(myStr):
    newStr = time.strftime("%Y_%m_%d_%H_%M_%S \t", time.localtime(time.time()))+myStr
    print newStr
    sys.stdout.flush()
    DUMP_FILE.write(newStr+"\n")
    DUMP_FILE.flush()

###########################################################################################
def i2c_write(reg,val):
    reverse = (val%256)*256 + (val/256) #reformatting the responses for byte order:  0xAaBb => 0xBbAa
    if MODE_SELECT==PROGRAM_MODE.HW:
        i2c.write_word_data(DEV_ADDRESS,reg,reverse)
    if MODE_SELECT==PROGRAM_MODE.HW_IN_THE_LOOP:
        i2c.write16(reg,reverse)
    if MODE_SELECT==PROGRAM_MODE.SW_IN_THE_LOOP:
        time.sleep(0.1)
        pass
###########################################################################################
def i2c_wait_to_read():
    if MODE_SELECT==PROGRAM_MODE.HW:
        time.sleep(0.010)
        while (i2c_read(I2C_REG_CONF)<32768):
            pass
    if MODE_SELECT==PROGRAM_MODE.HW_IN_THE_LOOP:
        time.sleep(0.010)
        while (i2c_read(I2C_REG_CONF)<32768):
            pass
    if MODE_SELECT==PROGRAM_MODE.SW_IN_THE_LOOP:
        pass

###########################################################################################
def i2c_read(reg):
    if MODE_SELECT==PROGRAM_MODE.HW:
        reverse=i2c.read_word_data(DEV_ADDRESS,reg)
    if MODE_SELECT==PROGRAM_MODE.HW_IN_THE_LOOP:
        reverse=i2c.readU16(reg)
    if MODE_SELECT==PROGRAM_MODE.SW_IN_THE_LOOP:
        time.sleep(0.001)
        reverse=random.uniform(3.0,3.5)/ADC_SCALE  # this is an example value which relates to around 3-4V
        reverse = (reverse%256)*256 + (reverse/256) #reformatting the responses for byte order:  0xAaBb => 0xBbAa

    result = (reverse%256)*256 + (reverse/256) #reformatting the responses for byte order:  0xAaBb => 0xBbAa
    return result

###########################################################################################
def calibrate():
    global LEVEL_LIST
    dump("calibrating sensors, motors should not be running...")
    if MODE_SELECT==PROGRAM_MODE.SW_IN_THE_LOOP:
        LEVEL_LIST=[VDD/2.0]*NUMBER_OF_CHANNELS
        dump("SW_IN_THE_LOOP detected, calibrating all motors with default value: %.3f"%(VDD/2.0))
    else:
        LEVEL_LIST=[None]*NUMBER_OF_CHANNELS
        try:
            for channel in range(NUMBER_OF_CHANNELS):
                calibrate_sum = 0.0
                for sample in range(CALIBRATE_SAMPLES):
                    value=I2C_CONFIG
                    value+=channel*MUX_MULTIPLIER
                    i2c_write(I2C_REG_CONF,value)
                    i2c_wait_to_read()
                    value=i2c_read(I2C_REG_CONV)
                    voltage=value * ADC_SCALE
                    calibrate_sum += voltage

                LEVEL_LIST[channel] = calibrate_sum / CALIBRATE_SAMPLES
                dump("channel %d calibrated with %d samples: %.3f"%(channel, CALIBRATE_SAMPLES, LEVEL_LIST[channel]))
            dump("calibration successful")
        except:
            dump("calibration failed, using default value=%.3f for all channels, results might not be correct"%(VDD/2.0))
            for channel in range(NUMBER_OF_CHANNELS):
                LEVEL_LIST[channel]=VDD/2.0

###########################################################################################
def logging():
    global LOG_MARK
    global LOG_EVENT
    global MARK_VALUE
    global FINISH_LOGGING
    global LOG_INFO
    global INFO_STRING
    time.sleep(0.1)
    dump("start of logging thread")
    channel=0
    count=0
    start_time=0
    finish_time=0
    start_time=time.time()
    last_time=start_time
    myFile_name = LOG_DIR+"/"+SESSION_DIR+"/log_"+time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime(start_time))+"_power.log"
    dump("openning file: %s"%(myFile_name))
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
                if (LOG_EVENT):
                    LOG_EVENT=False
                    myLine="%14.3f\t%d"%(now,EVENT_TYPE.EVENT)
                    myBuffer.append(myLine)
                    continue

                if (LOG_MARK):
                    LOG_MARK=False
                    myLine="%14.3f\t%d\t%d"%(now,EVENT_TYPE.MARK,MARK_VALUE)
                    myBuffer.append(myLine)
                    continue

                if (LOG_INFO):
                    LOG_INFO=False
                    myLine="%14.3f\t%d\t%s"%(now,EVENT_TYPE.INFO,INFO_STRING)
                    myBuffer.append(myLine)
                    continue

                if (FINISH_LOGGING):
                    finish_time=now
                    myLine = "%14.3f: logged %d measurements. duration: %8.3f seconds. finishing up this log"%(now,count,finish_time-last_time)
                    dump(myLine)
                    for item in myBuffer:
                        myFile.write("%s\n" % item)
                    myFile.flush()
                    break


            value=I2C_CONFIG
            value+=channel*MUX_MULTIPLIER
            i2c_write(I2C_REG_CONF,value)
            i2c_wait_to_read()
            value=i2c_read(I2C_REG_CONV)
            voltage=value * ADC_SCALE
            current = (voltage - LEVEL_LIST[channel]) / SENSOR_STEP
            if current<0:   # no negative value
                current = 0
            myLine="%14.3f"%(now)+"\t"+str(EVENT_TYPE.MEASUREMENT)+"\t"+"%d"%(channel)+"\t"+"%6.2f"%(current)
            myBuffer.append(myLine)

            if MODE_SELECT==PROGRAM_MODE.HW_IN_THE_LOOP:
                avg[channel]+=current

            channel=channel+1
            if (channel>=NUMBER_OF_CHANNELS):
                channel=0

            count+=1

            if MODE_SELECT==PROGRAM_MODE.HW_IN_THE_LOOP and VERBOS_AVERAGE_WINDOW>0 and count%(NUMBER_OF_CHANNELS*VERBOS_AVERAGE_WINDOW)==0:
                myStr = "--- Average over last " + str(VERBOS_AVERAGE_WINDOW) + " measurements ---\n"
                for i in range(NUMBER_OF_CHANNELS):
                    myStr += "channel "+str(i)+" " + str(avg[i]/VERBOS_AVERAGE_WINDOW) + "\n"
                dump(myStr)
                avg=[0.0] * NUMBER_OF_CHANNELS


            if (count>=LOG_BUFF_COUNT):
                finish_time=now
                myLine = "%14.3f: logged %d measurements. duration: %8.3f seconds"%(now,count,finish_time-last_time)
                dump(myLine)
                for item in myBuffer:
                    myFile.write("%s\n" % item)
                myFile.flush()
                myBuffer=[]
                last_time=finish_time
                count=0

        except Exception as e:
            dump("some error in logging process, passing this loop: "+str(e))
            pass

    dump("end of logging thread here. (won't reach)")


###########################################################################################
#### MAIN
open_session()
dump("--------------------------------------")
dump("STARTED PROGRAM")
dump("Writing logs to folder: %s"%(LOG_DIR+"/"+SESSION_DIR))
dump("Make sure your constant.py file is set. MODE_SELECT, VDD, and LOG_DIR are important for logging")
dump("Currently these values are: %d, %5.3f, %s"%(MODE_SELECT, VDD, LOG_DIR))

ADDR = (HOST,PWR_PORT)
serversock=socket(AF_INET,SOCK_STREAM)
serversock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
serversock.bind(ADDR)
serversock.listen(5)

calibrate()

dump("waiting for the client to connect")
clientsock, add = serversock.accept()
dump("client connected")
while True:
    try: 
        dump("waiting for a command from client")
        data=clientsock.recv(BUFF)
        if data=="":
            dump("there seems to be something wrong with the socket, accepting another socket")
            clientsock, add = serversock.accept()
            open_session()
            dump("--------------------------------------")
            dump("RESTARTING SESSION")
            dump("writing logs to folder: %s"%(LOG_DIR+"/"+SESSION_DIR))
            dump("client connected")
            continue
        dump("data received from client:" + repr(data))
        for command in data.split(PACKET_END):
            if command=="":
                continue
            dump("the number for command is: %d"%(int(command[0].encode("hex"),16)))
            if int(command[0].encode("hex"),16)==PWR_Command.PWR_START and IS_LOGGING==False:
                LOG_EVENT = False
                LOG_MARK = False
                FINISH_LOGGING = False
                LOG_INFO = False
                INFO_STRING = ""
                IS_LOGGING=True
                myThread=Thread(target=logging)
                myThread.start()
                dump("logging thread started from main thread")
                continue

            if int(command[0].encode("hex"),16)==PWR_Command.PWR_STOP and IS_LOGGING==True:
                dump("client wants to finish logging")
                FINISH_LOGGING=True
                myThread.join()
                IS_LOGGING=False
                dump("child thread is done, this session is finished")

            if int(command[0].encode("hex"),16)==PWR_Command.PWR_EVENT and IS_LOGGING==True:
                dump("client wants to record an event")
                while(LOG_EVENT):
                    pass
                LOG_EVENT=True

            if int(command[0].encode("hex"),16)==PWR_Command.PWR_MARK and IS_LOGGING==True:
                dump("client wants to make a numbered mark")
                while(LOG_MARK):
                    pass
                MARK_VALUE=int(command[1:].encode("hex"), 16)
                dump("Mark is: %d"%(MARK_VALUE))
                LOG_MARK=True

            if int(command[0].encode("hex"),16)==PWR_Command.PWR_INFO and IS_LOGGING==True:
                dump("client has some info to log")
                while(LOG_INFO):
                    pass
                INFO_STRING=command[1:].decode('utf-8')
                dump("Info is: %s"%(INFO_STRING))
                LOG_INFO=True

    except KeyboardInterrupt:
        dump("interrupted by user, waiting for logging to finish")
        if IS_LOGGING==True:
            FINISH_LOGGING=True
            myThread.join()
            dump("child thread done")
        dump("now exiting program")
        time.sleep(1.0)
        exit()

