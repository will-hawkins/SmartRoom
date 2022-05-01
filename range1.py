"""
This runs on the RPi with Range sensor 1, The infrared sensor, and the light sensor
Data is collected from the sensors and sent to the control panel over TCP.
"""

import socket
import time
import threading
import json
import argparse

from security import RSA, DES, tripleDES
from security.Handshake import sensorHandshake

from src.HCSR04_lib import HCSR04
import RPi.GPIO as GPIO
import serial
TOKEN = 'Sensor2Password'
sensor_data = {}


def rangeThread():
	GPIO.setwarnings(False)
	GPIO.setmode(GPIO.BCM)
	GPIO.cleanup()

	TRIG = 4
	ECHO = 17

	GPIO.setup(TRIG, GPIO.OUT)
	instance = HCSR04(TRIG_pin=TRIG, ECHO_pin=ECHO)  # BCM17
	instance.init_HCSR04()
	while True:
		sensor_data['range1'] = instance.measure_distance()
		time.sleep(.03)


def sendData(conn, n, key, data):
	payload = tripleDES.tripleDESCBCEncryptAny(str.encode(json.dumps(data)), key)
	conn.sendall(str.encode(payload))


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Sensor')
	parser.add_argument("-s", "--server", type=str, default="127.0.0.1",
	                    help="Control Panel's server IP (default: 127.0.0.1)")
	parser.add_argument("-p", "--port", type=int, default=54321,
	                    help="port of the server to connect")
	args = parser.parse_args()

	IP = args.server
	PORT = args.port

	server, key = sensorHandshake(IP, PORT, TOKEN, 2)
	#Start Sensor Threads

	range_sensor_thread = threading.Thread(target=rangeThread)
	range_sensor_thread.start()

	while True:
		sendData(server, 1024, key, sensor_data)
		print(sensor_data)
		time.sleep(1)
