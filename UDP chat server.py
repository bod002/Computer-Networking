# -*- coding: utf-8 -*-
"""
Created on Mon Feb  6 12:00:29 2023

@author: footf
"""

import socket
from sys import argv
    
def RunHost():
    port = 12346

    #user chose port when makeing the server
    if (len(argv)>1):
        port = int(argv[1])

    #creates socket that is usable for the internet
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    fullAdress = serverSocket.bind(('0.0.0.0', port))
    
    print('server is up on port: ' + str(port))
    clients=[]
    nName = [""]*100
    
    while True:
        data, clientAdress = serverSocket.recvfrom(4096)

        #adds client to list if not already connected
        if (clients.count(clientAdress) == 0):
            clients.append(clientAdress)

        temp = clients.index(clientAdress) #save index for future logic
        data = data.decode() #turns data into a string

        #establish nickname function
        if data[:5] == "/nick":
            nName[temp] = data[6:-1]

        #quit from server function
        if data[:5] == "/quit":
            serverSocket.sendto(b'Goodbye!', clientAdress)
            clients.remove(clientAdress)
        
        #listing all the cleints function
        if data[:5] == "/list":
            serverSocket.sendto(str(clients).encode(), clientAdress)



        if nName[temp] == '': #no established nickname
            print(clientAdress[0]+' '+ str(clientAdress[1])+ ": " +data[0:-1])
            data = clientAdress[0] + ": " + data
        else: #established nickname
            print(nName[temp]+ ': ' +data[0:-1])
            data = nName[temp] + ": " + data

        #sends the activty to all the clients
        for i in clients:
            if (i != clientAdress):
                serverSocket.sendto(data.encode(),i)


RunHost()