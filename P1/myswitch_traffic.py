from heapq import *
from switchyard.lib.packet import *
from switchyard.lib.address import *
from switchyard.lib.common import *

def switchy_main(net):
    # Get list of interfaces and their address
    interfaces_list = net.interfaces()
    interfaces_addr_list = [intf.ethaddr for intf in interfaces_list]

    # Maximum number of entries for the forwarding table
    maximum_entries = 5
    # Variable to keep track of number of items in heapq
    heapq_num_items = 0

    # Initialize forwarding table, forwarding table will store tuple (traffic, tie_breaker, addr, interface)
    # Break ties by removing the least recently used entry
    forwarding_table = []

    # Reduce the tie_breaker for every other entry except for ctr and increment the traffic count for ctr
    def update_table(forwarding_table, ctr, maximum_entries):
    	for i,(j,k,l,m) in enumerate(forwarding_table):
    		if i != ctr:
    			forwarding_table[i] = (j, k - 1, l, m)
    		else:
    			forwarding_table[i] = (j + 1, maximum_entries, l, m)

    	heapify(forwarding_table)

    # Print the table for debugging purposes
    def print_table(forwarding_table):
    	print([[k.toStr()[15:],i] for i,j,k,l in forwarding_table]);

    while True:
        try:
            # Receive packet
            input_port,packet = net.recv_packet()

            # Add source address to forwarding table
            src_addr = packet[Ethernet].src

            source_exist = False

            for i,(j,k,l,m) in enumerate(forwarding_table):
                if l == src_addr:
                    forwarding_table[i] = (j, maximum_entries, l, input_port)
                    heapify(forwarding_table)
                    source_exist = True
                    break

            if not source_exist:
                if heapq_num_items >= maximum_entries:
                    heapreplace(forwarding_table, (0, maximum_entries, src_addr, input_port))
                else:
                    heappush(forwarding_table, (0, maximum_entries, src_addr, input_port))
                    heapq_num_items += 1

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
        for i,(j,k,l,m) in enumerate(forwarding_table):
            if l == dest_addr:
                net.send_packet(m, packet)

                update_table(forwarding_table, i, maximum_entries)

                destination_exist = True
                break

        if not destination_exist or dest_addr == "ff:ff:ff:ff:ff:ff":
            # Send the packet out to all ports except the source of the packet
            for port in interfaces_list:
                if port.name != input_port:
                    net.send_packet(port.name, packet)

        # print_table(forwarding_table)
    net.shutdown()