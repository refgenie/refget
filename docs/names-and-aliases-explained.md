# Names, Aliases, and Identifiers

RefgetStore uses three distinct systems for identifying sequences and collections. Each solves a different problem, operates at a different scope, and exists for a different reason. Understanding the differences -- and why all three are necessary -- is key to working effectively with RefgetStore.

## The identification problem in genomics

Consider the string "chr1". It appears in GRCh38, GRCh37, mm10, dm6, and hundreds of other genome assemblies. Each time, it refers to a completely different sequence. The string "chr1" is meaningless on its own -- it only becomes meaningful when you know *which assembly* you are talking about.

Now consider the accession "NC_000001.11". This is assigned by INSDC (the International Nucleotide Sequence Database Collaboration) and refers to exactly one sequence worldwide: human chromosome 1 from the GRCh38 assembly. No matter where you encounter this identifier, it means the same thing.

Finally, consider the digest `EjrJJS1FmLaytz_EHgNvVZ8owSU7kbNb`. This is computed directly from the sequence content using a cryptographic hash. Nobody assigned it. Nobody manages it. It is a mathematical consequence of the sequence itself. Two independent labs on opposite sides of the world, working with the same sequence, will compute the same digest without any coordination.

These three kinds of identifiers -- local names, registry-assigned accessions, and content-derived digests -- form a hierarchy from most ambiguous to most universal.

## Three levels of identification

### Level 1: Refget digests (content-addressed, computed)

At the foundation of RefgetStore sits the refget digest. Every sequence gets one. Every collection gets one. They are computed from content using the GA4GH algorithm (SHA-512, truncated to 24 bytes, base64url-encoded), and they are globally unique by mathematical guarantee -- not by convention, not by policy, but by the properties of cryptographic hashing.

Digests are the canonical identifiers in RefgetStore. They are what the store uses internally to organize files on disk, to deduplicate sequences across assemblies, and to enable content-addressable retrieval. When you call `store.get_sequence(digest)`, you are using the most fundamental form of identification the system offers.

The strength of digests is their universality. The weakness is their opacity. No human can look at `EjrJJS1FmLaytz_EHgNvVZ8owSU7kbNb` and know it represents human chromosome 1. That is where the other two identification systems come in.

For a deeper treatment of how digests are computed and what they encode, see [What are refget digests?](digests-explained.md).

### Level 2: Registry identifiers / Aliases (assigned by authorities, globally unique)

Between the raw universality of digests and the local ambiguity of names sits a middle layer: identifiers assigned by authoritative registries. INSDC assigns accessions like "NC_000001.11". GenBank assigns "CM000663.2". Ensembl assigns "1" (within its own namespace). These are all globally unique *within their respective registries* and each refers to exactly one sequence worldwide.

In RefgetStore, these are called **aliases**, and they are organized by **namespace** -- a string identifying which registry or authority assigned the identifier. An alias is the combination of a namespace and an identifier: `insdc/NC_000001.11`, `genbank/CM000663.2`, `ensembl/1`.

Aliases must be explicitly registered in the store. They are not computed or discovered automatically. You add them with calls like:

```python
store.add_sequence_alias("insdc", "NC_000001.11", digest)
store.add_collection_alias("ncbi", "GRCh38", collection_digest)
```

And you resolve them with:

```python
record = store.get_sequence_by_alias("insdc", "NC_000001.11")
coll = store.get_collection_by_alias("ncbi", "GRCh38")
```

A single sequence can have aliases in many registries. The same underlying sequence (same digest) might be known as `insdc/NC_000001.11`, `genbank/CM000663.2`, and `ensembl/1`. These are three different names for the same thing, each assigned by a different authority.

### Level 3: Sequence names (local identifiers, collection-scoped)

At the most local level are **sequence names** -- the identifiers that come from FASTA headers. When you load a FASTA file into RefgetStore, the header lines (`>chr1`, `>chrX`, `>scaffold_123`) become the names of sequences within that collection. These are stored automatically as part of the collection metadata.

