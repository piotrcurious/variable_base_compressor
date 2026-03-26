#ifndef MOCK_ARDUINO_H
#define MOCK_ARDUINO_H

#include <iostream>
#include <iomanip>
#include <vector>
#include <string>
#include <stdint.h>

#define PROGMEM
#define pgm_read_byte_near(addr) (*(const uint8_t*)(addr))
#define pgm_read_word_near(addr) (*(const int16_t*)(addr))

typedef uint8_t byte;

class MockSerial {
public:
    void begin(int baud) {}
    void print(const char* s) { std::cout << s; }
    void print(int n) { std::cout << n; }
    void print(std::string s) { std::cout << s; }
    void print(int n, int base) {
        if (base == 16) {
            std::cout << std::hex << n << std::dec;
        } else {
            std::cout << n;
        }
    }
    void println(const char* s = "") { std::cout << s << std::endl; }
    void println(int n) { std::cout << n << std::endl; }
};

extern MockSerial Serial;

void setup();
void loop();

#endif
