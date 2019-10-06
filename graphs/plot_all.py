import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import random
import math
import os,re
import shutil
import sys
import time
sys.path.append("../")
from constants import *
global DUMP_FILE

SMOOTHING_WINDOW=20
NUMBER_OF_CHANNELS=7        #TODO this is ### CUSTOMZE ###
CHANNEL_MOTOR_MAPPING=[1, 2, 3, 4, -1, -1, -1]  # what motor is on each channel (put -1 for a channel that is not connected to a motor), refer to hardware specification to see where each motor is on the UAV. this may later on go to constant.py
#not implemented CHANNEL_COUNT_IN_TOTAL=['True', 'True', 'True', 'True', 'False', 'True', 'False']  # whether each channel is counted towards the "total" power/energy

BATTERY_VOLTAGE=25.4 # this ensures power = current * voltage, should get updated with readings
NUMBER_OF_ROUNDS=1
NUMBER_OF_SETUPS=2
INITIAL_SETUP=0  #USUALLY should be 0. unless you want to skip setups. for example if all trials are 90 degree, then NUMBER_OF_SETUPS=1 and INITIAL_SETUP=2
SPEED_SETUPS = [2.0, 5.0, 7.0]    #       <- ATTENTION
TURN_SETUPS = [0, 45, 90, 135]
HOVER_SETUPS = ['North', 'East', 'South', 'West']
ROTATE_SETUPS = ['North', 'East', 'South', 'West']
DISTANCE_SETUPS = [20.0, 40.0, 60.0, 80.0, 100.0]
WEIGHT_SETUPS = ['Webcam', 'Kinect']
TARGET_SPEED = 5.0    #this will be updated automatically for "Speed" experiments
TARGET_SETUP = "Weight" # either "Speed" or "Turn" or "Hover" or "Rotate" or "Distance" or "Weight"
SPEED_MARKER_THRESHOLD=1.0     #first time and last time haveing targetSpeed - threshold, will be marked default: 1.0
WAIT_FOR_MEASURE_FLAG = False # *** CAUTION ***. if on, anything before the first EVENT is ignored. each EVENT flags the measurement on/off
                              # *** CAUTION *** This flag changes TIME_REFERENCE, and INFO_TIME will be unreliable and wrong.

STEADY_DETECTION = False        #whether we ar einterested in steady velocity detection or not
SAVE_GRAPH_CHANNELS = True      #individual channel current vs. time
SAVE_GRAPH_TOTAL = False        #total current vs. time
SAVE_GRAPH_VELOCITY = False
SAVE_GRAPH_ENERGY = False
SAVE_GRAPH_POWER = True
SAVE_GRAPH_PATH = False         # showing the trace
GRAPH_PATH_ANIMATION = False     # animating the path
RESET_INITIAL_LAT_LON = False   # reset initial position based on each trial
SAVE_GRAPH_SETUP_BASED = False
SAVE_GRAPH_ROUND_BASED = False
APPLY_GRAPH_CUSTOMIZATION = True #yticks, ylimit range, etc.
VALUE_MAKE_ABSOLUTE = True    # adjust negative values positive
VALUE_LOWER_WARNING = -0.1     # value below which the script warns
VALUE_UPPER_WARNING = 30        # value above which the script warns
LOG_HEADER_LINES = 2  #how many lines in log files are okay to be ignored, typically at header
STR_GRAPHS='current_graphs'
STR_CROUND='constant_round'
STR_CSETUP='constant_setup'
GRAPH_FORMAT='eps'   #png, pdf, ps, eps, svg.
GRAPH_DPI=300
GRAPH_FIG_WIDTH = 15
GRAPH_FIG_HEIGHT= 10
global INITIAL_LONGITUDE
global INITIAL_LATITUDE
global EARTH_R

if ((len(sys.argv)>1) and (sys.argv[1]=='-h')) or len(sys.argv)<2 :
    print "----------------------------------------------"
    print "This is for creating graphs for a single trial, showing some results only for that trial"
    print "Input file is REQUIRED, or you can input ALL to process every file. (ALL in caps)"
    print "Log(s) should be in the %s folder."%(LOG_DIR)
    print "----------------------------------------------"
    exit();

START_TIME = 50
DURATION= 100	#0 means no limit
#    DURATION=int(sys.argv[2])

myFile=sys.argv[1]
if (myFile!='ALL'):
    if (myFile.startswith(LOG_DIR)):
        print "File name includes LOG_DIR name: %s"%(myFile)
        print "Trimming input to: "
        myFile = myFile[len(LOG_DIR)+1:]
        print myFile

