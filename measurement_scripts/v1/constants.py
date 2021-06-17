class PWR_Command:
	PWR_START	=	0
        PWR_STOP	=	1
        PWR_EVENT	=	2
	PWR_MARK	=	3
	PWR_INFO	=	4


class PROGRAM_MODE:
	HW		=	0	#1 for PC, 0 for Pi
	HW_IN_THE_LOOP	=	1
	SW_IN_THE_LOOP	=	2

class EVENT_TYPE:
	MEASUREMENT	=	1
	EVENT		=	2
	MARK		=	3
        INFO            =       4

NUMBER_OF_CHANNELS	=	4

#<<<<<<< 4f1b144ebb1ac7dfdad53bf6d6322f0519fd4f57
MODE_SELECT	=	PROGRAM_MODE.HW #SW_IN_THE_LOOP  #HW
=======
MODE_SELECT	=	PROGRAM_MODE.HW_IN_THE_LOOP	#SW_IN_THE_LOOP  #HW
#>>>>>>> adding some files from summer. check constants.py

PWR_PORT	=	35760
PACKET_END	=	'\r\r\n\n'
LITTLE_ENDIAN	=	False
#BATTERY		=	23.0	#voltage of battery, for power calculation
VDD		=	5.2 #4.90	#actual voltage on a 5V pin powering the measurement module

if MODE_SELECT==PROGRAM_MODE.HW:
	LOG_BUFF_COUNT	=	40 #4000	#number of readings before saving to file
if MODE_SELECT==PROGRAM_MODE.HW_IN_THE_LOOP:
	LOG_BUFF_COUNT	=	1000	#number of readings before saving to file
if MODE_SELECT==PROGRAM_MODE.SW_IN_THE_LOOP:
	LOG_BUFF_COUNT	=	100

CALIBRATE_SAMPLES   =   20              #number of samples for each channel, for initial calibration
LOG_DIR		=	"current"

#this string is just for information
#it is printed in the second line of the log file after startTime
LOG_HEADER	=	"#time		#event_type	#event_data(channel&current(A), MarkNumber, ..."

#struct pwr_pkt {
#  uint_8 cmd;
#  uint_8 length;
#  uint_8[length] data;
#}
