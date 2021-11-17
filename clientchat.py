import socket
import selectors
import sys
import argparse
import errno
import signal
import fcntl
import os
from urllib.parse import urlparse

HEADER = 1024

def signal_handler(sig, frame):     #called when received ^C

    print('Interrupt received, shutting down ...')
    disconnect = ("DISCONNECT " + username.decode("utf-8") + " CHAT/1.0").encode("utf-8") #send server a disconnect message and exit
    disconnectHeader = f'{len(disconnect):<{HEADER}}'.encode('utf-8')
    clientSocket.send(disconnectHeader + disconnect)
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)    #set up listener to exit
mySelector = selectors.DefaultSelector()        #create a selector
file = fcntl.fcntl(sys.stdin, fcntl.F_GETFL)    #make sys.stdin non-blocking 
fcntl.fcntl(sys.stdin, fcntl.F_SETFL, file | os.O_NONBLOCK)

try:
    # Check command line arguments to retrieve a URL.
    parsedArgs = urlparse(sys.argv[2])
    host = parsedArgs.hostname
    port = parsedArgs.port

    if sys.argv[1] == "all":            #if username is reserved name "all" print error and exit
        print("Username 'all' is reserved. Please choose another username.")
        sys.exit(0)

    username = sys.argv[1].encode('utf-8')
    
    print('Connecting to server ...')

    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientSocket.connect((host, port))                  #connect to the server
    clientSocket.setblocking(False)
    
    print('Connection to server established. Sending intro message...')
    print('Registration successful. Ready for messaging!')

except argparse.ArgumentError:
    if len(sys.argv) < 2:
        print("Fill in ALL command lines: <username> chat://<IP>:<port>")

    elif len(sys.argv) > 2:
        print("Too many arguments. Use in form: <username> chat://<IP>:<port>")
    
    else:
        print("Invalid command line arguments")

except Exception as e:
    print('AN ERROR HAS OCCURED: \n' .format(str(e))) 


usrnameHeader = f'{len(username):<{HEADER}}'.encode('utf-8')
clientSocket.send(usrnameHeader + username) #send the server the username header and username


def sendMessage(arg1, arg2): #called when we receive input from stdin
        message = arg1.read()
        if message:
            if message.strip('\n') == "!exit":      #if client sends !exit, disconnect
                print("Disconnecting from server...exiting!")
                disconnect = ("DISCONNECT " + username.decode("utf-8") + " CHAT/1.0").encode("utf-8") #send server a disconnect message and exit
                disconnectHeader = f'{len(disconnect):<{HEADER}}'.encode('utf-8')
                clientSocket.send(disconnectHeader + disconnect)
                sys.exit(0)

            else:
                message = "@" + username.decode('utf-8') + ": " + message   #send message to server 
                message = message.strip('\n').encode('utf-8') 
                messageHeader = f"{len(message):<{HEADER}}".encode('utf-8') 
                clientSocket.send((messageHeader + message)) 


def readMessage(conn, mask): #called when we receive input from server
    try:
        usrnameHeader = clientSocket.recv(HEADER) #get username header

        if not len(usrnameHeader): #if receive no data, server closed
            print("Disconnected from server...exiting!") 
            sys.exit()

        usrnameLength = int(usrnameHeader.decode('utf-8').strip())
        username = clientSocket.recv(usrnameLength).decode('utf-8')

        messageHeader = clientSocket.recv(HEADER)
        messageLength = int(messageHeader.decode('utf-8').strip())
        message = clientSocket.recv(messageLength).decode('utf-8')


        if message.startswith("REQUEST"): #if we receive a REQUEST from the server
            filename = message.split(" ")
            filename = filename[1]
            try:
                filesize = str(os.path.getsize(filename)) #get filesize of requested file               
                delimiter = "<delimiter>"

                fileInformation = (filename + delimiter + filesize).encode("utf-8")
                fileHeader = f"{len(fileInformation):<{HEADER}}".encode('utf-8')
                clientSocket.send(fileHeader + fileInformation)         #send server the filename and filesize

                f = open(filename, 'rb')
                l = f.read(4096)
                while(l):                                       #send over the content of the file        
                    clientSocket.sendall(l)
                    l = f.read(4096)
                f.close()
                print("Attachment " + filename + " attached and distributed")

            except FileNotFoundError as e:              #if filename is not in directory, print error
                fileInformation = ("ERROR").encode("utf-8")
                fileHeader = f"{len(fileInformation):<{HEADER}}".encode('utf-8')
                clientSocket.send(fileHeader + fileInformation) 



        elif message.startswith("RECEIVE"):                 #if we receive a RECEIVE from the server
            received = clientSocket.recv(4096).decode()     #get filename, filesize, and sender name of incoming
            filename, filesize, sender = received.split("<delimiter>") 
            filename = os.path.basename(filename)
            filesize = int(filesize)

            print(" ")
            print("Incoming file: " + filename)
            print("Origin: " + sender)
            print("Content-Length: " + str(filesize))
            
            with open(filename, "wb") as f:  #download the file
                readSize = 0
                while True:
                    dataRead = clientSocket.recv(4096)
                    readSize = readSize + 4096
                    if not dataRead:         #if nothing received, process is done
                        break

                    f.write(dataRead)

                    if readSize >= filesize: #if we've read more than enough of the filesize, theres nothing to download
                        break


        else:                           #if its not a command from the server, print the incoming message
            print(f'{message}')


    except IOError as e: 
        if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
            print('Reading error: {}'.format(str(e)))
            sys.exit()

    except Exception as e:
        print(e) 
        sys.exit()

mySelector.register(clientSocket, selectors.EVENT_READ, readMessage)    #when we receive messages from server, handle at readMessage
mySelector.register(sys.stdin, selectors.EVENT_READ, sendMessage)       #when we get input from stdin, send message through sendMessage


def main():
    while(1):
        sys.stdout.write('> ')
        sys.stdout.flush()
        for k, mask in mySelector.select():
            callback = k.data
            callback(k.fileobj, mask)


if __name__ == '__main__':
    main()

