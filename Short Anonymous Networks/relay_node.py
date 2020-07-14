import subprocess # For Ping and Traceroute.
import socket # Pretty explanatory.
import urllib # Connects to the server and fetches the file.
import os # To delete file from system.

relaySocket = None


#@author Sundorius

# Creates the socket for the relay.
def CreateRelay():
    global relaySocket
    relaySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    relaySocketIP=socket.gethostname()
    relayPort = 3000
    try:
        relaySocket.bind((relaySocketIP,relayPort))
        print "Relay created:"
        print "IP: " + socket.gethostbyname(socket.gethostname())
        print "Port: " + str(relayPort)
    except:
        print "Relay socket creation failed!"
        print "Program exiting..."
        exit(1)
    relaySocket.listen(1)


# Waits for a request, if "test" received it makes Ping,Traceroute tests and sends the results to client via
# TCP socket, if "getfile" received, it fetches the file from the server, sends it to the client via TCP
# socket, and deletes the file from the system, if something else is received it closes the relay socket.
def Listen():
    global relaySocket
    while 1:
        client, address = relaySocket.accept()
        request = client.recv(2048)
        mode, request = request.split(',',1)

        if mode == "getfile":
            serverIP, fileURL = request.split(',')
            #Download file from server.
            objects = []
            objects = fileURL.split('/')
            imageObject = objects.__getitem__(objects.__len__() - 1)
            # Gets file and saves it to program folder.
            try:
                try:
                    print "**Trying to download file.."
                    conn = urllib.urlretrieve(fileURL, imageObject)
                    print "**File downloaded successfully"
                except:
                    print "**Failed to download file."
                # Send file back to client.
                try:
                    imageFile = open(imageObject, 'rb')
                    print "Sending file to client..."
                    dataSent = imageFile.read(1024)
                    while (dataSent):
                        print "Sending..."
                        client.send(dataSent)
                        dataSent = imageFile.read(1024)
                    imageFile.close()
                    try:
                        os.remove(imageObject)
                        print "**File sent to client!"
                        print "**File deleted from system!"
                    except:
                        print "**File sent to client!"
                        print "**Error in file deletion from system!"
                except:
                    print "**Error in senting file to client!"
                print "**Program exiting..."
                relaySocket.close()
                break
            except:
                print "**File error in download!"
                print "**Program exiting..."
                relaySocket.close()
                break

        elif mode == "test":
            print "\n=================================="
            print "RTT and Traceroute starting..."
            serverIP, latency = request.split(',')
            averageRTT, numOfHops = TestRelay(serverIP, int(latency))
            sendString = str(averageRTT) + "," + str(numOfHops)
            print "Average RTT: " + averageRTT
            print "RTT and Traceroute ended."
            print "=================================="
            client.send(sendString)
        else:
            relaySocket.close()
            break



# Makes the Ping and Traceroute tests, and returns the results, via TCP socket
# to the client.
def TestRelay(serverIP, latency):
    global relaySocket
    pingResult, averageRTT = CalculateRTT(serverIP, latency)
    numOfHops = CalculateHops(serverIP)
    return averageRTT, numOfHops



# Calculates the number of hops from the relay to the end server, returns number
# of hops if successful, else returns -1.
def CalculateHops(targetIP):
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

    lines = result.split('\n')  # Split result to lines, and store them into a list.
    lastLine = lines.__getitem__(lines.__len__() - 2)  # Get last line, we pick the N-2 element, because the last one
    # is an empty string.
    words = lastLine.split()  # Split last line in words.
    for i in range(0, words.__len__() - 1):
        if "(" + targetIP + ")" == words.__getitem__(i):
            print "  Traceroute successful for IP: " + str(targetIP) + ", with number of hops: " + str(numOfHops)
            return numOfHops
    print "  Traceroute unsuccessful for IP: " + str(targetIP)
    return -1



# Calculates the RTT from the relay to the end server, returns the ping result and average RTT,if successful,
#  else returns ping result and -1.
def CalculateRTT(targetIP,latency):
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
        return returnCode, rtt
    else:
        return returnCode, -1

##############     Main     ##############
CreateRelay()
Listen()
