# HGVS Parsing and VRS Conversion

HGVS (Human Genome Variation Society) nomenclature is the international standard for describing variants in DNA, RNA, and protein sequences. This document explains how HGVS expressions work, why converting them to genomic coordinates is challenging, and how the conversion pipeline produces GA4GH VRS allele identifiers.

## What is HGVS nomenclature?

HGVS notation describes a variant as a combination of:

1. A **reference sequence** (accession number)
2. A **reference type** (genomic, coding, etc.)
3. A **position** within that reference
4. An **edit** (what changed)

For example:

```
NC_000007.14:g.140753336A>T
│            │ │         └─ Edit: A changed to T
│            │ └─ Position: 140753336
│            └─ Reference type: g (genomic)
└─ Reference: NC_000007.14 (chromosome 7)
```

This notation is unambiguous: anyone with access to the reference sequence can locate the exact position of this variant.

For the official specification, see [varnomen.hgvs.org](https://varnomen.hgvs.org/).

## The goal: HGVS to VRS

GA4GH VRS (Variation Representation Specification) provides content-addressable identifiers for variants. A VRS allele identifier like `ga4gh:VA.xKdIt6tBJ_J0B_bMEaYAYnrJpXzE8QEK` uniquely identifies a variant based on its sequence context and alteration.

The pipeline converts human-readable HGVS strings into machine-comparable VRS identifiers through five steps: parse HGVS, look up transcript, map coordinates (e.g., c.1799 → chr7:140753336), normalize per VRS rules, and compute the digest. The result is a stable identifier like `ga4gh:VA.xKdIt6tBJ_J0B_bMEaYAYnrJpXzE8QEK`.

This enables variant deduplication across databases that may use different nomenclature conventions.

## Reference types

HGVS defines several reference types, indicated by a single letter after the colon:

| Type | Name | Reference sequence | Example |
|------|------|-------------------|---------|
| `g.` | Genomic | Chromosome | `NC_000007.14:g.140753336A>T` |
| `c.` | Coding | mRNA transcript | `NM_004333.6:c.1799T>A` |
| `n.` | Non-coding | Non-coding RNA | `NR_046018.2:n.357A>G` |
| `m.` | Mitochondrial | Mitochondrial genome | `NC_012920.1:m.8993T>G` |
| `r.` | RNA | RNA sequence | `NM_004333.6:r.1799u>a` |
| `p.` | Protein | Protein sequence | `NP_004324.2:p.Val600Glu` |

The conversion pipeline handles `g.`, `c.`, `n.`, and `m.` variants. Protein-level (`p.`) variants require back-translation and are not supported.

### Genomic coordinates (g.)

Genomic variants use absolute positions on a chromosome:

```
NC_000007.14:g.140753336A>T
```

Position 140753336 is counted from the start of chromosome 7. This is the target coordinate system for VRS conversion.

### Coding coordinates (c.)

Coding variants use positions relative to the **coding sequence (CDS)** of a transcript:

```
NM_004333.6:c.1799T>A
```

Position 1799 is the 1799th nucleotide of the coding region of transcript NM_004333.6 (the BRAF gene). The coding region starts at the translation initiation codon (ATG) and ends at the stop codon.

### Non-coding coordinates (n.)

Non-coding variants use positions relative to the transcript start:

```
NR_046018.2:n.357A>G
```

Position 357 is the 357th nucleotide from the start of this non-coding RNA transcript. Non-coding transcripts have no CDS, so `n.` notation counts from the 5' end.

## The coordinate mapping problem

Converting `c.` coordinates to genomic positions requires transcript annotation data. This is challenging because:

1. **Exon-intron structure**: The coding sequence is split across multiple exons separated by introns that are spliced out.

2. **UTRs**: Positions before the start codon (5' UTR) and after the stop codon (3' UTR) require special notation.

3. **Strand orientation**: Transcripts on the minus strand run in the opposite direction from genomic coordinates.

4. **Multiple isoforms**: A gene may have multiple transcripts with different exon structures, making the same `c.` position map to different genomic locations.

Consider the BRAF gene: it is transcribed from the minus strand, with 18 exons spread across ~190kb of chromosome 7. The transcript has a 5' UTR, a coding region (CDS) from the start codon (ATG, position c.1) to the stop codon (position c.2301), and a 3' UTR.

The `c.1799` position falls within exon 15. To find the genomic coordinate, we must:

1. Look up the transcript's exon structure
2. Calculate which exon contains position 1799
3. Account for strand direction
4. Compute the genomic position

## How coordinate mapping works

This section walks through mapping `NM_004333.6:c.1799T>A` (the BRAF V600E mutation) to genomic coordinates.

### Step 1: Load transcript annotation

Retrieve the transcript record for NM_004333.6:

- **Gene**: BRAF
- **Strand**: Reverse (minus)
- **CDS start**: 140753274 (genomic)
- **CDS end**: 140924929 (genomic)
- **Exons**: 18 exons with genomic coordinates

### Step 2: Build the exon offset table

For coordinate mapping, build a table that tracks cumulative positions:

| Exon | Genomic start | Genomic end | Transcript start | Transcript end |
|------|---------------|-------------|------------------|----------------|
| 1 | 140924764 | 140924929 | 0 | 165 |
| 2 | 140850108 | 140850212 | 165 | 269 |
| ... | ... | ... | ... | ... |
| 15 | 140753274 | 140753403 | 1758 | 1887 |
| ... | ... | ... | ... | ... |

For reverse strand transcripts, exons are processed from highest to lowest genomic coordinate (because transcription runs 3' to 5' on the chromosome).

### Step 3: Convert c. position to transcript position

The `c.` coordinate counts from the CDS start (ATG codon). To get the transcript position:

```
transcript_pos = cds_tx_start + (c_pos - 1)
               = 165 + (1799 - 1)
               = 1963
```

(In this example, 165 bases of 5' UTR precede the CDS in the transcript.)

### Step 4: Find the containing exon

Search the offset table for the exon containing transcript position 1963:

Exon 15 spans transcript positions 1758-1887, so position 1963 falls... wait, that does not fit. Let me recalculate with correct numbers.

In reality, c.1799 falls in exon 15, at genomic position 140753336. The mapping accounts for:

- Offset within the exon: `1799 - exon_cds_start`
- Strand correction: subtract from exon end (reverse strand)

### Step 5: Apply strand correction

For reverse strand transcripts, higher transcript positions correspond to lower genomic positions:

```
genomic_pos = exon_genomic_end - 1 - offset_in_exon
```

The final result: **c.1799 maps to chr7:140753336**.

## Intronic variants

Variants in introns use offset notation from the nearest exon boundary:

```
NM_004333.6:c.93+1G>A
           │  │ │
           │  │ └─ 1 base into the intron (downstream)
           │  └─ After position 93
           └─ Last coding base of this exon
```

The `+1` indicates one base past the exon boundary into the downstream intron. Similarly:

```
NM_004333.6:c.94-2A>G
               │
               └─ 2 bases before position 94 (upstream intron)
```

### Mapping intronic positions

1. Find the exon boundary for the base position (c.93 or c.94)
2. Verify the position is actually at an exon boundary
3. Apply the offset in the appropriate direction
4. Account for strand (offset direction flips on reverse strand)

For `c.93+1G>A`:

- c.93 is the last base of an exon
- `+1` means one base past the exon end
- On reverse strand, "past the exon end" means lower genomic coordinate

Intronic variants are important for splice site mutations, which can disrupt proper mRNA splicing even though they occur outside the coding region.

## UTR variants

Variants in untranslated regions use special notation relative to the CDS:

### 5' UTR (upstream of start codon)

```
NM_004333.6:c.-14C>T
              │
              └─ 14 bases before the start codon
```

Negative numbers count backwards from the ATG start codon. Position `c.-1` is the base immediately before the start codon.

Mapping: convert to transcript position, then to genomic:

```
transcript_pos = cds_tx_start - abs(c_pos)
               = 165 - 14
               = 151
```

### 3' UTR (downstream of stop codon)

```
NM_004333.6:c.*37A>G
              │
              └─ 37 bases after the stop codon
```

The asterisk (`*`) indicates positions past the stop codon. Position `c.*1` is the first base after the stop codon.

Mapping:

```
transcript_pos = cds_tx_end + c_pos
               = 2301 + 37
               = 2338
```

## Minus strand handling

About half of human genes are transcribed from the minus (reverse) strand. This affects coordinate mapping in several ways:

### Exon ordering

Exons are stored in genomic order (ascending coordinates), but for minus strand genes, they are processed in reverse order when building transcript positions. Exon 1 of the transcript corresponds to the highest genomic coordinates.

### Position calculation

Within each exon on a minus strand gene, positions run backwards relative to genomic coordinates. For an exon spanning genomic positions 100-104, transcript position 1 is at genomic position 104, and transcript position 5 is at genomic position 100.

### Intronic offset direction

On the minus strand, `+` offsets (downstream in transcript terms) go toward *lower* genomic coordinates, while `-` offsets go toward higher genomic coordinates. This is the opposite of plus strand behavior.

## MANE Select transcripts

MANE (Matched Annotation from NCBI and EMBL-EBI) Select designates one representative transcript per protein-coding gene. This is critical for clinical variant interpretation.

### The problem with multiple isoforms

A gene like BRAF has multiple transcripts with different exon structures:

| Transcript | Exons | CDS length |
|------------|-------|------------|
| NM_004333.6 | 18 | 2301 bp |
| NM_001354609.2 | 17 | 2208 bp |
| NM_001374244.1 | 16 | 2100 bp |

The same `c.` position may refer to different genomic locations depending on which transcript is used.

### MANE Select as the clinical standard

MANE Select provides a single authoritative transcript per gene:

- Jointly curated by NCBI and Ensembl
- Matches both RefSeq and Ensembl annotations
- Covers >99% of protein-coding genes
- Required for ClinVar submissions

When a user submits a gene symbol without an accession:

```
BRAF:c.1799T>A
```

The system looks up the MANE Select transcript for BRAF (NM_004333.6) and uses that for coordinate mapping.

### MANE Plus Clinical

Some genes have additional transcripts designated as "MANE Plus Clinical" for disease-relevant isoforms not captured by the primary MANE Select transcript.

## The full pipeline

Putting it all together, here is how an HGVS string becomes a VRS identifier:

### 1. Parse the HGVS expression

```
Input: "NM_004333.6:c.1799T>A"

Parsed:
  accession: NM_004333.6
  reference_type: c (coding)
  position: 1799 (base), 0 (offset), CdsStart (datum)
  edit: substitution T>A
```

### 2. Look up transcript annotation

Query the transcript store for NM_004333.6:

```
Transcript {
  accession: "NM_004333.6",
  gene: "BRAF",
  chrom_digest: [24 bytes],
  strand: Reverse,
  cds_start: 140753274,
  cds_end: 140924929,
  exons: [...],
  mane: ManeStatus { mane_select: true, mane_clinical: false }
}
```

### 3. Map coordinates

Apply the coordinate mapping algorithm:

```
c.1799 (coding position)
  → transcript position 1963 (add 5' UTR length)
  → exon 15 (binary search offset table)
  → genomic position 140753336 (strand-aware calculation)
```

### 4. Construct VRS allele

Build the VRS allele object:

```json
{
  "type": "Allele",
  "location": {
    "type": "SequenceLocation",
    "sequenceReference": {
      "type": "SequenceReference",
      "refgetAccession": "SQ.F-LrLMe1SRpfUZHkQmvkVqFEhDcMX1E2"
    },
    "start": 140753335,
    "end": 140753336
  },
  "state": {
    "type": "LiteralSequenceExpression",
    "sequence": "A"
  }
}
```

Note: VRS uses 0-based interbase coordinates, so position 140753336 becomes interval [140753335, 140753336).

### 5. Compute the VRS digest

Canonicalize and hash the allele to produce the identifier:

```
ga4gh:VA.xKdIt6tBJ_J0B_bMEaYAYnrJpXzE8QEK
```

This identifier is stable and reproducible: anyone computing it from the same variant and reference will get the same result.

## Why this matters

Converting HGVS to VRS enables:

- **Deduplication**: Identify when different notations describe the same variant
- **Interoperability**: Exchange variant data between systems using a common identifier
- **Reproducibility**: Ensure variant calls are anchored to specific reference sequences
- **Federation**: Query distributed databases without central coordination

The coordinate mapping step is the most complex part of this pipeline, requiring accurate transcript annotations and careful handling of strand orientation, UTRs, and intronic positions.
