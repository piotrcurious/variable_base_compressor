# Arduino Variable-Base Decompressor Benchmark (Bit-Packed + Multi-Filter)

Generated on: 2026-03-29 09:41:58

## Summary Table

| File Name | Size (B) | Speed (B/s) | Ratio | Seek (us) | Status |
| --- | --- | --- | --- | --- | --- |
| image_16kb_bin | 16384 | 23,305,800 | 1.32 | 4 | PASS |
| sparse_1kb_bin | 1024 | 37,925,900 | 1.98 | 2 | PASS |
| text_12kb_txt | 8487 | 23,773,100 | 1.24 | 1 | PASS |
| map_8kb_bin | 8192 | 20,327,500 | 1.22 | 5 | PASS |

## Performance Charts

### Decompression Speed (Bytes/sec)
```
image_16kb_bin  | ████████████░░░░░░░░ | 23,305,800 B/s
sparse_1kb_bin  | ████████████████████ | 37,925,900 B/s
text_12kb_txt   | ████████████░░░░░░░░ | 23,773,100 B/s
map_8kb_bin     | ██████████░░░░░░░░░░ | 20,327,500 B/s
```

### Random Access Seek Time (Last Byte)
```
image_16kb_bin  | ████████████████░░░░ | 4 us
sparse_1kb_bin  | ████████░░░░░░░░░░░░ | 2 us
text_12kb_txt   | ████░░░░░░░░░░░░░░░░ | 1 us
map_8kb_bin     | ████████████████████ | 5 us
```

## Conclusion
The addition of Bit-Packed mode and Paeth predictors further improves density for low-entropy and structured data.
