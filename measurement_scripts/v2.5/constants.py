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

MODE_SELECT = PROGRAM_MODE.PI
PWR_PORT = 35760
PACKET_END = '\r\r\n\n'
VDD = 5.0 #actual voltage on a 5V pin powering the measurement module as float
CALIBRATION_SAMPLES = 100

#LOG_BUFF_COUNT = number of readings before saving to file
if MODE_SELECT == PROGRAM_MODE.PI:
	LOG_BUFF_COUNT = 4000 
if MODE_SELECT == PROGRAM_MODE.PC:
	LOG_BUFF_COUNT = 1000
if MODE_SELECT == PROGRAM_MODE.PC_SIMULATE_DATA:
	LOG_BUFF_COUNT = 100

LOG_DIR = "current"

#this string is just for information, it is printed
#on the second line of the log file after startTime
LOG_HEADER = "#time		#event_type	#event_data(channel&current(A), MarkNumber, ..."


CHANNEL_SENSOR_MAP = [
        SENSOR_TYPE.HALL,           #channel 0
        SENSOR_TYPE.HALL, 
        SENSOR_TYPE.DISABLE, 
        SENSOR_TYPE.DISABLE, 
        SENSOR_TYPE.VOLTAGE, 
        SENSOR_TYPE.DISABLE, 
        SENSOR_TYPE.HALL, 
        SENSOR_TYPE.HALL            #channel 7
        ]
