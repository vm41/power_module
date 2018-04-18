from constants import *
import socket
import sys

TCP_IP = '127.0.0.1'
TCP_PORT = PWR_PORT
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((TCP_IP, TCP_PORT))
print ('connected to the server')
print ('now you can use commands: S F E M# Q')
print ('----------------------------------')
MESSAGE=''
sys.stdout.flush()
while True:
	try:
		sys.stdout.write('Enter command: ')
		sys.stdout.flush()
		MESSAGE = raw_input()
		if MESSAGE=='Q':
			print ('exiting')
			sys.stdout.flush()
			break
		command=bytearray()
		if MESSAGE=='S':
			command.append(PWR_Command.PWR_START)
		if MESSAGE=='F':
			command.append(PWR_Command.PWR_STOP)
		if MESSAGE=='E':
			command.append(PWR_Command.PWR_EVENT)
		if MESSAGE.startswith('M'):
			command.append(PWR_Command.PWR_MARK)
			number=int(MESSAGE[1:])
			command.append(hex2bytes(int2hex(number)))
		for i in PACKET_END:
			command.append(i)
		s.send(command)
	except:
		print ('program stopped')
		sys.stdout.flush()
		break
s.close()
