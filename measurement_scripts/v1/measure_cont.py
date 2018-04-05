import Adafruit_GPIO.FT232H as FT232H
import sys
import time

#print sys.argv[0]  read_word.py
#print sys.argv[1]  device address

BATTERY = 12.0
LEVEL=2.43

dev_address=0x48

# Temporarily disable FTDI serial drivers.
FT232H.use_FT232H()

# Find the first FT232H device.
ft232h = FT232H.FT232H()

# Create an I2C device at address.
i2c = FT232H.I2CDevice(ft232h, dev_address)

print "setting Config register..."
value=0xC283 #11000010 10000011 #OS=1 MUX=100,A0_GND  PGA=001,1/1 MODE=0,cont. second byte default
reverse = (value%256)*256 + (value/256) #reformatting the responses for byte order:  0xAaBb => 0xBbAa
i2c.write16(0x01,reverse)

print "reading current Config register:"
response=i2c.readU16(0x01)
value = (response%256)*256 + (response/256) #reformatting the responses for byte order:  0xAaBb => 0xBbAa
print value

print "Conversion Software Version 7.0"
i2c.write16(0x00,0x00)

count=0
start_time=0
finish_time=0
last_time=0
start_time=time.time()
myFile_name = "log_"+time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime(start_time))+"_power.log"
myFile=open(myFile_name,'a')
myFile.write("#time #current(A) #power(W)\t")
myFile.write("start time: %13.3f\t"%(start_time))
myFile.write("battery voltage: %6.2f"%(BATTERY))
myFile.write("\n")

myBuffer=[]


while True:
	# Read a 16 bit unsigned little endian value from registers 0x01 (shunt) and 0x02 (bus).
	try:
		response=i2c.readU16(0x00)
                now=time.time()-start_time
		value = (response%256)*256 + (response/256) #reformatting the responses for byte order:  0xAaBb => 0xBbAa
		voltage=(4.096 * value) / 32768
		current = (voltage - LEVEL) * 10 #100mv/A
		if (current<0):
			 current=0

                power=current*BATTERY
                my_str="%14.3f"%(now)+"\t"+"%6.3f"%(current)+"\t"+"%8.1f"%(power)
		print my_str
#                myBuffer.append(my_str)


#                count+=1
                if (count>=100):
                        finish_time=now
                        print "%8.3f"%(now), ": logged 100 measurement. duration: ", "%8.3f"%(finish_time-last_time)," seconds"
                        for item in myBuffer:
                                myFile.write("%s\n" % item)
                        myBuffer=[]
                        last_time=finish_time
                        count=0

	except KeyboardInterrupt:
		break
	except:
		pass
