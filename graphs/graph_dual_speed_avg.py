import numpy as np
import matplotlib.pyplot as plt
import sys
sys.path.append("../")
from constants import *
global DUMP_FILE
font = {"family" : "normal",
        "weight" : "bold",
        "size"   : 24}
plt.rc("font", **font)
plt.rcParams["pdf.fonttype"] = 42
plt.rcParams["ps.fonttype"] = 42

N_DAYS = 3 #number of whole sets
N_ROUNDS = 4 #number of rounds
N_SETUPS = 4 #number of setup/distance/speed/turn
SETUPS_TO_SHOW = 3  # for example N_SETUP may be 4, but you don't want the last one.
TARGET_SETUP = "Speed" #used in filename. either "Speed" or "Angle"
STR_GRAPHS='current_graphs' #folder in which the database is
NUMBER_OF_DATA_COLUMNS = 15 #these are the columns containing values (will be read as float)
FIRST_DATA_COLUMN = 5 #first column containing values (will be read as float)
APPLY_SCALE = 1 # default = 1
#0      1       2       3       4       5           6               7           8               9           10          11              12              13          14          15              16              17              18              19
#Trial 	File    Day 	Round 	Setup 	TotalTime 	TotalEnergy 	Distance 	Displacement 	AvgPower 	AvgJ/m 		TargetAngle 	TargetSpeed 	AvgSpeed 	SteadyTime 	AvgSteadySpeed 	SteadyDistance 	SteadyEnergy 	AvgSteadyJ/m    AvgSteadyPower
data = [[] for _dummy in xrange(NUMBER_OF_DATA_COLUMNS)]
means = [[] for _dummy in xrange(NUMBER_OF_DATA_COLUMNS)] #each column has N_SETUPS means and stds. one for each setup
stds = [[] for _dummy in xrange(NUMBER_OF_DATA_COLUMNS)]

LEGENDS=["Average Overall Speed", "Average Steady Speed"]
COLUMN_TO_SHOW = [13, 15] #each time one graph, this is the column number change this to generate new ones. start from 0, it is adjusted by FIRST_DATA_COLUMN
COLUMN_TO_SHOW[:] = [x - FIRST_DATA_COLUMN for x in COLUMN_TO_SHOW]
GRAPH_WITHOUT_OFFSET = False  #draw a graph with first offset taken off from all (for angle)
STR_GRAPH_TITLE = "Target and Achieved Speed Over %d Trials"%(N_DAYS*N_ROUNDS)
#"Total Energy Comparison Over %d Trials per Setup"%(N_DAYS*N_ROUNDS)
#"Energy/Meter metric Over %d Trials per Setup"%(N_DAYS*N_ROUNDS)
STR_Y_LABELS = ["Achieved Speed (m/s)"]#,"Achieved Speed (m/s)"]  #"Average Speed (m/s)", "Steady Speed (m/s)"] #"Achieved Speed (m/s)", "Average Steady Speed (m/s)"]

STR_FILENAME = "average_speed.eps"
#"power_time.png"

APPLY_GRAPH_CUSTOMIZATION = True #yticks, ylimit range, etc.
if TARGET_SETUP == "Angle":
    X_LABELS=["0","45","90","135","180"]
    SETUP_X_LABEL = "Turn (degree)"    # "Speed (m/s)"  or "Angle (deg)"
elif TARGET_SETUP == "Speed":
    X_LABELS=["2.0","5.0","7.0","10.0"]
    SETUP_X_LABEL = "Target Speed (m/s)"    # "Speed (m/s)"  or "Angle (deg)"
else:
    print "UNKNOWN TARGET_SETUP: ",TARGET_SETUP
    exit(0)

BAR_LINE_WIDTH=3
BAR_WIDTH = 0.133       # the width of the bars
BAR_ERR_LINE_WIDTH = 8
BAR_ERR_CAP_SIZE = 12
BAR_ERR_CAP_THICK = 4


if ((len(sys.argv)>1) and (sys.argv[1]=='-h')) or len(sys.argv)<2 :
    print "----------------------------------------------"
    print "This is for creating bar graphs to show behavior"
    print "Input file is REQUIRED, if not mentioned default is in %s/%s"%(LOG_DIR, STR_GRAPHS)
    print "----------------------------------------------"

###########################################################################################
def dump(myStr):
    global DUMP_FILE
    print myStr
    sys.stdout.flush()
    DUMP_FILE.write(myStr+"\n")
    DUMP_FILE.flush()
###########################################################################################
if (len(sys.argv)<2):
    fileAddress = LOG_DIR+"/"+STR_GRAPHS+"/all.txt"
else:
    fileAddress = sys.argv[1]

my_file=open(fileAddress,"r")
DUMP_FILE = open('%s/%s/bars_log.txt'%(LOG_DIR,STR_GRAPHS),'w')


