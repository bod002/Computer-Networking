# UDP-chat-server
simple chat server
my server is able to run by activating it through a terminal using "python3 .../.../chatServer.py"     note that custom port can be entered after this entery.
Then clients can be added by using other terminals using "nc -u localhost 12346"       note that 12346 is the port
The client can send messages by inputing things in the terminal.
these inputs show up on the server end with the name and ip of the client that sent them
the inputs with the name and ip of the sender also aper as well as for the other cleints
"/nick nickname" input will make "nickname" repace the name and IP for the server and other clients
"/list" will give the client a list of all the client connected to the server
"/quit" will give the client a little goodby message and remove that client from the server effectivly dissconnecting it
