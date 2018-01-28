import matplotlib.pyplot as plt
import numpy as np
import math
import os,re
import shutil
import sys
import time
sys.path.append("../")
from constants import *
global DUMP_FILE
font = {"family" : "normal",
        "weight" : "bold",
        "size"   : 24}

plt.rc("font", **font)
plt.rcParams["pdf.fonttype"] = 42
plt.rcParams["ps.fonttype"] = 42

SMOOTHING_WINDOW=20

SCALE = 0.001  #for energy graphs 0.001 for power_time 1
BATTERY_VOLTAGE=23 # this ensures power = current * voltage
NUMBER_OF_DAYS=3
NUMBER_OF_ROUNDS=4
NUMBER_OF_SETUPS=4
SETUPS_TO_SHOW=3
SPEED_SETUPS = [2.0, 5.0, 7.0, 10.0]  
SPEED_COLORS = ['r', 'b', 'g', 'k']
ANGLE_SETUPS = [0, 45, 90, 135, 180]
ANGLE_CONSTANT_SPEED=5.0
TARGET_SETUP = "Speed" # either "Speed" or "Angle"
SPEED_MARKER_THRESHOLD=1.0     #first time and last time haveing targetSpeed - threshold, will be marked default: 1.0
SAVE_GRAPH_CHANNELS = False     #individual channel current vs. time
SAVE_GRAPH_TOTAL = False        #total current vs. time
SAVE_GRAPH_VELOCITY = False
SAVE_GRAPH_ENERGY = False
SAVE_GRAPH_SETUP_BASED = False
SAVE_GRAPH_ROUND_BASED = False
APPLY_GRAPH_CUSTOMIZATION = False #yticks, ylimit range, etc.
STR_GRAPHS='current_graphs'
STR_CROUND='constant_round'
STR_CSETUP='constant_setup'
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

DURATION=0	#0 means no limit
#    DURATION=int(sys.argv[2])

myFile=sys.argv[1]
if (myFile!='ALL'):
    if (myFile.startswith(LOG_DIR)):
        print "File name includes LOG_DIR name: %s"%(myFile)
        print "Trimming input to: "
        myFile = myFile[len(LOG_DIR)+1:]
        print myFile


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
def extract_coordinate(lat, lon):
    lat = lat * math.pi / 180.0
    lon = lon * math.pi / 180.0
    x = EARTH_R * (lon - INITIAL_LONGITUDE) * math.cos(INITIAL_LATITUDE) 
    y = EARTH_R * (lat - INITIAL_LATITUDE)
    return [x , y]
##############################################################################
#extracting information from info messages
#
def extract_info(msg):
    global INITIAL_LONGITUDE
    global INITIAL_LATITUDE
    global EARTH_R
    EARTH_R = 6371000
    v_msg = "VEL="
    lat_msg = "LAT="
    lon_msg = "LON="
    v = []
    lat = []
    lon = []
    pos = []
    for m in msg:
        v.append(float(m[m.find(v_msg)+len(v_msg):].split(',')[0]))
        lat.append(float(m[m.find(lat_msg)+len(lat_msg):].split(',')[0]))
        lon.append(float(m[m.find(lon_msg)+len(lon_msg):].split(',')[0]))
    INITIAL_LATITUDE = lat[0] * math.pi / 180.0
    INITIAL_LONGITUDE = lon[0] * math.pi / 180.0
    for i in range(len(lat)):
        pos.append(extract_coordinate(lat[i], lon[i]))
    return v, pos
##############################################################################
#avg using r points to the left
#and r points to the right of the point
def AvgING(watts, r):
    Avg=[]
    if len(watts)==0:
        return Avg

    for x in range(len(watts)):
        avg = watts[x]
        count = 1
        for i in range(1,r):
            try:
                avg += watts[x-i]
                count += 1
            except:
                pass
            try:
                avg += watts[x+i]
                count += 1
            except:
                pass
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
            os.makedirs('%s/%s/%s/round-%d'%(LOG_DIR,STR_GRAPHS,STR_CROUND,i+1))

    if (SAVE_GRAPH_SETUP_BASED):
        os.makedirs('%s/%s/%s'%(LOG_DIR,STR_GRAPHS,STR_CSETUP))
        for i in range(NUMBER_OF_SETUPS):
            os.makedirs('%s/%s/%s/%s-%d'%(LOG_DIR,STR_GRAPHS,STR_CSETUP,TARGET_SETUP,i+1))
            
    resultFile=open('%s/%s/all.txt'%(LOG_DIR,STR_GRAPHS),'a')
    resultFile.write("#Trial \tFile \t\t\t\t\tDay \tRound \tSetup \tTotalTime \tTotalEnergy \tDistance \t" + \
                        "Displacement \tAvgPower \tAvgJ/m \t\tTargetAngle \tTargetSpeed \tAvgSpeed \tSteadyTime \tAvgSteadySpeed \tSteadyDistance \tSteadyEnergy \tAvgSteadyJ/m \tAvgSteadyPower\n")
    resultFile.close()

