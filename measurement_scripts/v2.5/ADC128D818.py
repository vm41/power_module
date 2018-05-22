import i2c_utilities
import constants
import time

class ADC_MODE:
	#Single ended inputs on IN0-IN6, temperature on IN7
	MODE_0 = 0x00
	#Single ended inputs on IN0-IN7
	MODE_1 = 0x01
	#Pseudo differential inputs by pairs on IN0-IN3
	#e.g IN0 = IN0(+) and IN1(-)
	MODE_2 = 0x02
	#Single ended inputs on IN0-IN3
	#Pseudo differntial inputs by pairs on IN4-IN5
	MODE_3 = 0x03
class ADC_ADDRESS:
	LOW_LOW = 0x1D
	LOW_MID = 0x1E
	LOW_HIGH = 0x1F
	MID_LOW = 0x2D
	MID_MID = 0x2E
	MID_HIGH = 0x2F
	HIGH_LOW = 0x35
	HIGH_MID = 0x36
	HIGH_HIGH = 0x37
class ADC_VREF:
	INT = 0x00
	EXT = 0x01
class ADC_RATE:
	LOW_POWER = 0x00
	CONTINUOUS = 0x01
class ADC_LIMIT:
	HIGH = 0x00
	LOW = 0x01
class ADC_CHANNEL: 
	IN0 = 0x00
	IN1 = 0x01
	IN2 = 0x02
	IN3 = 0x03
	IN4 = 0x04
	IN5 = 0x05
	IN6 = 0x06
	IN7 = 0x07
	TEMP = 0x07
class ADC_INT:
	IN0 = (0x01 << 0)
	IN1 = (0x01 << 1)
	IN2 = (0x01 << 2)
	IN3 = (0x01 << 3)
	IN4 = (0x01 << 4)
	IN5 = (0x01 << 5)
	IN6 = (0x01 << 6)
	IN7 = (0x01 << 7)
	TEMP = (0x01 << 7)
	ALL = 0x00
class ADC_ENABLE:
	IN0 = (0x01 << 0)
	IN1 = (0x01 << 1)
	IN2 = (0x01 << 2)
	IN3 = (0x01 << 3)
	IN4 = (0x01 << 4)
	IN5 = (0x01 << 5)
	IN6 = (0x01 << 6)
	IN7 = (0x01 << 7)
	TEMP = ~(0x01 << 7)
	ALL = 0x00
class ADC_REG:
	Configuration_Register = 0x00
	Interrupt_Status_Register = 0x01
	Interrupt_Mask_Register = 0x03
	Conversion_Rate_Register = 0x07
	Channel_Disable_Register = 0x08
	One_Shot_Register = 0x09
	Deep_Shutdown_Register = 0x0A
	Advanced_Configuration_Register = 0x0B
	Busy_Status_Register = 0x0C
	Channel_Readings_Registers = 0x20
	Limit_Registers = 0x2A
	Manufacturer_ID_Register = 0x3E
	Revision_ID_Register = 0x3F
class Configuration_Register:
	Start = 1 << 0
	INT_Enable = 1 << 1
	INT_Clear = 1 << 3
	Initialization = 1 << 7
class Busy_Status_Register:
	Busy = 1 << 0
	Not_Ready = 1 << 1
class Advanced_Configuration_Register:
	External_Reference_Enable = 1 << 0
	Mode_Select_0 = 1 << 1
	Mode_Select_1 = 1 << 2
class Conversion_Rate_Register:
   	Rate_Register = 1 << 0
	Rate_Register = 1 << 0

