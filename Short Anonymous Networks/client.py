import urllib   # Connects to the server and fetches the file.
import random  # To create random port number in a range, and to select if relays or relay/client have the same results.
import socket  # Pretty explanatory.
import subprocess  # For Ping and Traceroute.
from optparse import OptionParser  # For the command line arguments
import threading # For the threads.
import os # To delete file if failed transaction.
import time # To calculate download time.


#@author Sundorius

# Option Parser for the command line arguments.
parser = OptionParser()
parser.add_option('-e', dest="end_servers", type='str',
                  help="give the name of the file containing the list of the end-servers")
parser.add_option('-r', dest="relay_nodes", type='str',
                  help="give the name of the file containing the list of the relay nodes")
(options, args) = parser.parse_args()

# Global variables.
serverAlias = None  # Server alias will be cast to lowercase in func SearchURL(serverURL).
testOption = None
serverURL = None
serverIP = 0
client_socket = None
latency = 0

directRTT = 0.0
directNumOfHops = 0

relayResultList = [] # Result of func RelayMode().


end_servers = options.end_servers
relay_nodes = options.relay_nodes
files2download = 'files2download.txt'


# Asking client to give the server alias, the latency and the test mechanism,
# then searches for the server URL, if client gives an invalid alias, program ends.
def Initialize():
    global serverAlias
    global serverURL
    global latency
    global serverIP
    global testOption
    global client_socket

    while 1:
        userInput = str(raw_input("Please give the alias of the end server, the latency and the desired test mechanism(latency / hops): "))\
            .lower()
        inputs = userInput.split()
        if(inputs.__len__()<3):
            print "** Please fill all fiedls! **"
            continue
        serverAlias = inputs.__getitem__(0)
        latency = inputs.__getitem__(1)
        testOption = inputs.__getitem__(2)
        latency = int(latency)
        break

    # =======================  CHECKS  =======================
    while latency < 0:
        print "Latency must be greater than 0, please type a right one:"
        latency = int(input())
    serverURL = SearchURL(serverAlias)
    while testOption != "latency" and testOption != "hops":
        print "Please give a valid test mechanism!"
        testOption = str(raw_input()).strip()
    if serverURL is None:
        print "Wrong alias given, URL not found, program ends!"
        exit(1)
    serverIP = socket.gethostbyname(serverURL)
    client_socket = CreateSocket(socket.gethostname()) # Create socket with random port.
    print "\nLatency: " + str(latency)
    print "Server Alias: " + serverAlias
    print "Server URL:  " + serverURL
    print "Server IP: " + serverIP



# Searches the end_servers.txt file for the given alias, if found it returns the server URL
# of the given alias, else returns None.
def SearchURL(serverAlias):
    with open(end_servers) as file_servers:  # Opens the file, and closes it at the end.
        for line in file_servers:  # Read line by line.
            line.strip()
            line, alias = line.split(',')  # Split line when comma found.
            alias = str(alias).strip()  # Cast to string and remove white spaces.
            if (serverAlias == alias):
                return str(line)
    return None


# Searches the relay_node.txt file for the relay alias, relay IP and relay port.
# When found, it returns them as a list.
def SearchRelays():
    global relay_nodes
    relays_list = []
    with open(relay_nodes) as file_relays:  # Opens the file, and closes it at the end.
        for line in file_relays:  # Read line by line.
            line.strip()
            alias, line = line.split(',',1)  # Split line when comma found.
            IP , Port = line.split(',') # Split line when comma found.
            Port=Port.strip('\n')
            list = [alias, IP, Port]  # Put them in a list.
            relays_list.append(list) # Add list in the relays list.
        return relays_list


# Creates socket for a specified IP.
def CreateSocket(socketIP):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # TCP socket.
    port = random.randint(49152, 62630)  # Opens a random port in the specified range.
    try:
        client_socket.bind((socketIP, port))
    except:
        print "**Error in socket creation!"
        print "  Program exiting..."
        exit(1)
    print "\nClients socket:"
    print "Socket for IP " + socket.gethostbyname(socketIP) + " created successfully."
    print "IP: " + socket.gethostbyname(socketIP)
    print "Port: " + str(port)
    return client_socket


