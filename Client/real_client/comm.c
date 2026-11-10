#include "comm.h"
#include <WinSock2.h>
#include <ws2tcpip.h>
#include <stdio.h>


int send_and_receive(const char* message, char* reply, int reply_max_len){
    WSADATA wsadata;
    struct sockaddr_in  sockaddr ;
    int bytes_received;
    if (WSAStartup(MAKEWORD(2,2), &wsadata) < 0){
        printf("Can't init WSA\n");
    }
    SOCKET sock = socket(AF_INET, SOCK_STREAM, 0);
    sockaddr.sin_family = AF_INET;
    sockaddr.sin_port = htons(9000);
    sockaddr.sin_addr.s_addr = inet_addr("127.0.0.1");
    int connection_established = connect(sock,  (struct sockaddr *) &sockaddr, sizeof(sockaddr));
    if(connection_established == 0){
        int sent_successfully = send(sock, message, strlen(message), 0);
        printf("Finished Sending with results: %d\n", sent_successfully);
        if (sent_successfully != SOCKET_ERROR){
            do{
                bytes_received = recv(sock, reply, reply_max_len, 0);
                printf("Received %d bytes.\n", bytes_received);
            } while (bytes_received > 0);
            int socket_closed = closesocket(sock);
            WSACleanup();
        }
        else {
            printf("Couldn't send keepalive\n");
            int socket_closed = closesocket(sock);
            WSACleanup();
            return -1;
        }
    }
    else {
        printf("\nCan't connect to server\n");
        return -1;
    }
    return 0;

}

