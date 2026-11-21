# Understanding FHR Metadata

FHR (FAIR Headers Reference genome) metadata is structured, assembly-level information that you can attach to sequence collections in RefgetStore. It provides a standard way to record *what a genome assembly is*—species, version, masking, taxonomy, licensing, and more—following the FAIR principles (Findable, Accessible, Interoperable, Reusable).

## Why assembly-level metadata matters

A refget collection digest tells you *exactly* which sequences are present—by mathematical proof. What it does not tell you is the biological context: which species, which assembly version, whether repeats are hard-masked or soft-masked, who published the assembly, or under what license it was released.

That context lives in FHR metadata. It answers questions like:

- Is this GRCh38 or GRCh38.p14?
- Is masking soft or hard?
- What taxonomy ID corresponds to this organism?
- Who should I cite if I use this assembly?
- Is there a paper describing this reference?

Without structured metadata, this information is typically scattered across README files, filenames, and institutional memory. FHR provides a single, machine-readable location for it—attached directly to the collection digest.

## The FHR specification

FHR is an open specification developed by the [FAIR-bioHeaders community](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification). It defines a JSON schema for genome assembly metadata. RefgetStore implements FHR metadata as sidecar files attached to collection digests.

Commonly used fields:

| Field | Type | Description |
|-------|------|-------------|
| `schema` | string | URI of the FHR JSON schema |
| `schemaVersion` | number or string | FHR 1 uses the number `1`; FHR 2.0 uses the string `"2.0"` |
| `genome` | string | Species or organism name |
| `version` | string | Assembly version (e.g., "GRCh38.p14") |
| `taxon` | object | Taxonomy info: `name` and `uri` (an identifiers.org taxonomy URI) |
| `masking` | string | One of `not-masked`, `hard-masked`, `soft-masked`, `repeat-masked`, `unknown` |
| `genomeSynonym` | array | Alternative names (e.g., ["hg38"]) |
| `dateCreated` | string | ISO 8601 date |
| `reuseConditions` | string | License and reuse conditions (e.g., "CC0-1.0") |
| `metadataAuthor` | array | Authors of the metadata record (`name` and `uri`) |
| `assemblyAuthor` | array | Authors/producers of the genome assembly (`name` and `uri`) |
| `checksum` | string | Checksum of the FASTA file |
| `scholarlyArticle` | string | DOI of a related publication, without a resolver prefix (e.g., "10.5281/zenodo.6762550") |
| `funding` | string | Funding information |
| `identifier` | array | Identifiers as `prefix:accession` strings (e.g., ["insdc.gca:GCA_000001405.29"]) |

This is not the full list, and the specification is still evolving. See the [FHR specification](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification) for every field and the current rules.

FHR requires `schema`, `schemaVersion`, `genome`, `taxon`, `version`, `metadataAuthor`, `assemblyAuthor`, `dateCreated`, `masking`, and `checksum`. RefgetStore does not enforce this: it accepts partial records, such as one with only `genome`, `version`, and `taxon`. A partial record is still useful, but it will not validate as FHR.

## How FHR metadata is stored

On-disk RefgetStores persist FHR metadata as JSON sidecar files in the `fhr/` directory:

```
my_store/
  collections/
    NikmJ6xnuvO741NgL-zszh5_p4DsD3nV.rgsi   ← collection file
  fhr/
    NikmJ6xnuvO741NgL-zszh5_p4DsD3nV.fhr.json   ← FHR sidecar
```

The sidecar filename is `<collection_digest>.fhr.json`. When you open a store with `RefgetStore.open_local()`, all sidecar files in the `fhr/` directory are loaded automatically. FHR metadata travels with the store: copying a store directory to another machine preserves all attached metadata.

In-memory stores support FHR metadata in memory, but it is not persisted when the store goes out of scope.

## FHR metadata is collection-level, not sequence-level

FHR metadata is attached to collection digests, not to individual sequence digests. This reflects how genome assembly metadata works in practice: masking, taxonomy, versioning, and licensing are properties of an assembly as a whole, not of individual chromosomes or contigs.

If you have two collections derived from the same FASTA but with different processing (e.g., one soft-masked and one hard-masked), each has a different collection digest and can carry its own FHR metadata record describing the difference.

## Relationship to digests and aliases

FHR metadata complements aliases rather than replacing them. Aliases link a registry identifier to a digest ("this collection is also known as GRCh38 in NCBI"). FHR metadata describes what that collection *is* ("it is Homo sapiens, version GRCh38.p14, soft-masked, licensed CC0-1.0").

In a well-maintained store, a collection might have:

- A collection digest (computed from content)
- Collection aliases in multiple namespaces (`ncbi/GRCh38`, `ucsc/hg38`)
- FHR metadata with species, version, masking, taxon, and license

Together, these three layers provide complete, machine-readable provenance for the assembly.

## Learn more

- [FHR Metadata Headers](using-services/fhr-metadata.py) - Hands-on guide: creating, attaching, retrieving, and removing FHR metadata
- [FHR Specification](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification) - The upstream FAIR-bioHeaders specification
- [Names, aliases, and identifiers](names-and-aliases-explained.md) - How aliases complement FHR metadata
- [RefgetStore file format](reference/refgetstore-format.md) - Technical specification including the `fhr/` directory and sidecar file format
