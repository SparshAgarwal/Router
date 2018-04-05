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

    # [01:0:0][02:1:0][03:2:0]
    # [01:0:0][02:1:0][03:2:0][04:0:0]        
    # [02:1:0][03:2:0][04:0:0][05:1:0][01:0:1]    
    # Add five entries
    # Change port of entry 01 to eth1 and test to see if the entry is correct
    # [02:1:0][03:2:0][04:0:0][05:1:0][01:1:1]
    # [02:1:0][03:2:0][04:0:0][05:1:0][01:1:2]
    # Increase the traffic count of all other entries to 3
    # ........................................
    # ........................................
    # [01:1:2][02:1:3][03:2:3][04:0:3][05:1:3]
    # If a new entry is introduced entry 01 should be dropped
    # [06:2:0][02:1:3][03:2:3][04:0:3][05:1:3]
    # [07:1:0][02:1:3][03:2:3][04:0:3][05:1:3]
    # Add the traffic count for entry 7 to 4
    # [02:1:3][03:2:3][04:0:3][05:1:3][07:1:4]
    # If a new entry is added entry 02 should be dropped and entry 07 should remained
    # [08:1:0][03:2:3][04:0:3][05:1:3][07:1:5]

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

    pkt = packet('30:00:00:00:00:01', '30:00:00:00:00:02')
    s.expect(PacketInputEvent("eth1", pkt, display=Ethernet), "Arrive: eth1");
    s.expect(PacketOutputEvent("eth1", pkt, display=Ethernet), "Forward: eth1");

    pkt = packet('30:00:00:00:00:01', '30:00:00:00:00:02')
    s.expect(PacketInputEvent("eth1", pkt, display=Ethernet), "Arrive: eth1");
    s.expect(PacketOutputEvent("eth1", pkt, display=Ethernet), "Forward: eth1");

    pkt = packet('30:00:00:00:00:01', '30:00:00:00:00:02')
    s.expect(PacketInputEvent("eth1", pkt, display=Ethernet), "Arrive: eth1");
    s.expect(PacketOutputEvent("eth1", pkt, display=Ethernet), "Forward: eth1");

    pkt = packet('30:00:00:00:00:01', '30:00:00:00:00:03')
    s.expect(PacketInputEvent("eth1", pkt, display=Ethernet), "Arrive: eth1");
    s.expect(PacketOutputEvent("eth2", pkt, display=Ethernet), "Forward: eth2");

    pkt = packet('30:00:00:00:00:01', '30:00:00:00:00:03')
    s.expect(PacketInputEvent("eth1", pkt, display=Ethernet), "Arrive: eth1");
    s.expect(PacketOutputEvent("eth2", pkt, display=Ethernet), "Forward: eth2");

    pkt = packet('30:00:00:00:00:01', '30:00:00:00:00:03')
    s.expect(PacketInputEvent("eth1", pkt, display=Ethernet), "Arrive: eth1");
    s.expect(PacketOutputEvent("eth2", pkt, display=Ethernet), "Forward: eth2");

    pkt = packet('30:00:00:00:00:01', '30:00:00:00:00:04')
    s.expect(PacketInputEvent("eth1", pkt, display=Ethernet), "Arrive: eth1");
    s.expect(PacketOutputEvent("eth0", pkt, display=Ethernet), "Forward: eth0");

    pkt = packet('30:00:00:00:00:01', '30:00:00:00:00:04')
    s.expect(PacketInputEvent("eth1", pkt, display=Ethernet), "Arrive: eth1");
    s.expect(PacketOutputEvent("eth0", pkt, display=Ethernet), "Forward: eth0");

    pkt = packet('30:00:00:00:00:01', '30:00:00:00:00:04')
    s.expect(PacketInputEvent("eth1", pkt, display=Ethernet), "Arrive: eth1");
    s.expect(PacketOutputEvent("eth0", pkt, display=Ethernet), "Forward: eth0");

    pkt = packet('30:00:00:00:00:01', '30:00:00:00:00:05')
    s.expect(PacketInputEvent("eth1", pkt, display=Ethernet), "Arrive: eth1");
    s.expect(PacketOutputEvent("eth1", pkt, display=Ethernet), "Forward: eth1");

    pkt = packet('30:00:00:00:00:01', '30:00:00:00:00:05')
    s.expect(PacketInputEvent("eth1", pkt, display=Ethernet), "Arrive: eth1");
    s.expect(PacketOutputEvent("eth1", pkt, display=Ethernet), "Forward: eth1");

    pkt = packet('30:00:00:00:00:01', '30:00:00:00:00:05')
    s.expect(PacketInputEvent("eth1", pkt, display=Ethernet), "Arrive: eth1");
    s.expect(PacketOutputEvent("eth1", pkt, display=Ethernet), "Forward: eth1");

    pkt = packet('30:00:00:00:00:06', '30:00:00:00:00:01')
    s.expect(PacketInputEvent("eth2", pkt, display=Ethernet), "Arrive: eth2");
    s.expect(PacketOutputEvent("eth0", pkt, "eth1", pkt, display=Ethernet), "Forward: eth0, eth1");

    pkt = packet('30:00:00:00:00:07', '30:00:00:00:00:01')
    s.expect(PacketInputEvent("eth1", pkt, display=Ethernet), "Arrive: eth1");
    s.expect(PacketOutputEvent("eth0", pkt, "eth2", pkt, display=Ethernet), "Forward: eth0, eth2");

    pkt = packet('30:00:00:00:00:04', '30:00:00:00:00:07')
    s.expect(PacketInputEvent("eth0", pkt, display=Ethernet), "Arrive: eth0");
    s.expect(PacketOutputEvent("eth1", pkt, display=Ethernet), "Forward: eth1");

    pkt = packet('30:00:00:00:00:04', '30:00:00:00:00:07')
    s.expect(PacketInputEvent("eth0", pkt, display=Ethernet), "Arrive: eth0");
    s.expect(PacketOutputEvent("eth1", pkt, display=Ethernet), "Forward: eth1");

    pkt = packet('30:00:00:00:00:04', '30:00:00:00:00:07')
    s.expect(PacketInputEvent("eth0", pkt, display=Ethernet), "Arrive: eth0");
    s.expect(PacketOutputEvent("eth1", pkt, display=Ethernet), "Forward: eth1");

    pkt = packet('30:00:00:00:00:04', '30:00:00:00:00:07')
    s.expect(PacketInputEvent("eth0", pkt, display=Ethernet), "Arrive: eth0");
    s.expect(PacketOutputEvent("eth1", pkt, display=Ethernet), "Forward: eth1");

    pkt = packet('30:00:00:00:00:08', '30:00:00:00:00:07')
    s.expect(PacketInputEvent("eth1", pkt, display=Ethernet), "Arrive: eth1");
    s.expect(PacketOutputEvent("eth1", pkt, display=Ethernet), "Forward: eth1");
    return s

scenario = create_scenario()