#ifndef MOCK_ARDUINO_H
#define MOCK_ARDUINO_H

#include <iostream>
#include <vector>
#include <chrono>
#include <cstdint>

#define pgm_read_byte_near(addr) (*(const uint8_t*)(addr))
#define pgm_read_word_near(addr) (*(const int16_t*)(addr))
#define PROGMEM

class MockSerial {
public:
    void begin(int speed) {}
    void print(const char* s) { std::cout << s; }
    void print(int n) { std::cout << n; }
    void print(unsigned long n) { std::cout << n; }
    void println(const char* s = "") { std::cout << s << std::endl; }
    void println(int n) { std::cout << n << std::endl; }
    void println(unsigned long n) { std::cout << n << std::endl; }
};

extern MockSerial Serial;

inline unsigned long micros() {
    auto now = std::chrono::steady_clock::now();
    return std::chrono::duration_cast<std::chrono::microseconds>(now.time_since_epoch()).count();
}

#endif
