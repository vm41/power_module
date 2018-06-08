from constants import *
import time
import random
#Converts data between big and little endian e.g.  0xAaBb => 0xBbAa
def reverse_endian(value):
	return (value % 256) * 256 + (value / 256)

def write(i2c_bus, address, register, data):
	if MODE_SELECT == PROGRAM_MODE.PI:
		i2c_bus.write_byte_data(address, register, data)
	if MODE_SELECT == PROGRAM_MODE.PC:
		i2c_bus.write8(register, data)
	if MODE_SELECT == PROGRAM_MODE.PC_SIMULATE_DATA:
		time.sleep(0.1) #delay to simulate write time
		pass

def read(i2c_bus, address, register, num_bytes):
	if num_bytes == 1:
		if MODE_SELECT == PROGRAM_MODE.PI:
			data = i2c_bus.read_byte_data(address, register)
		if MODE_SELECT == PROGRAM_MODE.PC:
			data = i2c_bus.readU8(register)
		if MODE_SELECT == PROGRAM_MODE.PC_SIMULATE_DATA:
			time.sleep(0.001) #delay to simulate read time
			data = int(random.uniform(0, 256))
			data = reverse_endian(data)
		
	elif num_bytes == 2:
		if MODE_SELECT == PROGRAM_MODE.PI:
			data = i2c_bus.read_word_data(address, register)
		if MODE_SELECT == PROGRAM_MODE.PC:
			data = i2c_bus.readU16(register)
		if MODE_SELECT == PROGRAM_MODE.PC_SIMULATE_DATA:
			time.sleep(0.001) #delay to simulate read time
			data = int(random.uniform(0, 4095)) #check this
			data = reverse_endian(data)
	return data

#Don't think we'll need this anymore
#def i2c_wait_to_read():
#	if MODE_SELECT==PROGRAM_MODE.PI:
#		time.sleep(0.010)
#		while (i2c_read(I2C_REG_CONF)<32768):
#			pass
#	if MODE_SELECT==PROGRAM_MODE.PC:
#		time.sleep(0.010)
#		while (i2c_read(I2C_REG_CONF)<32768):
#			pass
#	if MODE_SELECT==PROGRAM_MODE.PC_SIMULATE_DATA:
#		pass
