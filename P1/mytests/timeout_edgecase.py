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

    # [address:port]
    # [01:0]
    # [01:0][02:1]
    # [01:0][02:1][03:2]
    # [01:0][02:1][03:2][04:0]        
    # [02:1][03:2][04:0][05:1][01:0:1]    
    # Add five entries
    # Change port of entry 01 to eth1 and test to see if the entry is correct
    # [02:1][03:2][04:0][05:1][01:1]
    # [02:1][03:2][04:0][05:1][01:1]
    # Send packet to all destination 01-05 once to refresh the timeout
    # Delay for 7s, entry should still be in the table
    # [02:1][03:2][04:0][05:1][01:1]
    # Delay for 10s, entry should not be there anymore

    #Table [address:port]
    pkt = packet('30:00:00:00:00:01', 'ff:ff:ff:ff:ff:ff')
    s.expect(PacketInputEvent("eth0", pkt, display=Ethernet), "Arrive: eth0");
    s.expect(PacketOutputEvent("eth1", pkt, "eth2", pkt, display=Ethernet), "Forward: eth1, eth2")

    pkt = packet('30:00:00:00:00:02', 'ff:ff:ff:ff:ff:ff')
    s.expect(PacketInputEvent("eth1", pkt, display=Ethernet), "Arrive: eth1");
    s.expect(PacketOutputEvent("eth0", pkt, "eth2", pkt, display=Ethernet), "Forward: eth0, eth2")

    pkt = packet('30:00:00:00:00:03', 'ff:ff:ff:ff:ff:ff')
    s.expect(PacketInputEvent("eth2", pkt, display=Ethernet), "Arrive: eth2");
    s.expect(PacketOutputEvent("eth0", pkt, "eth1", pkt, display=Ethernet), "Forward: eth0, eth1")    

    pkt = packet('30:00:00:00:00:04', '10:00:00:00:00:01')
    s.expect(PacketInputEvent("eth0", pkt, display=Ethernet), "Arrive: eth0");
    s.expect(PacketInputTimeoutEvent(1.0), "Timeout: 1")

    pkt = packet('30:00:00:00:00:05', '30:00:00:00:00:01')
    s.expect(PacketInputEvent("eth1", pkt, display=Ethernet), "Arrive: eth1");
    s.expect(PacketOutputEvent("eth0", pkt, display=Ethernet), "Forward: eth0")

    pkt = packet('30:00:00:00:00:01', '10:00:00:00:00:01')
    s.expect(PacketInputEvent("eth1", pkt, display=Ethernet), "Arrive: eth1");
    s.expect(PacketInputTimeoutEvent(1.0), "Timeout: 1")

    pkt = packet('30:00:00:00:00:05', '30:00:00:00:00:01')
    s.expect(PacketInputEvent("eth1", pkt, display=Ethernet), "Arrive: eth1");
    s.expect(PacketOutputEvent("eth1", pkt, display=Ethernet), "Forward: eth1");

    pkt = packet('30:00:00:00:00:06', '30:00:00:00:00:01')
    s.expect(PacketInputEvent("eth0", pkt, display=Ethernet), "Arrive: eth0");
    s.expect(PacketOutputEvent("eth1", pkt, display=Ethernet), "Forward: eth1");

    pkt = packet('30:00:00:00:00:06', '30:00:00:00:00:02')
    s.expect(PacketInputEvent("eth0", pkt, display=Ethernet), "Arrive: eth0");
    s.expect(PacketOutputEvent("eth1", pkt, display=Ethernet), "Forward: eth1");

    pkt = packet('30:00:00:00:00:06', '30:00:00:00:00:03')
    s.expect(PacketInputEvent("eth0", pkt, display=Ethernet), "Arrive: eth0");
    s.expect(PacketOutputEvent("eth2", pkt, display=Ethernet), "Forward: eth2");

    pkt = packet('30:00:00:00:00:06', '30:00:00:00:00:04')
    s.expect(PacketInputEvent("eth0", pkt, display=Ethernet), "Arrive: eth0");
    s.expect(PacketOutputEvent("eth0", pkt, display=Ethernet), "Forward: eth0");

    pkt = packet('30:00:00:00:00:06', '30:00:00:00:00:05')
    s.expect(PacketInputEvent("eth0", pkt, display=Ethernet), "Arrive: eth0");
    s.expect(PacketOutputEvent("eth1", pkt, display=Ethernet), "Forward: eth1");

    # Delay for 7s
    s.expect(PacketInputTimeoutEvent(7.0), "Timeout: 7")

    pkt = packet('30:00:00:00:00:06', '30:00:00:00:00:01')
    s.expect(PacketInputEvent("eth0", pkt, display=Ethernet), "Arrive: eth0");
    s.expect(PacketOutputEvent("eth1", pkt, display=Ethernet), "Forward: eth1");

    pkt = packet('30:00:00:00:00:06', '30:00:00:00:00:02')
    s.expect(PacketInputEvent("eth0", pkt, display=Ethernet), "Arrive: eth0");
    s.expect(PacketOutputEvent("eth1", pkt, display=Ethernet), "Forward: eth1");

    pkt = packet('30:00:00:00:00:06', '30:00:00:00:00:03')
    s.expect(PacketInputEvent("eth0", pkt, display=Ethernet), "Arrive: eth0");
    s.expect(PacketOutputEvent("eth2", pkt, display=Ethernet), "Forward: eth2");

    pkt = packet('30:00:00:00:00:06', '30:00:00:00:00:04')
    s.expect(PacketInputEvent("eth0", pkt, display=Ethernet), "Arrive: eth0");
    s.expect(PacketOutputEvent("eth0", pkt, display=Ethernet), "Forward: eth0");

    pkt = packet('30:00:00:00:00:06', '30:00:00:00:00:05')
    s.expect(PacketInputEvent("eth0", pkt, display=Ethernet), "Arrive: eth0");
    s.expect(PacketOutputEvent("eth1", pkt, display=Ethernet), "Forward: eth1");

    # Delay for 10s
    s.expect(PacketInputTimeoutEvent(10.0), "Timeout: 1")

    pkt = packet('30:00:00:00:00:06', '30:00:00:00:00:01')
    s.expect(PacketInputEvent("eth0", pkt, display=Ethernet), "Arrive: eth0");
    s.expect(PacketOutputEvent("eth1", pkt, "eth2", pkt, display=Ethernet), "Forward: eth1, eth2");

    pkt = packet('30:00:00:00:00:06', '30:00:00:00:00:02')
    s.expect(PacketInputEvent("eth0", pkt, display=Ethernet), "Arrive: eth0");
    s.expect(PacketOutputEvent("eth1", pkt, "eth2", pkt, display=Ethernet), "Forward: eth1, eth2");

    pkt = packet('30:00:00:00:00:06', '30:00:00:00:00:03')
    s.expect(PacketInputEvent("eth0", pkt, display=Ethernet), "Arrive: eth0");
    s.expect(PacketOutputEvent("eth1", pkt, "eth2", pkt, display=Ethernet), "Forward: eth1, eth2");

    pkt = packet('30:00:00:00:00:06', '30:00:00:00:00:04')
    s.expect(PacketInputEvent("eth0", pkt, display=Ethernet), "Arrive: eth0");
    s.expect(PacketOutputEvent("eth1", pkt, "eth2", pkt, display=Ethernet), "Forward: eth1, eth2");

    pkt = packet('30:00:00:00:00:06', '30:00:00:00:00:05')
    s.expect(PacketInputEvent("eth0", pkt, display=Ethernet), "Arrive: eth0");
    s.expect(PacketOutputEvent("eth1", pkt, "eth2", pkt, display=Ethernet), "Forward: eth1, eth2");
    return s

scenario = create_scenario()