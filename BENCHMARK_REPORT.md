# Arduino Variable-Base Decompressor Benchmark Report (Optimized)

Generated on: 2026-03-29 01:40:39

## Summary Table

| File Name | Size (B) | Speed (B/s) | Ratio | Status |
| --- | --- | --- | --- | --- |
| image_16kb_bin | 16384 | 46,152,100 | 2.63 | PASS |
| sparse_1kb_bin | 1024 | 48,761,900 | 1.97 | PASS |
| text_12kb_txt | 8646 | 33,905,900 | 1.39 | PASS |
| map_8kb_bin | 8192 | 29,153,000 | 1.84 | PASS |

## Performance Charts

### Decompression Speed (Bytes/sec)
```
image_16kb_bin  | ██████████████████░░ | 46,152,100 B/s
sparse_1kb_bin  | ████████████████████ | 48,761,900 B/s
text_12kb_txt   | █████████████░░░░░░░ | 33,905,900 B/s
map_8kb_bin     | ███████████░░░░░░░░░ | 29,153,000 B/s
```

### Compression Ratio (Original/Compressed Bits)
```
image_16kb_bin  | ████████████████████ | 2.63x
sparse_1kb_bin  | ███████████████░░░░░ | 1.97x
text_12kb_txt   | ██████████░░░░░░░░░░ | 1.39x
map_8kb_bin     | █████████████░░░░░░░ | 1.84x
```

## Verification Details

**Overall Status: PASSED**

## Conclusion
The optimized nested variable-base decompressor with bit caching and Delta mode support shows significantly improved compression and performance.
