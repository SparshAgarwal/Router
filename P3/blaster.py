#!/usr/bin/env python3

from switchyard.lib.address import *
from switchyard.lib.packet import *
from switchyard.lib.common import *
from random import randint
import time
import sys

class Blaster:
	def __init__(self):
		self.ip = None
		self.num_packets = None
		self.length = None
		self.win_size = None
		self.timeout = None
		self.recv_timeout = None

		# Get arguments
		with open('blaster_params.txt', 'r') as file:
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
					elif name == 'l':
						if int(value) < 0 or int(value) > 65535:
							sys.exit("Length must be in the range of 0 <= length <= 65535")
						self.length = int(value)
						
						# Limits the payload size because switchyard won't allow a packet that large
						if self.length >= 1400:
							self.payload = (b'x')*1400
						else:
							self.payload = (b'x')*self.length
					elif name == 'w':
						self.win_size = int(value)
					elif name == 't':
						self.timeout = int(value)/1000
					elif name =='r':
						self.recv_timeout = int(value)/1000
					else:
						sys.exit("Invalid arguments")
				except ValueError:
					sys.exit("Invalid arguments: ValueError(" + value + " is not an integer)")

		if self.ip == None or self.num_packets == None or self.length == None or self.win_size == None or self.timeout == None or self.recv_timeout == None:
			sys.exit("Wrong number of arguments")

		# Set up window stuff
		self.lhs = 1
		self.rhs = 0
		self.has_packet = False
		self.time = time.time()

		# Buffer to keep track of acknowledge packet
		# Key = packet number, Value = Ack received
		self.buf = {}
		# Packets to be retransmitted
		self.re_packets = []

		# Stats for printing
		self.first_packet_sent = False
		self.total_time_start = None
		self.total_time_end = None
		self.number_of_retransmitted_packet = 0
		self.number_of_coarse_timeouts = 0
		self.num_ack_received = 0

	# Return the next sequence number to be sent
	# Return None if no packet need to be sent
	def next_packet(self):
		# If LHS timeout
		if time.time() - self.time > self.timeout:
			self.number_of_coarse_timeouts += 1
			for seq, ack in self.buf.items():
				# If packet has not been acknowledged
				if not ack:
					self.re_packets += [seq]
					self.number_of_retransmitted_packet += 1

			self.time = time.time()

		if self.re_packets:
			return self.re_packets.pop(0)

		if self.rhs < self.num_packets and self.rhs - self.lhs + 1 < self.win_size:
			self.rhs += 1
			self.buf[self.rhs] = False
			return self.rhs

	# Receive acknowledge packet with sequence number = num
	def receive_ack(self, num):
		self.total_time_end = time.time()

		if num in self.buf:
			self.buf[num] = True

		self.increment_lhs()

	# Increment lhs only if the acknowledgement for the packet is received
	def increment_lhs(self):
		while True:
			if self.lhs in self.buf :
				if self.buf[self.lhs]:
					del self.buf[self.lhs]
					self.num_ack_received += 1
					self.lhs += 1
					self.time = time.time() # Reset timeout when LHS moves
				else:
					break
			else:
				break

	def __str__(self):
		info = "Blaster Info:\n"
		info += "Blastee IP: " + str(self.ip) + "\n"
		info += "Number of packets: " + str(self.num_packets) + "\n"
		info += "Length of variable payload: " + str(self.length) + "\n"
		info += "Window size: " + str(self.win_size) + "\n"
		info += "Timeout: " + str(self.timeout) + "\n"
		info += "Recv_timeout: " + str(self.recv_timeout) + "\n"

		return info

class header_x:
	def __init__(self, seq=-1, length=-1):
		self.seq = seq
		self.length = length

def switchy_main(net):
	blaster = Blaster()

	my_intf = net.interfaces()
	mymacs = [intf.ethaddr for intf in my_intf]
	myips = [intf.ipaddr for intf in my_intf]

	while True:
		gotpkt = True
		try:
			#Timeout value will be parameterized!
			dev,pkt = net.recv_packet(timeout=blaster.recv_timeout)
		except NoPackets:
			log_debug("No packets available in recv_packet")
			gotpkt = False
		except Shutdown:
			log_debug("Got shutdown signal")
			break
		if gotpkt:
			log_debug("I got a packet")
			byte_string = pkt[3].to_bytes()
			seq = int.from_bytes(byte_string[:4], byteorder='big')
			# print("Receive ack: " + str(seq))
			blaster.receive_ack(seq)
		else:
			log_debug("Didn't receive anything")

			# print(blaster.num_ack_received)

			if blaster.num_packets <= blaster.num_ack_received:
				total_time = blaster.total_time_end - blaster.total_time_start
				total_bytes = (blaster.number_of_retransmitted_packet + blaster.num_packets) * blaster.length
				good_bytes = blaster.num_packets * blaster.length
				throughput = total_bytes / total_time
				goodput = good_bytes / total_time
				print("Total TX time (in seconds): " + str(total_time))
				print("Number of reTX: " + str(blaster.number_of_retransmitted_packet))
				print("Number of coarse TOs: " + str(blaster.number_of_coarse_timeouts))
				print("Throughput (Bps): " + str(throughput))
				print("Goodput (Bps): " + str(goodput))
				break

			'''
			Creating the headers for the packet
			'''
			seq = blaster.next_packet()

			if seq:
				# print("Send packet: " + str(seq))
				seq_bytes = seq.to_bytes(4, byteorder='big')
				length_bytes = blaster.length.to_bytes(2, byteorder='big')

				pkt = Ethernet() + IPv4() + UDP() + RawPacketContents(seq_bytes + length_bytes) + RawPacketContents(blaster.payload)
				pkt[0].src = mymacs[0]
				pkt[0].dst = '20:00:00:00:00:00'
				pkt[1].src = myips[0]
				pkt[1].dst = blaster.ip
				pkt[1].protocol = IPProtocol.UDP
				pkt[2].srcport = 4444
				pkt[2].dstport = 8888

				# Keep track of stats
				if not blaster.first_packet_sent:
					blaster.total_time_start = time.time()
					blaster.first_packet_sent = True
				
				net.send_packet(my_intf[0].name, pkt)

			'''
			Do other things here and send packet
			'''

	net.shutdown()
