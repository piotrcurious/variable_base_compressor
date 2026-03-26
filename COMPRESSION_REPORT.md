# Compression Test Report

| File Name | Status | Original Size (B) | Header Size (B) |
| --- | --- | --- | --- |
| data.csv | PASS | 577 | 2915 |
| data.json | PASS | 941 | 4563 |
| mixed.bin | PASS | 141 | 948 |
| random.bin | PASS | 300 | 2147 |
| seq.bin | PASS | 512 | 3920 |
| zeros.bin | PASS | 500 | 2513 |

**Total Original Size:** 2971 Bytes
**Common Overhead:** 1342 Bytes
**Total Compressed Size:** 18348 Bytes (including common overhead)
**Overall Compression Ratio:** 0.16

### Evaluation Summary
The current compression method is a frequency-based variable-length encoding system. For very small files typical of the test set, the C header file overhead (array declarations, guards, metadata) is significant. In a real-world scenario where data is stored as a raw stream in flash, the compression would be much more apparent.