headerLines = []
for line in my_file:
    l=line.strip().split()
    if line.strip().startswith('#'):
        headerLines.append("  ".join(l))
        continue
    for col in range(NUMBER_OF_DATA_COLUMNS):
        data[col].append(float(l[FIRST_DATA_COLUMN + col])*APPLY_SCALE)

dump("all entries read from the file")
dump("------------")

for i in range(N_SETUPS):
    for col in range(NUMBER_OF_DATA_COLUMNS):
        list=[]
        for j in range(N_DAYS):
            for k in range(N_ROUNDS):
                list.append(data[col][j*(N_ROUNDS*N_SETUPS) + i*N_ROUNDS+k])    #some might need re-scale. for example from J to mJ or ...
                
        means[col].append(np.mean(list))
        stds[col].append(np.std(list))
    
dump( "Headerlines:")
for line in headerLines:
    dump(line)
dump( "------------------------------------------")
dump( "raw data (in format: column->list_of_entries):")
dump(str(data))
dump( "------------------------------------------")
dump( "mean data (in format: column->each_setup):")
dump(str(means))
dump( "------------------------------------------")
dump( "std data (in format: column->each_setup):")
dump(str(stds))
dump( "------------------------------------------")

###################################################################################
def autolabel(rects):
    # attach some text labels
    for tmp_rect in rects:
        height = tmp_rect.get_height()
#        print height
        ax.text(tmp_rect.get_x()+tmp_rect.get_width()/2., 1.05*height, "%dJ"%int(height),
                ha="center", va="bottom")
###################################################################################

if GRAPH_WITHOUT_OFFSET:
    means[COLUMN_TO_SHOW[0]][:]= [x - means[COLUMN_TO_SHOW[0]][0] for x in means[COLUMN_TO_SHOW[0]]]
    #STR_GRAPH_TITLE = "Differential "+STR_GRAPH_TITLE

ind_setups = np.arange(SETUPS_TO_SHOW)  # the x locations for the groups
fig1, ax1 = plt.subplots()
rects1=ax1.bar(ind_setups-2*BAR_WIDTH, means[COLUMN_TO_SHOW[0]][:SETUPS_TO_SHOW], 2*BAR_WIDTH, color="0.4", hatch='', log=False, linewidth=BAR_LINE_WIDTH,
                yerr = stds[COLUMN_TO_SHOW[0]][:SETUPS_TO_SHOW], error_kw = dict(ecolor = "red", lw=BAR_ERR_LINE_WIDTH, capsize=BAR_ERR_CAP_SIZE, capthick=BAR_ERR_CAP_THICK))
# add some text for labels, title and axes ticks
ax1.set_title(STR_GRAPH_TITLE,y=1.05)
ax1.set_xlabel(SETUP_X_LABEL)
ax1.set_xticks(ind_setups)
ax1.set_xticklabels(tuple(X_LABELS[:SETUPS_TO_SHOW]))

ax1.set_ylabel(STR_Y_LABELS[0])
if (APPLY_GRAPH_CUSTOMIZATION):
    ax1.set_ylim(0,8)
    ax1.set_xlim(-3*BAR_WIDTH, SETUPS_TO_SHOW-1+3*BAR_WIDTH)
    yticks = ax1.yaxis.get_major_ticks()
    yticks[-1].label1.set_visible(False)

ax2=ax1.twinx()
rects2=ax2.bar(ind_setups, means[COLUMN_TO_SHOW[1]][:SETUPS_TO_SHOW], 2*BAR_WIDTH, color="0.8", hatch='', log=False, linewidth=BAR_LINE_WIDTH,
                yerr = stds[COLUMN_TO_SHOW[1]][:SETUPS_TO_SHOW], error_kw = dict(ecolor = "red", lw=BAR_ERR_LINE_WIDTH, capsize=BAR_ERR_CAP_SIZE, capthick=BAR_ERR_CAP_THICK))
# add some text for labels, title and axes ticks
#ax2.set_ylabel(STR_Y_LABELS[1])
if (APPLY_GRAPH_CUSTOMIZATION):
#    ax2.set_ylim(0,8)
    ax2.set_xlim(-3*BAR_WIDTH, SETUPS_TO_SHOW-1+3*BAR_WIDTH)
#    yticks = ax2.yaxis.get_major_ticks()
#    yticks[-1].label2.set_visible(False)
    ax2.get_yaxis().set_ticks([])

plt.tight_layout()
plt.legend(tuple([rects1,rects2]), tuple(LEGENDS), loc=2, prop={'size':24})
plt.savefig(LOG_DIR+"/"+STR_GRAPHS+"/dual_"+TARGET_SETUP+"_"+STR_FILENAME,dpi=600) 

plt.show()
#autolabel(rects)
#plt.grid(True)

