main: lruedge trafficedge toedge lru traffic to

to:
	./srpy.py -t -s tests/timeouttest.srpy myswitch_to.py

lru:
	./srpy.py -t -s tests/lrutest.srpy myswitch_lru.py

traffic:
	./srpy.py -t -s tests/traffictest.srpy myswitch_traffic.py

lruedge:
	./srpy.py -t -s mytests/lru_edgecase.py myswitch_lru.py

trafficedge:
	./srpy.py -t -s mytests/traffic_edgecase.py myswitch_traffic.py

toedge:
	./srpy.py -t -s mytests/timeout_edgecase.py myswitch_to.py

mininet:
	sudo python mininet.py

tar:
	tar -czvf network1.tar.gz mytests/ myswitch_to.py myswitch_lru.py myswitch_traffic.py README.txt Makefile srpy.py mininet.py switchyard

clean:
	rm -rf */__pycache__ *.pyc __pycache__ network1.tar.gz