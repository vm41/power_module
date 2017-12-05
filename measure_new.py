from constants import *
import sys
import os
import time
import random
from socket import *
from threading import Thread
#Mode selection
if MODE_SELECT==PROGRAM_MODE.HW:
    import smbus
if MODE_SELECT==PROGRAM_MODE.HW_IN_THE_LOOP:
    import Adafruit_GPIO.FT232H as FT232H
class Measure(object):
    """Encapsulates all the necessary functions and attributes required for logging the current measurement:

    Attributes:
        LEVEL_LIST: description
        LOG_MARK: description
        MARK_VALUE:
        LOG_EVENT:
        LOG_INFO:
        INFO_STRING:
        IS_LOGGING:
        FINISH_LOGGING:
        DUMP_FILE:
        SESSION_DIR:
        SESSION_DIR_INIT:
    Methods:
        open_session():
        dump(myStr):
    """
    LEVEL_LIST
    LOG_MARK
    MARK_VALUE
    LOG_EVENT
    LOG_INFO
    INFO_STRING
    IS_LOGGING
    FINISH_LOGGING
    DUMP_FILE
    SESSION_DIR
    SESSION_DIR_INIT
    def __init__(self, name, balance=0.0):
        """Return a Customer object whose name is *name* and starting
        balance is *balance*."""
        self.name = name
        self.balance = balance

    ###########################################################################################
    def open_session():
        session_id=1
        while os.path.exists(Measure.LOG_DIR+"/"+Measure.SESSION_DIR_INIT+"%03d"%(session_id)):
            session_id+=1
        Measure.SESSION_DIR=Measure.SESSION_DIR_INIT+"%03d"%(session_id)
        os.makedirs(Measure.LOG_DIR+"/"+Measure.SESSION_DIR)
        DUMP_FILE = open(Measure.LOG_DIR+"/"+Measure.SESSION_DIR+"/dump.log","a")

    ###########################################################################################
    def dump(myStr):
        newStr = time.strftime("%Y_%m_%d_%H_%M_%S \t", time.localtime(time.time()))+myStr
        print newStr
        sys.stdout.flush()
        Measure.DUMP_FILE.write(newStr+"\n")
        Measure.DUMP_FILE.flush()