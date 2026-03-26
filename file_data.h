#ifndef FILE_DATA_H
#define FILE_DATA_H
struct FileData {
    const char* name;
    const unsigned char* data;
    unsigned int len;
    unsigned long bits;
};
#endif
