#ifndef MOCK_ARDUINO_H
#define MOCK_ARDUINO_H

#include <iostream>
#include <iomanip>
#include <vector>
#include <string>
#include <stdint.h>
#include <chrono>

#define PROGMEM
#define pgm_read_byte_near(addr) (*(const uint8_t*)(addr))
#define pgm_read_word_near(addr) (*(const int16_t*)(addr))

typedef uint8_t byte;

class MockSerial {
public:
    void begin(int baud) {}
    void print(const char* s) { std::cout << s; }
    void print(int n) { std::cout << n; }
    void print(unsigned int n) { std::cout << n; }
    void print(unsigned long n) { std::cout << n; }
    void print(double d) { std::cout << d; }
    void print(std::string s) { std::cout << s; }
    void print(int n, int base) {
        if (base == 16) {
            std::cout << "0x" << std::hex << n << std::dec;
        } else {
            std::cout << n;
        }
    }
    void println(const char* s = "") { std::cout << s << std::endl; }
    void println(int n) { std::cout << n << std::endl; }
    void println(unsigned int n) { std::cout << n << std::endl; }
    void println(unsigned long n) { std::cout << n << std::endl; }
    void println(double d) { std::cout << d << std::endl; }
};

extern MockSerial Serial;

inline unsigned long micros() {
    static auto start = std::chrono::steady_clock::now();
    auto now = std::chrono::steady_clock::now();
    return (unsigned long)std::chrono::duration_cast<std::chrono::microseconds>(now - start).count();
}

#endif
