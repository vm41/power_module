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
    def __init__(self):
        '''
        Initilisation goes here
        '''
        self.LOG_MARK        = False
        self.LOG_EVENT       = False
        self.MARK_VALUE      = 0
        self.IS_LOGGING      = False
        self.LOG_INFO        = False
        self.INFO_STRING     = ""

        self.DEV_ADDRESS     = 0x48
        self.I2C_CONFIG      = 0xC3E3 #11000011 11100011 #OS=1 MUX=100,A0_GND  PGA=001,1/1 MODE=1,single. data rate 111, rest unchanged
        self.SENSOR_STEP     = 0.1 #100mv/A for the 20A sensor module (-20 to 20 Amps in about 4V)
        self.ADC_SCALE       = 4.096/32768.0
        self.MUX_MULTIPLIER  = 4096 #bits [13-12]
        self.I2C_REG_CONF    = 0x01
        self.I2C_REG_CONV    = 0x00

        self.BUFF            = 1024
        self.HOST            = "127.0.0.1"

    ###########################################################################################
    def open_session():
        session_id=1
        while os.path.exists(LOG_DIR+"/"+Measure.SESSION_DIR_INIT+"%03d"%(session_id)):
            session_id+=1
        Measure.SESSION_DIR=Measure.SESSION_DIR_INIT+"%03d"%(session_id)
        os.makedirs(LOG_DIR+"/"+Measure.SESSION_DIR)
        DUMP_FILE = open(LOG_DIR+"/"+Measure.SESSION_DIR+"/dump.log","a")

    ###########################################################################################
    def dump(myStr):
        newStr = time.strftime("%Y_%m_%d_%H_%M_%S \t", time.localtime(time.time()))+myStr
        print newStr
        sys.stdout.flush()
        Measure.DUMP_FILE.write(newStr+"\n")
        Measure.DUMP_FILE.flush()

    ###########################################################################################
    def i2c_write(reg,val):
        reverse = (val%256)*256 + (val/256) #reformatting the responses for byte order:  0xAaBb => 0xBbAa
        if MODE_SELECT==PROGRAM_MODE.HW:
            i2c.write_word_data(DEV_ADDRESS,reg,reverse)
        if MODE_SELECT==PROGRAM_MODE.HW_IN_THE_LOOP:
            i2c.write16(reg,reverse)
        if MODE_SELECT==PROGRAM_MODE.SW_IN_THE_LOOP:
            time.sleep(0.1)
            pass
    ###########################################################################################
    def i2c_wait_to_read():
        if MODE_SELECT==PROGRAM_MODE.HW:
            time.sleep(0.010)
            while (i2c_read(I2C_REG_CONF)<32768):
                pass
        if MODE_SELECT==PROGRAM_MODE.HW_IN_THE_LOOP:
            time.sleep(0.010)
            while (i2c_read(I2C_REG_CONF)<32768):
                pass
        if MODE_SELECT==PROGRAM_MODE.SW_IN_THE_LOOP:
            pass

    ###########################################################################################
    def i2c_read(reg):
        if MODE_SELECT==PROGRAM_MODE.HW:
            reverse=i2c.read_word_data(DEV_ADDRESS,reg)
        if MODE_SELECT==PROGRAM_MODE.HW_IN_THE_LOOP:
            reverse=i2c.readU16(reg)
        if MODE_SELECT==PROGRAM_MODE.SW_IN_THE_LOOP:
            time.sleep(0.001)
            reverse=random.uniform(3.0,3.5)/ADC_SCALE  # this is an example value which relates to around 3-4V
            reverse = (reverse%256)*256 + (reverse/256) #reformatting the responses for byte order:  0xAaBb => 0xBbAa

        result = (reverse%256)*256 + (reverse/256) #reformatting the responses for byte order:  0xAaBb => 0xBbAa
        return result

    ###########################################################################################
    def calibrate():
        global LEVEL_LIST
        dump("calibrating sensors, motors should not be running...")
        if MODE_SELECT==PROGRAM_MODE.SW_IN_THE_LOOP:
            LEVEL_LIST=[VDD/2.0]*NUMBER_OF_CHANNELS
            dump("SW_IN_THE_LOOP detected, calibrating all motors with default value: %.3f"%(VDD/2.0))
        else:
            LEVEL_LIST=[None]*NUMBER_OF_CHANNELS
            try:
                for channel in range(NUMBER_OF_CHANNELS):
                    calibrate_sum = 0.0
                    for sample in range(CALIBRATE_SAMPLES):
                        value=I2C_CONFIG
                        value+=channel*MUX_MULTIPLIER
                        i2c_write(I2C_REG_CONF,value)
                        i2c_wait_to_read()
                        value=i2c_read(I2C_REG_CONV)
                        voltage=value * ADC_SCALE
                        calibrate_sum += voltage

                    LEVEL_LIST[channel] = calibrate_sum / CALIBRATE_SAMPLES
                    dump("channel %d calibrated with %d samples: %.3f"%(channel, CALIBRATE_SAMPLES, LEVEL_LIST[channel]))
                dump("calibration successful")
            except:
                dump("calibration failed, using default value=%.3f for all channels, results might not be correct"%(VDD/2.0))
                for channel in range(NUMBER_OF_CHANNELS):
                    LEVEL_LIST[channel]=VDD/2.0

