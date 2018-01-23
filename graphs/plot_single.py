import matplotlib.pyplot as plt
import numpy as np
import math
import os,re
import shutil
import sys
sys.path.append("../")
from constants import *
font = {"family" : "normal",
        "weight" : "bold",
        "size"   : 24}

plt.rc("font", **font)
plt.rcParams["pdf.fonttype"] = 42
plt.rcParams["ps.fonttype"] = 42

SMOOTHING_WINDOW=20

BATTERY_VOLTAGE=23 # this ensures power = current * voltage
NUMBER_OF_ROUNDS=1
NUMBER_OF_SPEEDS=1
SPEED_SETUPS = [5.0]*30
SPEED_MARKER_THRESHHOLD=1.0     #first time and last time haveing targetSpeed - threshold, will be marked
SAVE_GRAPH_CHANNELS = True     #individual channel current vs. time
SAVE_GRAPH_TOTAL = False         #total current vs. time
SAVE_GRAPH_VELOCITY = False      
SAVE_GRAPH_ENERGY = False
SAVE_GRAPH_SPEED_BASED = False
SAVE_GRAPH_ROUND_BASED = False
STR_GRAPHS='current_graphs'
STR_CROUND='constant_round'
STR_CSPEED='constant_speed'
global INITIAL_LONGITUDE
global INITIAL_LATITUDE
global EARTH_R

if ((len(sys.argv)>1) and (sys.argv[1]=='-h')) or len(sys.argv)<2 :
    print "----------------------------------------------"
    print "this is for creating graphs for a single trial, showing some results only for that test and an input file is REQUIRED, or you can input ALL to process every file."
    print "log should be in the %s folder. hence DO NOT include folder name in file name."%(LOG_DIR)
    print "----------------------------------------------"
    exit();

DURATION=0	#0 means no limit

myFile=sys.argv[1]
#    DURATION=int(sys.argv[2])

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

    shutil.rmtree('%s/%s'%(LOG_DIR, STR_GRAPHS), ignore_errors=True)
    os.makedirs('%s/%s'%(LOG_DIR,STR_GRAPHS))
    os.makedirs('%s/%s/all'%(LOG_DIR,STR_GRAPHS))
    os.makedirs('%s/%s/compare'%(LOG_DIR,STR_GRAPHS))
    os.makedirs('%s/%s/logs'%(LOG_DIR,STR_GRAPHS))

    if (SAVE_GRAPH_ROUND_BASED):
        os.makedirs('%s/%s/%s'%(LOG_DIR,STR_GRAPHS,STR_CROUND))
        for i in range(NUMBER_OF_ROUNDS):
            os.makedirs('%s/%s/%s/round-%d'%(LOG_DIR,STR_GRAPHS,STR_CROUND,i+1))

    if (SAVE_GRAPH_SPEED_BASED):
        os.makedirs('%s/%s/%s'%(LOG_DIR,STR_GRAPHS,STR_CSPEED))
        for i in range(NUMBER_OF_SPEEDS):
            os.makedirs('%s/%s/%s/speed-%d'%(LOG_DIR,STR_GRAPHS,STR_CSPEED,i+1))


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

        print '----------------------------------------'
        print 'processing file: '+f

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
                    energy[trials].append(energy[trials][-1]+(total_curr[trials][-1]+total_curr[trials][-2])/2 * (micro_time[trials][-1]-micro_time[trials][-2]) * BATTERY_VOLTAGE)

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
                print "error at line: ", line_number
                if len(l)>0:
                    print l

                print e
                break

        print line_number," lines were read, ",counted, " lines counted"
        print "withing the trial#%d we found %d reading sets, %d events+markers, %d info messages"%(trials, len(reading[trials][0]),len(markers[trials]),len(info[trials]))
        fv.close()

        trials += 1	


        ######################################### OUTPUT  #############################################

        ######################################### GRAPHS  #############################################
print '========================================'

round_power = []
for i in range(NUMBER_OF_ROUNDS):
    round_power.append([]) # to keep the powers of different rounds before averaging

avg_power = []
for i in range(NUMBER_OF_SPEEDS):
    avg_power.append([])        
    avg_power[i].append([]) #one for time
    avg_power[i].append([]) #corresponding average power

velocity = [[]] * trials
position = [[]] * trials
start_marker_index = [-1] * trials
stop_marker_index = [-1] * trials
start_micro_time_index = [-1]*trials
stop_micro_time_index = [-1]*trials
steady_duration = [-1] * trials
steady_distance = [-1] * trials #only a direct distance between start and stop of steady
delta_energy = [0] * trials
total_distance = [-1] * trials  #only a direct distance between start and end point
sum_distance = [0] * trials   #sum of all delta_x

