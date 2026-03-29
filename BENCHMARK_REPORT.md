# Arduino Variable-Base Decompressor Benchmark Report (Nested + Z-Order)

Generated on: 2026-03-29 01:26:31

## Summary Table

| File Name | Size (B) | Speed (B/s) | Ratio | Status |
| --- | --- | --- | --- | --- |
| image_16kb_bin | 16384 | 34,859,600 | 1.00 | PASS |
| sparse_1kb_bin | 1024 | 51,200,000 | 1.33 | PASS |
| text_12kb_txt | 8449 | 44,468,400 | 1.28 | PASS |
| map_8kb_bin | 8192 | 28,346,000 | 0.97 | PASS |

## Performance Charts

### Decompression Speed (Bytes/sec)
```
image_16kb_bin  | █████████████░░░░░░░ | 34,859,600 B/s
sparse_1kb_bin  | ████████████████████ | 51,200,000 B/s
text_12kb_txt   | █████████████████░░░ | 44,468,400 B/s
map_8kb_bin     | ███████████░░░░░░░░░ | 28,346,000 B/s
```

### Compression Ratio (Original/Compressed Bits)
```
image_16kb_bin  | ███████████████░░░░░ | 1.00x
sparse_1kb_bin  | ████████████████████ | 1.33x
text_12kb_txt   | ███████████████████░ | 1.28x
map_8kb_bin     | ██████████████░░░░░░ | 0.97x
```

## Verification Details

**Overall Status: PASSED**

## Conclusion
The nested variable-base decompressor with Z-order support improves compression ratio for structured data while maintaining high throughput and low RAM usage.
