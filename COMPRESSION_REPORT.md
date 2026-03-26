# Compression Test Report

| File Name | Status | Original Size (B) | Compressed Size (B) | Ratio |
| --- | --- | --- | --- | --- |
| data.csv | PASS | 577 | 443 | 1.30 |
| data.json | PASS | 941 | 711 | 1.32 |
| mixed.bin | PASS | 141 | 118 | 1.19 |
| random.bin | PASS | 300 | 313 | 0.96 |
| seq.bin | PASS | 512 | 608 | 0.84 |
| zeros.bin | PASS | 500 | 375 | 1.33 |

**Total Original Size:** 2971 Bytes
**Common Parameter Overhead:** 520 Bytes
**Total Compressed Size:** 3088 Bytes (including common overhead)
**Overall Compression Ratio:** 0.96

### Evaluation Summary
The current compression method is a frequency-based variable-length encoding system. The reported compressed size reflects the actual raw data bits stored in flash. The ratio accounts for both the compressed data and the common frequency/parameter table required for decompression.
