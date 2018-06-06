import ADC128D818

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
MODE_SELECT = PROGRAM_MODE.PI#selected mode
VDD = 5.2 #actual voltage on a 5V pin powering the measurement module as float
DEBUG_MODE = false
VERBOS_AVERAGE_WINDOW = 100
DEVICE_ADDRESS=ADC128D818.ADC_ADDRESS.MID_MID

PWR_HOST = "127.0.0.1"
PWR_PORT = 35760
PACKET_END = '\r\r\n\n'
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


# Defining type of sensor on each channel of the ADC.
# each cahnnel is a tuple, the first element is sensor type
# second element is a calibration flag (true is to calibrate and false is raw readings)
# you may want to calibrate those channels only, that have a biased reading
# CUSTOMIZE
CHANNEL_SENSOR_MAP = [
        (SENSOR_TYPE.HALL, true),           #channel 0
        (SENSOR_TYPE.HALL, true), 
        (SENSOR_TYPE.DISABLE, false), 
        (SENSOR_TYPE.DISABLE, false), 
        (SENSOR_TYPE.DISABLE, false), 
        (SENSOR_TYPE.VOLTAGE, false), 
        (SENSOR_TYPE.HALL, true), 
        (SENSOR_TYPE.HALL, true),            #channel 7
        ]
