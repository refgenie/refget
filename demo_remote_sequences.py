import requests

res = requests.get(
    "https://beta.ensembl.org/data/refget/sequence/6681ac2f62509cfc220d78751b8dc524"
)


import refget

seq_client = refget.SequenceClient()
seq_client.raise_errors

seq_client.get_sequence("6681ac2f62509cfc220d78751b8dc524", start=0, end=10)
r = seq_client.get_sequence("BogusDigest")
