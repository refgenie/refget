# Missing seqcolapi collections

8 collections hosted on seqcolapi.databio.org are not in any RefgetStore.
These were loaded into the PostgreSQL-backed seqcolapi directly from
`fasta/pangenome_reference/` FASTAs that weren't included in the combined store build.

## TODO

Load these into the jungle store. 7 of 8 are confirmed in `$BRICK_ROOT/fasta/pangenome_reference/`:

| Digest | Seqs | FASTA |
|---|---|---|
| `2WhejNO718T5jvB4DVTAz-A_JF03iIkz` | 25 | `GCA_009914755.4_CHM13_T2T_v2.0_genomic.fna.gz` |
| `6DfkalgYxFZiYAKpJf19dbpnS-dGzi4m` | 24 | `chm13.draft_v1.1.fasta.gz` |
| `Hve5dblWYLxu1p9Cp930NB8twHGCsf6X` | 640 | `GCA_000001405.28_GRCh38.p13_genomic.fa.gz` |
| `VDUOdAUYpXHUhvU-MNmOTgYQAl67yRMs` | 445 | `Homo_sapiens.GRCh38.dna.alt.fa.gz` |
| `WwIG41XDzO0BTmEpzT7nPXv6Dfx7h4ju` | 1 | `CM000663.2.fasta.gz` |
| `awlJ5Q7EPDVlwXWH8LPN93oJ5jY2uajW` | 24 | `T2T-CHM13v2.0.unmasked.fa.gz` |
| `qJ79liNTAD-LShR3j_2xntOEt-eC3vhM` | 639 | `Homo_sapiens.GRCh38.dna.toplevel.fa.gz` |
| `gHcfbUVnFzHv3QSqz2sSqVHdUQbDO8N5` | 3366 | Not in pangenome_reference. Likely `GRCh38_full_analysis_set_plus_decoy_hla.fa.gz` from `fasta/jungle/homo_sapiens/` |

These are needed for seqcol compliance testing since they're currently served by the API.
