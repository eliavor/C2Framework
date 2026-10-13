# Initial Description & Requirements
This project will include a full C2 Framework. 
It will consist of 2 main parts - a client and a server.

## Server
The server will be centralized, and will have access to all the different clients that are currently connected.
It will provide an interface to choose a client and control it remotely, and will have access to all the functionality of a client.
The server will be written in a high level language (python) to save time and make implementation easier.

## Client
This is the interesting part of the project. 
The client will be a program that supplies the server with functionalities on an infected device.
The functionalities are yet to be determined.
The client will be written in C and will have to work even when there are AVs and EDRs on the host.

## Protocol
The client and the server will communicate via a shared protocol. 
The initial implementation should be simple but it should get more complex and less triggering the more I advance the project.