// Include the header files with the compressed data and the common parameters
#include "common.h"
#include "file1.h"
#include "file2.h"
#include "file3.h"

// Define constants
#define MAX_FILES 3 // Maximum number of files to decompress
#define MAX_FILE_SIZE 1024 // Maximum size of each file in bytes

// Define global variables
int common_denom; // The common denominator for all data
int base_size; // The custom number base size

// Define functions
void setup() {
  // Initialize serial communication at 9600 bits per second
  Serial.begin(9600);

  // Read the common parameters from the common header file
  common_denom = pgm_read_word_near(common_h); // The first element is the common denominator
  base_size = pgm_read_word_near(common_h + 1); // The second element is the base size
  
}

void loop() {
  
  // Decompress each compressed file using the frequency table, the multiplication table and the base size with variable-length codes
  for (int i = 0; i < MAX_FILES; i++) {
    int index = 0; // Initialize an index variable to keep track of the current position in the compressed file byte array
    int bit_index = 7; // Initialize a bit index variable to keep track of the current position in the current byte
    int freq = 0; // Initialize a frequency variable to store the frequency of each data element
    int mod = 0; // Initialize a modulo variable to store the modulo of each data element
    
    Serial.print("File ");
    Serial.print(i + 1);
    Serial.print(": ");
    
    for (int j = 0; j < MAX_FILE_SIZE; j++) {
      if (index >= sizeof(file1_h) / sizeof(file1_h[0]) / base_size) { // If reached the end of file1, break out of the loop
        break;
      }
      
      byte current_byte = pgm_read_byte_near(file1_h + index * base_size); // Get the current byte from file1
      
      while (bit_index >= 0) { // Loop over each bit in the current byte
        
        if (freq == 0) { // If frequency is zero, read unary code until a zero bit is encountered
          if (current_byte & (1 << bit_index)) { // If current bit is one, increment frequency
            freq++;
          } else { // If current bit is zero, stop reading frequency and read modulo
            bit_index--; // Decrement bit index
            break;
          }
        } else { // If frequency is non-zero, read modulo as a byte
          mod = current_byte; // Set modulo to current byte
          bit_index = -1; // Set bit index to -1 to move to the next byte
          break;
        }
        
        bit_index--; // Decrement bit index
      }
      
      if (bit_index == -1) { // If bit index is -1, move to the next byte
        index++; // Increment index
        bit_index = 7; // Reset bit index to 7
      }
      
      if (freq > 0 && mod > 0) { // If both frequency and modulo are non-zero, decode the data element
        
        int mult = pgm_read_word_near(common_h + freq * base_size + mod % base_size + 2 + base_size * 2); 
// Get the corresponding value from the multiplication table using frequency and modulo
        
        for (int k = 0; k < base_size; k++) { // Loop over the keys in the frequency table to find the matching value
          if (pgm_read_word_near(common_h + k + 2 + base_size) == mult) { 
// If found a matching value, decode the data element and print it to serial port
            
            Serial.print(k * common_denom, HEX); 
// Multiply the key by the common denominator and print it in hexadecimal format
            
            break;
          }
        }
        
        freq = 0; // Reset frequency to zero
        mod = 0; // Reset modulo to zero
      }
    }
    
    Serial.println(); 
// Print a new line
    
  }

  // Stop the loop
  while (true);
}
