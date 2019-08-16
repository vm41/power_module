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

class SENSOR_PURPOSE:
    NONE = 0
    BATTERY_VOLTAGE = 1
    MOTOR_CURRENT = 2
    DEVICE_CURRENT = 3

# CUSTOMIZE
MODE_SELECT = PROGRAM_MODE.PI#selected mode
VDD = 5.00 #actual voltage on a 5V pin powering the measurement module as float
DEBUG_MODE = False
VERBOS_AVERAGE_WINDOW = 1000

#if True (default), then the measurement will finish when tcp_client closes
#if false, the measurement will ocntinue after disconnection (and should probably be killed manually)
TCP_CLIENT_DEPENDENT=False

PWR_HOST = "127.0.0.1"
PWR_PORT = 35760
PACKET_END = '\r\r\n\n'
CALIBRATION_SAMPLES = 100


EARTH_R = 6371000.0 # radius of earth for calculations
REF_LONGITUDE = -78.79 # this may or may not be used within graph script
REF_LATITUDE = 43.009 # this may or may not be used within graph script



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
# third element is purpose type, is this sensor for a motor? is this measuring battery? or what?
# you may want to calibrate those channels only, that have a biased reading
# this list can be longer than needed (use for various number of channels)
# CUSTOMIZE
CHANNEL_SENSOR_MAP = [
        (SENSOR_TYPE.HALL, True, SENSOR_PURPOSE.MOTOR_CURRENT),           #channel 0
        (SENSOR_TYPE.HALL, True, SENSOR_PURPOSE.MOTOR_CURRENT), 
        (SENSOR_TYPE.SHUNT, False, SENSOR_PURPOSE.DEVICE_CURRENT), 
        (SENSOR_TYPE.DISABLE, False, SENSOR_PURPOSE.NONE), 
        (SENSOR_TYPE.DISABLE, False, SENSOR_PURPOSE.NONE),        #this is enabled to be stored at calibration, later should be uncalibrated.
        (SENSOR_TYPE.VOLTAGE, False, SENSOR_PURPOSE.BATTERY_VOLTAGE),
        (SENSOR_TYPE.HALL, True, SENSOR_PURPOSE.MOTOR_CURRENT),
        (SENSOR_TYPE.HALL, True, SENSOR_PURPOSE.MOTOR_CURRENT),
        (SENSOR_TYPE.DISABLE, False, SENSOR_PURPOSE.NONE),
        (SENSOR_TYPE.DISABLE, False, SENSOR_PURPOSE.NONE),
        (SENSOR_TYPE.DISABLE, False, SENSOR_PURPOSE.NONE),
        ]
