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

## Upload to S3

```bash
module load awscli
export AWS_ACCESS_KEY_ID=`pass databio/refgenie/s3_access_key_id`
export AWS_SECRET_ACCESS_KEY=`pass databio/refgenie/s3_secret_access_key`

aws s3 sync $BRICKYARD/datasets_downloaded/pangenome_fasta/refget_store s3://refgenie/pangenome_refget_store
```

## Load from S3

```python
from refget import RefgetStore

store = RefgetStore.load_remote(
    "~/.refget/pangenome_cache",
    "https://refgenie.s3.us-east-1.amazonaws.com/pangenome_refget_store"
)
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