###########################################################################################
def dump(myStr):
    global DUMP_FILE
    print myStr
    sys.stdout.flush()
    DUMP_FILE.write(myStr+"\n")
    DUMP_FILE.flush()

##############################################################################
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
info_time = []
markers = []
markers_time = []

micro_time = []
total_curr = []
energy = []

file_names = []

trials=0

for f in fileList:
    if (f.endswith('.log') and f.startswith('log')):
        myFile=f
        file_names.append(myFile)

        dump('----------------------------------------')
        dump('processing file: '+f)
        shutil.copy(LOG_DIR+'/'+myFile, '%s/%s/logs'%(LOG_DIR, STR_GRAPHS))

        fv=open (LOG_DIR+'/'+myFile,"r")

        reading.append([])
        reading_time.append([])
        for i in range(NUMBER_OF_CHANNELS):
            reading[trials].append([])
            reading_time[trials].append([])

        markers.append([]) 
        markers_time.append([]) 
        info.append([])
        info_time.append([])

        micro_time.append([])
        total_curr.append([])
        energy.append([])

        micro_time[trials].append(0.0)
        total_curr[trials].append(0.0)
        energy[trials].append(0.0)
        lastValue=[0.0]*NUMBER_OF_CHANNELS

        line_number=0
        counted=0
        TIME_REFERENCE=0
        while True:
            try:
                line_number=line_number+1
                l=fv.readline()
                if (l.startswith('#')):
                    continue
                if l=='':
                    break
                l=l.strip().split()
                now=float(l[0])  

                if (TIME_REFERENCE==0):
                    TIME_REFERENCE=now

                time = now - TIME_REFERENCE
                if (DURATION>0) and (time > DURATION):
                    break

                event_type=int(l[1])

                if event_type==EVENT_TYPE.MEASUREMENT:
                    channel=int(l[2])
                    curr=float(l[3])
                    reading_time[trials][channel].append(time)
                    reading[trials][channel].append(curr)
                    lastValue[channel]=curr
                    micro_time[trials].append(time)
                    total_curr[trials].append(sum(lastValue))
                    energy[trials].append(energy[trials][-1]+(total_curr[trials][-1]+total_curr[trials][-2])/2 * (micro_time[trials][-1]-micro_time[trials][-2]) * BATTERY_VOLTAGE * SCALE)

                if event_type==EVENT_TYPE.EVENT:
                    markers_time[trials].append(time)
                    markers[trials].append(0)           #an event is a marker with mark = 0

                if event_type==EVENT_TYPE.MARK:
                    mark=int(l[2])
                    markers_time[trials].append(time)
                    markers[trials].append(mark)

                if event_type==EVENT_TYPE.INFO:
                    information="".join(l[2:])
                    info_time[trials].append(time)
                    info[trials].append(information)

                counted=counted+1

            except Exception as e:
                dump("error at line: %d"%(line_number))
                if len(l)>0:
                    dump(str(l))

                dump(str(e))
                break

        dump ("%d lines were read, %d lines counted"%(line_number, counted)) 
        dump ("within the trial#%d we found %d reading sets, %d events+markers, %d info messages"%(trials, len(reading[trials][0]),len(markers[trials]),len(info[trials])))
        fv.close()

        trials += 1	


        ######################################### OUTPUT  #############################################

        ######################################### GRAPHS  #############################################
dump('========================================')

velocity = [[] for i in range(trials)]
position = [[] for i in range(trials)]
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

max_start_time = 0
min_stop_time = sys.maxint
max_start_distance = 0
min_stop_distance = sys.maxint


if (TARGET_SETUP=="Angle"):
    SPEED_MARKER_THRESHOLD = -100.0 #/ not applicable for turns, set it to -100.0 so we don't cath anything
    SPEED_SETUPS=[ANGLE_CONSTANT_SPEED]*len(ANGLE_SETUPS)

fig1, ax1 = plt.subplots()
graph_x1 = [0]*SETUPS_TO_SHOW
graph_y1 = [0]*SETUPS_TO_SHOW
graph_m  = [0]*SETUPS_TO_SHOW

