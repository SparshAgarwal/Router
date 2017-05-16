from switchyard.lib.testing import Scenario, PacketInputEvent, PacketOutputEvent, PacketInputTimeoutEvent
from switchyard.lib.packet import *
from switchyard.lib.common import *
from switchyard.lib.address import *

def create_packet(srceth, desteth, srcip, destip):
	testpkt = Ethernet() + IPv4() + ICMP()
	testpkt[0].src = srceth
	testpkt[0].dst = desteth
	testpkt[1].src = srcip
	testpkt[1].dst = destip

	return testpkt

def construct_icmp(packet, input_port, port_src, icmp_type, icmp_code=None):
		# Construct new icmp_header with the first 28 bytes of the packet as data (Ethernet header not included)
		new_packet = IPv4() + packet[2]
		new_packet[IPv4].dst = packet[IPv4].dst
		new_packet[IPv4].src = packet[IPv4].src
		new_packet[IPv4].ttl = packet[IPv4].ttl - 1
		icmp_header = ICMP(icmptype=icmp_type)
		icmp_header.icmpdata.data = new_packet.to_bytes()[:28]

		if icmp_code:
			icmp_header.icmpcode = icmp_code

		ip_header = IPv4()
		ip_header.ttl = 32
		ip_header.src, ip_header.dst = port_src, new_packet[IPv4].src

		return Ethernet() + ip_header + icmp_header

def construct_icmp_ttl(packet, input_port, port_src, icmp_type, icmp_code=None):
		# Construct new icmp_header with the first 28 bytes of the packet as data (Ethernet header not included)
		new_packet = IPv4() + packet[2]
		new_packet[IPv4].dst = packet[IPv4].dst
		new_packet[IPv4].src = packet[IPv4].src
		new_packet[IPv4].ttl = packet[IPv4].ttl
		icmp_header = ICMP(icmptype=icmp_type)
		icmp_header.icmpdata.data = new_packet.to_bytes()[:28]

		if icmp_code:
			icmp_header.icmpcode = icmp_code

		ip_header = IPv4()
		ip_header.ttl = 32
		ip_header.src, ip_header.dst = port_src, new_packet[IPv4].src

		return Ethernet() + ip_header + icmp_header

