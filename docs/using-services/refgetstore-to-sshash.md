# Tutorial: From a RefgetStore to an SSHash k-mer index

In this tutorial you start with a reference FASTA and finish with a queryable
SSHash k-mer dictionary, using a gtars **RefgetStore** as the verifiable source
of sequence data. Along the way you will build a content-addressed store, export
a clean FASTA from it, collapse the genome into de Bruijn graph unitigs with
GGCAT, and finally build and query an SSHash index.

This tutorial assumes you can already run commands at a shell, have built the
`gtars` binary, and know what a FASTA file and a k-mer are. You do not need any
prior experience with RefgetStore, GGCAT, or SSHash.

!!! success "Learning objectives"
    - Build a RefgetStore from a reference FASTA
    - Export an unwrapped, one-sequence-per-line FASTA from the store
    - Collapse a genome into maximal unitigs with GGCAT
    - Build and query an SSHash k-mer dictionary
    - Record the collection digest so the index's provenance is verifiable

## The pipeline at a glance

Four stages, and each stage is owned by exactly one tool. The two RefgetStore
stages produce faithful sequence bytes; GGCAT prepares those bytes for k-mer
indexing; SSHash builds the queryable dictionary.

```
   reference.fa
       │
       ▼
 ┌──────────────────────┐
 │ 1. gtars refget build│   owner: RefgetStore   → content-addressed store
 └──────────────────────┘
       │  store_dir/
       ▼
 ┌──────────────────────┐
 │ 2. gtars refget      │   owner: RefgetStore   → unwrapped FASTA (-w 0)
 │    export -w 0       │
 └──────────────────────┘
       │  reference.unwrapped.fa
       ▼
 ┌──────────────────────┐
 │ 3. ggcat build       │   owner: GGCAT         → maximal unitigs
 │                      │                          (dedup k-mers, ACGT only)
 └──────────────────────┘
       │  unitigs.fa
       ▼
 ┌──────────────────────┐
 │ 4. sshash build      │   owner: SSHash        → queryable k-mer dictionary
 │    + sshash query    │
 └──────────────────────┘
       │  index.sshash
       ▼
   Lookup / Access / membership queries
```

## Prerequisites

- A built `gtars` binary with the `refget` feature. From the gtars source tree,
  run `cargo build --release --all-features`; the binary lands at
  `target/release/gtars`. Put it on your `PATH`, or call it by path.
