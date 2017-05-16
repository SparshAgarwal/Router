#!/usr/bin/env python3
'''
Router
'''

import sys
import os
import time
from threading import Thread, Lock
from switchyard.lib.packet import *
from switchyard.lib.address import *
from switchyard.lib.common import *

# Class to handle arp_request, constructing and sending ip packets
class arp_req:
		# packet = (packet, input_port), input_port is used to keep track of the packet's input port when sending icmp error
		def __init__(self, target_ip, interface, packet, net, interfaces_mapping):
			self.target_ip = target_ip
			self.interface = interface
			self.time = time.time() - 1
			self.count = 0
			self.packets = [packet]
			self.net = net
			self.interfaces_mapping = interfaces_mapping

		# Send a new arp_request if every one second, if it exceeds five times, drop the packet
		def send_arp_request(self):
			if self.count >= 5:
				return False

			if time.time() - self.time > 1:
				request_packet = create_ip_arp_request(self.interfaces_mapping[self.interface][0], self.interfaces_mapping[self.interface][1], self.target_ip)
				self.net.send_packet(self.interface, request_packet)
				self.time = time.time()
				self.count += 1

			return True

		# Add a new packet to the queue
		def add_packet_to_queue(self, packet):
			self.packets += [packet]

		# Send all the packets in queue
		def send_packets(self, mac_addr):
			for packet, input_port in self.packets:
				eth_header = packet[Ethernet]
				eth_header.src = self.interfaces_mapping[self.interface][0]
				eth_header.dst = mac_addr
				self.net.send_packet(self.interface, packet)

		def get_packets(self):
			return self.packets