def create_scenario():
	s = Scenario("switch tests")
	s.add_interface("router-eth0", "30:00:00:00:00:01", "10.1.1.1", "255.255.255.0")
	s.add_interface("router-eth1", "30:00:00:00:00:02", "10.1.1.2", "255.255.255.0")
	s.add_interface("router-eth2", "30:00:00:00:00:03", "10.1.1.3", "255.255.255.0")

	# Test 1: Test if Router reply Arp_Request with IP that is destined for the Router's interface
	arpreq = create_ip_arp_request("20:00:00:00:00:01", "11.1.1.1", "10.1.1.1")
	s.expect(PacketInputEvent("router-eth0", arpreq), "Incoming ARP request")
	arprep = create_ip_arp_reply("30:00:00:00:00:01", "20:00:00:00:00:01", "10.1.1.1", "11.1.1.1")
	s.expect(PacketOutputEvent("router-eth0", arprep), "Outgoing ARP reply")

	arpreq = create_ip_arp_request("20:00:00:00:00:02", "11.1.1.2", "10.1.1.2")
	s.expect(PacketInputEvent("router-eth1", arpreq), "Incoming ARP request")
	arprep = create_ip_arp_reply("30:00:00:00:00:02", "20:00:00:00:00:02", "10.1.1.2", "11.1.1.2")
	s.expect(PacketOutputEvent("router-eth1", arprep), "Outgoing ARP reply")

	arpreq = create_ip_arp_request("20:00:00:00:00:03", "11.1.1.3", "10.1.1.3")
	s.expect(PacketInputEvent("router-eth2", arpreq), "Incoming ARP request")
	arprep = create_ip_arp_reply("30:00:00:00:00:03", "20:00:00:00:00:03", "10.1.1.3", "11.1.1.3")
	s.expect(PacketOutputEvent("router-eth2", arprep), "Outgoing ARP reply")

	arpreq = create_ip_arp_request("20:00:00:00:00:03", "11.1.1.3", "10.1.1.3")
	s.expect(PacketInputEvent("router-eth2", arpreq), "Incoming ARP request")
	arprep = create_ip_arp_reply("30:00:00:00:00:03", "20:00:00:00:00:03", "10.1.1.3", "11.1.1.3")
	s.expect(PacketOutputEvent("router-eth2", arprep), "Outgoing ARP reply")	

	# Test 2: Router should ignore Arp_Request with IP that is not for the Router's interface
	packet = create_ip_arp_request("20:00:00:00:00:01", "11.1.1.1", "11.1.1.4")
	s.expect(PacketInputEvent("router-eth0", packet), "Incoming ARP request")

	packet = create_ip_arp_request("20:00:00:00:00:04", "11.1.1.4", "20.11.1.5")
	s.expect(PacketInputEvent("router-eth0", packet), "Incoming ARP request")

	# Create forwarding table for the rest of the tests
	with open("forwarding_table.txt", 'w') as f:
		f.write("172.16.0.0 255.255.0.0 192.168.1.2 router-eth0\n")
		f.write("172.16.128.0 255.255.255.0 10.10.0.254 router-eth0\n")
		f.write("172.16.64.0 255.255.255.0 10.10.1.254 router-eth1\n")
		f.write("10.100.0.0 255.255.0.0 155.24.42.2 router-eth2\n")

	# Test 3: Send only 1 Arp_Request
	pkt = create_packet("40:00:00:00:00:03","30:00:00:00:00:03", "11.1.2.5", "172.16.64.73")
	pkt[IPv4].ttl = 36
	s.expect(PacketInputEvent("router-eth1", pkt), "Incoming packet")

	arp_req = create_ip_arp_request("30:00:00:00:00:02","10.1.1.2","10.10.1.254")
	s.expect(PacketOutputEvent("router-eth1", arp_req), "Outgoing ARP request")
	
	# Receive Arp_Reply
	arprep = create_ip_arp_reply("55:10:10:00:00:01", "30:00:00:00:00:02", "10.10.1.254", "10.1.1.2")
	s.expect(PacketInputEvent("router-eth0", arprep),"Incoming arp reply")
	send_pkt = create_packet("30:00:00:00:00:02","55:10:10:00:00:01", "11.1.2.5", "172.16.64.73")
	send_pkt[IPv4].ttl = 35
	s.expect(PacketOutputEvent("router-eth1", send_pkt), "Outgoing Packet")

	# Test 4: Send 5 Arp_Request with Arp_reply received
	# pkt = create_packet("40:00:00:00:00:03","30:00:00:00:00:03", "11.1.1.3", "172.16.0.0")
	# pkt[IPv4].ttl = 36
	# s.expect(PacketInputEvent("router-eth1", pkt), "Incoming packet")

	# arp_req = create_ip_arp_request("30:00:00:00:00:01","10.1.1.1","192.168.1.2")
	# s.expect(PacketOutputEvent("router-eth0", arp_req), "Outgoing ARP request")
	# s.expect(PacketInputTimeoutEvent(1), "Timeout = 1s, waiting for arp_reply")

	# s.expect(PacketOutputEvent("router-eth0", arp_req), "Outgoing ARP request")
	# s.expect(PacketInputTimeoutEvent(1), "Timeout = 1s, waiting for arp_reply")

	# s.expect(PacketOutputEvent("router-eth0", arp_req), "Outgoing ARP request")
	# s.expect(PacketInputTimeoutEvent(1), "Timeout = 1s, waiting for arp_reply")

	# s.expect(PacketOutputEvent("router-eth0", arp_req), "Outgoing ARP request")
	# s.expect(PacketInputTimeoutEvent(1), "Timeout = 1s, waiting for arp_reply")

	# s.expect(PacketOutputEvent("router-eth0", arp_req), "Outgoing ARP request")

	# # Receive Arp_Reply
	# arprep = create_ip_arp_reply("22:11:00:00:00:11", "30:00:00:00:00:03", "192.168.1.2", "10.1.1.1")
	# s.expect(PacketInputEvent("router-eth3", arprep),"Incoming arp reply")
	# send_pkt = create_packet("30:00:00:00:00:01","22:11:00:00:00:11", "11.1.1.3", "172.16.0.0")
	# send_pkt[IPv4].ttl = 35
	# s.expect(PacketOutputEvent("router-eth0", send_pkt), "Outgoing Packet")

	# Test 5: Router should forward the packet without sending an Arp_Request because the mac,ip is already in the cache
	# Test 6: At the same time this test also tested for the longest matching ip in the forwarding table
	# between 172.16.0.0 and 172.16.64.0, it should match 172.16.64.0 instead of 172.16.0.0
	pkt = create_packet("40:00:00:00:00:03","30:00:00:00:00:03", "11.1.1.5", "172.16.64.173")
	pkt[IPv4].ttl = 36
	s.expect(PacketInputEvent("router-eth1", pkt), "Incoming packet")

	send_pkt = create_packet("30:00:00:00:00:02","55:10:10:00:00:01", "11.1.1.5", "172.16.64.173")
	send_pkt[IPv4].ttl = 35
	s.expect(PacketOutputEvent("router-eth1", send_pkt), "Outgoing Packet")

	# Test 6: Send 5 Arp_Request with no Arp_reply received, it should send and ICMP error with
	# ICMP type: destination unreachable, ICMP code: host unreachable
	pkt = create_packet("40:00:00:00:00:03","30:00:00:00:00:03", "10.100.5.6", "172.16.0.4")
	pkt[IPv4].ttl = 36
	s.expect(PacketInputEvent("router-eth1", pkt), "Incoming packet")

	arp_req = create_ip_arp_request("30:00:00:00:00:01","10.1.1.1","192.168.1.2")
	s.expect(PacketOutputEvent("router-eth0", arp_req), "Outgoing ARP request")
	s.expect(PacketInputTimeoutEvent(1), "Timeout = 1s, waiting for arp_reply")

	s.expect(PacketOutputEvent("router-eth0", arp_req), "Outgoing ARP request")
	s.expect(PacketInputTimeoutEvent(1), "Timeout = 1s, waiting for arp_reply")

	s.expect(PacketOutputEvent("router-eth0", arp_req), "Outgoing ARP request")
	s.expect(PacketInputTimeoutEvent(1), "Timeout = 1s, waiting for arp_reply")

	s.expect(PacketOutputEvent("router-eth0", arp_req), "Outgoing ARP request")
	s.expect(PacketInputTimeoutEvent(1), "Timeout = 1s, waiting for arp_reply")

	s.expect(PacketOutputEvent("router-eth0", arp_req), "Outgoing ARP request")
	s.expect(PacketInputTimeoutEvent(1), "Timeout = 1s, waiting for arp_reply")

	# No arp_reply received, construct icmp error
	arp_req = create_ip_arp_request("30:00:00:00:00:02","10.1.1.2", "10.100.5.6")
	s.expect(PacketOutputEvent("router-eth1", arp_req), "Outgoing ARP request")

	arprep = create_ip_arp_reply("44:44:44:44:44:44", "30:00:00:00:00:02", "10.100.5.6", "10.1.1.2")
	s.expect(PacketInputEvent("router-eth2", arprep),"Incoming arp reply")

	icmp_type = ICMPType.DestinationUnreachable
	icmp_code = ICMPTypeCodeMap[icmp_type].HostUnreachable
	send_pkt = construct_icmp(pkt, "router-eth2", "10.1.1.2", icmp_type, icmp_code)
	send_pkt[Ethernet].src = "30:00:00:00:00:02"
	send_pkt[Ethernet].dst = "44:44:44:44:44:44"
	s.expect(PacketOutputEvent("router-eth1", send_pkt), "Outgoing Packet")

	# Test 7: TTL = 0 error, ICMP type: time exceeded, ICMP Code: ttl expired
	pkt = create_packet("40:00:00:00:00:03","30:00:00:00:00:03", "10.100.5.6", "172.16.0.4")
	pkt[IPv4].ttl = 1
	s.expect(PacketInputEvent("router-eth1", pkt), "Incoming packet")

	icmp_type = ICMPType.TimeExceeded
	icmp_code = ICMPTypeCodeMap[icmp_type].TTLExpired
	send_pkt = construct_icmp_ttl(pkt, "router-eth2", "10.1.1.2", icmp_type, icmp_code)
	send_pkt[Ethernet].src = "30:00:00:00:00:02"
	send_pkt[Ethernet].dst = "44:44:44:44:44:44"
	s.expect(PacketOutputEvent("router-eth1", send_pkt), "Outgoing Packet")

	# Test 8: No Match in forwarding table error, ICMP Type: destination unreachable, ICMP Code: 
	pkt = create_packet("40:00:00:00:00:03","30:00:00:00:00:03", "10.100.5.6", "111.111.111.111")
	pkt[IPv4].ttl = 36
	s.expect(PacketInputEvent("router-eth1", pkt), "Incoming packet")

	icmp_type = ICMPType.DestinationUnreachable
	icmp_code = ICMPTypeCodeMap[icmp_type].NetworkUnreachable
	send_pkt = construct_icmp_ttl(pkt, "router-eth2", "10.1.1.2", icmp_type, icmp_code)
	send_pkt[Ethernet].src = "30:00:00:00:00:02"
	send_pkt[Ethernet].dst = "44:44:44:44:44:44"
	s.expect(PacketOutputEvent("router-eth1", send_pkt), "Outgoing Packet")

	# Test 9: Packet assigned to router's interface but it is not an arp_header or icmp echo request
	pkt = create_packet("40:00:00:00:00:03","30:00:00:00:00:03", "10.100.5.6", "111.111.111.111")
	pkt[ICMP].icmptype = ICMPType.TimeExceeded
	pkt[IPv4].ttl = 36
	s.expect(PacketInputEvent("router-eth1", pkt), "Incoming packet")

	icmp_type = ICMPType.DestinationUnreachable
	icmp_code = ICMPTypeCodeMap[icmp_type].NetworkUnreachable
	send_pkt = construct_icmp_ttl(pkt, "router-eth2", "10.1.1.2", icmp_type, icmp_code)
	send_pkt[Ethernet].src = "30:00:00:00:00:02"
	send_pkt[Ethernet].dst = "44:44:44:44:44:44"
	s.expect(PacketOutputEvent("router-eth1", send_pkt), "Outgoing Packet")

	# Test 10: Respond to ICMP Echo Requests
	tpkt = create_packet("55:10:10:00:00:01","30:00:00:00:00:02", "172.16.64.173", "10.1.1.1")
	tpkt[IPv4].ttl = 36
	tpkt[ICMP].icmptype = ICMPType.EchoRequest
	s.expect(PacketInputEvent("router-eth1", tpkt), "Incoming packet")

	icmp_header = tpkt[ICMP]
	icmp_data = icmp_header.icmpdata

	icmp_reply_header = ICMP(icmptype=ICMPType.EchoReply)
	reply_data = icmp_reply_header.icmpdata
	reply_data.identifier = icmp_data.identifier
	reply_data.sequence = icmp_data.sequence
	reply_data.data = icmp_data.data

	ip_header = IPv4()
	ip_header.src, ip_header.dst = tpkt[IPv4].dst, tpkt[IPv4].src
	ip_header.ttl = 32

	icmp_reply = tpkt[Ethernet] + ip_header + icmp_reply_header
	icmp_reply[Ethernet].src, icmp_reply[Ethernet].dst = icmp_reply[Ethernet].dst, icmp_reply[Ethernet].src

	s.expect(PacketOutputEvent("router-eth1", icmp_reply), "Outgoing Packet")
	return s


scenario = create_scenario()

