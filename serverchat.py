import socket
import select
import string
import sys
import signal
import os

BUFFER = 1024
HEADER = 1024


def signal_handler(sig, frame):
    print('Interrupt received, shutting down ...')
    sys.exit(0)

def receiveMessage(clientSocket):
    try:
        textHeader = clientSocket.recv(HEADER) #read the message header
        if len(textHeader) == 0:     #if connection closed, no header, exit
            return False 
        
        textLength = int(textHeader.decode('utf-8').strip()) #get length of message
        return {'header': textHeader, 'data': clientSocket.recv(textLength)} #return the header and the message
        
    except:

        return False

def main():
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) #allow people to reconnect to server
    serverSocket.bind(('', 0))  
    serverSocket.listen(20)
    signal.signal(signal.SIGINT, signal_handler)                    #set up listener to exit

    print('Will wait for client connections at port ' + str(serverSocket.getsockname()[1]))
    print('Waiting for incoming client connections ...')

    socketList = [serverSocket]                                     #list of all connected sockets
    clients = {}                                                    #dictionary of client usernames and corresponding ports
    terms = {}                                                      #key: username  value: list of followed terms


    while(1):   #continue to listen for messages
                                        
            readSocket, writeSocket, errorSocket = select.select(socketList, [], socketList) #get sockets that have data in them and store in readSocket
            
            
            #go through the sockets with data in them
            for dataSocket in readSocket:
                if dataSocket == serverSocket:                          #if the socket is from server, new connection
                    clientSocket, clientAddress = serverSocket.accept() #get their socket number and username
                    user = receiveMessage(clientSocket)
                    
                    if user is False: 
                        continue
                
                    socketList.append(clientSocket)                     #add their socket to the list of connections
                    clients[clientSocket] = user
                    terms[user["data"].decode("utf-8")] = ["@all", "@" + user["data"].decode("utf-8")] #add @all and @<usrname> to their following list
                    print('Accepted connection from client address: ({}, {})'.format(*clientAddress, clientSocket))
                    print(f'Connection to client established, waiting to receive messages from user \' {user["data"].decode("utf-8")} \'...')

                else:   #it is a message 
                    message = receiveMessage(dataSocket)

                    if message is False: #if its empty because someone disconnected
                        continue
                        
                    else:   #the message contains something
                        user = clients[dataSocket]  
                        print(f'Received message from user {user["data"].decode("utf-8")} : {message["data"].decode("utf-8")}')
                        
                        if message['data'].decode("utf-8").startswith("DISCONNECT"): #remove disconnecting user
                            print('Disconnecting user {}'.format(clients[dataSocket]['data'].decode('utf-8')))
                            socketList.remove(dataSocket)                            #remove user
                            del clients[dataSocket]


                        else:
                            #check if message is a command
                            followMessage = ("").encode("utf-8")            #set default message
                            sentence = message['data'].decode("utf-8")      #the raw string received
                            symbols = string.punctuation.replace("@", "")  #string of all punctuation excluding @
                            filteredMessage = ''.join(' ' if c in symbols else c for c in sentence) #the message stripped of punctuation
                            filteredMessage = filteredMessage.split()
                            del filteredMessage[0]                          #get rid of <username> at beginning of message
                                
                            sentence = sentence.split()                                 
                            del sentence[0]                                 #get rid of <username> at beginning of message

                            

                            if sentence[0] == "!follow":
                                if len(sentence) == 2:
                                    if(sentence[-1] in terms[user["data"].decode("utf-8")]):    #if already following topic
                                        followMessage = ("Already following " + sentence[-1]).encode("utf-8")
                                         
                                    else:
                                        terms[user["data"].decode("utf-8")].append(sentence[-1])       #add the term to term list
                                        followMessage = ("Now following " + sentence[-1]).encode("utf-8")

                                else:
                                    followMessage = ("Please use in form '!follow <term>'").encode("utf-8") #if used incorrectly

                                followHeader = f"{len(followMessage):<{HEADER}}".encode('utf-8')
                                dataSocket.send(user['header'] + user['data'] + followHeader + followMessage) 


                            elif sentence[0] == "!follow?":
                                if len(sentence) == 1:
                                    followMessage = (", ".join(terms[user["data"].decode("utf-8")])).encode("utf-8") #display follow list
                                     
                                else:
                                    followMessage = ("Please use in form '!follow?'").encode("utf-8")   #if used incorrectly

                                followHeader = f"{len(followMessage):<{HEADER}}".encode('utf-8')
                                dataSocket.send(user['header'] + user['data'] + followHeader + followMessage)


                            elif sentence[0] == "!unfollow":
                                if len(sentence) == 2:
                                    if(not sentence[-1] in terms[user["data"].decode("utf-8")]):    #if not following that term
                                        followMessage = ("You already aren't following " + sentence[-1]).encode("utf-8")

                                    else:
                                        if sentence[-1].strip("\n") == "@all" or sentence[-1].strip("\n") == ("@" + user["data"].decode("utf-8")): #if trying to unfollow default follows
                                            followMessage = ("You cannot unfollow " + sentence[-1]).encode("utf-8")
                                        else:
                                            terms[user["data"].decode("utf-8")].remove(sentence[-1]) #remove the term from the term list
                                            followMessage = ("Unfollowing " + sentence[-1]).encode("utf-8")
                                else:
                                    followMessage = ("Please use in form '!unfollow <term>'").encode("utf-8")  #if used incorrectly

                                followHeader = f"{len(followMessage):<{HEADER}}".encode('utf-8')
                                dataSocket.send(user['header'] + user['data'] + followHeader + followMessage) 


                            elif sentence[0] == "!list":
                                if len(sentence) == 1:
                                    activeUsers = []
                                    for clientSocket in clients:
                                        activeUsers.append(((clients[clientSocket])["data"]).decode("utf-8"))
                                    followMessage = (", ".join(activeUsers)).encode("utf-8")      #send list of active users
                                     
                                else:
                                    followMessage = ("Please use in form '!list'").encode("utf-8")    #if used incorrectly

                                followHeader = f"{len(followMessage):<{HEADER}}".encode('utf-8')
                                dataSocket.send(user['header'] + user['data'] + followHeader + followMessage)
                                
                            

                            elif sentence[0] == "!attach":
                                if len(sentence) > 1:
                                    followMessage = ("REQUEST " + sentence[1]).encode("utf-8")
                                    followHeader = f"{len(followMessage):<{HEADER}}".encode('utf-8')
                                    dataSocket.send(user['header'] + user['data'] + followHeader + followMessage) #send the client a request for file
                                     
                                    received = receiveMessage(dataSocket)                           #receive responce from client
                                    if received["data"].decode("utf-8").startswith("ERROR"):        #if the client could not find the file to send
                                        followMessage = ("Could not find file " + sentence[1]).encode("utf-8")
                                        followHeader = f"{len(followMessage):<{HEADER}}".encode('utf-8')
                                        dataSocket.send(user['header'] + user['data'] + followHeader + followMessage) #send the client the error

                                    else:
                                        filename, filesize = received['data'].decode("utf-8").split("<delimiter>") #get the filename and size
                                        filename = os.path.basename(filename)
                                        

                                        with open(filename, "wb") as f:  #download the file
                                            readSize = 0
                                            while True:
                                                dataRead = dataSocket.recv(4096)
                                                readSize = readSize + 4096
                                                if not dataRead:        #if nothing received, process is done
                                                    break
                                                
                                                f.write(dataRead)
                                                if readSize >= int(filesize): #if read at least the size of the file
                                                    break

                                        f.close()

                                        for clientSocket in clients:  #find the users that the file should be sent to 
                                            if clientSocket != dataSocket:
                                                currUsrname = clients[clientSocket]

                                                for word in filteredMessage:    #compare each word in the message without punctuation to all active users following list
                                                    if word in terms[currUsrname["data"].decode('utf-8')] or "@" + (clients[dataSocket])["data"].decode("utf-8") in terms[currUsrname["data"].decode('utf-8')]:
                                                        
                                                        followMessage = ("RECEIVE").encode("utf-8")                         #let the client know something is going to be downloaded           
                                                        followHeader = f"{len(followMessage):<{HEADER}}".encode('utf-8')
                                                        clientSocket.send(user['header'] + user['data'] + followHeader + followMessage) 
                                                        
                                                        sender = (clients[dataSocket])["data"].decode("utf-8")              #send the client the filename, filesize, and sender
                                                        delimiter = "<delimiter>"
                                                        clientSocket.send(f"{filename}{delimiter}{filesize}{delimiter}{sender}".encode("utf-8")) 

                                                        f = open(filename, 'rb')
                                                        l = f.read(4096)
                                                        while(l):                                           #send over the content of the file        
                                                            clientSocket.sendall(l)
                                                            l = f.read(4096)
                                                        f.close()
                        
                                                        break
                                        
                                        os.remove(filename)                                                 #delete the downloaded file from the server


                                else:
                                    followMessage = ("Please use in form '!attach <filename> <term1> <term2> ...'").encode("utf-8")  #if used incorrectly 

                                    followHeader = f"{len(followMessage):<{HEADER}}".encode('utf-8')
                                    dataSocket.send(user['header'] + user['data'] + followHeader + followMessage)




                            else: #send message to all clients that follow a term in the message
                                
                                for clientSocket in clients:
                                    if clientSocket != dataSocket:
                                        currUsrname = clients[clientSocket]

                                        for word in filteredMessage:
                                            if word in terms[currUsrname["data"].decode('utf-8')] or "@" + (clients[dataSocket])["data"].decode("utf-8") in terms[currUsrname["data"].decode('utf-8')]:
                                                clientSocket.send(user['header'] + user['data'] + message['header'] + message['data'])
                                                break
                                        


if __name__ == '__main__':
    main()