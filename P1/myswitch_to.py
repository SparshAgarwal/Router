import time
from switchyard.lib.packet import *
from switchyard.lib.address import *
from switchyard.lib.common import *

def switchy_main(net):
    # Get list of interfaces and their address
    interfaces_list = net.interfaces()
    interfaces_addr_list = [intf.ethaddr for intf in interfaces_list]

    # Timeout duration
    timeout_duration = 10

    # check to see if any entry in the forwarding_table is stale
    # forwarding_table = (addr, interface, start_time)
    # remove entry if time.time() - start_time > timeout_duration
    def checkTimeout(forwarding_table, timeout_duration):
        for i,(j,k,l) in enumerate(forwarding_table):
            if time.time() - l > timeout_duration:
                forwarding_table.remove((j,k,l))

    # Print the table for debugging purposes
    def print_table(forwarding_table):
        print([i.toStr()[15:] for i,j,k in forwarding_table]);

    # Initialize forwarding table, forwarding table will store tuple (addr, interface, start_time)
    # start_time is the time the entry is inserted into the forwarding table
    forwarding_table = []

    while True:
        try:
            # Receive packet
            input_port,packet = net.recv_packet()

            # Add source address to forwarding table
            src_addr = packet[Ethernet].src

            source_exist = False
            for i,(j,k,l) in enumerate(forwarding_table):
                if j == src_addr:
                    forwarding_table[i] = (j, input_port, time.time())
                    source_exist = True
                    break

            if not source_exist:
                forwarding_table += [(src_addr, input_port, time.time())]

            # Purge stale entries
            checkTimeout(forwarding_table, timeout_duration)

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
        for i,j,k in list(forwarding_table):
            if i == dest_addr:
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