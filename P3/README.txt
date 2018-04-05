WAYNE CHEW MING CHAN 9071997606
SPARSH AGARWAL 9075905142

Blaster:
After initializing the blaster, the blaster begins by sending out packets. It sends one packet after every recv_timeout. In other words, the recv_timeout control the speed at which packets are sent. The blaster sends packet based on the window_size. RHS - LHS + 1 <= window_size. A buffer is used to keep track of ACK received for packets based on seq number.

The blaster only increments the LHS once it receives the ACK packets with the seq number of LHS. If the LHS in not incremented after course_timeout, it will retransmit non-ACKs packets. The retransmission of non-ACKs packets is sent one by one after every recv_timeout.
If ACK is received for the LHS, increment LHS and reset coarse_timeout.

After LHS is incremented, keep sending packets until RHS reaches the limit for window_size. Once N number of packets are sent, which is given through the parameter, the blaster stops and print out the stats.

Some test runs:
1) PARAMETERS GIVEN ON PROJECT DESCRIPTION PAGE
Total TX time (in seconds): 32.21217703819275
Number of reTX: 80
Number of coarse TOs: 50
Throughput (Bps): 558.7948923370838
Goodput (Bps): 310.44160685393547

coarse_timeout is then set to 500ms

2) DROP_RATE = 0
Total TX time (in seconds): 19.891525268554688
Number of reTX: 0
Number of coarse TOs: 0
Throughput (Bps): 502.72665695518066
Goodput (Bps): 502.72665695518066

3) DROP_RATE = 0.8
Total TX time (in seconds): 107.99665832519531
Number of reTX: 447
Number of coarse TOs: 183
Throughput (Bps): 506.49715322940364
Goodput (Bps): 92.5954576287758

4) NUMBER_OF_PACKETS = 1
Total TX time (in seconds): 0.39731788635253906
Number of reTX: 0
Number of coarse TOs: 0
Throughput (Bps): 251.68763711601514
Goodput (Bps): 251.68763711601514

5) WINDOW_SIZE = 1
Total TX time (in seconds): 58.99159502983093
Number of reTX: 22
Number of coarse TOs: 22
Throughput (Bps): 206.8091224492352
Goodput (Bps): 169.51567413871737

6) WINDOW_SIZE = 50, COARSE_TIMEOUT = 5000
Total TX time (in seconds): 28.590627908706665
Number of reTX: 34
Number of coarse TOs: 5
Throughput (Bps): 468.685054514641
Goodput (Bps): 349.76496605570225

7) WINDOW_SIZE = 100, COARSE_TIMEOUT = 7500
Total TX time (in seconds): 27.097169876098633
Number of reTX: 21
Number of coarse TOs: 4
Throughput (Bps): 446.5410983998348
Goodput (Bps): 369.0422300825081


