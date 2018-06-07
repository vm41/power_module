from constants import *

class Conversion:
    @classmethod
    def convert(self, sensor_type, data_raw):
        result = data_raw
        if(sensor_type == SENSOR_TYPE.HALL): # for hall effect sensor
            result =  data_raw * 10  #  100mV per 1Amp 
        if(sensor_type == SENSOR_TYPE.VOLTAGE): # for voltage
            result =  data_raw * 11 # divider using 10k-100k resistors
        return result

