#ifndef UTIL_H
#define UTIL_H

// takes in a buffer and a string array of size 2, and splits them to 2 strings in the first space. Then returns the addresses of the 2 strings inside commands.
int parse_data(char* buffer, char ** commands);
int get_unique_id(char* buffer);

#endif