for this_trial in range(trials):
    this_day=this_trial/(NUMBER_OF_ROUNDS * NUMBER_OF_SETUPS)
    this_setup=(this_trial/NUMBER_OF_ROUNDS) % NUMBER_OF_SETUPS
    this_round=this_trial%NUMBER_OF_ROUNDS
    
    dump('processing trial %d: day %d setup %d round %d ...'%(this_trial, this_day, this_setup, this_round))

    velocity[this_trial], position[this_trial] = extract_info(info[this_trial])
    total_movement[this_trial] = extract_distance(position[this_trial][0], position[this_trial][-1])
    for u in range(len(position[this_trial])-1):
        sum_distance[this_trial] += extract_distance(position[this_trial][u], position[this_trial][u+1])
    
    try:
        start_marker_index[this_trial] = [ n for n,i in enumerate(velocity[this_trial]) if i>SPEED_SETUPS[this_setup]-SPEED_MARKER_THRESHOLD][0]
        stop_marker_index[this_trial] = [ n for n,i in enumerate(velocity[this_trial]) if i>SPEED_SETUPS[this_setup]-SPEED_MARKER_THRESHOLD][-1]
        start_micro_time_index[this_trial] = binary_search(micro_time[this_trial], info_time[this_trial][start_marker_index[this_trial]])
        stop_micro_time_index[this_trial] = binary_search(micro_time[this_trial], info_time[this_trial][stop_marker_index[this_trial]])
        steady_duration[this_trial] = info_time[this_trial][stop_marker_index[this_trial]] - info_time[this_trial][start_marker_index[this_trial]]
        steady_movement[this_trial] = extract_distance(position[this_trial][start_marker_index[this_trial]], position[this_trial][stop_marker_index[this_trial]])
        delta_energy[this_trial] = energy[this_trial][stop_micro_time_index[this_trial]] - energy[this_trial][start_micro_time_index[this_trial]]
        for u in range(start_marker_index[this_trial],stop_marker_index[this_trial]):
            sum_distance_steady[this_trial] += extract_distance(position[this_trial][u], position[this_trial][u+1])
                
        if (max_start_time < micro_time[this_trial][start_micro_time_index[this_trial]]):
            max_start_time = micro_time[this_trial][start_micro_time_index[this_trial]]
        if (min_stop_time > micro_time[this_trial][stop_micro_time_index[this_trial]]):
            min_stop_time = micro_time[this_trial][stop_micro_time_index[this_trial]]

        if (max_start_distance < extract_distance(position[this_trial][start_marker_index[this_trial]], position[this_trial][0])):
            max_start_distance = extract_distance(position[this_trial][start_marker_index[this_trial]], position[this_trial][0])
        if (min_stop_distance > extract_distance(position[this_trial][stop_marker_index[this_trial]], position[this_trial][0])):
            min_stop_distance = extract_distance(position[this_trial][stop_marker_index[this_trial]], position[this_trial][0])
    except:
        pass

    dump("------------------------")
    if (steady_duration[this_trial]>0):
        dump("\tSTEADY DURATION DETECTED:")
        dump("\tstart time -> stop time  --- steady duration -----     start position      ->     stop position       ----- steady movement --- steady distance")
        dump("\t%8.3f   -> %8.3f   ---  %11.3f    ----- (%10.3f,%10.3f) -> (%10.3f,%10.3f) ----- %10.3f     --- %10.3f    " \
            %(info_time[this_trial][start_marker_index[this_trial]], info_time[this_trial][stop_marker_index[this_trial]], steady_duration[this_trial], 
                position[this_trial][start_marker_index[this_trial]][0], position[this_trial][start_marker_index[this_trial]][1],
                position[this_trial][stop_marker_index[this_trial]][0], position[this_trial][stop_marker_index[this_trial]][1],
                steady_movement[this_trial], sum_distance_steady[this_trial]))
        dump("\tfor this tiral, target Velocity = %.2f average Steady Velocity = %.2f and steady E/X = %.3f" \
            %(SPEED_SETUPS[this_setup], sum_distance_steady[this_trial]/steady_duration[this_trial], delta_energy[this_trial] / sum_distance_steady[this_trial]))
    else:
        dump("\tCOULD NOT DETECT STEADY DURATION, STEADY DATA NOT RELIABLE")
    dump("------------------------")

    myFile=file_names[this_trial][4:-10]

    if (TARGET_SETUP=="Speed"):
        added_setup_label = 'Speed = %.1f m/s'%(SPEED_SETUPS[this_setup])
    elif (TARGET_SETUP=="Angle"):
        added_setup_label = 'Angle = %d deg'%(ANGLE_SETUPS[this_setup])
    else:
        dump("UKNOWN TARGET SETUP: "+TARGET_SETUP)
        

    overhead_distance = sum_distance[this_trial] - sum_distance_steady[this_trial]
    overhead_energy = energy[this_trial][start_micro_time_index[this_trial]] + energy[this_trial][-1] - energy[this_trial][stop_micro_time_index[this_trial]]
    slope = delta_energy[this_trial] / sum_distance_steady[this_trial]
    if (this_setup<SETUPS_TO_SHOW):
        graph_x1[this_setup] += overhead_distance 
        graph_y1[this_setup] += overhead_energy
        graph_m[this_setup] += slope
        print "Slope = %f"%(slope*1000)
        sys.stdout.flush()
        ax1.plot(overhead_distance, overhead_energy,'o', color=SPEED_COLORS[this_setup]) 