Sequence names are scoped to a single collection. The name "chr1" is meaningless without knowing which collection you are referring to, so looking up a sequence by name always requires the collection digest as context:

```python
record = store.get_sequence_by_name(collection_digest, "chr1")
```

This is fundamentally different from alias lookup, which needs only a namespace and identifier -- no collection context required.

### Names vs. aliases at a glance

| | Sequence names | Aliases |
|---|---|---|
| Origin | FASTA headers (automatic) | Registered explicitly |
| Scope | Collection-scoped | Global (within namespace) |
| Uniqueness | Not unique across assemblies | Unique within registry |
| Example | "chr1" | "insdc/NC_000001.11" |
| Lookup | `get_sequence_by_name(collection, "chr1")` | `get_sequence_by_alias("insdc", "NC_000001.11")` |

## Why all three are necessary

It might seem redundant to have three identification systems. But each fills a gap the others cannot.

**Digests are universal but inhuman.** They guarantee uniqueness and enable deduplication, but you cannot communicate them verbally, remember them, or use them in casual conversation. A bioinformatician will never say "I aligned my reads to `EjrJJS1FmLaytz_EHgNvVZ8owSU7kbNb`." They will say "I aligned to hg38 chr1."

**Aliases are human-readable and globally unique, but require infrastructure.** Someone has to assign them, someone has to maintain a registry, and someone has to register them in your store. They bridge the gap between mathematical identifiers and everyday usage, but they don't come for free.

**Names are what people actually use, but they are ambiguous.** Every genome assembly has a "chr1". The name is immediately recognizable and useful in context, but dangerous without it. RefgetStore handles this by requiring you to specify the collection whenever you look up by name.

## Why namespaces exist

Namespaces prevent collisions between registries. Without them, the identifier "1" could refer to Ensembl's chromosome 1 or some other registry's sequence labeled "1". By pairing each identifier with its namespace (`ensembl/1` vs. `ucsc/chr1`), RefgetStore keeps them distinct.

Different registries can -- and do -- assign different identifiers to the same sequence. INSDC calls human chromosome 1 "NC_000001.11" while GenBank calls it "CM000663.2". Both point to the same underlying sequence with the same refget digest. Namespaces make this many-to-one mapping explicit: multiple aliases across multiple namespaces can all resolve to a single digest.

The namespace is always the first argument when adding or resolving aliases. This is a deliberate design choice. It forces you to be explicit about *which authority* you are trusting, rather than hoping that an identifier is unambiguous across all possible registries.

## Common namespaces

The namespace string is free-form -- you can use any string that identifies your authority. Some conventions that are widely used:

| Namespace | Authority | Example identifier |
|-----------|-----------|-------------------|
| `insdc` | International Nucleotide Sequence Database Collaboration (NCBI/ENA/DDBJ) | `NC_000001.11` |
| `genbank` | GenBank | `CM000663.2` |
| `refseq` | NCBI RefSeq | `NC_000001.11` |
| `ensembl` | Ensembl | `1` or `ENSG00000139618` |
| `ucsc` | UCSC Genome Browser | `chr1`, `hg38` |
| `ncbi` | NCBI (for assembly names) | `GRCh38` |

Using widely recognized namespace strings makes alias data easier to share and interpret across tools and teams.

## Collections have the same structure

Everything described above applies to collections as well as sequences. A collection (like a genome assembly) has:

- A **digest**, computed from the digests of its component arrays (names, lengths, sequences). This is determined automatically when the collection is created.

- **Aliases**, assigned by external authorities. NCBI might call it "GRCh38", UCSC might call it "hg38". These are registered explicitly:

    ```python
    store.add_collection_alias("ncbi", "GRCh38", collection_digest)
    store.add_collection_alias("ucsc", "hg38", collection_digest)
    ```