# Pings an IP 'latency' times, and returns the return code and the average RTT.
def Ping(targetIP, latency):
    result = subprocess.Popen(['ping', '-c' + str(latency) , targetIP], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    returnCode = result.wait()
    if (returnCode == 0):
        result2 = result.stdout.read()
        for char in range(0, result2.__len__() - 1):  # Check char to char the string.
            if (result2[char] == '%'):  # Find the '%'.
                rtt, result2 = result2.split('%', 1)  # Split.
                break
        rtt, result2 = result2.split('/', 1)
        rtt, result2 = result2.split('/', 1)
        rtt, result2 = result2.split('/', 1)
        rtt, result2 = result2.split('/', 1)
        rtt, result2 = result2.split('/', 1)  # rtt now holds the average rtt.
        print "  Ping ended successfully, with average RTT: " + str(rtt)
        return returnCode, rtt
    else:
        print "  Ping failed!"
        return returnCode, -1



# Calculates the number of hops, an returns the number of hops if target responds,
# else returns -1.
def Traceroute(targetIP):
    numOfHops = 0
    lineStart = 0
    result = subprocess.check_output(["traceroute", targetIP])
    print result
    for char in range(0, result.__len__() - 1):  # Check char to char the string.
        if (result[char] == '\n'):  # If it has reached the end of a line.
            if (result.count('*', lineStart, char) <= 3 and result.count('(', lineStart, char)>=1):  # Checks if there are stars in the line, which
                                                                    #  means that the target is unreachable at that moment or ever .
                lineStart = char + 1
                numOfHops += 1
    lines = result.split('\n') # Split result to lines, and store them into a list.
    lastLine = lines.__getitem__(lines.__len__()-2) # Get last line, we pick the N-2 element, because the last one
                                                    # is an empty string.
    words = lastLine.split() # Split last line in words.
    for i in range(0, words.__len__()-1):
        if "("+targetIP+")" == words.__getitem__(i):
            print "  Traceroute successful for IP: " + str(targetIP) + ", with number of hops: " + str(numOfHops)
            return numOfHops
    print "  Traceroute unsuccessful for IP: " + str(targetIP)
    return -1



# Direct mode testing for ping and traceroute.
def DirectMode(targetIP, latency):
    print "==============================================="
    print "Direct Mode"
    print "==============================================="
    global directRTT
    global directNumOfHops

    print "\n**Ping started for direct mode:"
    pingResult, directRTT = Ping(targetIP, latency)
    directRTT = float(directRTT)
    print "**Ping ended for direct mode."
    print "\n**Traceroute started for direct mode:"
    directNumOfHops = Traceroute(targetIP)
    print "**Traceroute ended for direct mode."


# Relay mode testing for ping and traceroute.
def RelayMode(relayAlias, relayIP, relayPort, serverIP, latency):
    print "==============================================="
    print "Relay Mode"
    print "==============================================="
    global relayResultList

    client_socket = CreateSocket(socket.gethostbyname(socket.gethostname()))

    # Ping and traceroute test for route: client -> relay node.
    print "\n**Ping started for relay mode, for route: client -> relay node:"
    clientRelayPingResult, clientRelayRTT = Ping(relayIP, latency)
    print "**Ping ended for relay mode, for route: client -> relay node."
    print "\n**Traceroute started for relay mode, for route: client -> relay node:"
    clientRelayHops = Traceroute(relayIP)
    print "**Traceroute ended for relay mode, for route: client -> relay node."

    # Ping and traceroute test for route: relay node -> end server.
    print "\n**Ping and traceroute started for relay mode, for route: relay node -> end server:"
    client_socket.connect((relayIP, relayPort))
    sendString = "test,"+serverIP+","+str(latency)
    client_socket.send(sendString)
    dataRecv = client_socket.recv(2048)
    relayEndServerRTT , relayEndServerHops = dataRecv.split(',')

    # Casting to float so the sum will be a valid number.
    relayEndServerRTT = float(relayEndServerRTT)
    clientRelayRTT = float(clientRelayRTT)
    relayEndServerHops = int(relayEndServerHops)
    if relayEndServerRTT!=-1:
        print "  Ping for relay with alias: "+ relayAlias+\
              ", ended successfully, with average RTT: "+ str(relayEndServerRTT)
    else:
        print "  Ping for relay with alias: " + relayAlias + ", failed!"
    if relayEndServerHops!=-1:
        print "  Traceroute successful for relay with alias: "+relayAlias+\
              ", with number of hops: " +str(relayEndServerHops)
    else:
        print "  Traceroute failed for relay with alias: " + relayAlias
    print "**Ping and traceroute ended for relay mode, for route: relay node -> end server:"
    if clientRelayRTT == -1 or relayEndServerRTT == -1:
        totalRTT = -1
    else:
        totalRTT = clientRelayRTT + relayEndServerRTT
    if clientRelayHops == -1 or relayEndServerHops == -1:
        totalHops = -1
    else:
        totalHops = clientRelayHops + relayEndServerHops
    relayResultList.append([totalRTT, totalHops, relayIP, relayPort, relayAlias])
    client_socket.close()



# Finds the fastest route and downloads the file, it also prints the results of Direct and Relay Mode.
def FindFastestRoute(serverIP, latency):
    global relayResultList
    global testOption
    global directNumOfHops
    global directRTT

    relaysInfo = SearchRelays() # Relay Alias, IP and Port.

    # Thread for direct Mode.
    #DirectMode(serverIP,latency)
    directThread = threading.Thread(target=DirectMode, args=(serverIP, latency))
    directThread.start()
    directThread.join()
    # Threads for relays.
    for i in range(0, relaysInfo.__len__()):
        relay = relaysInfo.__getitem__(i)  # From relay list extract one relay.
        relayAlias = str(relay.__getitem__(0)).strip() # Get relay Alias.
        relayIP = str(relay.__getitem__(1)).strip()    # Get relay IP.
        relayPort = str(relay.__getitem__(2)).strip() # Get relay Port.
        #RelayMode(relayAlias, relayIP, int(relayPort), serverIP, latency)
        relayThread = threading.Thread(target=RelayMode, args=(relayAlias, relayIP, int(relayPort), serverIP, latency))
        relayThread.start()
        relayThread.join()
    while relayResultList.__len__<relaysInfo.__len__(): # Waits until all threads have saved their results in the list,
                            # it prevents the next lines of codes from accessing elements of the list that do not exist.
        continue
    print "\n=====================  RESULTS  ======================="
    print "Direct RTT :" + str(directRTT)
    print "Direct Hops: " + str(directNumOfHops)
    print "Relays Results: [RTT, HOPS, Relay IP, Relay Port, Relay Alias]"
    print  relayResultList
    print "========================================================"

    # Find fastest RTT and Hops relay.
    fastestRTTRelay = [float(relayResultList.__getitem__(0).__getitem__(0)), relayResultList.__getitem__(0).__getitem__(2),
                       relayResultList.__getitem__(0).__getitem__(3), relayResultList.__getitem__(0).__getitem__(4)]
    fastestHopsRelay = [relayResultList.__getitem__(0).__getitem__(1), relayResultList.__getitem__(0).__getitem__(2),
                        relayResultList.__getitem__(0).__getitem__(3), relayResultList.__getitem__(0).__getitem__(4)]
    for i in range(1, relayResultList.__len__()):
        results = relayResultList.__getitem__(i)
        currRTTRelay = [float(results.__getitem__(0)), results.__getitem__(2), results.__getitem__(3), results.__getitem__(4)]
        currHopsRelay = [results.__getitem__(1), results.__getitem__(2), results.__getitem__(3), results.__getitem__(4)]
        if currRTTRelay.__getitem__(0) == -1:
            pass
        else:
            if currRTTRelay.__getitem__(0) == fastestRTTRelay.__getitem__(0): #If they have the same value, choose random.
                randomNum = random.randint(0,1)
                if randomNum == 0:
                    fastestRTTRelay = currRTTRelay
                else:
                    pass
            elif currRTTRelay.__getitem__(0) < fastestRTTRelay.__getitem__(0):
                fastestRTTRelay = currRTTRelay
        if currHopsRelay.__getitem__(0) == -1:
            pass
        else:
            if currHopsRelay.__getitem__(0) == fastestHopsRelay.__getitem__(0):#If they have the same value, choose random.
                randomNum = random.randint(0, 1)
                if randomNum == 0:
                    fastestHopsRelay = currHopsRelay
                else:
                    pass
            elif currHopsRelay.__getitem__(0) < fastestHopsRelay.__getitem__(0):
                fastestHopsRelay = currHopsRelay


    # Finds fastest path according to testOption and makes the connection to download the file.
    if testOption == "latency":
        if fastestRTTRelay.__getitem__(0) == -1 and directRTT == -1:
            print "Ping is not acceptable as a test mechanism, all the relays and the direct mode failed!"
            print "The fastest path will be found by Traceroute!"
            if fastestHopsRelay.__getitem__(0) == directNumOfHops:
                randomChoise = random.randint(0, 1)
                if randomChoise == 0:
                    ConnectDownload(None, None, None)  # Direct mode.
                else:
                    ConnectDownload(fastestRTTRelay.__getitem__(1), fastestRTTRelay.__getitem__(2),
                                    fastestRTTRelay.__getitem__(3))  # Fastest Hops relay.
            elif fastestHopsRelay.__getitem__(0) < directNumOfHops:
                ConnectDownload(fastestHopsRelay.__getitem__(1), fastestHopsRelay.__getitem__(2),
                                fastestHopsRelay.__getitem__(3))  # Fastest Hops relay.
            else:
                ConnectDownload(None, None, None)  # Direct mode.
        else:
            # If results are the same, check Hops.
            if fastestRTTRelay.__getitem__(0) == directRTT:
                print "The RTT of the fastest relay and the RTT of the direct mode have the same value."
                print "The fastest path will be found by Traceroute!"
                if fastestHopsRelay.__getitem__(0) == directNumOfHops:
                    randomChoise = random.randint(0,1)
                    if randomChoise == 0:
                        ConnectDownload(None, None, None) # Direct mode.
                    else:
                        ConnectDownload(fastestRTTRelay.__getitem__(1), fastestRTTRelay.__getitem__(2),
                                        fastestRTTRelay.__getitem__(3)) # Fastest Hops relay.
                elif fastestHopsRelay.__getitem__(0) < directNumOfHops:
                    ConnectDownload(fastestHopsRelay.__getitem__(1), fastestHopsRelay.__getitem__(2),
                                        fastestHopsRelay.__getitem__(3)) # Fastest Hops relay.
                else:
                    ConnectDownload(None, None, None) # Direct mode.
            elif fastestRTTRelay.__getitem__(0) != -1:
                if directRTT != -1:
                    if fastestRTTRelay.__getitem__(0) < directRTT:
                        ConnectDownload(fastestRTTRelay.__getitem__(1), fastestRTTRelay.__getitem__(2),
                                        fastestRTTRelay.__getitem__(3)) # Fastest RTT relay.
                    else:
                        ConnectDownload(None, None, None) # Direct mode.
                else:
                    ConnectDownload(fastestRTTRelay.__getitem__(1), fastestRTTRelay.__getitem__(2),
                                    fastestRTTRelay.__getitem__(3)) # Direct has failed, so fastest is
                                    #  the fastest RTT relay.
            else:
                ConnectDownload(None, None, None) # Direct is for sure != -1 because of the
                                # "if fastestRTTRelay.__getitem__(0) == -1 and directRTT == -1:" check!!
    else: # For testOption == "hops"
        if fastestHopsRelay.__getitem__(0) == -1 and directNumOfHops == -1:
            print "Traceroute is not acceptable as a test mechanism, all the relays and the direct mode failed!"
            print "The fastest path will be found by Ping!"
            if fastestRTTRelay.__getitem__(0) == directRTT:
                randomChoise = random.randint(0, 1)
                if randomChoise == 0:
                    ConnectDownload(None, None, None)  # Direct mode.
                else:
                    ConnectDownload(fastestRTTRelay.__getitem__(1), fastestRTTRelay.__getitem__(2),
                                    fastestRTTRelay.__getitem__(3))  # Fastest RTT relay.
            elif fastestRTTRelay.__getitem__(0) < directRTT:
                ConnectDownload(fastestRTTRelay.__getitem__(1), fastestRTTRelay.__getitem__(2),
                                fastestRTTRelay.__getitem__(3))  # Fastest RTT relay.
            else:
                ConnectDownload(None, None, None)  # Direct mode.
        else:
            if fastestHopsRelay.__getitem__(0) == directNumOfHops:
                print "The number of hops of the fastest relay and the number of hops" \
                      " of the direct mode have the same value."
                print "The fastest path will be found by Ping!"
                if fastestRTTRelay.__getitem__(0) == directRTT:
                    randomChoise = random.randint(0,1)
                    if randomChoise == 0:
                        ConnectDownload(None, None, None) # Direct mode.
                    else:
                        ConnectDownload(fastestRTTRelay.__getitem__(1), fastestRTTRelay.__getitem__(2),
                                        fastestRTTRelay.__getitem__(3)) # Fastest RTT relay.
                elif fastestRTTRelay.__getitem__(0) < directRTT:
                    ConnectDownload(fastestRTTRelay.__getitem__(1), fastestRTTRelay.__getitem__(2),
                                    fastestRTTRelay.__getitem__(3))  # Fastest RTT relay.
                else:
                    ConnectDownload(None, None, None) # Direct mode.
            elif fastestHopsRelay.__getitem__(0) != -1:
                if directNumOfHops != -1:
                    if fastestHopsRelay.__getitem__(0) < directNumOfHops:
                        ConnectDownload(fastestHopsRelay.__getitem__(1), fastestHopsRelay.__getitem__(2),
                                        fastestHopsRelay.__getitem__(3)) # Fastest Hops relay.
                    else:
                        ConnectDownload(None, None, None)
                else:
                    ConnectDownload(fastestHopsRelay.__getitem__(1),fastestHopsRelay.__getitem__(2),
                                    fastestHopsRelay.__getitem__(3))  # Direct has failed, so fastest is
                                            #  the fastest Hops relay.
            else:
                ConnectDownload(None, None, None)  # Direct is for sure != -1 because of the
                                # "if fastestHopsRelay.__getitem__(0) == -1 and directNumOfHops == -1:" check!!




# Makes the connection (direct or via relay) and downloads the file.
def ConnectDownload(relayIP, relayPort, relayAlias):
    global serverIP
    global serverURL

    global directRTT
    global directNumOfHops
    global relayResultList

    client_socket = CreateSocket(socket.gethostbyname(socket.gethostname()))
    if relayIP is None: # Make connection with direct mode.
        start = end = 0
        print "\n**The best path is: client -> server!"
        print "  Attempting connection with Direct Mode:"
        #try: # TODO Bale sto teliko programma to try: except:
        fileURL = str(raw_input("Give the file URL: ")).lower()
        objects = []
        objects = fileURL.split('/')
        imageObject = objects.__getitem__(objects.__len__()-1)
        # Gets object and saves it to program folder.
        try:
            start = time.time()  # Sarting counting download time.
            conn = urllib.urlretrieve(fileURL, imageObject)
            end = time.time()  # Ending counting download time.
            print "**File downloaded!"
            print "**Total time to download the file: " + str(end-start)  +" sec."
            print "  Program exiting..."
            client_socket.close()
        except:
            print "**File error in download!"
            print "  Program exiting..."
            client_socket.close()
    else: # Make connection via the fastest relay.
        startC = endC = timeC = 0
        print "\n**The best path is: client -> "+relayAlias+" -> server!"
        print "  Attempting connection with Relay Mode via Relay: "+relayAlias
        fileURL = str(raw_input("Give the file URL: ")).lower()
        relayIP = str(relayIP)
        try:
            startC = time.time()  # Start connection time.
            client_socket.connect((relayIP, relayPort))
            endC = time.time()  # End connection time.
            timeC = endC-startC
            print "  Client connected successfully to relay: "+relayAlias
            print "  Connection took: " +str(timeC) +" sec."
        except:
            print "  Client could not connect to relay: "+relayAlias
            print "  Program exiting..."
            exit(1)
        stringSent = "getfile"+","+str(serverIP)+","+str(fileURL)
        startR= time.time()  # Start request time.
        client_socket.send(stringSent)
        endR = time.time()  # Start request time.
        timeR = endR-startR # Total time to send the request.
        print "  Sending request to relay took: " + str(timeR) +" sec."
        fileRecv = client_socket.recv(1024)
        objects = []
        objects = fileURL.split('/')
        imageObject = objects.__getitem__(objects.__len__() - 1)
        imageFile = open(imageObject, 'wb')
        if fileRecv is None:
            print "**File error in download!"
            print "  Program exiting..."
            imageFile.close()
            os.remove(imageFile)
            client_socket.close()
        else:
            startD = time.time() # Start time for downloading the file from relay.
            while fileRecv:
                print "  Downloading file...."
                imageFile.write(fileRecv)
                fileRecv = client_socket.recv(1024)
            imageFile.close()
            endD = time.time() # End time for downloading the file from relay.
            timeD = endD-startD
            print "**File downloaded!"
            print "  Total time to download the file: "+str(timeD) +" sec."
            print "  Total time for Connection, Request, Download: "+str(timeC+timeR+timeD) +" sec."
            print "  Program exiting..."
            client_socket.close()


######    Here starts the client program.    ######
Initialize()
FindFastestRoute(serverIP, latency)
