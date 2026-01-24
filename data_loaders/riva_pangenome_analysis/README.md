# RIVA Pangenome RefgetStore

## Build the store

```python
import os
from pathlib import Path
from refget.store import RefgetStore

fa_root = Path(os.path.expandvars("$BRICKYARD/datasets_downloaded/pangenome_fasta/2023_hprc_draft"))
output_dir = Path(os.path.expandvars("$BRICKYARD/datasets_downloaded/pangenome_fasta/refget_store2"))

store = RefgetStore.on_disk(str(output_dir))

for fasta in sorted(fa_root.glob("**/*.fa.gz")):
    print(f"Loading {fasta.name}...")
    store.add_sequence_collection_from_fasta(str(fasta))

print(store.stats())
```

## Check local store

```python
import os
from pathlib import Path
from refget.store import RefgetStore

store_dir = Path(os.path.expandvars("$BRICKYARD/datasets_downloaded/pangenome_fasta/refget_store2"))

store = RefgetStore.on_disk(str(store_dir))

store.list_collections()
cm = store.get_collection_metadata("s0nMiOFHPsIBrm2bd3PkzWXKLKWQZq70")


EXAMPLE_COLLECTION = "0aHV7I-94paL9Z1H4LNlqsW3WxJhlou5"
EXAMPLE_SEQ_NAME = "JAGYVX010000006.1 unmasked:primary_assembly HG03540.pri.mat.f1_v2:JAGYVX010000006.1:1:96320881:1"

record = store.get_sequence_by_collection_and_name(EXAMPLE_COLLECTION, EXAMPLE_SEQ_NAME)


## Upload to S3

```bash
module load awscli
export AWS_ACCESS_KEY_ID=`pass databio/refgenie/s3_access_key_id`
export AWS_SECRET_ACCESS_KEY=`pass databio/refgenie/s3_secret_access_key`

aws s3 sync $BRICKYARD/datasets_downloaded/pangenome_fasta/refget_store2 s3://refgenie/pangenome_refget_store
```

## Load from S3

```python
from refget.store import RefgetStore
import os
store = RefgetStore.open_remote(
    os.path.expanduser("~/.refget/pangenome_cache"),
    "https://refgenie.s3.us-east-1.amazonaws.com/pangenome_refget_store"
)

collections = store.list_collections()
col1 = collections[0]
col1_loaded = store.get_collection_metadata(col1.digest)
col1_loaded_seqs = store.get_collection(col1.digest)
col1_loaded
col1_loaded_seqs
col1_loaded_seqs.sequences
s1 = col1_loaded_seqs.sequences[0]
seq = store.get_sequence(col1_loaded_seqs.sequences[0].metadata.sha512t24u)
seq
s1
seq.decode()
store.get_collection_metadata(col1.digest)
col1_loaded.is_loaded()


```

## Alternative: building from the CLI:

On rivanna, this is *waaaay slower* than doing it from python.

cd $BRICKYARD/datasets_downloaded/pangenome_fasta/
```
for f in 2023_hprc_draft/*.fa.gz; do
 refget store add "$f" -p refget_store2; done
```

refget store init -p refget_store2

```
for f in /media/nsheff/t5/pangeome_fasta//*.fa.gz; do
 refget store add "$f" -p refget_store2; done
```