- **No "names" in the sequence-name sense.** Collections do not come from FASTA headers the way sequences do, so there is no automatic local-name layer for collections. Aliases serve that role.

Collection aliases tend to feel more intuitive than sequence aliases, because assembly names like "GRCh38" and "hg38" are already widely understood to refer to specific, distinct things. Sequence names like "chr1" feel less unique because we encounter the same string in so many different contexts.

## Lookup methods at a glance

| What you know | Method | Scope |
|---|---|---|
| Sequence digest | `get_sequence(digest)` | Global |
| Registry + identifier | `get_sequence_by_alias("insdc", "NC_000001.11")` | Global |
| Collection + name | `get_sequence_by_name(collection_digest, "chr1")` | Collection-scoped |
| Collection alias | `get_collection_by_alias("ncbi", "GRCh38")` | Global |

The pattern is consistent: digest-based lookups and alias-based lookups are global (no additional context needed), while name-based lookups are collection-scoped (you must provide the collection).

## Reverse lookups

Given a digest, you can discover all aliases that point to it:

```python
aliases = store.get_aliases_for_sequence(digest)
for namespace, alias in aliases:
    print(f"{namespace}/{alias}")
```

This is useful for answering questions like "what do other registries call this sequence?" or "has anyone registered a human-readable name for this collection?" The same pattern works for collections via `get_aliases_for_collection()`.

## Persistence and storage

On-disk RefgetStores persist aliases in the `aliases/` directory of the store:

```
my_store/
  aliases/
    sequences/
      insdc.tsv      <- one file per sequence alias namespace
      genbank.tsv
      ensembl.tsv
    collections/
      ncbi.tsv       <- one file per collection alias namespace
      ucsc.tsv
```

Each TSV file contains `alias<TAB>digest` pairs, one per line. Comment lines begin with `#`. This plain-text format means alias files are human-readable, diff-friendly, and can be shared or edited independently of the rest of the store.

The manifest (`rgstore.json`) is the authority on which namespaces exist: both `RefgetStore.open_local()` and `RefgetStore.open_remote()` load exactly the sequence and collection alias namespaces the manifest declares, rather than scanning the `aliases/` directory for files. A `.tsv` file sitting in `aliases/` that the manifest doesn't list is simply ignored. This keeps local and remote behavior identical, since a remote store cannot be directory-listed over HTTP in the first place. Opening locally tolerates a declared namespace whose file is missing (it is skipped); opening remotely treats a declared-but-unfetchable namespace as an error, since a remote manifest that advertises a namespace it can't actually serve indicates the remote is broken. Aliases travel with the store: copying a store directory to another machine preserves all registered aliases, as long as the manifest and the alias files stay in sync.

In-memory stores support aliases in memory, but they are not persisted when the store goes out of scope.

## The design trade-off

RefgetStore could have tried to unify all three identification systems into one. It did not, and for good reason.

Unifying names and digests would require computing a digest for every FASTA header, which confuses the distinction between *what something is* (its content) and *what someone calls it* (its name in a particular context). Two assemblies can have sequences with the same name ("chr1") that are entirely different sequences with different digests.

Unifying names and aliases would require treating FASTA headers as globally unique, which they are not. Or it would require always specifying a namespace when working with names, which adds friction to the most common use case (looking up "chr1" in a known assembly).

The three-level system reflects the reality of how biological sequences are identified in practice: by content (digests), by authority (aliases), and by local convention (names). RefgetStore provides the lookup methods for each, keeping them cleanly separated while allowing free movement between them when you know the digest that ties them together.

## Learn more

- [Working with Aliases](using-services/aliases.py) -- How to add, resolve, browse, and remove aliases
- [RefgetStore tutorial](using-services/refgetstore.py) -- Hands-on guide including sequence name lookups
- [What are refget digests?](digests-explained.md) -- How digests are computed and what they encode
- [The reference genome jungle](genome-collections-explained.md) -- How aliases are used in practice across a large genome collection
