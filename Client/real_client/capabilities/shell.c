#include "shell.h"
#include <string.h>
#include <stdio.h>

int run_command(char* command, char* output, int max_output_len){
    printf(command);
    FILE* result_stream = _popen(command, "r");
    int chatacters_left = max_output_len;
    // char* fgets_result = fgets(output, max_output_len, result_stream);
    while (fgets(output+strlen(output), chatacters_left, result_stream)){
        chatacters_left = max_output_len - strlen(output);
        if(chatacters_left == 1){
            printf("No more room in buffer.\n");
            break;
        } 
    }
    printf("Final Output: \n%s\n", output);
    _pclose(result_stream);

    return 0;
}