for this_trial in range(trials):
    this_round=this_trial%NUMBER_OF_ROUNDS
    this_speed=this_trial/NUMBER_OF_ROUNDS
    print 'processing trial %d: round %d speed %d ...'%(this_trial, this_round, this_speed)

    velocity[this_trial], position[this_trial] = extract_info(info[this_trial])
    total_distance[this_trial] = extract_distance(position[this_trial][0], position[this_trial][-1])
    for u in range(len(position[this_trial])-1):
        sum_distance[this_trial] += extract_distance(position[this_trial][u], position[this_trial][u+1])

    try:
        start_marker_index[this_trial] = [ n for n,i in enumerate(velocity[this_trial]) if i>SPEED_SETUPS[this_speed]-SPEED_MARKER_THRESHHOLD][0]
        stop_marker_index[this_trial] = [ n for n,i in enumerate(velocity[this_trial]) if i>SPEED_SETUPS[this_speed]-SPEED_MARKER_THRESHHOLD][-1]
        start_micro_time_index[this_trial] = binary_search(micro_time[this_trial], info_time[this_trial][start_marker_index[this_trial]])
        stop_micro_time_index[this_trial] = binary_search(micro_time[this_trial], info_time[this_trial][stop_marker_index[this_trial]])
        steady_duration[this_trial] = info_time[this_trial][stop_marker_index[this_trial]] - info_time[this_trial][start_marker_index[this_trial]]
        steady_distance[this_trial] = extract_distance(position[this_trial][start_marker_index[this_trial]], position[this_trial][stop_marker_index[this_trial]])
        delta_energy[this_trial] = energy[this_trial][stop_micro_time_index[this_trial]] - energy[this_trial][start_micro_time_index[this_trial]]
    except:
        pass

    if (steady_duration[this_trial]>0):
        print "------------------------"
        print "\tSTEADY DURATION DETECTED:"
        print "\tstart time -> stop time --- steady duration ---- start position  ->   stop position ------ steady distance"
        print "\t%f -> %f ----- %f ---- (%f,%f) -> (%f,%f) ---- %f"%(info_time[this_trial][start_marker_index[this_trial]], info_time[this_trial][stop_marker_index[this_trial]],
            steady_duration[this_trial], position[this_trial][start_marker_index[this_trial]][0], position[this_trial][start_marker_index[this_trial]][1],
                                position[this_trial][stop_marker_index[this_trial]][0], position[this_trial][stop_marker_index[this_trial]][1],
                                steady_distance[this_trial])
        print "\tfor this tiral, target Velocity = %.2f average Steady Velocity = %.2f and steady E/X = %.3f"%(SPEED_SETUPS[this_speed], 
            steady_distance[this_trial]/steady_duration[this_trial], delta_energy[this_trial] / steady_distance[this_trial])
        print "------------------------"

    myFile=file_names[this_trial][4:-10]

    if (SAVE_GRAPH_CHANNELS):
        fig1, ax1 =plt.subplots()
        for i in range(NUMBER_OF_CHANNELS):
            reading[this_trial][i]=AvgING(reading[this_trial][i],SMOOTHING_WINDOW)
            ax1.plot(reading_time[this_trial][i],reading[this_trial][i])

        for i in range(len(markers_time[this_trial])):
            ax1.axvline(x=markers_time[this_trial][i],color='k')      #TODO apply colors based on marker number

        ax1.set_xlabel('Time (s)')
        ax1.set_ylabel('Current (A)')
        plt.title('%d Channels')# - Round = %d Speed = %.1f m/s'%(NUMBER_OF_CHANNELS,this_round+1,SPEED_SETUPS[this_speed]))
        plt.savefig('%s/%s/all/%s_channels.png'%(LOG_DIR,STR_GRAPHS,file_names[this_trial]),dpi=600,format="png")
        if (SAVE_GRAPH_ROUND_BASED):
            plt.savefig('%s/%s/%s/round-%d/channels_speed-%.1f.png'%(LOG_DIR,STR_GRAPHS,STR_CROUND,this_round+1,SPEED_SETUPS[this_speed]))
        if (SAVE_GRAPH_SPEED_BASED):
            plt.savefig('%s/%s/%s/speed-%.1f/channels_round-%d.png'%(LOG_DIR,STR_GRAPHS,STR_CSPEED,SPEED_SETUPS[this_speed],this_round+1))


    if (SAVE_GRAPH_TOTAL):
        fig2, ax2 =plt.subplots()
        total_curr[this_trial]=AvgING(total_curr[this_trial],SMOOTHING_WINDOW)
        ax2.plot(micro_time[this_trial],total_curr[this_trial], 'b')

        for i in range(len(markers_time[this_trial])):
            ax2.axvline(x=markers_time[this_trial][i],color='k')      #TODO apply colors based on marker number

        if (start_marker_index[this_trial]>=0):
            ax2.axvline(info_time[this_trial][start_marker_index[this_trial]],color='r')
            ax2.axvline(info_time[this_trial][stop_marker_index[this_trial]],color='r')
        ax2.set_xlabel('Time (s)')
        ax2.set_ylabel('Total Current (A)')
        ax2.set_ylim(11.5,16.5)
        ax2.set_xlim(0,28)
        yticks = ax2.yaxis.get_major_ticks()
