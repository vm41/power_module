from constants import *
import sys
import os
import time
import random
from ADC128D818 import *
import socket
from threading import Thread

if MODE_SELECT == PROGRAM_MODE.PI:
	import smbus
if MODE_SELECT == PROGRAM_MODE.PC:
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

SESSION_DIR_INIT = "session_"
VERBOS_AVERAGE_WINDOW = 10

if not os.path.exists(LOG_DIR):
	os.makedirs(LOG_DIR)

LOG_MARK = False
LOG_EVENT = False
MARK_VALUE = 0
IS_LOGGING = False
LOG_INFO = False
INFO_STRING = ""
BUFF = 1024
HOST = "127.0.0.1"

if MODE_SELECT == PROGRAM_MODE.PI:
	i2c = smbus.SMBus(1)
if MODE_SELECT == PROGRAM_MODE.PC:
	FT232H.use_FT232H() # Temporarily disable FTDI serial drivers.
	ft232h = FT232H.FT232H() #Find the first FT232H device.
	i2c = FT232H.I2CDevice(ft232h, ADC_ADDRESS.MID_MID) # Create an I2C device at address.

#create the ADC object
adc = ADC128D818(i2c, ADC_ADDRESS.MID_MID)

###########################################################################################
def open_session():
	global DUMP_FILE
	global SESSION_DIR
	global SESSION_DIR_INIT

	session_id = 1
	while os.path.exists(LOG_DIR + "/" + SESSION_DIR_INIT + "%03d" % (session_id)):
		session_id+=1
	SESSION_DIR = SESSION_DIR_INIT + "%03d" % (session_id)
	os.makedirs(LOG_DIR + "/" + SESSION_DIR)
	DUMP_FILE = open(LOG_DIR + "/" + SESSION_DIR + "/dump.log","a")
###########################################################################################
def dump(myStr):
	newStr = time.strftime("%Y_%m_%d_%H_%M_%S \t", time.localtime(time.time())) + myStr
	print(newStr)
	sys.stdout.flush()
	DUMP_FILE.write(newStr + "\n")
	DUMP_FILE.flush()
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
	channel = 0
	count = 0
	start_time = 0
	finish_time = 0
	start_time = time.time()
	last_time = start_time
	myFile_name = LOG_DIR + "/" + SESSION_DIR + "/log_" + time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime(start_time)) + "_power.log"
	dump("openning file: %s" % (myFile_name))
	myFile = open(myFile_name,"a")
	myFile.write("#start time: %13.3f\t" % (start_time))
	myFile.write("\n")
	myFile.write(LOG_HEADER)
	myFile.write("\n")


	myBuffer = []
	avg = [0.0] * adc.NUMBER_OF_CHANNELS
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
					myLine = "\n--------------------------------------"
					myLine += "\nMeasurements Logged: %d" % (count)
					myLine += "\nDuration: %8.3f seconds" % (finish_time-last_time)
					myLine += "\nFinishing up this log"
					myLine += "\n--------------------------------------"
					dump(myLine)
					for item in myBuffer:
						myFile.write("%s\n" % item)
					myFile.flush()
					adc.stop()
					break

			current = adc.read_channel(channel)
			myLine = "%14.3f" % (now) + "\t" + str(EVENT_TYPE.MEASUREMENT) + "\t" + "%d" % (channel) + "\t" + "%6.2f" % (current)
			myBuffer.append(myLine)

			if MODE_SELECT == PROGRAM_MODE.PC:
				avg[channel]+=current

			count += 1
			channel += 1
			if(channel >= adc.NUMBER_OF_CHANNELS):
				channel = 0

                        if (MODE_SELECT == PROGRAM_MODE.PC and VERBOS_AVERAGE_WINDOW > 0 and count % (adc.NUMBER_OF_CHANNELS * VERBOS_AVERAGE_WINDOW) == 0):
				myStr = "\n--- Average over last " + str(VERBOS_AVERAGE_WINDOW) + " measurements ---\n"
				for i in range(0, adc.NUMBER_OF_CHANNELS):
					myStr += "channel " + str(i) + " " + str(avg[i] / VERBOS_AVERAGE_WINDOW) + "\n"
				dump(myStr)
				avg = [0.0] * adc.NUMBER_OF_CHANNELS

			if (count >= LOG_BUFF_COUNT):
				finish_time = now
				myLine = "\n--------------------------------------"
				myLine += "\nMeasurements Logged: %d" % (count)
				myLine += "\nDuration: %8.3f seconds" % (finish_time-last_time)
				myLine += "\nFinishing up this log"
				myLine += "\n--------------------------------------"
				dump(myLine)
				for item in myBuffer:
					myFile.write("%s\n" % item)
				myFile.flush()
				myBuffer = []
				last_time = finish_time
				count = 0

		except Exception as e:
			dump("some error in logging process, passing this loop: " + str(e))
			pass

