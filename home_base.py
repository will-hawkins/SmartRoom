#Home Base control panel

import socket
import time
import logging
import threading
from bitarray.util import int2ba
from bitarray import bitarray
import argparse
from security import RSA, tripleDES, sha1
import json

kill = False
sensor_data = {'range1': 0, 'range2': 0, 'temp': 0, 'light': 0}
conns = []

ACCEPTING_CONNECTIONS = True

token_fd = open('sensor_tokens.txt','r')
global connected_sensors
connected_sensors = 0
TOKENS = token_fd.read().split('\n')

print(connected_sensors)


def receiveUpdate(conn, n, key):
	while not kill:
		data_encrypted = conn.recv(n)
		data = json.loads(tripleDES.tripleDESCBCDecryptAny(data_encrypted.decode('utf-8'),key))

		for k in data.keys():
			sensor_data[k] = data[k]

def rfidThread(conn, n, key):
	while not kill:
		data_encrypted = conn.recv(n)
		data = tripleDES.tripleDESCBCDecryptAny(data_encrypted.decode('utf-8'),key)
		print(data)



def validateConnection(conn,addr):
	#STEP 2: Server sends RSA Params
	print("=======Sending RSA Public Keys=======")
	p,q,e,d = RSA.RSA_params(512)
	N = p*q
	public_keys = {'e': e, 'N': N}
	conn.sendall(str.encode(json.dumps(public_keys)))

	#STEP 3: Receive DES key & Verify Token
	print("=======Receiving DES Key=======")
	data = json.loads(conn.recv(1024))
	key = int2ba(RSA.decrypt(data['key'],d,N), length=192)
	sensor_number = data['sensor']
	token = tripleDES.tripleDESCBCDecryptAny(data['token'],key)

	#STEP 4: Confirm Handshake
	if sha1.sha1(token) == TOKENS[sensor_number-1]:
		#ACCEPT CONNECTION
		if sensor_number != 1:
			receive_sensor_thread = threading.Thread(target=receiveUpdate,args=(conn,1024,key))
			conn.sendall(b'SUCCESS')

			receive_sensor_thread.start()
			cdr = (conn, addr)
			conns.append( cdr )
		else:
			rfid_thread = threading.Thread(target=rfidThread, args=(conn, 1024, key))
			conn.sendall(b'SUCCESS')
			rfid_thread.start()
			cdr = (conn, addr)
			conns.append( cdr )
		return True


	else:
		#TERMINATE CONNECTION
		print('Received Token:',token )
		print('Received Hash:', sha1.sha1(token))
		print("Expected Hash:", TOKENS[sensor_number-1])
		#print('Expected Token:', TOKENS[sensor_number])
		raise Exception(f"Invalid Connection {addr}")


def acceptConnection(socket):
	while ACCEPTING_CONNECTIONS:
		#STEP 1: Sensor Connects to Server
		conn, addr = socket.accept()

		print('Connected by', addr, 'Awaiting Validation')

		validate_thread = threading.Thread(target=validateConnection, args=(conn, addr))
		#recv_thread = threading.Thread(target=receiveAsync, args=(conn, 1024, None, conn_num))
		validate_thread.start()


if __name__ == '__main__':

	parser = argparse.ArgumentParser(description='Sensor')
	parser.add_argument("-s", "--server", type=str, default="127.0.0.1",
	                    help="Control Panel's server IP (default: 127.0.0.1)")
	parser.add_argument("-p", "--port", type=int, default=54321,
	                    help="port of the server to connect")
	args = parser.parse_args()

	IP = args.server
	PORT = args.port

	#establish server
	server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	#bind to the server
	server.bind( (IP, PORT) )

	#wait for sensors to connect
	server.listen()

	conn_thread = threading.Thread(target=acceptConnection, args=(server,))
	conn_thread.start()


	while len(conns) == 0:
		print("Waiting For sensors")
		time.sleep(1)
	while True:
		print(sensor_data)
		time.sleep(1)