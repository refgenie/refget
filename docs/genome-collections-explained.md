# The reference genome jungle

The reference genome jungle is a public RefgetStore of human and mouse reference assemblies gathered from many providers: NCBI, Ensembl, UCSC, GENCODE, iGenomes, ENA, DDBJ, the Broad Institute, refgenie, and the 1000 Genomes Project. It exists because the same genome build is published many times over. Each provider formats its FASTA differently, with its own chromosome names, masking, sequence order, and choice of alt contigs and patches, and every one of those files is a distinct sequence collection with a distinct digest. The jungle gathers them into one content-addressed store so the relationships between them can be seen and queried.

The store is served as static files from S3:

```
https://refgenie.s3.us-east-1.amazonaws.com/refget-store/jungle/
```

It is also the store behind the public seqcol API at `seqcolapi.databio.org`, and it is the dataset from the paper *Taming the reference genome jungle: the refget sequence collection standard*.

## The store at a glance

| Metric | Value |
|--------|-------|
| Sequence collections (FASTA files) | 79 |
| Unique sequences | 6,359 |
| Total sequence content | 41.8 Gbp |
| Source FASTA entries | 96, from 10 providers |

Several source files produce the same collection (identical content from different providers, or soft-masked and unmasked versions of one file), so there are fewer collections than input files. Identical sequences are stored once and shared between collections, which is why 79 whole genomes amount to only a few thousand unique sequences.

## One store per purpose

The jungle is one of a family of public stores maintained through the [refgenie-registry](https://github.com/refgenie/refgenie-registry) repository. Earlier, a single "brickyard" store held everything, including the pangenome haplotypes and hundreds of vertebrate assemblies. That store was split into stores with one purpose each, all published under the same `refget-store/` prefix:

| Store | Contents | Collections |
|-------|----------|-------------|
| `jungle` | Human and mouse reference assemblies across providers | 79 |
| `pangenome` | HPRC year-1 haplotype-resolved human assemblies | 96 |
| `igenomes` | AWS iGenomes references used by nf-core and Illumina pipelines | 99 |
| `vgp` | Vertebrate Genomes Project assemblies | 605 |
| `refseq` | NCBI RefSeq protein and transcript sequences | 32 |
| `vrs` | Reference sequences for VRS variant representation | 39 |
| `demo` | Small test FASTAs; the GA4GH compliance reference | 6 |

Each store's contents are defined by a `sources.csv` in the registry's `stores/` directory, and the registry's build scripts produce and publish the stores. See the [store list](https://refget.databio.org/explore) to browse any of them.

## How genomes are identified

Every collection has a refget digest computed from its sequence content. On top of that, the jungle carries five collection alias namespaces so genomes can be found by familiar identifiers. For how aliases work in general, see [Names, aliases, and identifiers](names-and-aliases-explained.md).

| Namespace | Holds | Example |
|-----------|-------|---------|
| `accession` | NCBI assembly accessions, both RefSeq and GenBank | `GCF_000001405.40` |
| `refseq` | RefSeq accessions only | `GCF_000001405.40` |
| `insdc` | GenBank accessions only | `GCA_000001405.29` |
| `genome_assembly` | Short build names | `hg38`, `hg19`, `mm39`, `mm10` |
| `name` | A descriptive name for every collection, recording build and provider | `GRCh38.p14-fasta-genomic`, `hg38-primary-113-ensembl` |

Only NCBI files carry accessions, so the `accession`, `refseq`, and `insdc` namespaces cover a subset of the store. The `name` namespace covers every collection and is the best way to see everything the jungle holds. A short build name in `genome_assembly` resolves to one representative collection for that build.

The store also declares sequence alias namespaces (`ucsc`, `ensembl`, `refseq`, `gencode`, and others) that map provider-specific sequence names to sequence digests.

## The same build from many providers

GRCh38 appears in the jungle many times: NCBI's genomic, full-analysis, and no-alt files across patch releases, Ensembl primary and top-level files, UCSC files, GENCODE releases, iGenomes bundles, and more. These differ in ways that matter for analysis:

- **Chromosome naming.** NCBI uses accessions such as `NC_000001.11`, Ensembl uses `1`, and UCSC uses `chr1`.
- **Masking.** Soft-masked and unmasked files have the same digest, because digests are computed on uppercased sequence. Hard-masked files do not.
- **Scope.** Primary-assembly files hold the 25 chromosomes; top-level and full-analysis files add unplaced scaffolds, alt contigs, and patches.

Because sequences are identified by content, a RefgetStore can relate these files to one another. The seqcol comparison reports which attributes and array elements two collections share, the `sorted_name_length_pairs` digest identifies collections with the same coordinate system regardless of naming, and `match_sequence_names` translates chromosome names between two collections by joining them on sequence digest. The [jungle tutorial](using-services/genome-store.py) walks through each of these.

## On-disk layout

The jungle follows the standard [RefgetStore format](reference/refgetstore-format.md): a manifest, a sequence index, a collection index, one `.rgsi` file per collection, deduplicated sequence files, and alias tables under `aliases/`. Opening it remotely fetches the manifest, the collection index, and the alias tables, and downloads sequences only when they are read. See [How RefgetStore defers loading](lazy-loading-explained.md) for the details.

## Learn more

- [Exploring the reference genome jungle](using-services/genome-store.py) -- Hands-on tutorial against the public store
- [Names, aliases, and identifiers](names-and-aliases-explained.md) -- How the alias system works in general
- [What is RefgetStore?](refgetstore-explained.md) -- The storage format underlying the collection
- [Understanding FHR metadata](fhr-metadata-explained.md) -- Attaching species and assembly metadata to collections
