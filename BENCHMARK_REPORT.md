# Arduino Variable-Base Decompressor Benchmark (Contextual Adaptive)

Generated on: 2026-03-29 20:07:35

## Summary Table

| File Name | Size (B) | Speed (B/s) | Ratio | Seek (us) | Status |
| --- | --- | --- | --- | --- | --- |
| terrain_8kb.bin | 8192 | 21,222,800 | 1.49 | 2 | PASS |
| image_16kb.bin | 16384 | 43,574,500 | 2.22 | 2 | PASS |
| gradient_8kb.bin | 8192 | 38,280,400 | 2.18 | 3 | PASS |
| syslog_10kb.txt | 11980 | 17,114,300 | 1.09 | 5 | PASS |
| checker_4kb.bin | 4096 | 17,731,600 | 1.98 | 4 | PASS |
| sparse_1kb.bin | 1024 | 35,310,300 | 1.98 | 3 | PASS |
| text_12kb.txt | 8835 | 14,483,600 | 1.06 | 1 | PASS |
| map_8kb.bin | 8192 | 22,567,500 | 1.68 | 1 | PASS |

## Performance Charts

### Decompression Speed
```
terrain_8kb.bin | █████████░░░░░░░░░░░ | 21,222,800 B/s
image_16kb.bin  | ████████████████████ | 43,574,500 B/s
gradient_8kb.bin | █████████████████░░░ | 38,280,400 B/s
syslog_10kb.txt | ███████░░░░░░░░░░░░░ | 17,114,300 B/s
checker_4kb.bin | ████████░░░░░░░░░░░░ | 17,731,600 B/s
sparse_1kb.bin  | ████████████████░░░░ | 35,310,300 B/s
text_12kb.txt   | ██████░░░░░░░░░░░░░░ | 14,483,600 B/s
map_8kb.bin     | ██████████░░░░░░░░░░ | 22,567,500 B/s
```

### Compression Ratio
```
terrain_8kb.bin | █████████████░░░░░░░ | 1.49x
image_16kb.bin  | ████████████████████ | 2.22x
gradient_8kb.bin | ███████████████████░ | 2.18x
syslog_10kb.txt | █████████░░░░░░░░░░░ | 1.09x
checker_4kb.bin | █████████████████░░░ | 1.98x
sparse_1kb.bin  | █████████████████░░░ | 1.98x
text_12kb.txt   | █████████░░░░░░░░░░░ | 1.06x
map_8kb.bin     | ███████████████░░░░░ | 1.68x
```

## Conclusion
Context-Adaptive Base Profiles deliver high compression efficiency within <150 bytes RAM.