CHOSEN_SETUPS=[]
if (TARGET_SETUP=="Speed"):
    CHOSEN_SETUPS = SPEED_SETUPS
elif (TARGET_SETUP=="Distance"):
    CHOSEN_SETUPS = DISTANCE_SETUPS
elif (TARGET_SETUP=="Turn"):
    CHOSEN_SETUPS = TURN_SETUPS
elif (TARGET_SETUP=="Hover"):
    CHOSEN_SETUPS = HOVER_SETUPS
elif (TARGET_SETUP=="Rotate"):
    CHOSEN_SETUPS = ROTATE_SETUPS
elif (TARGET_SETUP=="Weight"):
    CHOSEN_SETUPS = WEIGHT_SETUPS
else:
    print("UKNOWN TARGET SETUP: "+TARGET_SETUP)
    exit(0)

##############################################################################
#finding index of closest value
#
def binary_search(data, val):
    lo, hi = 0, len(data) - 1
    best_ind = lo
    while lo <= hi:
        mid = lo + (hi - lo) / 2

        if data[mid] < val:
            lo = mid + 1
        elif data[mid] > val:
            hi = mid - 1
        else:
            best_ind = mid      
            break
        # check if data[mid] is closer to val than data[best_ind] 
        if abs(data[mid] - val) < abs(data[best_ind] - val):
            best_ind = mid
    return best_ind
