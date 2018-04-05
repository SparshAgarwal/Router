from collections import deque
from switchyard.lib.packet import *
from switchyard.lib.address import *
from switchyard.lib.common import *

def switchy_main(net):
    # Get list of interfaces and their address
    interfaces_list = net.interfaces()
    interfaces_addr_list = [intf.ethaddr for intf in interfaces_list]

    # Maximum number of entries for the forwarding table
    maximum_entries = 5

    # Initialize forwarding table, forwarding table will store tuple (addr, interface)
    forwarding_table = deque(maxlen=maximum_entries)

    # Print the table for debugging purposes
    def print_table(forwarding_table):
        print([i.toStr()[15:] for i,j in forwarding_table]);

    while True:
        try:
            # Receive packet
            input_port,packet = net.recv_packet()

            # Add source address to forwarding table
            src_addr = packet[Ethernet].src

            source_exist = False

            for i,(j,k) in enumerate(forwarding_table):
                if j == src_addr:
                    forwarding_table[i] = (j, input_port)
                    source_exist = True
                    break

            if not source_exist:
                forwarding_table += [(src_addr, input_port)]

        except Shutdown:
            # Shutdown signal
            # print("Shutdown signal detected, exiting.")
            break
        except NoPackets:
            # No packet is received, code only reachable if timeout is set
            # print("No packets available.")
            continue

        # Received packet
        dest_addr = packet[Ethernet].dst

        # Destination address is the same as switch address
        if dest_addr in interfaces_addr_list:
            # print_table(forwarding_table)
            continue

        destination_exist = False

        # If destination address exist in the forwarding table
        for i,j in list(forwarding_table):
            if i == dest_addr:
                forwarding_table.remove((i,j))
                forwarding_table += [(i,j)]
                net.send_packet(j, packet)
                destination_exist = True
                break

        if not destination_exist or dest_addr == "ff:ff:ff:ff:ff:ff":
            # Send the packet out to all ports except the source of the packet
            for port in interfaces_list:
                if port.name != input_port:
                    net.send_packet(port.name, packet)

        # print_table(forwarding_table)
    net.shutdown()