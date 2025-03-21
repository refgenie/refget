# Use this script to generate "correct" answers for the compliance tests,
# using a known good client.
# Assumes you have a sequence collections server running, with the
# demo collections loaded from the test_fasta folder.
# If you don't have this set up, use the `load_demo_fasta.py` script
# to load the demo fasta files into the database.

import json
import os
import refget

from refget import SequenceCollection
from tests.conftest import DEMO_FILES

# The first section doesn't require a server, just the fasta files.
# We will just compute the digests for the demo fasta files using the local
# digest functions, and then save the results to a file.

fa_root = "test_fasta"
demo_results = {}
demo_results_json = {}
for demo_file in DEMO_FILES:
    file_path = f"{fa_root}/{demo_file}"
    basename = os.path.basename(file_path)
    print(f"Fasta file to be loaded: {basename}")
    res = SequenceCollection.from_dict(
        refget.fasta_to_seqcol_dict(f"{fa_root}/{demo_file}"),
        inherent_attrs=["names", "sequences"],
    )
    demo_results[basename] = res
    demo_results_json[basename] = {
            "name": basename,
            "top_level_digest": res.digest,
            "sorted_name_length_pairs_digest": res.sorted_name_length_pairs_digest,
            "level1": res.level1(),
            "level2": res.level2(),
        }


print(json.dumps(demo_results_json, indent=2))




for n, sc in demo_results.items():
    print(f"{n}: {sc.digest} {sc.sorted_name_length_pairs_digest}")

# write this to a file:
demo_results_json
with open("test_fasta/test_fasta_digests.json", "w") as f:
    f.write(json.dumps(demo_results_json, indent=2))

refget.validate_seqcol(demo_results["base.fa"].level2())

# This would be used to validate against the pydantic schema,
# a jsonschema derived from the pydantic model itself.
# SequenceCollection.model_validate(demo_results['base.fa'].level2())


# Now we can use the client to generate the correct answers for the compliance tests
# For this we need to have a running server with the demo fasta files loaded

col_client = refget.SequenceCollectionClient(urls=["http://127.0.0.1:8100"])

# comparisons
attribute_root = "test_api/attribute"
collection_root = "test_api/collection"
comparison_root = "test_api/comparison"
for x in demo_results.keys():
    print("X: ", x)
    # save collection
    collection_file = f"{collection_root}/{x}.json"
    res = col_client.get_collection(demo_results[x].digest)
    with open(collection_file, "w") as f:
        f.write(json.dumps(res, indent=2))
    for y in demo_results.keys():
        print("Y: ", y)
        if x >= y:
            continue
        res = col_client.compare(demo_results[x].digest, demo_results[y].digest)
        # save the result to a file
        comparison_file = f"{comparison_root}/compare_{x}_{y}.json"
        with open(comparison_file, "w") as f:
            f.write(json.dumps(res, indent=2))


# def serialize_sqlmodel(obj):
#     data = obj.model_dump()
#     for key, value in obj.__dict__.items():
#         if key.startswith("_"):
#             continue
#         elif isinstance(value, SQLModel):
#             data[key] = serialize_sqlmodel(value)  # Handle nested objects
#     return data
# serialize_sqlmodel(demo_results[x])

# res = refget.compare_seqcols(serialize_sqlmodel(demo_results[x]), serialize_sqlmodel(demo_results[y]))
