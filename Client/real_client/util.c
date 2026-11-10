#include "util.h"
#include <windows.h>
#include <string.h>
#include <stdio.h>

int parse_data(char* buffer, char ** commands){
    int length = strlen(buffer);
    commands[0] = buffer;
    commands[1] = 0;
    for(int i = 0; i < length; i++){
        if (buffer[i] == ' '){
            buffer[i] = '\0';
            commands[1] = &buffer[i+1];
            break;
        }
    }
    return 0;
}

int get_unique_id(char* buffer){
    HKEY hkey;
    LPCWSTR lpSubKey =  L"SOFTWARE\\Microsoft\\Cryptography";
    LPCWSTR value = L"MachineGuid";
    WCHAR keyString[40];
    DWORD size = sizeof(keyString);
    memset(buffer, 0, 10);
    RegOpenKeyExW(HKEY_LOCAL_MACHINE, lpSubKey, 0, KEY_QUERY_VALUE , &hkey);
    RegQueryValueExW(hkey, value, NULL, NULL,(LPBYTE) keyString, &size);
    wprintf(keyString);
    for (int i = 0; i < 40; i++){
        buffer[i % 10] = buffer[i % 10] ^ keyString[i];
    }
    for (int i = 0; i < 10; i++){
        buffer[i] = buffer[i] % 26 + 97;
    }
    buffer[10] = 0;
    return 0;


}