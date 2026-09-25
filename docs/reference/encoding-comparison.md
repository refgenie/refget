# RefgetStore Encoding vs UCSC 2bit Format

RefgetStore's encoded mode and the UCSC 2bit format both pack DNA sequences into 2 bits per base. They differ in how they handle bases outside the 4-letter DNA alphabet (A, C, G, T), particularly N (unknown base).

## Base encoding

Both formats use the same 2-bit encoding for the four standard DNA bases:

| Base | Binary |
|------|--------|
| T    | 00     |
| C    | 01     |
| A    | 10     |
| G    | 11     |

Four bases pack into one byte, MSB-first. The sequence `TCAG` encodes as `00 01 10 11` = `0x1B`.

## Handling N bases

The two formats diverge in how they represent positions that are not A, C, G, or T.

### UCSC 2bit: sideband N-blocks

The UCSC 2bit format stores all positions as 2-bit values, even N positions (which are written as T/`00` in the bitstream). N positions are recorded separately as **N-block** metadata: an array of (start, size) pairs identifying each contiguous run of N bases. On read, the 2-bit stream is first decoded to ACGT, then N-block regions are overwritten with N.

Soft masking (lowercase bases indicating repeat regions) uses the same sideband approach: **mask blocks** record (start, size) pairs for lowercase regions. Other IUPAC ambiguity codes (R, Y, W, S, etc.) are converted to N on input and cannot be recovered.

### RefgetStore: wider alphabet

RefgetStore selects the narrowest alphabet that can represent all characters in a sequence:

| Alphabet | Bits/base | Characters |
|----------|-----------|------------|
| dna2bit  | 2         | A, C, G, T |
| dna3bit  | 3         | A, C, G, T, N, R, Y, X |
| dnaio    | 4         | All 15 IUPAC ambiguity codes |
| protein  | 5         | 20 amino acids + stop/gap |
| ASCII    | 8         | Any byte value |

If a DNA sequence contains any N bases, RefgetStore upgrades from 2-bit to 3-bit encoding, where N has its own code (`100`). Every position is self-describing — no sideband metadata is needed. The alphabet is auto-detected during import and recorded in the sequence index.

## Storage cost comparison

For pure ACGT sequences (no N bases), both formats use 2 bits per base.

For sequences containing N bases:

| Format | Bits per base | N overhead |
|--------|--------------|------------|
| UCSC 2bit | 2 (uniform) | 8 bytes per contiguous N run (start + size, both 32-bit) |
| RefgetStore dna3bit | 3 (uniform) | None — N is encoded inline |

UCSC 2bit uses fewer bits per base (2 vs 3) but pays a fixed cost per N-run. RefgetStore uses more bits per base but has no per-run overhead.

The crossover depends on N distribution. For a sequence of length *L* with *K* contiguous N-runs, the encoded sizes are:

- **UCSC 2bit:** `L/4` bytes + `8K` bytes (N-block metadata)
- **RefgetStore 3-bit:** `3L/8` bytes

UCSC 2bit is smaller when `8K < L/8`, i.e., when `K < L/64`. For the human genome (~3.1 Gb with ~150–300 N-block regions), this holds by a wide margin. For sequences with many short, scattered N positions, the per-run overhead accumulates.

## Feature differences

| Feature | UCSC 2bit | RefgetStore |
|---------|-----------|-------------|
| IUPAC ambiguity codes | Converted to N (lossy) | Preserved in 4-bit mode (lossless) |
| Protein sequences | Not supported | 5-bit encoding |
| Soft masking (lowercase) | Mask blocks (sideband metadata) | Not stored |
| File size limit | ~4 GB (32-bit offsets) | No inherent limit |
| File structure | Single file, multiple sequences | One file per sequence |
| Random access to sequences | Index with byte offsets | Separate files, memory-mapped |
| Alphabet selection | Always 2-bit DNA | Auto-detected per sequence |

## UCSC 2bit file structure

For reference, the UCSC 2bit file layout:

```
Header (16 bytes)
  signature (32-bit)      — 0x1A412743 (also used for endianness detection)
  version (32-bit)        — currently 0
  sequence count (32-bit)
  reserved (32-bit)

Index (one entry per sequence)
  name length (8-bit)
  name (variable)
  offset (32-bit)         — byte offset to sequence record

Sequence record (one per sequence)
  dnaSize (32-bit)        — number of bases
  nBlockCount (32-bit)    — number of N-block regions
  nBlockStarts (32-bit[]) — start positions of N runs
  nBlockSizes (32-bit[])  — lengths of N runs
  maskBlockCount (32-bit)
  maskBlockStarts (32-bit[])
  maskBlockSizes (32-bit[])
  reserved (32-bit)
  packedDna               — ceil(dnaSize/4) bytes, 2 bits per base
```

## See also

- [RefgetStore File Format](refgetstore-format.md) — full specification of the RefgetStore directory layout and file formats
- [UCSC 2bit format specification](https://genome.ucsc.edu/FAQ/FAQformat.html#format7)
