from constants import *
import socket
import sys

TCP_IP = '127.0.0.1'
TCP_PORT = PWR_PORT
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((TCP_IP, TCP_PORT))
print ('connected to the server')
print ('now you can use commands:')
print ('S  : start measuremnt')
print ('F  : finish mesaurement')
print ('E  : record event')
print ('M# : record marker with number #')
print ('Q  : quit this program')
print ('----------------------------------')
MESSAGE=''
sys.stdout.flush()
while True:
    try:
	sys.stdout.write('Enter command: ')
	sys.stdout.flush()
	MESSAGE = raw_input()
	if (MESSAGE=='Q' or MESSAGE=='q'):
	    print ('exiting')
	    sys.stdout.flush()
	    break
	command=bytearray()
	if (MESSAGE=='S' or MESSAGE=='s'):
	    command.append(PWR_Command.PWR_START)
	if (MESSAGE=='F' or MESSAGE=='f'):
	    command.append(PWR_Command.PWR_STOP)
	if (MESSAGE=='E' or MESSAGE=='e'):
	    command.append(PWR_Command.PWR_EVENT)
	if (MESSAGE.startswith('M') or MESSAGE.startswith('m')):
	    command.append(PWR_Command.PWR_MARK)
	    number=int(MESSAGE[1:])
	    command.append(bytes(bytearray([number])))
	for i in PACKET_END:
	    command.append(i)
	s.send(command)

    except Exception as e:
        print e
	print ('program stopped')
	sys.stdout.flush()
	break
s.close()