#    if (start_marker_index[this_trial]>0):
#        line_x = np.arange(0,20,0.1)
#        line_y = [ (energy[this_trial][start_micro_time_index[this_trial]] + energy[this_trial][-1] - energy[this_trial][stop_micro_time_index[this_trial]]) +
#                    (delta_energy[this_trial]/sum_distance_steady[this_trial]) * (x-(sum_distance[this_trial] - sum_distance_steady[this_trial])) for x in line_x] 
#        ax1.plot(line_x,line_y,'-', label='Trial %d'%(this_trial), linewidth=1, markersize=1)  

#    ax2.plot(distance_vector,energy_vector,'-', label='Trial %d'%(this_trial), linewidth=1, markersize=1)  
#    ax3.plot(micro_time[this_trial],energy[this_trial])

    resultFile=open('%s/%s/all.txt'%(LOG_DIR,STR_GRAPHS),'a')

    resultFile.write("%d \t%s \t%d \t%d \t%d \t%.3f \t\t%.3f \t%.3f \t\t%.3f \t\t%.2f \t\t%.2f \t\t%5d \t\t%5.2f \t\t%5.2f \t\t%.2f \t\t%5.2f \t\t%7.3f \t%10.3f \t%.3f \t%.3f\n" \
                %(this_trial+1, file_names[this_trial],this_day, this_round, this_setup, micro_time[this_trial][-1],energy[this_trial][-1], 
            sum_distance[this_trial], total_movement[this_trial], energy[this_trial][-1]/micro_time[this_trial][-1], energy[this_trial][-1]/sum_distance[this_trial], 
            ANGLE_SETUPS[this_setup], SPEED_SETUPS[this_setup], sum_distance[this_trial]/micro_time[this_trial][-1], steady_duration[this_trial], sum_distance_steady[this_trial]/steady_duration[this_trial], 
            sum_distance_steady[this_trial], delta_energy[this_trial], delta_energy[this_trial]/sum_distance_steady[this_trial], delta_energy[this_trial]/steady_duration[this_trial]))
    resultFile.close()
			
dump('----------------------------------------')
dump("in total %d trials processed"%(trials))


STR_GRAPH_TITLE = "Estimated Energy"# for Target Distance Over %d Trials"%(trials)
DUAL_STR_GRAPH_TITLE = "Power and Time Comparison Over %d Trials"%(trials)
STR_X_LABEL = "Target Distance (m)"
STR_Y_LABEL = "Estimated Energy (kJ)"
STR_FILENAME = "estimation.eps"
LINE_WIDTH=3

line_x = np.arange(0,70,0.1)
for s in range(SETUPS_TO_SHOW):
    graph_x1[s] /= NUMBER_OF_DAYS * NUMBER_OF_ROUNDS
    graph_y1[s] /= NUMBER_OF_DAYS * NUMBER_OF_ROUNDS
    graph_m[s] /= NUMBER_OF_DAYS * NUMBER_OF_ROUNDS
    line_y = [ graph_y1[s] + graph_m[s] * (x-graph_x1[s]) for x in line_x] 
    ax1.plot(line_x,line_y,'-', label='Speed: %d(m/s)'%(SPEED_SETUPS[s]), linewidth=LINE_WIDTH, color=SPEED_COLORS[s])  

# add some text for labels, title and axes ticks
ax1.set_title(STR_GRAPH_TITLE,y=1.05)
ax1.set_xlabel(STR_X_LABEL)
ax1.set_ylabel(STR_Y_LABEL)
#ax1.set_xticks(ind_setups)
#ax1.set_xticklabels([i * 20 for i in range(20)])

if (APPLY_GRAPH_CUSTOMIZATION):
#    ax1.set_ylim(0,10)
#    ax1.set_xlim(-2*BAR_WIDTH,SETUPS_TO_SHOW-1 + 2*BAR_WIDTH)
#    yticks = ax1.yaxis.get_major_ticks()
#    yticks[-1].label1.set_visible(False)
    pass

handles, labels = ax1.get_legend_handles_labels()
plt.legend(handles, labels, loc=2, prop={'size':24})   
fig1.tight_layout()
#plt.savefig(LOG_DIR+"/"+STR_GRAPHS+"/"+STR_FILENAME,dpi=600) 
#plt.show()
#plt.close('all')

