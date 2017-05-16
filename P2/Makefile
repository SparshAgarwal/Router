main: alltest

alltest: t3 t4 t5 t6 t7 t8 mt

mt: mytest removeFT

t1: test1 removeFT

t2: test2 removeFT

t3: test3 removeFT

t4: test4 removeFT

t5: test5 removeFT

t6: test6 removeFT

t7: test7 removeFT

t8: test8 removeFT

test1:
	./srpy.py -t -s tests/routertest1.srpy myrouter.py

test2:
	./srpy.py -t -s tests/routertest2.srpy myrouter.py

test3:
	./srpy.py -t -s tests/routertest3.srpy myrouter.py

test4:
	./srpy.py -t -s tests/routertest4.srpy myrouter.py

test5:
	./srpy.py -t -s tests/routertest5.srpy myrouter.py

test6:
	./srpy.py -t -s tests/routertest6.srpy myrouter.py

test7:
	./srpy.py -t -s tests/icmp_tests.srpy myrouter.py

test8:
	./srpy.py -t -s tests/more_tests.srpy myrouter.py

mytest:
	./srpy.py -t -s testcase.py myrouter.py

mininet:
	sudo python mininet.py

removeFT:
	rm forwarding_table.txt

tar:
	tar -czvf network2.tar.gz myrouter.py testcase.py README.txt

clean:
	rm -rf */__pycache__ *.pyc __pycache__ forwarding_table.txt network2.tar.gz