class Router(object):
	def __init__(self, net):
		self.net = net
		self.interfaces_list = net.interfaces()

		# List of interfaces_ip
		self.interfaces_ip = [intf.ipaddr for intf in self.interfaces_list]

		# Maping of eth name to mac address and ip
		self.interfaces_mapping = {intf.name:(intf.ethaddr,intf.ipaddr) for intf in self.interfaces_list}

		# Map ip to mac address
		self.ip_mapping = {}
		for mac,ip in self.interfaces_mapping.values():
			self.ip_mapping[ip] = mac

		# Load forwarding table = (prefix, mask, next_hop_ip, interface, prefix_length)
		# Load from file
		self.forwarding_table = []

		try:
			with open('forwarding_table.txt', 'r') as file:
				for line in file:
					row = line.strip().split(" ")
					self.forwarding_table += [(IPv4Address(row[0]), IPv4Address(row[1]), IPv4Address(row[2]), row[3], IPv4Network(row[0] + '/' + row[1]).prefixlen)]
		except FileNotFoundError:
			print("forwarding_table.txt does not exist")

		# Load from interfaces
		for i in self.interfaces_list:
			prefix = IPv4Address(int(i.ipaddr) & int(i.netmask))
			self.forwarding_table += [(prefix, i.netmask, i.ipaddr, i.name, IPv4Network(str(prefix) + '/' + str(i.netmask)).prefixlen)]

		# Queue of Key,Value pair, to store arp replies
		# Key = target_ip, Value = [arp_req]
		# arp_req is a class that handles arp_request, construct ip packets and send ip packets
		self.arp_queue = []

		self.got_arp_response = False


	def router_main(self):    
		'''
		Main method for router
		'''
		while True:
			try:
				hasError = False

				if not self.got_arp_response:
					for i,(ip,arp) in enumerate(self.arp_queue):
						# Send arp request
						if not arp.send_arp_request():
							# If five request is already sent, drop arp_req item and send icmp error
							error_packets = arp.get_packets()
							del self.arp_queue[i]
							
							icmp_type = ICMPType.DestinationUnreachable
							icmp_code = ICMPTypeCodeMap[icmp_type].HostUnreachable	
							for packet, input_port in error_packets:
								if input_port:
									# input_port used to remove loop if there is no arp_reply from both source and destination
									target_ip, packet, intf = self.construct_icmp_error(packet, input_port, icmp_type, icmp_code)
									self.send_packet(target_ip, intf, packet, None)

							hasError = True

				if not hasError:
					self.got_arp_response = False
					input_port,packet = self.net.recv_packet(timeout=1)
				else:
					continue

			except NoPackets:
				# print("No packet available")
				continue
			except Shutdown:
				# print("Shutdown signal detected, exiting.")
				break

			arp_header = packet.get_header(Arp)
			if arp_header:
				self.got_arp_response = False
				# If it is an arp packet
				if arp_header.operation == ArpOperation.Request:
					# If it is an arp request
					# Map the (ip, mac)
					self.ip_mapping[arp_header.senderprotoaddr] = arp_header.senderhwaddr
					# Send arp reply if target ip is one of the router's interface ip
					self.send_arp_reply(arp_header, input_port)

				elif arp_header.operation == ArpOperation.Reply:
					# If it is an arp reply
					target_ip = arp_header.senderprotoaddr
					mac_addr = arp_header.senderhwaddr

					for i,(ip,arp) in enumerate(self.arp_queue):
						if ip == target_ip:
							arp.send_packets(mac_addr)
							del self.arp_queue[i]
							self.ip_mapping[target_ip] = mac_addr
							break

					self.got_arp_response = True
			else:
				self.got_arp_response = False
				# Reduce ttl and get target ip
				ip_header = packet[IPv4]
				target_ip = ip_header.dst

				# If the packet is for the router's interface
				if target_ip in self.interfaces_ip:
					# If packet is an icmp echo request
					icmp_header = packet.get_header(ICMP)
					not_icmp_echo_request = False

					if icmp_header:
						if icmp_header.icmptype == ICMPType.EchoRequest:
							target_ip, packet = self.construct_icmp_reply(packet)
						else:
							not_icmp_echo_request = True
					else:
						not_icmp_echo_request = True

					if not_icmp_echo_request:
						# Packet destined for router's interface but it is not a ICMP echo request packet
						icmp_type = ICMPType.DestinationUnreachable
						icmp_code = ICMPTypeCodeMap[icmp_type].PortUnreachable	
						target_ip, packet, intf = self.construct_icmp_error(packet, input_port, icmp_type, icmp_code)

				# Check for a match in forwarding table
				target_ip,intf = self.get_best_match(target_ip)

				# Does not match any entry in the forwarding table
				if not target_ip:
					icmp_type = ICMPType.DestinationUnreachable
					icmp_code = ICMPTypeCodeMap[icmp_type].NetworkUnreachable
					target_ip, packet, intf = self.construct_icmp_error(packet, input_port, icmp_type, icmp_code)
				else:
					# Decrement ttl after forward table lookup and send an icmp error if ttl is 0
					if ip_header.ttl <= 1:
						icmp_type = ICMPType.TimeExceeded
						icmp_code = ICMPTypeCodeMap[icmp_type].TTLExpired
						target_ip, packet, intf = self.construct_icmp_error(packet, input_port, icmp_type, icmp_code)
					else:
						ip_header.ttl -= 1

				self.send_packet(target_ip, intf, packet, input_port)

	# Send packet, add packet to arp_request queue if ip is not in the cache
	def send_packet(self, target_ip, intf, packet, input_port):
		if target_ip:
			# If target_ip is in the cache
			if target_ip in self.ip_mapping:
				eth_header = packet[Ethernet]
				eth_header.src = self.interfaces_mapping[intf][0]
				eth_header.dst = self.ip_mapping[target_ip]
				self.net.send_packet(intf, packet)
				return

			# Add arp_req to queue or add packet if target_ip already exists as a key
			exist = False
			for ip,arp in self.arp_queue:
				if ip == target_ip:
					arp.add_packet_to_queue((packet, input_port))
					exist = True
					break

			if not exist:
				self.arp_queue  += [(target_ip,arp_req(target_ip, intf, (packet, input_port), self.net, self.interfaces_mapping))]

	# Construct an icmp_error packet, given the type of error and the error code
	def construct_icmp_error(self, packet, input_port, icmp_type, icmp_code=None):
		# Construct new icmp_header with the first 28 bytes of the packet as data (Ethernet header not included)
		icmp_header = ICMP(icmptype=icmp_type)
		del packet[Ethernet]
		icmp_header.icmpdata.data = packet.to_bytes()[:28]

		if icmp_code:
			icmp_header.icmpcode = icmp_code

		ip_header = IPv4()
		ip_header.ttl = 32
		ip_header.src, ip_header.dst = self.interfaces_mapping[input_port][1], packet[IPv4].src

		return ip_header.dst, Ethernet() + ip_header + icmp_header, input_port


	def construct_icmp_reply(self, packet):
		icmp_header = packet[ICMP]
		icmp_data = icmp_header.icmpdata

		icmp_reply_header = ICMP(icmptype=ICMPType.EchoReply)
		reply_data = icmp_reply_header.icmpdata
		reply_data.identifier = icmp_data.identifier
		reply_data.sequence = icmp_data.sequence
		reply_data.data = icmp_data.data

		ip_header = packet[IPv4]
		ip_header.src, ip_header.dst = ip_header.dst, ip_header.src
		ip_header.ttl = 32

		return ip_header.dst, packet[Ethernet] + ip_header + icmp_reply_header


	# Given the target_ip, return the best match for the ip address, return None if no match is found
	# best_match = (next_hop_ip, interface, prefix_length)
	def get_best_match(self, target_ip):
		best_match = None
		for pfx, mask, n_ip, intf, pfx_len in self.forwarding_table:
			if int(target_ip) & int(mask) == int(pfx):
				# Look for best match by comparing the prefix length
				if not best_match:
					best_match = (n_ip, intf, pfx_len)
				else:
					if best_match[2] < pfx_len:
						best_match = (n_ip, intf, pfx_len)

		# If best_match is found
		# best_match = [next_hop_ip, interface, prefix_length]
		if best_match:
			if best_match[0] in self.interfaces_ip:
				return target_ip,best_match[1]
			else:
				return best_match[0],best_match[1]

		return None,None

	# Given the arp_header and input_port
	# Send an Arp reply our the input_port if the target ip of the arp_header matches any of the router's interface ip
	def send_arp_reply(self, arp_header, input_port):
		# Look for interface ip that matches the arp request
		target_ip = arp_header.targetprotoaddr
		if target_ip in self.interfaces_ip:
			reply_packet = create_ip_arp_reply(self.ip_mapping[target_ip], arp_header.senderhwaddr, target_ip, arp_header.senderprotoaddr)
			self.net.send_packet(input_port, reply_packet)

def switchy_main(net):
	'''
	Main entry point for router.  Just create Router
	object and get it going.
	'''
	router = Router(net)
	router.router_main()
	net.shutdown()
	# router.debug()
