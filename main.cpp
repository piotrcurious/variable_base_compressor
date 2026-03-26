#include "mock_arduino.h"
#include <vector>

MockSerial Serial;

int main() {
    setup();
    // For mock, loop once
    loop();
    return 0;
}
