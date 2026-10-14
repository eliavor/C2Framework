#ifndef PROTOCOL_H
#define PROTOCOL_H

typedef enum {
    CMD_KEEPALIVE = 0,
    CMD_OK = 1,
    CMD_SHELL = 2
} CommandType;

const char* const commands[] = {"keepalive", "OK", "shell_exec"};

#endif