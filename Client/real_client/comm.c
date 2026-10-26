#include "comm.h"
#include <WinSock2.h>
#include <ws2tcpip.h>


int send_and_receive(const char* message, char* reply, int reply_max_len){
    LPWSADATA wsadata;
    SOCKADDR_IN sockaddr ;
    int bytes_received;
    WSAStartup(MAKEWORD(2,2), wsadata);
    SOCKET sock = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    sockaddr.sin_family = AF_INET;
    sockaddr.sin_port = htons(9000);
    inet_pton(AF_INET, "127.0.0.1", &sockaddr.sin_addr);
    int connection_established = connect(sock,  (SOCKADDR *) &sockaddr, sizeof(sockaddr));
    int sent_successfully = send(sock, message, strlen(message), 0);
    do{
        bytes_received = recv(sock, reply, reply_max_len, 0);
    } while (bytes_received > 0);
    int socket_closed = closesocket(sock);
    WSACleanup();

    return 0;

}

