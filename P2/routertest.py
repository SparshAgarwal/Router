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
    s = Scenario("router test")
    s.add_interface('eth0', '10:00:00:00:00:01', '192.168.1.1')
    s.add_interface('eth1', '10:00:00:00:00:02', '192.168.1.2')
    s.add_interface('eth2', '10:00:00:00:00:03', '192.168.1.3')

    pkt = create_ip_arp_request('30:00:00:00:00:01', '142.32.44.1', '192.168.1.2')
    r_pkt = create_ip_arp_reply('10:00:00:00:00:02', '30:00:00:00:00:01', '192.168.1.2', '142.32.44.1')
    s.expect(PacketInputEvent('eth0', pkt, display=Ethernet), 'Arp request for router\'s interface eth1')
    s.expect(PacketOutputEvent("eth0", r_pkt,display=Ethernet), "Arp reply from router")

    pkt = create_ip_arp_request('30:00:00:00:00:01', '142.32.44.1', '192.168.1.3')
    r_pkt = create_ip_arp_reply('10:00:00:00:00:03', '30:00:00:00:00:01', '192.168.1.3', '142.32.44.1')
    s.expect(PacketInputEvent('eth2', pkt, display=Ethernet), 'Arp request for router\'s interface eth2')
    s.expect(PacketOutputEvent("eth2", r_pkt,display=Ethernet), "Arp reply from router")

    # #Table [address:port]
    # # Table [01:0]
    # pkt = packet('30:00:00:00:00:01', 'ff:ff:ff:ff:ff:ff')
    # s.expect(PacketInputEvent("eth0", pkt, display=Ethernet), "Arrive: eth0");
    # s.expect(PacketOutputEvent("eth1", pkt, "eth2", pkt, display=Ethernet), "Forward: eth1, eth2")

    # # Table [01:0][02:1]
    # pkt = packet('30:00:00:00:00:02', 'ff:ff:ff:ff:ff:ff')
    # s.expect(PacketInputEvent("eth1", pkt, display=Ethernet), "Arrive: eth1");
    # s.expect(PacketOutputEvent("eth0", pkt, "eth2", pkt, display=Ethernet), "Forward: eth0, eth2")

    # # Table [01:0][02:1][03:2]
    # pkt = packet('30:00:00:00:00:03', 'ff:ff:ff:ff:ff:ff')
    # s.expect(PacketInputEvent("eth2", pkt, display=Ethernet), "Arrive: eth2");
    # s.expect(PacketOutputEvent("eth0", pkt, "eth1", pkt, display=Ethernet), "Forward: eth0, eth1")    

    # # Table [01:0][02:1][03:2][04:0]
    # pkt = packet('30:00:00:00:00:04', '10:00:00:00:00:01')
    # s.expect(PacketInputEvent("eth0", pkt, display=Ethernet), "Arrive: eth0");
    # s.expect(PacketInputTimeoutEvent(1.0), "Timeout: 1")

    # # Table [02:1][03:2][04:0][05:1][01:0]
    # pkt = packet('30:00:00:00:00:05', '30:00:00:00:00:01')
    # s.expect(PacketInputEvent("eth1", pkt, display=Ethernet), "Arrive: eth1");
    # s.expect(PacketOutputEvent("eth0", pkt, display=Ethernet), "Forward: eth0")

    # # Table [02:1][03:2][04:0][05:1][01:1]
    # pkt = packet('30:00:00:00:00:01', '10:00:00:00:00:01')
    # s.expect(PacketInputEvent("eth1", pkt, display=Ethernet), "Arrive: eth1");
    # s.expect(PacketInputTimeoutEvent(1.0), "Timeout: 1")

    # # Table [04:0][05:1][01:1][06:2][03:2]
    # pkt = packet('30:00:00:00:00:06', '30:00:00:00:00:03')
    # s.expect(PacketInputEvent("eth2", pkt, display=Ethernet), "Arrive: eth2");
    # s.expect(PacketOutputEvent("eth2", pkt, display=Ethernet), "Forward: eth2");

    # # Table [01:1][06:2][03:2][07:0][05:1]
    # pkt = packet('30:00:00:00:00:07', '30:00:00:00:00:05')
    # s.expect(PacketInputEvent("eth0", pkt, display=Ethernet), "Arrive: eth0");
    # s.expect(PacketOutputEvent("eth1", pkt, display=Ethernet), "Forward: eth1");

    # # Table [06:2][03:2][07:0][05:1][08:0]
    # pkt = packet('30:00:00:00:00:08', '30:00:00:00:00:01')
    # s.expect(PacketInputEvent("eth0", pkt, display=Ethernet), "Arrive: eth0");
    # s.expect(PacketOutputEvent("eth1", pkt, "eth2", pkt, display=Ethernet), "Forward: eth1, eth2");

    return s

scenario = create_scenario()