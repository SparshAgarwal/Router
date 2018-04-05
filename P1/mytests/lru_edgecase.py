from switchyard.lib.testing import Scenario, PacketInputEvent, PacketOutputEvent, PacketInputTimeoutEvent
from switchyard.lib.packet import *

# Given two hexadecimal digits, create a generic packet with that number as the last 2 hexadecimal digits
def packet(src, dest):
    testpkt = Ethernet() + IPv4() + ICMP()
    testpkt[0].src = src
    testpkt[0].dst = dest
    testpkt[1].src = "192.168.100.1"
    testpkt[1].dst = "255.255.255.255"

    return testpkt

def create_scenario():
    s = Scenario("hub tests")
    s.add_interface('eth0', '10:00:00:00:00:01')
    s.add_interface('eth1', '10:00:00:00:00:02')
    s.add_interface('eth2', '10:00:00:00:00:03')

	# Make packet 01 the most recently used packet
	# Change the port of packet 01 from eth0 to eth1
	# This is to test if receiving a packet with 01 as the source will change only the port without affecting its position in the table
	# Then, push packet 01 to the least recently used and check if it is dropped from the table correctly
	# By receiving a packet (source:08, destination:01)
	# the entry 08 should be added and the entry 01 should be dropped, and the switch should broadcast the packet because 01 is not in the entry
	# At the same time, we also tested if the switch send packets out to all ports except for the source
	# If the switch send the packet out the correct port

    #Table [address:port]
    # Table [01:0]
    pkt = packet('30:00:00:00:00:01', 'ff:ff:ff:ff:ff:ff')
    s.expect(PacketInputEvent("eth0", pkt, display=Ethernet), "Arrive: eth0");
    s.expect(PacketOutputEvent("eth1", pkt, "eth2", pkt, display=Ethernet), "Forward: eth1, eth2")

    # Table [01:0][02:1]
    pkt = packet('30:00:00:00:00:02', 'ff:ff:ff:ff:ff:ff')
    s.expect(PacketInputEvent("eth1", pkt, display=Ethernet), "Arrive: eth1");
    s.expect(PacketOutputEvent("eth0", pkt, "eth2", pkt, display=Ethernet), "Forward: eth0, eth2")

    # Table [01:0][02:1][03:2]
    pkt = packet('30:00:00:00:00:03', 'ff:ff:ff:ff:ff:ff')
    s.expect(PacketInputEvent("eth2", pkt, display=Ethernet), "Arrive: eth2");
    s.expect(PacketOutputEvent("eth0", pkt, "eth1", pkt, display=Ethernet), "Forward: eth0, eth1")    

    # Table [01:0][02:1][03:2][04:0]
    pkt = packet('30:00:00:00:00:04', '10:00:00:00:00:01')
    s.expect(PacketInputEvent("eth0", pkt, display=Ethernet), "Arrive: eth0");
    s.expect(PacketInputTimeoutEvent(1.0), "Timeout: 1")

    # Table [02:1][03:2][04:0][05:1][01:0]
    pkt = packet('30:00:00:00:00:05', '30:00:00:00:00:01')
    s.expect(PacketInputEvent("eth1", pkt, display=Ethernet), "Arrive: eth1");
    s.expect(PacketOutputEvent("eth0", pkt, display=Ethernet), "Forward: eth0")

    # Table [02:1][03:2][04:0][05:1][01:1]
    pkt = packet('30:00:00:00:00:01', '10:00:00:00:00:01')
    s.expect(PacketInputEvent("eth1", pkt, display=Ethernet), "Arrive: eth1");
    s.expect(PacketInputTimeoutEvent(1.0), "Timeout: 1")

    # Table [04:0][05:1][01:1][06:2][03:2]
    pkt = packet('30:00:00:00:00:06', '30:00:00:00:00:03')
    s.expect(PacketInputEvent("eth2", pkt, display=Ethernet), "Arrive: eth2");
    s.expect(PacketOutputEvent("eth2", pkt, display=Ethernet), "Forward: eth2");

    # Table [01:1][06:2][03:2][07:0][05:1]
    pkt = packet('30:00:00:00:00:07', '30:00:00:00:00:05')
    s.expect(PacketInputEvent("eth0", pkt, display=Ethernet), "Arrive: eth0");
    s.expect(PacketOutputEvent("eth1", pkt, display=Ethernet), "Forward: eth1");

    # Table [06:2][03:2][07:0][05:1][08:0]
    pkt = packet('30:00:00:00:00:08', '30:00:00:00:00:01')
    s.expect(PacketInputEvent("eth0", pkt, display=Ethernet), "Arrive: eth0");
    s.expect(PacketOutputEvent("eth1", pkt, "eth2", pkt, display=Ethernet), "Forward: eth1, eth2");

    return s

scenario = create_scenario()