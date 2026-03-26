#ifndef FILE_DATA_H
#define FILE_DATA_H
#include <stdint.h>
struct FileData {
    const char* name;
    const uint8_t* data;
    unsigned int len;
    unsigned long bits;
};
#endif
