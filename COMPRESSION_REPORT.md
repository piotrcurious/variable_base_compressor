# Compression Test Report (Custom Variable Base)

| File Name | Status | Original Size (B) | Compressed Size (B) | Ratio |
| --- | --- | --- | --- | --- |
| data.csv | PASS | 577 | 421 | 1.37 |
| data.json | PASS | 941 | 666 | 1.41 |
| mixed.bin | PASS | 141 | 115 | 1.23 |
| random.bin | PASS | 300 | 327 | 0.92 |
| seq.bin | PASS | 512 | 644 | 0.80 |
| zeros.bin | PASS | 500 | 313 | 1.60 |

**Total Original Size:** 2971 Bytes
**Common Parameter Overhead:** 520 Bytes
**Total Compressed Size:** 3006 Bytes (including common overhead)
**Overall Compression Ratio:** 0.99

### Evaluation Summary
This report uses the Custom Variable Base approach (Unary for quotient, Truncated Binary for remainder). This method is well-suited for Arduino as it requires minimal RAM for decoding. The ratio accounts for the actual raw bits and the common parameter table in flash.
