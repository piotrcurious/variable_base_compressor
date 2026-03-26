# Compression Test Report (Canonical Huffman)

| File Name | Status | Original Size (B) | Compressed Size (B) | Ratio |
| --- | --- | --- | --- | --- |
| data.csv | PASS | 577 | 432 | 1.34 |
| data.json | PASS | 941 | 635 | 1.48 |
| mixed.bin | PASS | 141 | 124 | 1.14 |
| random.bin | PASS | 300 | 334 | 0.90 |
| seq.bin | PASS | 512 | 590 | 0.87 |
| zeros.bin | PASS | 500 | 188 | 2.66 |

**Total Original Size:** 2971 Bytes
**Common Parameter Overhead:** 536 Bytes
**Total Compressed Size:** 2839 Bytes (including common overhead)
**Overall Compression Ratio:** 1.05

### Evaluation Summary
Switching to Canonical Huffman coding significantly improves the compression ratio compared to the previous variable-base encoding. The decoder implementation on Arduino is efficient in both RAM and flash usage, as it leverages the canonical property to decode symbols without storing a tree structure in RAM.