#        yticks[-1].label1.set_visible(False)
        plt.title('Total Current')# - Round = %d Speed = %.1f m/s'%(this_round+1, SPEED_SETUPS[this_speed]))
        plt.tight_layout()
        plt.savefig('%s/%s/all/%s_total.eps'%(LOG_DIR,STR_GRAPHS,file_names[this_trial]),dpi=600)
        if (SAVE_GRAPH_ROUND_BASED):
            plt.savefig('%s/%s/%s/round-%d/total_speed-%.1f.png'%(LOG_DIR,STR_GRAPHS,STR_CROUND,this_round+1,SPEED_SETUPS[this_speed]))
        if (SAVE_GRAPH_SPEED_BASED):
            plt.savefig('%s/%s/%s/speed-%.1f/total_round-%d.png'%(LOG_DIR,STR_GRAPHS,STR_CSPEED,SPEED_SETUPS[this_speed],this_round+1))

    if (SAVE_GRAPH_ENERGY):
        fig3, ax3 =plt.subplots()
        ax3.plot(micro_time[this_trial],energy[this_trial], 'r')

        for i in range(len(markers_time[this_trial])):
            ax3.axvline(x=markers_time[this_trial][i],color='k')      #TODO apply colors based on marker number

        ax3.set_xlabel('Time (s)')
        ax3.set_ylabel('Total Energy (J)')
        plt.title('Cumulative Energy')# - Round = %d Speed = %.1f m/s'%(this_round+1, SPEED_SETUPS[this_speed]))
        plt.savefig('%s/%s/all/%s_energy.png'%(LOG_DIR,STR_GRAPHS,file_names[this_trial]),dpi=600,format="png")
        if (SAVE_GRAPH_ROUND_BASED):
            plt.savefig('%s/%s/%s/round-%d/energy_speed-%.1f.png'%(LOG_DIR,STR_GRAPHS,STR_CROUND,this_round+1,SPEED_SETUPS[this_speed]))
        if (SAVE_GRAPH_SPEED_BASED):
            plt.savefig('%s/%s/%s/speed-%.1f/energy_round-%d.png'%(LOG_DIR,STR_GRAPHS,STR_CSPEED,SPEED_SETUPS[this_speed],this_round+1))


    if (SAVE_GRAPH_VELOCITY):
        fig4, ax4 =plt.subplots()
        ax4.plot(info_time[this_trial],velocity[this_trial], 'm')

        for i in range(len(markers_time[this_trial])):
            ax4.axvline(x=markers_time[this_trial][i],color='k')      #TODO apply colors based on marker number

        if (start_marker_index[this_trial]>=0):
            ax4.axvline(info_time[this_trial][start_marker_index[this_trial]],color='r')
            ax4.axvline(info_time[this_trial][stop_marker_index[this_trial]],color='r')
        ax4.set_ylim(0,6)
        yticks = ax4.yaxis.get_major_ticks()
        yticks[-1].label1.set_visible(False)
        ax4.set_xlabel('Time (s)')
        ax4.set_ylabel('Velocity (m/s)')
        ax4.set_xlim(0,28)
        plt.title('Measured Velocity')# - Round = %d Speed = %.1f m/s'%(this_round+1, SPEED_SETUPS[this_speed]))
        plt.tight_layout()
        plt.savefig('%s/%s/all/%s_velocity.eps'%(LOG_DIR,STR_GRAPHS,file_names[this_trial]),dpi=600)
        if (SAVE_GRAPH_ROUND_BASED):
            plt.savefig('%s/%s/%s/round-%d/velocity_speed-%d.png'%(LOG_DIR,STR_GRAPHS,STR_CROUND,this_round+1,SPEED_SETUPS[this_speed]))
        if (SAVE_GRAPH_SPEED_BASED):
            plt.savefig('%s/%s/%s/speed-%.1f/velocity_round-%d.png'%(LOG_DIR,STR_GRAPHS,STR_CSPEED,SPEED_SETUPS[this_speed],this_round+1))

    resultFile=open('%s/%s/all.txt'%(LOG_DIR,STR_GRAPHS),'a')
    resultFile.write('Trial: %d \tFile: %s \tRound: %d \tSpeedSetup: %d \tTotalTime: %.3f \tTotalEnergy: %.3f \t \
        SumDistance: %.3f \tTotalDistance: %.3f \t AveragePower: %.2f \tAverageJ/m: %.2f\t \
        TargetVelocity: %5.2f \tAverageSpeed: %5.2f \tSteadyTime: %.2f \tAverageSteadyVelocity: %5.2f \t \
        SteadyDistanceTravelled: %.3f \t SteadyEnergy: %.3f \tSteadyJoulPerMeter: %.3f\n' 
                %(this_trial+1, file_names[this_trial],this_round+1,this_speed+1,micro_time[this_trial][-1],energy[this_trial][-1], 
            sum_distance[this_trial], total_distance[this_trial], energy[this_trial][-1]/micro_time[this_trial][-1], energy[this_trial][-1]/sum_distance[this_trial], 
            SPEED_SETUPS[this_speed], sum_distance[this_trial]/micro_time[this_trial][-1], steady_duration[this_trial], steady_distance[this_trial]/steady_duration[this_trial], 
            steady_distance[this_trial], delta_energy[this_trial], delta_energy[this_trial]/steady_distance[this_trial]))
    resultFile.close()


