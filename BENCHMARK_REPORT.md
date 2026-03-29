# Arduino Variable-Base Decompressor Benchmark Report

Generated on: 2026-03-29 01:09:27

## Summary Table

| File Name | Size (B) | Speed (B/s) | Ratio | Status |
| --- | --- | --- | --- | --- |
| image_16kb_bin | 16384 | 58,724,000 | 0.99 | PASS |
| sparse_1kb_bin | 1024 | 78,769,200 | 1.33 | PASS |
| text_12kb_txt | 8821 | 65,828,400 | 1.26 | PASS |
| map_8kb_bin | 8192 | 37,578,000 | 0.96 | PASS |

## Performance Charts

### Decompression Speed (Bytes/sec)
```
image_16kb_bin  | ██████████████░░░░░░ | 58,724,000 B/s
sparse_1kb_bin  | ████████████████████ | 78,769,200 B/s
text_12kb_txt   | ████████████████░░░░ | 65,828,400 B/s
map_8kb_bin     | █████████░░░░░░░░░░░ | 37,578,000 B/s
```

### Compression Ratio (Original/Compressed Bits)
```
image_16kb_bin  | ██████████████░░░░░░ | 0.99x
sparse_1kb_bin  | ████████████████████ | 1.33x
text_12kb_txt   | ██████████████████░░ | 1.26x
map_8kb_bin     | ██████████████░░░░░░ | 0.96x
```

## Verification Details

**Overall Status: PASSED**

## Conclusion
The decompressor demonstrates consistent high-speed performance across various data types. RAM usage remains constant (~27 bytes) regardless of input size.