###########################################################################################
#### MAIN
open_session()
dump("--------------------------------------")
dump("STARTED PROGRAM")
dump("Writing logs to folder: %s" % (LOG_DIR + "/" + SESSION_DIR))
dump("Make sure your constant.py file is set. MODE_SELECT, VDD, and LOG_DIR are important for logging")
dump("Currently these values are: %d, %5.3f, %s" % (MODE_SELECT, VDD, LOG_DIR))

#intialize the ADC to 8 single ended inputs, external VREF, continuous	#sampling and no masked channels or interrupts
#sampling and no masked channels or interrupts
#adc.initialize(ADC_MODE.MODE_1, ADC_VREF.EXT, ADC_RATE.CONTINUOUS, 0, 0)
adc.initialize(ADC_MODE.MODE_1, ADC_VREF.EXT, ADC_RATE.CONTINUOUS, ADC_ENABLE.IN2 | ADC_ENABLE.IN3 | ADC_ENABLE.IN4 | ADC_ENABLE.IN5, 0)#Motors only

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
adc.calibrate(2)
adc.calibrate(3)
adc.calibrate(4)
adc.calibrate(5)
adc.calibrate(6)
adc.calibrate(7)

ADDR = (HOST,constants.PWR_PORT)
serversock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serversock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
serversock.bind(ADDR)
serversock.listen(5)

dump("waiting for the client to connect")
clientsock, add = serversock.accept()
dump("client connected")
while True:
	try: 
		dump("waiting for a command from client")
		data = clientsock.recv(BUFF)
		if data == "":
			dump("there seems to be something wrong with the socket, accepting another socket")
			clientsock, add = serversock.accept()
			open_session()
			dump("--------------------------------------")
			dump("RESTARTING SESSION")
			dump("writing logs to folder: %s" % (LOG_DIR + "/" + SESSION_DIR))
			dump("client connected")
			continue
		dump("data received from client:" + repr(data))
		for command in data.split(PACKET_END):
			if command == "":
				continue
			dump("the number for command is: %d" % (int(command[0].encode("hex"),16)))
			if int(command[0].encode("hex"),16) == PWR_Command.PWR_START and IS_LOGGING == False:
				LOG_EVENT = False
				LOG_MARK = False
				FINISH_LOGGING = False
				LOG_INFO = False
				INFO_STRING = ""
				IS_LOGGING = True
				myThread = Thread(target=logging)
				myThread.start()
				dump("logging thread started from main thread")
				continue

			if int(command[0].encode("hex"),16) == PWR_Command.PWR_STOP and IS_LOGGING == True:
				dump("client wants to finish logging")
				FINISH_LOGGING = True
				myThread.join()
				IS_LOGGING = False
				dump("child thread is done, this session is finished")

			if int(command[0].encode("hex"),16) == PWR_Command.PWR_EVENT and IS_LOGGING == True:
				dump("client wants to record an event")
				while(LOG_EVENT):
					pass
				LOG_EVENT = True

			if int(command[0].encode("hex"),16) == PWR_Command.PWR_MARK and IS_LOGGING == True:
				dump("client wants to make a numbered mark")
				while(LOG_MARK):
					pass
				MARK_VALUE = int(command[1:].encode("hex"), 16)
				dump("Mark is: %d" % (MARK_VALUE))
				LOG_MARK = True

			if int(command[0].encode("hex"),16) == PWR_Command.PWR_INFO and IS_LOGGING == True:
				dump("client has some info to log")
				while(LOG_INFO):
					pass
				INFO_STRING = command[1:].decode('utf-8')
				dump("Info is: %s" % (INFO_STRING))
				LOG_INFO = True

	except KeyboardInterrupt:
		dump("interrupted by user, waiting for logging to finish")
		if IS_LOGGING == True:
			FINISH_LOGGING = True
			myThread.join()
			dump("child thread done")
		dump("now exiting program")
		time.sleep(1.0)
		exit()
