#!/usr/bin/env python3

from switchyard.lib.address import *
from switchyard.lib.packet import *
from switchyard.lib.common import *
from threading import *
import time
import sys

class Blastee:
	def __init__(self):
		self.ip = None
		self.num_packets = None

		# Get arguments
		with open('blastee_params.txt', 'r') as file:
			line = file.readline()
			args = line.split('-')

			for arg in args[1:]:
				arg_split = arg.strip().split()
				
				if len(arg_split) != 2:
					sys.exit("Invalid argument")

				name, value = arg_split[0], arg_split[1]

				try:
					if name == 'b':
						self.ip = value
					elif name == 'n':
						self.num_packets = int(value)
					else:
						sys.exit("Invalid arguments")
				except ValueError:
					sys.exit("Invalid arguments: ValueError(" + value + " is not an integer)")

		if self.ip == None or self.num_packets == None:
			sys.exit("Wrong number of arguments")

	def __str__(self):
		info = "Blastee Info:\n"
		info += "Blaster IP: " + str(self.ip) + "\n"
		info += "Number of packets: " + str(self.num_packets) + "\n"

		return info

def switchy_main(net):
	blastee = Blastee()

	my_interfaces = net.interfaces()
	mymacs = [intf.ethaddr for intf in my_interfaces]

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
			log_debug("I got a packet from {}".format(dev))
			log_debug("Pkt: {}".format(pkt))
			payload = pkt[3].to_bytes()[6:]
			pkt[3]= RawPacketContents(pkt[3].to_bytes()[:4])
			if len(payload)<8:
				payload = RawPacketContents(payload+('0'*(8-len(payload))))
			else:
				payload = RawPacketContents(payload[:8])
			pkt+= payload
			# print(pkt)
			net.send_packet(my_interfaces[0].name, pkt)


	net.shutdown()