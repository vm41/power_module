import os,re
import shutil
import sys
import time
sys.path.append("../")
from constants import *
global DUMP_FILE

HEADER_LINES=2
SEPERATION_CHAR=25 # at which 2 lines should be separated. because of tabs, characters are not exactly columns
STR_FIXED_LOGS='trimmed'

if ((len(sys.argv)>1) and (sys.argv[1]=='-h')) or len(sys.argv)<2 :
    print "----------------------------------------------"
    print "This script is spicifically for trimming log files that miss a newline at the end of their buffer flush:"
    print "1528842539.026  1   4    22.991528842539.063    1   0     5.03"
    print "in the line above you can see there should have been a new line."
    print "this issue should be fixed in the logger script, but yet this may come useful"
    print "Input file is REQUIRED, or you can input ALL to process every file. (ALL in caps)"
    print "Log(s) should be in the %s folder."%(LOG_DIR)
    print "----------------------------------------------"
    exit();

myFile=sys.argv[1]
if (myFile!='ALL'):
    if (myFile.startswith(LOG_DIR)):
        print "File name includes LOG_DIR name: %s"%(myFile)
        print "Trimming input to: "
        myFile = myFile[len(LOG_DIR)+1:]
        print myFile
if not os.path.exists('%s/%s'%(LOG_DIR,STR_FIXED_LOGS)):
    os.makedirs('%s/%s'%(LOG_DIR,STR_FIXED_LOGS))

DUMP_FILE=open('%s/%s/process_log.txt'%(LOG_DIR,STR_FIXED_LOGS),'a')
###########################################################################################
def dump(myStr):
    global DUMP_FILE
    print myStr
    sys.stdout.flush()
    DUMP_FILE.write(myStr+"\n")
    DUMP_FILE.flush()

##########################################################################
##############################################################################
################# reading log file
#for i in range(1):
#	f=sys.argv[1].split('/',1)[1]
fileList=os.listdir(LOG_DIR)
fileList.sort()
if (sys.argv[1] != 'ALL'):
    fileList = [myFile]

file_names = []

for f in fileList:
    if (f.endswith('.log') and f.startswith('log')):
        myFile=f
        file_names.append(myFile)

        dump('----------------------------------------')
        dump('processing file: '+f)

        f_in=open (LOG_DIR+'/'+myFile,"r")
        f_out=open (LOG_DIR+'/'+STR_FIXED_LOGS+'/'+myFile, "w")

        line_number = 0
        for i in range(HEADER_LINES+1):
            l = f_in.readline()
            line_number+=1
            f_out.write(l);

        try:
            while(l):
                l = f_in.readline()
                if not l:
                    break
                line_number+=1
                if (len(l)>30 and int(l.strip().split()[1])==1):
                    l1=l[:SEPERATION_CHAR]
                    l2=l[SEPERATION_CHAR:]
                    dump("----------------------")
                    dump("Trimming line:")
                    dump('\t'+l.strip())
                    f_out.write(l1+'\n');
                    f_out.write(l2);
                    dump("Resulting lines:")
                    dump('\t'+l1)
                    dump('\t'+l2)
                else:
                    f_out.write(l);
        except Exception as e:
            dump("error at line: %d"%(line_number))
            if len(l)>0:
                dump(str(l))

            dump(str(e))

        dump ("%d lines were read"%(line_number)) 
        f_in.close()
        f_out.close()


