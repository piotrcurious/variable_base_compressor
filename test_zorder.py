import math

def part1d(n):
    n &= 0x0000ffff
    n = (n | (n << 8)) & 0x00ff00ff
    n = (n | (n << 4)) & 0x0f0f0f0f
    n = (n | (n << 2)) & 0x33333333
    n = (n | (n << 1)) & 0x55555555
    return n

def z_order_encode(x, y):
    return (part1d(y) << 1) | part1d(x)

def apply_z_order(data, width):
    if not data: return data
    height = (len(data) + width - 1) // width
    # Pad to power of 2 for simplicity in Z-order? Or just handle bounds.
    # Actually Z-order usually works on squares of power of 2.
    size = 1
    while size < width or size < height:
        size <<= 1

    reordered = [None] * (size * size)
    for y in range(height):
        for x in range(width):
            idx = y * width + x
            if idx < len(data):
                z = z_order_encode(x, y)
                reordered[z] = data[idx]

    # Filter out None and return
    return [x for x in reordered if x is not None]

def test_locality(data):
    if len(data) < 2: return 0
    diff_sum = sum(abs(data[i] - data[i-1]) for i in range(1, len(data)))
    return diff_sum / len(data)

# Test on a simple "map"
data = []
for y in range(16):
    for x in range(16):
        data.append(y + x)

print(f"Original locality: {test_locality(data):.2f}")
z_data = apply_z_order(data, 16)
print(f"Z-order locality: {test_locality(z_data):.2f}")
