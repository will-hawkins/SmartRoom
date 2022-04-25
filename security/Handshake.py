import socket
import json
from security import RSA, tripleDES, sha1


def sensorHandshake( IP,PORT, TOKEN, sensor_number):
	server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	#STEP 1: Sensor Connects to Server
	print("=======Connecting To Server=======")
	server.connect( (IP,PORT) )

	#STEP 2: Receive RSA Params
	print("=======Receiving RSA Public Keys=======")
	data = server.recv(1024)
	public_keys = json.loads(data)

	#STEP 3: Send DES Key & Token
	print("=======Sending DES Key=======")
	key = tripleDES.genRandomKey(192)
	print("key:",int(key,2))
	DES_key_encrypted = RSA.encrypt(key,public_keys['e'],public_keys['N'])
	token_encrypted = tripleDES.tripleDESCBCEncryptAny(TOKEN, key)

	server.sendall(str.encode(json.dumps({'key': DES_key_encrypted, 'token': token_encrypted, 'sensor': sensor_number})))

	#STEP 4: Confirmation Handshake Was Successful

	verification = server.recv(1024)
	print(str(verification))

	return server, key
