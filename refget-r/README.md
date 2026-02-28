# BiocRefgetStore

BSgenome-compatible interface to RefgetStore for R/Bioconductor.

## Overview

BiocRefgetStore provides a bridge between the gtars RefgetStore format and Bioconductor's BSgenome API. This allows you to use RefgetStore-backed genomes with the familiar `getSeq()` interface that Bioconductor users expect.

## Installation

```r
# Install gtars first (required)
# See: https://github.com/databio/gtars

# Install BiocRefgetStore
devtools::install_local("path/to/refget-r")
```

## Quick Start

```r
library(BiocRefgetStore)

# Create a genome from a FASTA file
genome <- RefgetGenome.from_fasta("genome.fa")

# BSgenome-compatible access
seq <- getSeq(genome, "chr1", 1000, 2000)           # Returns DNAString
seqs <- getSeq(genome, c("chr1", "chr2"))           # Returns DNAStringSet
genome[["chr1"]]                                    # Full chromosome

# Standard accessors
seqnames(genome)         # c("chr1", "chr2", ...)
seqlengths(genome)       # Named integer vector
seqinfo(genome)          # Seqinfo object
```

## Loading Genomes

```r
# From FASTA file (creates in-memory store)
genome <- RefgetGenome.from_fasta("/path/to/genome.fa")

# From persisted RefgetStore directory
genome <- RefgetGenome.from_directory("/path/to/store", digest = "abc123...")

# From RefgetStore with alias
store <- gtars::refget_store_open_local("/path/to/store")
genome <- RefgetGenome(store, namespace = "refseq", alias = "GRCh38")

# From remote store (cloud-backed with local caching)
genome <- RefgetGenome.from_remote(
  cache_path = "~/.cache/refget",
  remote_url = "https://refget.databio.org/store",
  namespace = "refseq",
  alias = "GRCh38"
)
```

## Sequence Extraction

```r
# Single region
seq <- getSeq(genome, "chr1", 1000, 2000)

# Multiple regions
seqs <- getSeq(genome,
               names = c("chr1", "chr2"),
               start = c(1000, 5000),
               end = c(2000, 6000))

# From GRanges (requires GenomicRanges)
library(GenomicRanges)
gr <- GRanges(c("chr1:1000-2000", "chr2:5000-6000:-"))
seqs <- getSeq(genome, gr)

# Strand-aware extraction
seq <- getSeq(genome, "chr1", 1000, 2000, strand = "-")  # Reverse complement
```

## Bulk Extraction

```r
# Extract multiple regions efficiently
regions <- data.frame(
  chrom = c("chr1", "chr2", "chr3"),
  start = c(1000, 5000, 10000),
  end = c(2000, 6000, 11000)
)
seqs <- extractRegions(genome, regions)

# Write regions to FASTA
extractToFasta(genome, regions, "extracted.fa")

# Export specific chromosomes
exportChromosomes(genome, c("chr1", "chr2"), "subset.fa")
```

## RefgetStore-Specific Features

```r
# Get the seqcol digest
collection_digest(genome)

# Get coordinate system (for compatibility checking)
coordinate_system(genome)

# Get per-sequence digests
sequence_digests(genome)

# Access underlying RefgetStore
store <- store(genome)
```

## Dependencies

- **Required**: gtars (for RefgetStore), GenomeInfoDb (for Seqinfo)
- **Optional**: Biostrings (for DNAString/DNAStringSet), GenomicRanges (for GRanges support)

Without Biostrings, sequences are returned as character strings.
