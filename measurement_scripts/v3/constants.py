#import ADC128D818
#from ADC128D818 import *
class PWR_Command:
	PWR_START = 0
	PWR_STOP = 1
	PWR_EVENT = 2
	PWR_MARK = 3
	PWR_INFO = 4

class EVENT_TYPE:
	MEASUREMENT = 1
	EVENT = 2
	MARK = 3
	INFO = 4

class PROGRAM_MODE:
        PI = 0
    	PC = 1
    	PC_SIMULATE_DATA = 2

class SENSOR_TYPE:
    DISABLE = 0
    VOLTAGE = 1
    HALL = 2
    SHUNT = 3

# CUSTOMIZE
MODE_SELECT = PROGRAM_MODE.PI #selected mode
VDD = 4.85 #actual voltage on a 5V pin powering the measurement module as float
DEBUG_MODE = False
VERBOS_AVERAGE_WINDOW = 1000
#DEVICE_ADDRESS=ADC_ADDRESS.MID_MID

PWR_HOST = "127.0.0.1"
PWR_PORT = 35760
PACKET_END = '\r\r\n\n'
CALIBRATION_SAMPLES = 100

#LOG_BUFF_COUNT = number of readings before saving to file
if MODE_SELECT == PROGRAM_MODE.PI:
	LOG_BUFF_COUNT = 10000 
if MODE_SELECT == PROGRAM_MODE.PC:
	LOG_BUFF_COUNT = 1000
if MODE_SELECT == PROGRAM_MODE.PC_SIMULATE_DATA:
	LOG_BUFF_COUNT = 4000

LOG_DIR = "current"

#this string is just for information, it is printed
#on the second line of the log file after startTime
LOG_HEADER = "#time		#event_type	#event_data(channel&current(A), MarkNumber, ..."


# Defining type of sensor on each channel of the ADC.
# each cahnnel is a tuple, the first element is sensor type
# second element is a calibration flag (true is to calibrate and false is raw readings)
# you may want to calibrate those channels only, that have a biased reading
# CUSTOMIZE
CHANNEL_SENSOR_MAP = [
        (SENSOR_TYPE.HALL, True),           #channel 0
        (SENSOR_TYPE.HALL, True), 
        (SENSOR_TYPE.HALL, True), 
        (SENSOR_TYPE.HALL, True), 
        (SENSOR_TYPE.VOLTAGE, True),        #this is enabled to be stored at calibration, later should be uncalibrated.
        (SENSOR_TYPE.DISABLE, False), 
        (SENSOR_TYPE.DISABLE, False), 
        (SENSOR_TYPE.DISABLE, False), 
        (SENSOR_TYPE.DISABLE, False), 
        (SENSOR_TYPE.DISABLE, False), 
        (SENSOR_TYPE.DISABLE, False), 
        (SENSOR_TYPE.DISABLE, False), 
        ]
