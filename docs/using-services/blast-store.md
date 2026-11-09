# Search a RefgetStore with BLAST

A RefgetStore holds each unique sequence once, so it is a compact way to keep many genome assemblies side by side. This tutorial turns a store into a [BLAST](https://blast.ncbi.nlm.nih.gov/) database, searches the store, and then asks the question that motivates it: which genomes could this DNA sequence have come from?

It uses the `refget blast` commands, which come from the `gtars` package. Everything below runs on a laptop in a few minutes.

## Before you start

Install refget with the store extra, and make sure your `gtars` includes BLAST support:

```console
pip install 'refget[store]'
python -c "import gtars.blast"
```

Searches run with **rgblastn**, a Rust implementation of `blastn` inside gtars. It needs nothing else installed and covers the common searches (tasks `megablast`, `blastn` and `blastn-short`, tabular output). For any other blastn option, build a database (step 2) and search it with the real [BLAST+](https://www.ncbi.nlm.nih.gov/books/NBK279690/) `blastn`, using `--engine blastn --db BASE`. Install BLAST+ with `conda install -c bioconda blast` or `apt install ncbi-blast+`.

## 1. Get a store

You can use a store you built with `refget store add`, or read the public demo store over HTTP with `-r` instead of `-p`:

```console
refget blast reps -r https://refgenie.s3.us-east-1.amazonaws.com/refget-store/demo/ --all
```

For the rest of this page, `./store` is a local store. Collections are chosen by digest, `NAMESPACE:ALIAS` or a bare alias (see [Working with aliases](aliases.py)).

## 2. Build a BLAST database

```console
refget blast build -p ./store --all --out db/all
```

This writes a standard BLAST version 5 database. `blastn -db db/all` reads it like any other, and `refget blast verify --db db/all -p ./store` checks it against the store. Building straight from the store is much faster than exporting FASTA and running `makeblastdb`: hg38 takes about a second on 16 cores.

To pick part of a store, use `--collection ucsc:hg38`, `--namespace ucsc` or `--taxon "Homo sapiens"`. `refget blast view --db db/all --per-collection` then writes one searchable view per assembly, with no rebuild.

## 3. Search it

`refget blast search` searches the store directly, with no database. Everything after `--` goes to the search engine:

```console
refget blast search -p ./store --all -- -query query.fa -outfmt 6
```

To search the database from step 2 with BLAST+ instead:

```console
refget blast search --engine blastn --db db/all -- -query query.fa -outfmt 6
```

The ids in the hits are `SQ.<digest>` for the sequence, followed by `gnl|<collection>|<name>` entries that say which assemblies hold it and under what name.

## 4. See which genomes the hits come from

`report` reads the hit file and prints the best hit per genome, grouped by species, one line per query:

```console
refget blast search -p ./store --all -- -query query.fa -out hits.tsv
refget blast report hits.tsv --query query.fa
```

`search` writes `hits.tsv.meta.json` next to the hits, and `report` reads the store and collections from it.

## 5. Ask where a sequence came from

`origin` does both steps. It searches one representative assembly per species first, then only the species that matched:

```console
refget blast origin -p ./store --all --query query.fa
```

The output is one line per query: the status (`taxon` when one species clearly wins), the species, the best genome and sequence, identity, coverage and how many genomes tie. `refget blast reps -p ./store --all` shows which assembly represents each species and what a staged search will cost.

## More

- [`refget blast` command reference](../reference/cli.md#blast-commands)
- [`gtars blast`](https://docs.refgenie.org/gtars/) for the same commands in the gtars CLI, Python and R
