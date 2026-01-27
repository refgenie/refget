# Show how to use a refget client to interact with a refgenie server

from refget import SequenceCollectionClient

seqcol_client = SequenceCollectionClient(urls=["https://api.refgenie.org/seqcol"])

cols = seqcol_client.list_collections()

example_digest = cols["results"][0]

seqcol_client.get_collection(example_digest)
