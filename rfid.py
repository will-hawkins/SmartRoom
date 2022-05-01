"""
This runs on RPi 1 which houses the RFID scanner
"""
import socket
import time
import threading
import json
import argparse

import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522

from security import RSA, DES, tripleDES
from security.Handshake import sensorHandshake

reader = SimpleMFRC522()

def scanRFID():
	id, rin = reader.read()
	return rin

def reject():
	#do stuff with LCD
	print("REJECTED")

TOKEN = 'Sensor1Password'

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Sensor')
	parser.add_argument("-s", "--server", type=str, default="127.0.0.1",
	                    help="Control Panel's server IP (default: 127.0.0.1)")
	parser.add_argument("-p", "--port", type=int, default=54321,
	                    help="port of the server to connect")
	args = parser.parse_args()

	IP = args.server
	PORT = args.port

	server, key = sensorHandshake(IP, PORT, TOKEN,1)

	while True:
		rin = scanRFID()

		payload = tripleDES.tripleDESCBCEncryptAny(rin, key)

		server.sendall(str.encode(payload))
	GPIO.cleanup()