##############################################################################
#extracting distance of 2 xy pairs
#
def extract_distance(pos1, pos2):
    return math.sqrt( (pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2 )
##############################################################################
#extracting xy coordinates from LAT/LON
#
def extract_coordinate(lat, lon, alt):
    global INITIAL_LONGITUDE
    global INITIAL_LATITUDE
    global EARTH_R
    lat = lat * math.pi / 180.0
    lon = lon * math.pi / 180.0
    x = EARTH_R * (lon - INITIAL_LONGITUDE) * math.cos(INITIAL_LATITUDE) 
    y = EARTH_R * (lat - INITIAL_LATITUDE)
    z = alt
    return [x, y, z]
##############################################################################
#extracting information from info messages
#
def extract_info(msg):
    global INITIAL_LONGITUDE
    global INITIAL_LATITUDE
    global EARTH_R
    v_msg = "VEL="
    lat_msg = "LAT="
    lon_msg = "LON="
    alt_msg = "ALT="
    t = []
    v = []
    lat = []
    lon = []
    alt = []
    pos = []

    for m in msg:
        # first we should make sure if this message is a whole, and does not miss a pice of info.
        if ((m.find(v_msg) < 0) or 
                (m.find(lat_msg) < 0) or
                (m.find(lon_msg) < 0) or
                (m.find(alt_msg) < 0)):
            # ignore the whole message and keep previous values (we do this to match length of lists)
            t.append(t[-1])
            v.append(v[-1])
            lat.append(lat[-1])
            lon.append(lon[-1])
            alt.append(alt[-1])
            dump("WARNING: there seems to be a problem with this info(missing info), produces duplicate: "+m)
            continue

        tmp_t=m.split('\t')[0] #TODO info starts with time?
        tmp_v=m[m.find(v_msg)+len(v_msg):].split('\t')[0]
        tmp_lat=m[m.find(lat_msg)+len(lat_msg):].split('\t')[0]
        tmp_lon=m[m.find(lon_msg)+len(lon_msg):].split('\t')[0]
        tmp_alt=m[m.find(alt_msg)+len(alt_msg):].split('\t')[0]

        MEANINGFUL_CHARACTERS = 10 #each one should have at least this, to be considered legit (in case of corrupted info)
        if (len(tmp_t)<MEANINGFUL_CHARACTERS
             or len(tmp_v) < MEANINGFUL_CHARACTERS
             or len(tmp_lat) < MEANINGFUL_CHARACTERS
             or len(tmp_lon) < MEANINGFUL_CHARACTERS
             or len(tmp_alt) < MEANINGFUL_CHARACTERS): #problem reading one?
            # ignore the whole message and keep previous values (we do this to match length of lists)
            t.append(t[-1])
            v.append(v[-1])
            lat.append(lat[-1])
            lon.append(lon[-1])
            alt.append(alt[-1])
            dump("WARNING: there seems to be a problem with this info(corrupted info), produces duplicate: "+m)
            continue

        t.append(float(tmp_t))
        v.append(float(tmp_v))
        lat.append(float(tmp_lat))
        lon.append(float(tmp_lon))
        alt.append(float(tmp_alt))

    if (RESET_INITIAL_LAT_LON):
        INITIAL_LATITUDE = lat[0] * math.pi / 180.0
        INITIAL_LONGITUDE = lon[0] * math.pi / 180.0
    else:
        INITIAL_LATITUDE = REF_LATITUDE * math.pi / 180.0
        INITIAL_LONGITUDE = REF_LONGITUDE * math.pi / 180.0
    for i in range(len(lat)):
        pos.append(extract_coordinate(lat[i], lon[i], alt[i]))
    return t, v, pos
##############################################################################
#avg using r points to the left
#and r points to the right of the point
def AvgING(watts, r):
    Avg=[]
    if (len(watts)==0):
        return Avg

    for x in range(len(watts)):
        avg = watts[x]
        count = 1
        for i in range(1,r):
            if (x-i >= 0):
                avg += watts[x-i]
                count += 1
            if (x+i < len(watts)):
                avg += watts[x+i]
                count += 1
        avg = avg/count
        Avg+=[avg]

    return Avg
##############################################################################
def refresh_directories():
    global DUMP_FILE
    shutil.rmtree('%s/%s'%(LOG_DIR, STR_GRAPHS), ignore_errors=True)
    time.sleep(2)
    os.makedirs('%s/%s'%(LOG_DIR,STR_GRAPHS))
    os.makedirs('%s/%s/all'%(LOG_DIR,STR_GRAPHS))
    os.makedirs('%s/%s/logs'%(LOG_DIR,STR_GRAPHS))
    DUMP_FILE=open('%s/%s/process_log.txt'%(LOG_DIR,STR_GRAPHS),'a')
    
    if (SAVE_GRAPH_ROUND_BASED):
        os.makedirs('%s/%s/%s'%(LOG_DIR,STR_GRAPHS,STR_CROUND))
        for i in range(NUMBER_OF_ROUNDS):
            os.makedirs('%s/%s/%s/round-%d'%(LOG_DIR,STR_GRAPHS,STR_CROUND,i))

    if (SAVE_GRAPH_SETUP_BASED):
        os.makedirs('%s/%s/%s'%(LOG_DIR,STR_GRAPHS,STR_CSETUP))
        for i in range(NUMBER_OF_SETUPS):
            os.makedirs('%s/%s/%s/%s-%s'%(LOG_DIR,STR_GRAPHS,STR_CSETUP,TARGET_SETUP,str(CHOSEN_SETUPS[i])))
            
    resultFile=open('%s/%s/all.csv'%(LOG_DIR,STR_GRAPHS),'a')
    resultFile.write("#Trial,File,Set,Round,Setup,TotalTime,TotalEnergy,Distance," + \
                        "Displacement,AvgPower,AvgJ/m,TargetSetup(Turn/Speed/Distance/Orientation/etc.),AvgSpeed,SteadyTime,AvgSteadySpeed,SteadyDistance,SteadyEnergy,AvgSteadyJ/m,AvgSteadyPower\n")
    resultFile.close()
###########################################################################################
def dump(myStr):
    global DUMP_FILE
    print myStr
    sys.stdout.flush()
    DUMP_FILE.write(myStr+"\n")
    DUMP_FILE.flush()
###########################################################################################

################# reading log file
#for i in range(1):
#	f=sys.argv[1].split('/',1)[1]
fileList=os.listdir(LOG_DIR)
refresh_directories()
fileList.sort()
if (sys.argv[1] != 'ALL'):
    fileList = [myFile]

reading = []
reading_time = []
info= []
info_record_time = []
markers = []
markers_time = []

micro_time = []
total_curr = []
energy = []
power = []

file_names = []

trials=0

if (START_TIME > 0 or DURATION > 0):
	dump("*** START_TIME or DURATION is non-zero, some of the information will be ignored ***")

for f in fileList:
    if (f.endswith('.log') and f.startswith('log')):
        myFile=f
        file_names.append(myFile)

        dump('----------------------------------------')
        dump('processing file: '+f)
        shutil.copy(LOG_DIR+'/'+myFile, '%s/%s/logs'%(LOG_DIR, STR_GRAPHS))

        fv=open (LOG_DIR+'/'+myFile,"r")
        num_lines = sum(1 for line in fv)
        fv.seek(0)
        dump('Total number of lines in file: '+str(num_lines))

        reading.append([])
        reading_time.append([])
        for i in range(NUMBER_OF_CHANNELS):
            reading[trials].append([])
            reading_time[trials].append([])

        markers.append([]) 
        markers_time.append([]) 
        info.append([])
        info_record_time.append([])

        micro_time.append([])
        total_curr.append([])
        energy.append([])
        power.append([])

        micro_time[trials].append(0.0)
        total_curr[trials].append(0.0)
        energy[trials].append(0.0)
        power[trials].append(0.0)

        lastValue=[0.0]*NUMBER_OF_CHANNELS

        line_number=0
        counted=0
        TIME_REFERENCE=0
	ORIGINAL_TIME_REFERENCE=0

        MEASURE_FLAG = False
        MEASURE_TIME_STAMP = 0
        if (WAIT_FOR_MEASURE_FLAG):
            dump("** WAIT_FOR_MEASURE_FLAG is on. Waiting for an EVENT for measurement START/STOP **")

        while True:
            try:
                line=fv.readline()
                if not line:
                    break
                line_number=line_number+1
                if (line.startswith('#')):
                    continue

                l=line.strip().split()
                now=float(l[0])  

                if (ORIGINAL_TIME_REFERENCE==0):
                    ORIGINAL_TIME_REFERENCE=now

		if (START_TIME>0) and (now < START_TIME + ORIGINAL_TIME_REFERENCE): #ignoring anything before start_time
		    continue

                if (DURATION>0) and (now > START_TIME + DURATION + ORIGINAL_TIME_REFERENCE):
                    dump("Exceeded target duration")
                    break

                if (TIME_REFERENCE==0):
                    TIME_REFERENCE=now

                time = now - TIME_REFERENCE

                event_type=int(l[1])

                if event_type==EVENT_TYPE.EVENT:
                    if (WAIT_FOR_MEASURE_FLAG):
                        MEASURE_FLAG = not (MEASURE_FLAG)
                        if (MEASURE_FLAG):  # end of a NO_COUNT period, we should adjust time reference
                            TIME_REFERENCE += time - MEASURE_TIME_STAMP - 0.0001 #subtracting epsilon to prevent two equal timestamps
                            time = now - TIME_REFERENCE # re-adjusting time
                        else:
                            MEASURE_TIME_STAMP = time   #recording this time, so that later on we can adjust TIME_REFERENCE

                    dump("EVENT on line %d. Switching MEASURE_FLAG"%(line_number))
                    markers_time[trials].append(time)
                    markers[trials].append(0)           #an event is a marker with mark = 0

                if (WAIT_FOR_MEASURE_FLAG) and not (MEASURE_FLAG):  #ignoring measurements if not yet seen the mark.
                    continue

                if event_type==EVENT_TYPE.MEASUREMENT:
                    channel=int(l[2])
                    value=float(l[3])

                    if (value < VALUE_LOWER_WARNING or value > VALUE_UPPER_WARNING):  #raising attention
                        raise Exception('Value out of bound')

                    if (CHANNEL_SENSOR_MAP[channel][0]==SENSOR_TYPE.DISABLE):
                        raise Exception('Channel measurement for a disabled channel')

                    if (VALUE_MAKE_ABSOLUTE):
                        value = abs(value)

                    reading_time[trials][channel].append(time)
                    reading[trials][channel].append(value)

                    #updating battery voltage
                    if (CHANNEL_SENSOR_MAP[channel][2]==SENSOR_PURPOSE.BATTERY_VOLTAGE):
                        BATTERY_VOLTAGE = value

                    if (CHANNEL_SENSOR_MAP[channel][2]==SENSOR_PURPOSE.MOTOR_CURRENT): #total current is only for current measurements
                        lastValue[channel]=value                # only hall current sensors for motors should be summed for total
                        micro_time[trials].append(time)
                        total_curr[trials].append(sum(lastValue))
                        power[trials].append(BATTERY_VOLTAGE * (total_curr[trials][-1]+total_curr[trials][-2])/2)
                        energy[trials].append(energy[trials][-1] + power[trials][-1] * (micro_time[trials][-1]-micro_time[trials][-2]))

                if event_type==EVENT_TYPE.MARK:
                    mark=int(l[2])
                    markers_time[trials].append(time)
                    markers[trials].append(mark)

                if event_type==EVENT_TYPE.INFO:
                    information="\t".join(l[2:])
                    info_record_time[trials].append(time) #this is in reiception timing. might not be the actual time of the information, that should be extracted from within info message.
                    info[trials].append(information)

                counted=counted+1

            except Exception as e:
                dump("error at line: %d"%(line_number))
                if len(l)>0:
                    dump(line)

                dump(str(e))
                continue

        dump ("%d lines were read, %d lines counted"%(line_number, counted))
        if (line_number > counted + LOG_HEADER_LINES):
            dump("**** %d lines not counted (WAITING_FOR_MEASURE_FLAG enabled?) ****"%(line_number - counted - LOG_HEADER_LINES))
        dump ("within the trial#%d we found %d reading sets, %d events+markers, %d info messages"%(trials, len(reading[trials][0]),len(markers[trials]),len(info[trials])))
        fv.close()

        trials += 1	


        ######################################### OUTPUT  #############################################

        ######################################### GRAPHS  #############################################
dump('========================================')

info_time = [[]] * trials
velocity = [[]] * trials
position = [[]] * trials
start_marker_index = [-1] * trials
stop_marker_index = [-1] * trials
start_micro_time_index = [-1]*trials
stop_micro_time_index = [-1]*trials
steady_duration = [-1] * trials
steady_movement = [-1] * trials #only a direct distance between start and stop of steady
delta_energy = [0] * trials
total_movement = [-1] * trials  #only a direct distance between start and end point
sum_distance = [0.01] * trials   #sum of all delta_x (not zero, just because of division by zero)
sum_distance_steady = [0.01] * trials   #sum of all delta_x for steady time (not zero, just because of division by zero)

for this_trial in range(trials):
    this_set=this_trial/(NUMBER_OF_ROUNDS * NUMBER_OF_SETUPS)
    this_setup=INITIAL_SETUP + ((this_trial/NUMBER_OF_ROUNDS) % NUMBER_OF_SETUPS)
    this_round=this_trial%NUMBER_OF_ROUNDS
    if (TARGET_SETUP=="Speed"):
        TARGET_SPEED=SPEED_SETUPS[this_setup]
        added_setup_label = 'Speed = %.1f m/s'%(CHOSEN_SETUPS[this_setup])
    elif (TARGET_SETUP=="Distance"):
        added_setup_label = 'Distance = %d m'%(CHOSEN_SETUPS[this_setup])
    elif (TARGET_SETUP=="Turn"):
        added_setup_label = 'Turn = %d deg'%(CHOSEN_SETUPS[this_setup])
    elif (TARGET_SETUP=="Hover"):
        #added_setup_label = 'Current log for Thrust 1500 on 3 Cells Bat 1 Power supply'
        #added_setup_label = 'Current log for Thrust 1500 on 3 Cells Bat 2 Power supply'
        #added_setup_label = 'Current log for Thrust 1500 on 4 Cells Bat Power supply'
        added_setup_label = 'Orientation = %s'%(CHOSEN_SETUPS[this_setup])
    elif (TARGET_SETUP=="Rotate"):
        #CHOSEN_SETUPS = ROTATE_SETUPS
        added_setup_label = 'Orientation = %s'%(CHOSEN_SETUPS[this_setup])
    elif (TARGET_SETUP=="Weight"):
        added_setup_label = 'Sensor mount = %s'%(CHOSEN_SETUPS[this_setup])
    else:
        dump("UKNOWN TARGET SETUP: "+TARGET_SETUP)
        
    dump('processing trial %d: set %d setup %d round %d ...'%(this_trial, this_set, this_setup, this_round))
    #added_title="Round = %d - %s _ Set %d"%(this_round+1,added_setup_label, this_set)
    added_title="%s - Round %d"%(added_setup_label, this_round+1)

    info_time[this_trial], velocity[this_trial], position[this_trial] = extract_info(info[this_trial])
    dump("%d piece of information extracted"%len(info_time[this_trial]))
    #adjusting info times with recording times reference:
    if (info_time[this_trial]):
	    info_time[this_trial]= [t-info_time[this_trial][0]+info_record_time[this_trial][0] for t in info_time[this_trial]]
	    total_movement[this_trial] = extract_distance(position[this_trial][0], position[this_trial][-1])

    for ch in range(NUMBER_OF_CHANNELS):
        reading[this_trial][ch]=AvgING(reading[this_trial][ch],SMOOTHING_WINDOW)	    
    total_curr[this_trial]=AvgING(total_curr[this_trial],SMOOTHING_WINDOW)

    for u in range(len(position[this_trial])-1):
        sum_distance[this_trial] += extract_distance(position[this_trial][u], position[this_trial][u+1])

    if (STEADY_DETECTION):
        try:
            start_marker_index[this_trial] = [ n for n,i in enumerate(velocity[this_trial]) if i>TARGET_SPEED-SPEED_MARKER_THRESHOLD][0]        
            stop_marker_index[this_trial] = [ n for n,i in enumerate(velocity[this_trial]) if i>TARGET_SPEED-SPEED_MARKER_THRESHOLD][-1]
            start_micro_time_index[this_trial] = binary_search(micro_time[this_trial], info_time[this_trial][start_marker_index[this_trial]])
            stop_micro_time_index[this_trial] = binary_search(micro_time[this_trial], info_time[this_trial][stop_marker_index[this_trial]])
            steady_duration[this_trial] = info_time[this_trial][stop_marker_index[this_trial]] - info_time[this_trial][start_marker_index[this_trial]]
            steady_movement[this_trial] = extract_distance(position[this_trial][start_marker_index[this_trial]], position[this_trial][stop_marker_index[this_trial]])
            delta_energy[this_trial] = energy[this_trial][stop_micro_time_index[this_trial]] - energy[this_trial][start_micro_time_index[this_trial]]
            for u in range(start_marker_index[this_trial],stop_marker_index[this_trial]):
                sum_distance_steady[this_trial] += extract_distance(position[this_trial][u], position[this_trial][u+1])
        
        except:
            pass


        dump("---")
        if (steady_duration[this_trial]>0):
            dump("\tSTEADY DURATION DETECTED:")
            dump("\tstart time -> stop time  --- steady duration -----     start position      ->     stop position       ----- steady movement --- steady distance")
            dump("\t%8.3f   -> %8.3f   ---  %11.3f    ----- (%10.3f,%10.3f) -> (%10.3f,%10.3f) ----- %10.3f     --- %10.3f    " \
                %(info_time[this_trial][start_marker_index[this_trial]], info_time[this_trial][stop_marker_index[this_trial]], steady_duration[this_trial], 
                position[this_trial][start_marker_index[this_trial]][0], position[this_trial][start_marker_index[this_trial]][1],
                position[this_trial][stop_marker_index[this_trial]][0], position[this_trial][stop_marker_index[this_trial]][1],
                steady_movement[this_trial], sum_distance_steady[this_trial]))
            dump("\tfor this tiral, target Velocity = %.2f average Steady Velocity = %.2f and steady E/X = %.3f" \
                %(TARGET_SPEED, sum_distance_steady[this_trial]/steady_duration[this_trial], delta_energy[this_trial] / sum_distance_steady[this_trial]))
        else:
            dump("\tCOULD NOT DETECT STEADY DURATION, STEADY DATA NOT RELIABLE")

##############################################################################
# a template for saving plots with a template filenaming
    def save_this_plot(graph_type):
        plt.savefig('%s/%s/all/%s_%s.%s'%(LOG_DIR,STR_GRAPHS, file_names[this_trial], graph_type, GRAPH_FORMAT), dpi=GRAPH_DPI, format=GRAPH_FORMAT)
        if (SAVE_GRAPH_ROUND_BASED):
            plt.savefig('%s/%s/%s/round-%d/%s_%s-%s_%d.%s'%(LOG_DIR,STR_GRAPHS,STR_CROUND, this_round+1, graph_type, TARGET_SETUP, str(CHOSEN_SETUPS[this_setup]), this_set, GRAPH_FORMAT), dpi=GRAPH_DPI, format=GRAPH_FORMAT)
        if (SAVE_GRAPH_SETUP_BASED):
            plt.savefig('%s/%s/%s/%s-%s/%s_round-%d_%d.%s'%(LOG_DIR,STR_GRAPHS,STR_CSETUP,TARGET_SETUP,str(CHOSEN_SETUPS[this_setup]),graph_type, this_round+1, this_set, GRAPH_FORMAT), dpi=GRAPH_DPI, format=GRAPH_FORMAT)
        plt.close()
##############################################################################
# graphing this trial in various forms

    if (SAVE_GRAPH_CHANNELS):
        fig1, ax1 = plt.subplots()
        for ch in range(NUMBER_OF_CHANNELS):
	    if (CHANNEL_SENSOR_MAP[ch][2]==SENSOR_PURPOSE.MOTOR_CURRENT):
	        label = 'Motor '+str(CHANNEL_MOTOR_MAPPING[ch])
                ax1.plot(reading_time[this_trial][ch],reading[this_trial][ch], label=label)
	
	#ax1.plot(micro_time[this_trial], total_curr[this_trial], 'k', label="Total current")

        for i in range(len(markers_time[this_trial])):
            ax1.axvline(x=markers_time[this_trial][i],color='k')      #TODO apply colors based on marker number

        if (APPLY_GRAPH_CUSTOMIZATION):
            ax1.set_ylim(0,10)
            #yticks = ax1.yaxis.get_major_ticks()
            #yticks[-1].label1.set_visible(False)
            fig1.set_figwidth(GRAPH_FIG_WIDTH)
            fig1.set_figheight(GRAPH_FIG_HEIGHT)
            #fig1.tight_layout()
            pass
            
        ax1.set_xlabel('Time (s)')
        ax1.set_ylabel('Current (A)')
        ax1.legend(loc='lower left')

        ax1_twin = ax1.twinx()
        for ch in range(NUMBER_OF_CHANNELS):
	    if (CHANNEL_SENSOR_MAP[ch][2]==SENSOR_PURPOSE.BATTERY_VOLTAGE):
	        label = 'Battery Voltage'
                ax1_twin.plot(reading_time[this_trial][ch], reading[this_trial][ch], label=label)

        if (APPLY_GRAPH_CUSTOMIZATION):
            ax1_twin.set_ylim(0,30)
            yticks = ax1_twin.yaxis.get_major_ticks()
            yticks[-1].label1.set_visible(False)
            pass

        ax1_twin.set_ylabel('Voltage (V)')
        ax1_twin.legend(loc='lower right')
        
#        plt.title("%d Channels - %s"%(NUMBER_OF_CHANNELS, added_title))
        plt.title("Current Draw - %s"%(added_title))
	#plt.grid()
        save_this_plot("channels")
###### 
    if (SAVE_GRAPH_TOTAL):
        fig2, ax2 =plt.subplots()
        ax2.plot(micro_time[this_trial],total_curr[this_trial], 'b')

        for i in range(len(markers_time[this_trial])):
            ax2.axvline(x=markers_time[this_trial][i],color='k')      #TODO apply colors based on marker number

        if (STEADY_DETECTION and start_marker_index[this_trial]>=0):
            ax2.axvline(info_time[this_trial][start_marker_index[this_trial]],color='b')
            ax2.axvline(info_time[this_trial][stop_marker_index[this_trial]],color='r')

        if (APPLY_GRAPH_CUSTOMIZATION):
            ax2.set_ylim(8, 26)
            #yticks = ax2.yaxis.get_major_ticks()
            #yticks[-1].label1.set_visible(False)
            fig2.set_figwidth(GRAPH_FIG_WIDTH)
            fig2.set_figheight(GRAPH_FIG_HEIGHT)
            pass

        ax2.set_xlabel('Time (s)')
        ax2.set_ylabel('Total Current (A)')
        plt.title("Total Current - %s"%(added_title))
        save_this_plot("total")
###### 
    if (SAVE_GRAPH_ENERGY):
        fig3, ax3 =plt.subplots()
        ax3.plot(micro_time[this_trial], energy[this_trial], 'r')

        for i in range(len(markers_time[this_trial])):
            ax3.axvline(x=markers_time[this_trial][i],color='k')      #TODO apply colors based on marker number

        if (APPLY_GRAPH_CUSTOMIZATION):
            #ax3.set_ylim(9,15)
            #yticks = ax3.yaxis.get_major_ticks()
            #yticks[-1].label1.set_visible(False)
            fig3.set_figwidth(GRAPH_FIG_WIDTH)
            fig3.set_figheight(GRAPH_FIG_HEIGHT)
            pass
            
        ax3.set_xlabel('Time (s)')
        ax3.set_ylabel('Total Energy (J)')
        
        plt.title("Cumulative Energy - %s"%(added_title))
        save_this_plot("energy")
###### 
    if (SAVE_GRAPH_POWER):
        fig4, ax4 =plt.subplots()
        ax4.plot(micro_time[this_trial], power[this_trial], 'brown')

        for i in range(len(markers_time[this_trial])):
            ax4.axvline(x=markers_time[this_trial][i],color='k')      #TODO apply colors based on marker number

        if (APPLY_GRAPH_CUSTOMIZATION):
            ax4.set_ylim(200, 800)
            #yticks = ax3.yaxis.get_major_ticks()
            #yticks[-1].label1.set_visible(False)
            fig4.set_figwidth(GRAPH_FIG_WIDTH)
            fig4.set_figheight(GRAPH_FIG_HEIGHT)
            pass
            
        ax4.set_xlabel('Time (s)')
        ax4.set_ylabel('Power (W)')
        
        plt.title("Instantaneous Power - %s"%(added_title))
        save_this_plot("power")
###### 
    if (SAVE_GRAPH_VELOCITY):
        fig5, ax5 =plt.subplots()
        ax5.plot(info_time[this_trial], velocity[this_trial], 'm')

        for i in range(len(markers_time[this_trial])):
            ax5.axvline(x=markers_time[this_trial][i],color='k')      #TODO apply colors based on marker number

        if (STEADY_DETECTION and start_marker_index[this_trial]>=0):
            ax5.axvline(info_time[this_trial][start_marker_index[this_trial]],color='b')
            ax5.axvline(info_time[this_trial][stop_marker_index[this_trial]],color='r')

        if (APPLY_GRAPH_CUSTOMIZATION):
            ax5.set_ylim(0,10)
            yticks = ax5.yaxis.get_major_ticks()
            yticks[-1].label1.set_visible(False)
            fig5.set_figwidth(GRAPH_FIG_WIDTH)
            fig5.set_figheight(GRAPH_FIG_HEIGHT)

        ax5.set_xlabel('Time (s)')
        ax5.set_ylabel('Velocity (m/s)')
        plt.title("Velocity - %s"%(added_title))
        save_this_plot("velocity")
###### 
    if (SAVE_GRAPH_PATH):
        fig6, ax6 = plt.subplots()
        
        path_x = []
        path_y = []
        for u in range(len(position[this_trial])):
            path_x.append(position[this_trial][u][0])
            path_y.append(position[this_trial][u][1])

        ax6.plot(path_x, path_y, 'b', linewidth=2)
        ax6.scatter(path_x[0], path_y[0], c='r', s=10)

        if (APPLY_GRAPH_CUSTOMIZATION):
#            path_x = [_ - min_x +10 for _ in path_x]
#            path_y = [_ - min_y +10 for _ in path_y]
            pass

        if (APPLY_GRAPH_CUSTOMIZATION):
            ax6.set_xlim(-120,120)
            ax6.set_ylim(-120,120)
            #yticks = ax6.yaxis.get_major_ticks()
            #yticks[-1].label1.set_visible(False)
            plt.gca().set_aspect('equal', adjustable='box')
            pass

        ax6.set_xlabel('Position X (m)')
        ax6.set_ylabel('Position Y (m)')
        plt.title("Experiment Path - %s"%(added_title))
        save_this_plot("path")
######        
    if (GRAPH_PATH_ANIMATION):
        fig7, ax7 = plt.subplots()

        path_x = []
        path_y = []
        for u in range(len(position[this_trial])):
            path_x.append(position[this_trial][u][0])
            path_y.append(position[this_trial][u][1])

        ax7.scatter(path_x[0], path_y[0], c='r', s=10)
        trace_data, = ax7.plot([], [])
        ##############################################################################
        #trace_graph animation
        def trace_animate(frame):
            trace_data.set_data(path_x[:frame], path_y[:frame])
            return trace_data,


        anim = animation.FuncAnimation(fig7, trace_animate,
                                        frames=len(path_x), interval = 10, blit=True, repeat = True)

        if (APPLY_GRAPH_CUSTOMIZATION):
            ax7.set_xlim(-120,120)
            ax7.set_ylim(-120,120)
            #yticks = ax7.yaxis.get_major_ticks()
            #yticks[-1].label1.set_visible(False)
            plt.gca().set_aspect('equal', adjustable='box')
            pass
            
        ax7.set_xlabel('Position X (m)')
        ax7.set_ylabel('Position Y (m)')
        plt.title(file_names[this_trial]+" - %s"%(added_title)) 
#        plt.show()
        plt.draw()
        plt.pause(2.5)
######        
    plt.close('all')
##############################################################################
# Summing up and writing the numbers in files, adding each trial

    resultFile=open('%s/%s/all.csv'%(LOG_DIR,STR_GRAPHS),'a')
    
    resultFile.write("%d,%s,%d,%d,%d,%.3f,%.3f,%.3f,%.3f,%.2f,%.2f,%s,%5.2f,%.2f,%5.2f,%7.3f,%10.3f,%.3f,%.3f\n" \
                %(this_trial+1, file_names[this_trial],this_set, this_round, this_setup, micro_time[this_trial][-1],energy[this_trial][-1], 
            sum_distance[this_trial], total_movement[this_trial], energy[this_trial][-1]/micro_time[this_trial][-1], energy[this_trial][-1]/sum_distance[this_trial], 
            str(CHOSEN_SETUPS[this_setup]), sum_distance[this_trial]/micro_time[this_trial][-1], steady_duration[this_trial], sum_distance_steady[this_trial]/steady_duration[this_trial], 
            sum_distance_steady[this_trial], delta_energy[this_trial], delta_energy[this_trial]/sum_distance_steady[this_trial], delta_energy[this_trial]/steady_duration[this_trial]))
    resultFile.close()
    dump("------------------------")
			

dump('========================================')
dump("in total %d trials processed"%(trials))

#plt.show()
