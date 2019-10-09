from constants import *
import socket
import sys

class tcpClient(object):

	def __init__(self, ipAddress):
		self.TCP_IP = ipAddress
		self.TCP_PORT = PWR_PORT # from constants.py
		self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.s.connect((self.TCP_IP, self.TCP_PORT))
		print 'connected to the server'
		print 'now you can use commands: S F E M# Q'
		print '----------------------------------'
		self.MESSAGE = ''
		sys.stdout.flush()
		while(True):
			try:
				sys.stdout.write('Enter command: ')
				sys.stdout.flush()
				self.MESSAGE = raw_input()
				if self.MESSAGE == 'Q' or self.MESSAGE == 'q':
					print 'exiting'
					sys.stdout.flush()
					break
				self.command = bytearray()
				if self.MESSAGE == 'S' or self.MESSAGE == 's':
					self.command.append(PWR_Command.PWR_START)
				if self.MESSAGE == 'F' or self.MESSAGE == 'f':
					self.command.append(PWR_Command.PWR_STOP)
				if self.MESSAGE == 'E' or self.MESSAGE == 'E':
					self.command.append(PWR_Command.PWR_EVENT)
				if self.MESSAGE.startswith('M'):
					self.command.append(PWR_Command.PWR_MARK)
					self.number = int(self.MESSAGE[1:])
					self.command.append(hex2bytes(int2hex(self.number)))
				for i in PACKET_END:
					self.command.append(i)
				self.s.send(self.command)
			except:
				print 'program stopped'
				sys.stdout.flush()
				break

		self.s.close()

newClient = tcpClient('127.0.0.1')#instanciating the class object