class ADC128D818:
	NUMBER_OF_CHANNELS = 8

	def __init__(self, i2c_bus, address):
		self.i2c_bus = i2c_bus
		self.address = address
		self.channel_bias = [0.0]*self.NUMBER_OF_CHANNELS                

	#Configuring the settings that control channel configuration and function
	#MUST STOP THE ADC BEFORE INITIALIZING
	def initialize(self, mode, vref, rate, channels_to_measure, mask_interrupts):
		time.sleep(0.5) #wait to ensure the ADC is finished booting
		self.stop() #make sure the ADC is stopped
		i2c_utilities.write(self.i2c_bus, self.address, ADC_REG.Deep_Shutdown_Register, 0) #make sure the ADC is not in deep shutdown
		time.sleep(0.5)
		#Programming the Advanced Configuration Register
		data = 0

		#Setting the vref to external or external
		if vref == ADC_VREF.INT:
			data&=~Advanced_Configuration_Register.External_Reference_Enable
			self.Vref = 2.56 #internal refence voltage
		elif vref == ADC_VREF.EXT:
			data|=Advanced_Configuration_Register.External_Reference_Enable
			self.Vref = constants.VDD
	
		#Setting the ADC Mode, see ACD_MODE above for mode description
		if mode == ADC_MODE.MODE_0:
			data&=~Advanced_Configuration_Register.Mode_Select_0
			data&=~Advanced_Configuration_Register.Mode_Select_1
		elif mode == ADC_MODE.MODE_1:
			data&=~Advanced_Configuration_Register.Mode_Select_1
			data|=Advanced_Configuration_Register.Mode_Select_0
		elif mode == ADC_MODE.MODE_2:
			data|=~Advanced_Configuration_Register.Mode_Select_0
			data&=Advanced_Configuration_Register.Mode_Select_1
		elif mode == ADC_MODE.MODE_3:
			data|=Advanced_Configuration_Register.Mode_Select_0
			data|=Advanced_Configuration_Register.Mode_Select_1
		i2c_utilities.write(self.i2c_bus, self.address, ADC_REG.Advanced_Configuration_Register, data)

		#Programming the Rate Register
		data = 0
		if rate == ADC_RATE.LOW_POWER:
			data&=~Advanced_Configuration_Register.External_Reference_Enable #0
		elif rate == ADC_RATE.CONTINUOUS:
			data|=Advanced_Configuration_Register.External_Reference_Enable #1
		i2c_utilities.write(self.i2c_bus, self.address,
		ADC_REG.Conversion_Rate_Register, data)

		#Choose to enable/disable mask_channel with the Channel Disable Register
		#The nth bit channel is disabled if set to 1
		#For example to disable ch 3 mask_channel = 00001000
                bit_index = 1
                mask_channel = 0
                for ch in range(self.NUMBER_OF_CHANNELS):
                    if ch not in channels_to_measure:
                        mask_channel |= bit_index
                    else:
                        #Setting the limits for each channel from 0 to vref during initialize
                        self.initialize_limit(ch, ADC_LIMIT.HIGH, 0x80)
                        self.initialize_limit(ch, ADC_LIMIT.LOW, 0)

                    bit_index = bit_index << 1

		i2c_utilities.write(self.i2c_bus, self.address, ADC_REG.Channel_Disable_Register, mask_channel)

		#Using the Interrupt Mask Register
		#the nth bit channel is prevented from sending an interrupt signal
		#For example to prevent channel 3 from causing an interrupt
		#mask_interrupts = 00001000
		i2c_utilities.write(self.i2c_bus, self.address, ADC_REG.Interrupt_Mask_Register, mask_interrupts)

                #starting the sensor
                time.sleep(0.5)
                self.start()
                time.sleep(0.1)
	
	#Setting the high/low limit for each channel, an interrupt
	#will be thrown if the channel exceeds these limits
	#V_limit = ((value in decimal)*(Vref))/2^8
	def initialize_limit(self, channel, high_or_low, value):
		register = ADC_REG.Limit_Registers + channel * 2 + high_or_low
		i2c_utilities.write(self.i2c_bus, self.address, register, value)

	#Returns an adjusted
	def read_channel(self, channel):
		reading = i2c_utilities.read(self.i2c_bus, self.address, ADC_REG.Channel_Readings_Registers + channel, 2)
		real_reading = i2c_utilities.reverse_endian(reading) >> 4 #flip byte order and trim extra 0's
		converted_reading = (real_reading * self.Vref) / 4095
                unbiased_reading = converted_reading - self.channel_bias[channel]
		if(unbiased_reading < 0): #No negative values
			unbiased_reading = 0
		return unbiased_reading

	def read_channel_uncalibrated(self, channel):
		reading = i2c_utilities.read(self.i2c_bus, self.address, ADC_REG.Channel_Readings_Registers + channel, 2)
		real_reading = i2c_utilities.reverse_endian(reading) >> 4 #flip byte order and trim extra 0's
		converted_reading = (real_reading * self.Vref) / 4095
                return converted_reading

	def read_register(self, register, num_bytes):
		return i2c_utilities.read(self.i2c_bus, self.address, register, num_bytes) 

	#Measures and records the zero input response for the given channel
	#this is later subtracted from
	def calibrate(self, channel):
		sum = 0.0
		for i in range(0, constants.CALIBRATION_SAMPLES):
			sum += self.read_channel_uncalibrated(channel)
		self.channel_bias[channel] = (sum / constants.CALIBRATION_SAMPLES)
                print "calibrated channel %d : %f "%(channel, self.channel_bias[channel])
	
	#Turning on the ADC and its interrupt function
	def start(self):
		data = Configuration_Register.Start | Configuration_Register.INT_Enable
		i2c_utilities.write(self.i2c_bus, self.address, ADC_REG.Configuration_Register, data)
		time.sleep(0.1) #wait for the ADC to start and voltages to normalize

	#Turning off the ADC and its interrupt function
	def stop(self):
		i2c_utilities.write(self.i2c_bus, self.address, ADC_REG.Configuration_Register, 0)
