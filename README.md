
This is a project of class CS-335 from the University of Crete Department of Computer Science, that was completed by me from start to finish.

Implementation of a prototype of an innovative service
which 
1) will hide the "identity" (IP address) of the client from the server due to
     use an intermediate node and 
2) find better paths using as
    criteria the delay (round trip time) or the number of hops, from what it gives
    the standard Internet. 
This is achieved by using relays, as shown in previous studies essentially creating an overlay network.


How to run client.py
	python client.py -e end_servers.txt -r relay_nodes.txt
	
How to run relay_node.py
	python relay_node.py

For the relay_nodes.txt, you add your own ips with their ports.