- **GGCAT** installed. Install with `conda install -c conda-forge -c bioconda ggcat`.
  See the [GGCAT README](https://github.com/algbio/ggcat) for other options.
- **SSHash** installed. Install with `conda install -c bioconda sshash`.
  See the [SSHash README](https://github.com/jermp/sshash) for building from source.

Check that all three are reachable before you start:

```bash
gtars --help
ggcat --help
sshash
```

Each command should print its usage. Now make a working directory and move into it:

```bash
mkdir sshash-tutorial && cd sshash-tutorial
```

Throughout the tutorial we use a small k-mer length, **k = 11**, so the example
runs in a fraction of a second. Real reference genomes typically use k = 31.

## A tiny example genome

Create a small reference FASTA. It has two short sequences, and the second one
contains a run of `N` bases on purpose so you can see how the pipeline handles
non-ACGT characters later.

```bash
cat > reference.fa <<'EOF'
>chr1 tiny test sequence
ACGTACGTACGTTTGGCCAAACGTACGTACGTGGGGCCCCAAAATTTTACGT
>chr2 second sequence with an N run
TTTTGGGGCCCCAAAANNNNNNACGTACGTACGTACGTGGCCTTAACCGGTTA
EOF
```

You now have `reference.fa` with two sequences. This stands in for a reference
genome collection.

## Stage 1 — Build a RefgetStore (owner: RefgetStore)

Build a store from the FASTA. The `refget build` subcommand imports each FASTA
and computes GA4GH refget sequence digests plus a collection (seqcol) digest.

```bash
gtars refget build reference.fa -o store_dir
```

Expected output (digests will match your input, so they should be identical to
these):

```
Building RefgetStore at store_dir (mode=Encoded, jobs=auto)
  added reference.fa: <collection-digest> (2 sequences)
Done: 2 sequences, 105 bases in 0.00Xs (... Mbase/s, jobs=auto)
```

Note the `<collection-digest>` printed next to your FASTA. That string is the
content-addressed identifier for this exact set of sequences. Copy it somewhere;
you will use it in the final "provenance" step. The store itself now lives in
`store_dir/`.

## Stage 2 — Export an unwrapped FASTA (owner: RefgetStore)

Downstream k-mer tools want **one sequence per line** (unwrapped) FASTA. Export
from the store with line width `0`, which emits each sequence on a single line.

```bash
gtars refget export -s store_dir -o reference.unwrapped.fa -w 0
```

Expected output (the store loads the collection and its sequences, then writes
the FASTA):

```
Loading collection metadata <collection-digest>...
Loading sequence <seq-digest>...
Loading sequence <seq-digest>...
Exported collection <collection-digest> (all sequences) to reference.unwrapped.fa [unwrapped (one sequence per line)]
```

Inspect the result. Each sequence body is on exactly one line:

```bash
cat reference.unwrapped.fa
```

```
>chr1 tiny test sequence
ACGTACGTACGTTTGGCCAAACGTACGTACGTGGGGCCCCAAAATTTTACGT
>chr2 second sequence with an N run
TTTTGGGGCCCCAAAANNNNNNACGTACGTACGTACGTGGCCTTAACCGGTTA
```

The sequences come straight from the content-addressed store, so this FASTA is a
faithful, verifiable copy of the reference you built in Stage 1.

## Stage 3 — Build unitigs with GGCAT (owner: GGCAT)

This stage is **mandatory** and cannot be skipped. SSHash requires input with
**no duplicate k-mers** and **only the characters A, C, G, T**. A raw reference
genome violates both rules: it repeats k-mers (every genome has repeats) and it
contains `N` runs (like the one you added to `chr2`).

GGCAT builds a compacted de Bruijn graph and emits **maximal unitigs**: it
collapses shared k-mers into single paths (removing duplicates) and breaks
sequences at every non-ACGT character (removing the `N` runs). This is the
assembler's job. RefgetStore does **not** and **should not** do it — the store's
role is to emit faithful sequence bytes, and it ends at Stage 2.

```bash
ggcat build -k 11 -s 1 -o unitigs.fa reference.unwrapped.fa
```

The `-s 1` flag sets the minimum k-mer multiplicity to `1`, so every k-mer in
your single reference is kept (GGCAT's default of `2` is meant for filtering
sequencing errors out of read data, not for a reference genome). See the
[GGCAT README](https://github.com/algbio/ggcat) for the full option list.

Expected result: a `unitigs.fa` file whose sequences contain each distinct
k-mer exactly once, with the `N` run gone.

```bash
cat unitigs.fa
```

The exact unitig sequences depend on the graph structure, but every record will
be ACGT-only and one sequence per line — precisely what SSHash expects.

## Stage 4 — Build and query SSHash (owner: SSHash)

Now build the k-mer dictionary from the unitigs. Use the **same k** you gave
GGCAT (k = 11); the values must match or the index is incorrect. The `-m` flag
sets the minimizer length (must be smaller than k); `--check` verifies the
finished index.

```bash
sshash build -i unitigs.fa -k 11 -m 7 --check -o index.sshash
```

Expected output ends with a serialization message and, thanks to `--check`, a
confirmation that every k-mer was correctly indexed.

SSHash stores k-mer **membership and identifiers** (and optional abundances),
not the sequence bytes. It is order-preserving and treats a k-mer and its
reverse complement as the same. To query, hand it a FASTA of query sequences.
Pass `--multiline` when the query FASTA may wrap sequences across lines:

```bash
sshash query -i index.sshash -q reference.unwrapped.fa --multiline
```

Expected output is a query report summarizing how many k-mers were found:

```
==== query report:
num_kmers = ...
num_positive_kmers = ... (100.00%)
...
```

Because you queried with sequences drawn from the same reference, every ACGT
k-mer should be reported as present. See the
[SSHash README](https://github.com/jermp/sshash) for the full set of query modes
(streaming, navigational, and weighted queries).

## Why start from a RefgetStore?

You could have handed any random FASTA to GGCAT. Starting from a RefgetStore buys
you one thing that a loose FASTA cannot: **provenance**. The store's sequences are
content-addressed by GA4GH refget and seqcol digests, so you can state exactly
which reference collection a given SSHash index covers — verifiably, by digest.

Record the collection digest from Stage 1 alongside the index so the pairing is
never ambiguous:

```bash
echo "collection_digest=<collection-digest>  k=11  m=7" > index.sshash.provenance
```

Anyone who later has `index.sshash` can now look up exactly which sequence
collection it was built from, and re-derive that digest from the source FASTA to
confirm it.

## Challenge

Rebuild the whole pipeline with **k = 31** (the value real genomes use) instead
of 11. You will need to:

1. Supply longer sequences (each must be at least 31 bp) — extend `reference.fa`.
2. Pass `-k 31` to **both** `ggcat build` and `sshash build`.
3. Choose a minimizer length `-m` smaller than 31 (try `-m 13`).

Confirm with `sshash query` that the k-mers from your reference are all found.
What happens to the query report if you change `-k` in the `sshash query` step to
a value different from the one used at build time?

!!! success "Summary"
    - A **RefgetStore** is a content-addressed source of reference sequence,
      identified by GA4GH refget/seqcol **digests**
    - `gtars refget build` creates the store; `gtars refget export -w 0` emits an
      **unwrapped**, one-sequence-per-line FASTA
    - **GGCAT** is mandatory: SSHash needs input with **no duplicate k-mers** and
      **only A, C, G, T**, and GGCAT's maximal unitigs deliver exactly that
    - The **same k** must be used for `ggcat build` and `sshash build`
    - **SSHash** stores k-mer membership/IDs (and optional abundances), not
      sequence bytes, and treats reverse complements as identical
    - Recording the **collection digest** next to the index makes its provenance
      verifiable
