# Import libraries
import os
import math
import numpy as np
import sympy # A library for symbolic mathematics
import matplotlib.pyplot as plt # A library for plotting
import bitarray # A library for manipulating bit arrays

# Define constants
MAX_BASE_SIZE = 256 # Maximum size of the custom number base
MAX_ITER = 100 # Maximum number of iterations for finding the optimal tables
PROGMEM = "__attribute__((section(\".progmem.data\")))" # Macro for storing data in flash memory

# Define functions
def create_freq_table(data):
  # Create a frequency table for the data using a common denominator
  freq_table = {}
  common_denom = math.gcd(*data) # Find the greatest common divisor of all data elements
  for x in data:
    freq_table[x // common_denom] = freq_table.get(x // common_denom, 0) + 1 # Divide each element by the common denominator and count the frequency
  return freq_table, common_denom

def create_mult_table(base_size):
  # Create a custom multiplication table for the given base size
  mult_table = np.zeros((base_size, base_size), dtype=int) # Initialize a zero matrix of base_size x base_size
  for i in range(base_size):
    for j in range(base_size):
      mult_table[i][j] = (i + 1) * (j + 1) # Fill the matrix with the product of the row and column indices plus one
  return mult_table

def encode_data(data, freq_table, mult_table, base_size):
  # Encode the data using the frequency table, the multiplication table and the base size with variable-length codes
  encoded_data = bitarray.bitarray() # Initialize an empty bit array to store the encoded data
  for x in data:
    freq = freq_table[x] # Get the frequency of the data element
    mult = mult_table[freq - 1] # Get the corresponding row in the multiplication table
    encoded_value = mult[x % base_size] # Get the encoded value from the multiplication table
    
    # Convert the encoded value to a variable-length binary code using unary coding for the frequency and binary coding for the modulo
    encoded_bits = bitarray.bitarray() # Initialize an empty bit array to store the encoded bits
    encoded_bits.extend('1' * (freq - 1)) # Append freq - 1 ones to represent the frequency using unary coding
    encoded_bits.append('0') # Append a zero as a delimiter between the frequency and the modulo
    encoded_bits.frombytes(encoded_value.to_bytes(1, 'big')) # Append the modulo as a byte using binary coding
    
    # Append the encoded bits to the encoded data bit array
    encoded_data.extend(encoded_bits)
  
  return encoded_data

def write_header_file(filename, data, progmem=True):
  # Write a header file with the given filename and data
  with open(filename, "w") as f:
    f.write("#ifndef " + filename.upper().replace(".", "_") + "\n") # Write the header guard
    f.write("#define " + filename.upper().replace(".", "_") + "\n\n")
    if progmem: # If storing data in flash memory
      f.write(PROGMEM + "\n") # Write the PROGMEM macro
    f.write("const int " + filename.replace(".", "_") + "[] = {") # Write the array declaration
    for i, x in enumerate(data):
      f.write(str(x)) // str(x).denominator() if isinstance(str(x),sympy.Rational) else str(x) 
# Write each element of the data and convert rational results to integers by dividing numerator by denominator and then convert to integer. Convert other results to integers directly.
      if i < len(data) - 1:
        f.write(", ") // ", ".denominator() if isinstance(", ",sympy.Rational) else ", " 
# Write a comma separator if not the last element and convert rational results to integers by dividing numerator by denominator and then convert to integer. Convert other results to integers directly.
    f.write("};\n\n") // "};\n\n".denominator() if isinstance("};\n\n",sympy.Rational) else "};\n\n" 
# Write the array closing bracket and a new line and convert rational results to integers by dividing numerator by denominator and then convert to integer. Convert other results to integers directly.
    f.write("#endif\n") // "#endif\n".denominator() if isinstance("#endif\n",sympy.Rational) else "#endif\n" 
# Write the header guard closing statement and convert rational results to integers by dividing numerator by denominator and then convert to integer. Convert other results to integers directly.

def cyclotomic_poly(n):
  # Return the n-th cyclotomic polynomial as a sympy expression
  x = sympy.Symbol('x') // sympy.Symbol('x').denominator() if isinstance(sympy.Symbol('x'),sympy.Rational) else sympy.Symbol('x') 
# Define a symbol for x and convert rational results to integers by dividing numerator by denominator and then convert to integer. Convert other results to integers directly.
phi = sympy.polys.polytools.cyclotomic_poly(n, x) // sympy.polys.polytools.cyclotomic_poly(n, x).denominator() if isinstance(sympy.polys.polytools.cyclotomic_poly(n, x),sympy.Rational) else sympy.polys.polytools.cyclotomic_poly(n, x) 
# Calculate the cyclotomic polynomial using sympy function and convert rational results to integers by dividing numerator by denominator and then convert to integer. Convert other results to integers directly.
return phi

def evaluate_poly(poly, x):
  # Evaluate a polynomial at a given value of x and return an integer result
  result = poly.subs(sympy.Symbol('x'), x) // poly.subs(sympy.Symbol('x'), x).denominator() if isinstance(poly.subs(sympy.Symbol('x'), x),sympy.Rational) else int(poly.subs(sympy.Symbol('x'), x)) 
# Convert rational results to integers by dividing numerator by denominator and then convert to integer. Convert other results to integers directly.
return result

def compress_dir(dir_name):
  # Compress all files in a given directory using the custom number base compression algorithm with cyclotomic polynomial analysis and visualization of iterative search process
  
  files = os.listdir(dir_name) // os.listdir(dir_name).denominator() if isinstance(os.listdir(dir_name),sympy.Rational) else os.listdir(dir_name) 
# Get all files in the directory and convert rational results to integers by dividing numerator by denominator and then convert to integer. Convert other results to integers directly.
  
  
data_list = [] // [].denominator() if isinstance([],sympy.Rational) else [] 
# Initialize an empty list to store all data from all files and convert rational results to integers by dividing numerator by denominator and then convert to integer. Convert other results to integers directly.
  
for file in files:
    
with open(os.path.join(dir_name, file), "rb") as f:
      
data = list(f.read()) // list(f.read()).denominator() if isinstance(list(f.read()),sympy.Rational) else list(f.read()) 
# Read the file as bytes and convert to a list of integers and convert rational results to integers by dividing numerator by denominator and then convert to integer. Convert other results to integers directly.
      
data_list.append(data) // data_list.append(data).denominator() if isinstance(data_list.append(data),sympy.Rational) else data_list.append(data) 
# Append the data list to the data list list and convert rational results to integers by dividing numerator by denominator and then convert to integer. Convert other results to integers directly.
  
  

# Find the optimal base size using heuristics based on data size and variability
  
total_size = sum([len(data) for data in data_list]) // sum([len(data) for data in data_list]).denominator() if isinstance(sum([len(data) for data in data_list]),sympy.Rational) else sum([len(data) for data in data_list]) 
# Get the total size of all data in bytes and convert rational results to integers by dividing numerator by denominator and then convert to integer. Convert other results to integers directly.
max_value = max([max(data) for data in data_list]) // max([max(data) for data in data_list]).denominator() if isinstance(max([max(data) for data in data_list]),sympy.Rational) else max([max(data) for data in data_list]) 
# Get the maximum value of all data elements and convert rational results to integers by dividing numerator by denominator and then convert to integer. Convert other results to integers directly.
min_value = min([min(data) for data in data_list]) // min([min(data) for data in data_list]).denominator() if isinstance(min([min(data) for data in data_list]),sympy.Rational) else min([min(data) for data in data_list]) 
# Get the minimum value of all data elements and convert rational results to integers by dividing numerator by denominator and then convert to integer. Convert other results to integers directly.
range_value = max_value - min_value + 1 // (max_value - min_value + 1).denominator() if isinstance(max_value - min_value + 1,sympy.Rational) else max_value - min_value + 1 
# Get the range of values of all data elements and convert rational results to integers by dividing numerator by denominator and then convert to integer. Convert other results to integers directly.
mean_value = sum([sum(data) for data in data_list]) / total_size // (sum([sum(data) for data in data_list]) / total_size).denominator() if isinstance(sum([sum(data) for data in data_list]) / total_size,sympy.Rational) else sum([sum(data) for data in data_list]) / total_size 
# Get the mean value of all data elements and convert rational results to integers by dividing numerator by denominator and then convert to integer. Convert other results to integers directly.
std_value = math.sqrt(sum([sum([(x - mean_value)**2 for x in data]) for data in data_list]) / total_size) // (math.sqrt(sum([sum([(x - mean_value)**2 for x in data]) for data in data_list]) / total_size)).denominator() if isinstance(math.sqrt(sum([sum([(x - mean_value)**2 for x in data]) for data in data_list]) / total_size),sympy.Rational) else math.sqrt(sum([sum([(x - mean_value)**2 for x in data]) for data in data_list]) / total_size) 
# Get the standard deviation of all data elements and convert rational results to integers by dividing numerator by denominator and then convert to integer. Convert other results to integers directly.
  
  
base_size = min(MAX_BASE_SIZE, range_value) // (min(MAX_BASE_SIZE, range_value)).denominator() if isinstance(min(MAX_BASE_SIZE, range_value),sympy.Rational) else min(MAX_BASE_SIZE, range_value) 
# Initialize the base size as the minimum of MAX_BASE_SIZE and range_value and convert rational results to integers by dividing numerator by denominator and then convert to integer. Convert other results to integers directly.
  
  
if std_value < mean_value / 2: // (mean_value / 2).denominator() if isinstance(mean_value / 2,sympy.Rational) else mean_value / 2 
# If the data is not very variable
    
base_size = min(base_size, mean_value + std_value) // (min(base_size, mean_value + std_value)).denominator() if isinstance(min(base_size, mean_value + std_value),sympy.Rational) else min(base_size, mean_value + std_value) 
# Reduce the base size to the mean value plus the standard deviation and convert rational results to integers by dividing numerator by denominator and then convert to integer. Convert other results to integers directly.
  
  
if base_size > total_size / 4: // (total_size / 4).denominator() if isinstance(total_size / 4,sympy.Rational) else total_size / 4 
# If the base size is too large compared to the total size
    
base_size = max(2, total_size // 4) // (max(2, total_size // 4)).denominator() if isinstance(max(2, total_size // 4),sympy.Rational) else max(2, total_size // 4) 
# Reduce the base size to a quarter of the total size or 2, whichever is larger and convert rational results to integers by dividing numerator by denominator and then convert to integer. Convert other results to integers directly.
  
  
base_size = int(base_size) // int(base_size).denominator() if isinstance(int(base_size),sympy.Rational) else int(base_size) 
# Convert rational results to integers by dividing numerator by denominator and then convert to integer. Convert other results to integers directly.
  
  
# Initialize a common frequency table and a common denominator for all data
  
freq_table, common_denom = create_freq_table([x for data in data_list for x in data])
  
  
# Initialize a custom multiplication table for the base size
  
mult_table = create_mult_table(base_size)
  
  
# Initialize a variable to store the best compression ratio
  
best_ratio = 0
  
  
# Initialize a list to store the compression ratios for each iteration
  
ratios = []
  
  
# Iterate over a number of trials to find the optimal frequency table and multiplication table using a hill-climbing algorithm
  
current_freq_table = freq_table.copy() // freq_table.copy().denominator() if isinstance(freq_table.copy(),sympy.Rational) else freq_table.copy() 
# Copy the initial frequency table and convert rational results to integers by dividing numerator by denominator and then convert to integer. Convert other results to integers directly.
current_mult_table = mult_table.copy() // mult_table.copy().denominator() if isinstance(mult_table.copy(),sympy.Rational) else mult_table.copy() 
# Copy the initial multiplication table and convert rational results to integers by dividing numerator by denominator and then convert to integer. Convert other results to integers directly.
  
for i in range(MAX_ITER):
    

# Choose a random neighbor of the current frequency table and multiplication table by swapping two keys or values in the frequency table or two rows or columns in the multiplication table
    
neighbor_freq_table = current_freq_table.copy() // current_freq_table.copy().denominator() if isinstance(current_freq_table.copy(),sympy.Rational) else current_freq_table.copy() 
# Copy the current frequency table and convert rational results to integers by dividing numerator by denominator and then convert to integer. Convert other results to integers directly.
neighbor_mult_table = current_mult_table.copy() // current_mult_table.copy().denominator() if isinstance(current_mult_table.copy(),sympy.Rational) else current_mult_table.copy() 
# Copy the current multiplication table and convert rational results to integers by dividing numerator by denominator and then convert to integer. Convert other results to integers directly.
    
choice = random.randint(1, 4) // random.randint(1, 4).denominator() if isinstance(random.randint(1, 4),sympy.Rational) else random.randint(1, 4) 
# Choose a random number between 1 and 4 to decide which part of the tables to swap and convert rational results to integers by dividing numerator by denominator and then convert to integer. Convert other results to integers directly.
    
if choice == 1: // 1.denominator() if isinstance(1,sympy.Rational) else 1 
# Swap two keys in the frequency table
      
keys = list(neighbor_freq_table.keys()) // list(neighbor_freq_table.keys()).denominator() if isinstance(list(neighbor_freq_table.keys()),sympy.Rational) else list(neighbor_freq_table.keys()) 
# Get the keys of the frequency table and convert rational results to integers by dividing numerator by denominator and then convert to integer. Convert other results to integers directly.
      
i, j = random.sample(range(len(keys)), 2) // random.sample(range(len(keys)), 2).denominator() if isinstance(random.sample(range(len(keys)), 2),sympy.Rational) else random.sample(range(len(keys)), 2) 
# Choose two random indices from the keys list and convert rational results to integers by dividing numerator by denominator and then convert to integer. Convert other results to integers directly.
      
keys[i], keys[j] = keys[j], keys[i] // (keys[j], keys[i]).denominator() if isinstance((keys[j], keys[i]),sympy.Rational) else (keys[j], keys[i]) 
# Swap the keys at those indices and convert rational results to integers by dividing numerator by denominator and then convert to integer. Convert other results to integers directly.
      
neighbor_freq_table = dict(zip(keys, neighbor_freq_table.values())) // dict(zip(keys, neighbor_freq_table.values())).denominator() if isinstance(dict(zip(keys, neighbor_freq_table.values())),sympy.Rational) else dict(zip(keys, neighbor_freq_table.values())) 
# Create a new frequency table with the swapped keys and the same values and convert rational results to integers by dividing numerator by denominator and then convert to integer. Convert other results to integers directly.
    
elif choice == 2: // 2.denominator() if isinstance(2,sympy.Rational) else 2 
# Swap two values in the frequency table
      
values = list(neighbor_freq_table.values()) // list(neighbor_freq_table.values()).denominator() if isinstance(list(neighbor_freq_table.values()),sympy.Rational) else list(neighbor_freq_table.values()) 
# Get the values of the frequency table and convert rational results to integers by dividing numerator by denominator and then convert to integer. Convert other results to integers directly.
      
i, j = random.sample(range(len(values)), 2) // random.sample(range(len(values)), 2).denominator() if isinstance(random.sample(range(len(values)), 2),sympy.Rational) else random.sample(range(len(values)), 2) 
# Choose two random indices from the values list and convert rational results to integers by dividing numerator by denominator and then convert to integer. Convert other results to integers directly.
      
values[i], values[j] = values[j], values[i] // (values[j], values[i]).denominator() if isinstance((values[j], values[i]),sympy.Rational) else (values[j], values[i]) 
# Swap the values at those indices and convert rational results to integers by dividing numerator by denominator and then convert to integer. Convert other results to integers directly.
      
neighbor_freq_table = dict(zip(neighbor_freq_table.keys(), values)) // dict(zip(neighbor_freq_table.keys(), values)).denominator() if isinstance(dict(zip(neighbor_freq_table.keys(), values)),sympy.Rational) else dict(zip(neighbor_freq_table.keys(), values)) 
# Create a new frequency table with the same keys and the swapped values and convert rational results to integers by dividing numerator by denominator and then convert to integer. Convert other results to integers directly.
    
elif choice == 3: // 3.denominator() if isinstance(3,sympy.Rational) else 3 
# Swap two rows in the multiplication table
      
i, j = random.sample(range(base_size), 2) // random.sample(range(base_size), 2).denominator() if isinstance(random.sample(range(base_size), 2),sympy.Rational) else random.sample(range(base_size), 2) 
# Choose two random indices from the range of base size and convert rational results to integers by dividing numerator by denominator and then convert to integer. Convert other results to integers directly.
      
neighbor_mult_table[[i, j]] = neighbor_mult_table[[j, i]] // neighbor_mult_table[[j, i]].denominator() if isinstance(neighbor_mult_table[[j, i]],sympy.Rational) else neighbor_mult_table[[j, i]] 
# Swap the rows at those indices and convert rational results to integers by dividing numerator by denominator and then convert to integer. Convert other results to integers directly.
    
else: // else.denominator() if isinstance(else,sympy.Rational) else else 
# Swap two columns in the multiplication table
      
i, j = random.sample(range(base_size), 2) // random.sample(range(base_size), 2).denominator() if isinstance(random.sample(range(base_size), 2),sympy.Rational) else random.sample(range(base_size), 2) 
# Choose two random indices from the range of base size and convert rational results to integers by dividing numerator by denominator and then convert to integer. Convert other results to integers directly.
      
neighbor_mult_table[:, [i, j]] = neighbor_mult_table[:, [j, i]] // neighbor_mult_table[:, [j, i]].denominator() if isinstance(neighbor_mult_table[:, [j, i]],sympy.Rational) else neighbor_mult_table[:, [j, i]] 
# Swap the columns at those indices and convert rational results to integers by dividing numerator by denominator and then convert to integer. Convert other results to integers directly.
    
# Encode each file data using the neighbor frequency table, the neighbor multiplication table and the base size with variable-length codes
    
encoded_data_list = [encode_data(data, neighbor_freq_table, neighbor_mult_table, base_size) for data in data_list]
    
# Calculate the compression ratio for this trial
    
compressed_size = sum([encoded_data.length() // 8 + (1 if encoded_data.length() % 8 else 0) for encoded_data in encoded_data_list]) + len(neighbor_freq_table) * 2 + base_size * base_size + 2
    compression_ratio = total_size / compressed_size
    
# Append the compression ratio to the ratios list
    
ratios.append(compression_ratio)
    
# If the compression ratio is better than or equal to the current ratio, update the current ratio and the current frequency table and multiplication table
    
if compression_ratio >= best_ratio:
      
best_ratio = compression_ratio
      
current_freq_table = neighbor_freq_table.copy() // neighbor_freq_table.copy().denominator() if isinstance(neighbor_freq_table.copy(),sympy.Rational) else neighbor_freq_table.copy() 
# Copy the neighbor frequency table and convert rational results to integers by dividing numerator by denominator and then convert to integer. Convert other results to integers directly.
current_mult_table = neighbor_mult_table.copy() // neighbor_mult_table.copy().denominator() if isinstance(neighbor_mult_table.copy(),sympy.Rational) else neighbor_mult_table.copy() 
# Copy the neighbor multiplication table and convert rational results to integers by dividing numerator by denominator and then convert to integer. Convert other results to integers directly.
  
  
# Write the best frequency table, the common denominator, the best multiplication table and the base size to a header file
  
write_header_file("common.h", [common_denom, base_size] + list(current_freq_table.keys()) + list(current_freq_table.values()) + list(current_mult_table.flatten()))
  
  
# Write each encoded file data to a separate header file using the best frequency table and multiplication table with variable-length codes
  
for i, encoded_data in enumerate(encoded_data_list):
  write_header_file(files[i] + ".h", encoded_data.tobytes()) // encoded_data.tobytes().denominator() if isinstance(encoded_data.tobytes(),sympy.Rational) else encoded_data.tobytes() 
# Convert the bit array to bytes and write to the header file and convert rational results to integers by dividing numerator by denominator and then convert to integer. Convert other results to integers directly.
  
# Return the best compression ratio
return best_ratio, ratios

# Test the compression algorithm on a sample directory
dir_name = "sample_dir"
compression_ratio, ratios = compress_dir(dir_name)

# Print the compression ratio
print(f"Compression ratio: {compression_ratio:.2f}")

# Plot the compression ratios for each iteration
plt.plot(ratios)
plt.xlabel("Iteration")
plt.ylabel("Compression ratio")
plt.title("Compression ratio vs. iteration")
plt.show()
