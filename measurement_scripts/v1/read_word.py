import Adafruit_GPIO.FT232H as FT232H
import sys

#print sys.argv[0]  read_word.py
#print sys.argv[1]  device address

dev_address=int(sys.argv[1],0)
dev_reg=int(sys.argv[2],0)

# Temporarily disable FTDI serial drivers.
FT232H.use_FT232H()

# Find the first FT232H device.
ft232h = FT232H.FT232H()

# Create an I2C device at address 0x70.
i2c = FT232H.I2CDevice(ft232h, dev_address)

# Read a 16 bit unsigned little endian value from register 0x01.
response = i2c.readU16(dev_reg)

# Write a 8 bit value 0xAB to register 0x02.
#i2c.write8(0x02, 0xAB)



#reformatting the response for byte order:  0xAaBb => 0xBbAa

print format(response, '#04X')
result=response%256
result*=256
result+=response/256
print format(result, '#04X')
