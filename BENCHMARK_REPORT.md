# Arduino Variable-Base Decompressor Benchmark (Creative + Low-RAM)

Generated on: 2026-03-29 12:33:32

## Summary Table

| File Name | Size (B) | Speed (B/s) | Ratio | Seek (us) | Status |
| --- | --- | --- | --- | --- | --- |
| terrain_8kb_bin | 8192 | 31,507,700 | 1.26 | 2 | PASS |
| image_16kb_bin | 16384 | 35,008,500 | 1.35 | 4 | PASS |
| syslog_10kb_txt | 11982 | 18,988,900 | 1.11 | 4 | PASS |
| sparse_1kb_bin | 1024 | 42,666,700 | 2.79 | 2 | PASS |
| text_12kb_txt | 8707 | 19,178,400 | 1.10 | 0 | PASS |
| map_8kb_bin | 8192 | 27,769,500 | 1.27 | 2 | PASS |

## Performance Charts

### Decompression Speed
```
terrain_8kb_bin | ██████████████░░░░░░ | 31,507,700 B/s
image_16kb_bin  | ████████████████░░░░ | 35,008,500 B/s
syslog_10kb_txt | ████████░░░░░░░░░░░░ | 18,988,900 B/s
sparse_1kb_bin  | ████████████████████ | 42,666,700 B/s
text_12kb_txt   | ████████░░░░░░░░░░░░ | 19,178,400 B/s
map_8kb_bin     | █████████████░░░░░░░ | 27,769,500 B/s
```

### Compression Ratio
```
terrain_8kb_bin | ████████░░░░░░░░░░░░ | 1.26x
image_16kb_bin  | █████████░░░░░░░░░░░ | 1.35x
syslog_10kb_txt | ███████░░░░░░░░░░░░░ | 1.11x
sparse_1kb_bin  | ████████████████████ | 2.79x
text_12kb_txt   | ███████░░░░░░░░░░░░░ | 1.10x
map_8kb_bin     | █████████░░░░░░░░░░░ | 1.27x
```

## Conclusion
New creative optimizations (Predictive Z-order, Residual mapping) achieve better ratios within <200 bytes RAM budget.
