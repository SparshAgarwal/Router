#!/usr/bin/env python3

from switchyard.lib.address import *
from switchyard.lib.packet import *
from switchyard.lib.common import *
from threading import *
from random import random
import time
import sys

class Middlebox:
	def __init__(self):
		self.ip = None
		self.drop_rate = None

		# Get arguments
		with open('middlebox_params.txt', 'r') as file:
			line = file.readline()
			args = line.split('-')

			for arg in args[1:]:
				arg_split = arg.strip().split()
				
				if len(arg_split) != 2:
					sys.exit("Invalid argument")

				name, value = arg_split[0], arg_split[1]

				try:
					if name == 'd':
						if float(value) < 0 or float(value) > 1:
							sys.exit("Illegal value: 0 <= drop_rate <= 1")
						self.drop_rate = float(value)
					else:
						sys.exit("Invalid arguments")
				except ValueError:
					sys.exit("Invalid arguments: ValueError(" + value + " is not an float)")

		if self.drop_rate == None:
			sys.exit("Wrong number of arguments")

	# Return true if packet should be dropped, false otherwise
	# Uses a random number generator
	def drop_packet(self):
		if random() <= self.drop_rate:
			return True
		else:
			return False

	def __str__(self):
		info = "Middlebox Info:\n"
		info += "Drop Rate: " + str(self.drop_rate) + "\n"

		return info

def switchy_main(net):
	middlebox = Middlebox()

	my_intf = net.interfaces()
	mymacs = [intf.ethaddr for intf in my_intf]
	myips = [intf.ipaddr for intf in my_intf]

	while True:
		gotpkt = True
		try:
			dev,pkt = net.recv_packet()
			log_debug("Device is {}".format(dev))
		except NoPackets:
			log_debug("No packets available in recv_packet")
			gotpkt = False
		except Shutdown:
			log_debug("Got shutdown signal")
			break

		if gotpkt:
			log_debug("I got a packet {}".format(pkt))

		if dev == "middlebox-eth0":
			log_debug("Received from blaster")
			'''
			Received data packet
			Should I drop it?
			If not, modify headers & send to blastee
			'''
			if not middlebox.drop_packet():
				net.send_packet("middlebox-eth1", pkt)
			# else:
				# print(str(int.from_bytes(pkt[3].to_bytes()[:4], byteorder='big')) + " dropped by middle box")
		elif dev == "middlebox-eth1":
			log_debug("Received from blastee")
			net.send_packet("middlebox-eth0", pkt)
			'''
			Received ACK
			Modify headers & send to blaster. Not dropping ACK packets!
			net.send_packet("middlebox-eth0", pkt)
			'''
		else:
			log_debug("Oops :))")

	net.shutdown()