#TODO
#    round_power[this_round].append(power[0])
#    round_power[this_round].append(power[1])
#    if (this_round==NUMBER_OF_ROUNDS-1): #we should average over total_curr or energy
#        last_index=[1]*NUMBER_OF_ROUNDS # we start from 1, because all of their first value is 0 anyway.
#            count=NUMBER_OF_ROUNDS
#            timeStamp = 0.0
#            while (count>0):
#                chosen = -1
#                sum_value = 0.0
#                for j in range(NUMBER_OF_ROUNDS):
#                    if (last_index[j]>=len(round_power[j][0])): # a finished list
#                        continue
#                    if (chosen==-1):  #initial assignment
#                        timeStamp = round_power[j][0][last_index[j]]
#                        chosen = j
#                    if (round_power[j][0][last_index[j]] <= timeStamp): #if found a closer timestamp
#                        timeStamp = round_power[j][0][last_index[j]]
#                        chosen = j
#                    sum_value += round_power[j][1][last_index[j]-1]
#
#                avg_power[speed][0].append(timeStamp)
#                avg_power[speed][1].append(sum_value / count)
#
#                last_index[chosen] += 1
#                if (last_index[chosen] >= len(round_power[chosen][0])): # one of lists got finished
#                    count -= 1
#
#            for i in range(NUMBER_OF_ROUNDS):
#                round_power[i] =[]
#    
#        if (speed==0):
#            compare_power=[]
#            compare_energy=[]
#            for i in range(NUMBER_OF_SPEEDS):
#                compare_power.append([])
#                compare_energy.append([])
#
#            compare_markers=[]
#
#        compare_power[speed]=power
#        compare_energy[speed]=energy
#        compare_markers+=markers
#
#       if (speed==NUMBER_OF_SPEEDS-1):
#           fig4, ax4 =plt.subplots()
#           for i in range(NUMBER_OF_SPEEDS):
#               ax4.plot(compare_power[i][0],compare_power[i][1])
#
#           for i in compare_markers:
#               ax4.axvline(x=i,color='k')
#
#           ax4.set_xlabel('Time (s)')
#           ax4.set_ylabel('Total Power (W)')
#           plt.title('Compare power for different Speeds - Round = %d'%(this_round+1))
#           plt.savefig('%s/%s/compare/compare_power_round-%d.png'%(LOG_DIR,STR_GRAPHS,this_round+1),dpi=600,format="png")
#
#           fig5, ax5 =plt.subplots()
#           for i in range(NUMBER_OF_SPEEDS):
#               ax5.plot(compare_energy[i][0],compare_energy[i][1])
#
#           for i in compare_markers:
#               ax5.axvline(x=i,color='k')
#
#           ax5.set_xlabel('Time (s)')
#           ax5.set_ylabel('Total Energy (J)')
#           plt.title('Compare energy for different Speeds - Round = %d'%(this_round+1))
#           plt.savefig('%s/%s/compare/compare_energy_round-%d.png'%(LOG_DIR,STR_GRAPHS,this_round+1),dpi=600,format="png")
#
#        plt.show()
			
    plt.close('all')

#fig6, ax6 =plt.subplots()
#for i in range(NUMBER_OF_SPEEDS):
#    ax6.plot(avg_power[i][0],avg_power[i][1])
#
#ax6.set_xlabel('Time (s)')
#ax6.set_ylabel('Total Current (A)')
#plt.title('Compare current for different speeds')
#plt.savefig('%s/%s/compare/power.png'%(LOG_DIR,STR_GRAPHS),dpi=600,format="png")

print '----------------------------------------'
print "in total",trials,"trials processed"

#plt.show()
