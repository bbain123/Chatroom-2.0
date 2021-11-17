# Chatroom-2.0
Python server and client scripts that utilize socket programming (TCP). Clients can send other clients connected to the server messages, attach files, and follow specific topics or users 

## How to use
1. Run serverchat.py with at least Python3. Download python: https://www.python.org/downloads/
2. Run clientchat.py with arguments "*yourUsrname* chat://localhost:*portNumber*"
> Ex. python3 clientchat.py Brendan chat://localhost:12345

  
Note: You may connect up to 20 clients to the server  
To receive messages from other clients, you must be following a topic in their message
By default, all clients follow @all and @*yourUsrname*. You cannot unfollow these terms.  


## Commands
Commands you can use in clientchat.py:
- **!list**: displays a list of all active users on the server
- **!follow?**: displays your following list
- **!follow** ***term***: Adds *term* to your following list
- **!unfollow** ***term***: Removes *term* from your following list
- **!attach** ***filename*** ***message***: Attaches and sends the file *filename*. *message* can be left blank
- **!exit**: Disconnects from the server
>Note: The file you attach must be in the directory you're running clientchat.py in. To test with multiple clients running, I suggest you run them from different directories to avoid clobbering files

