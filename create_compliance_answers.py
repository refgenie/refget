# Use this script to generate "correct" answers for the compliance tests,
# using a known good client.
# Assumes you have a sequence collections server running, with the
# demo collections loaded from the test_fasta folder.
# If you don't have this set up, use the `load_demo_fasta.py` script
# to load the demo fasta files into the database.

import refget

col_client = refget.SequenceCollectionClient(urls=["http://127.0.0.1:8100"])

demo_results = {}
for demo_file in DEMO_FILES:
    file_path = f"{fa_root}/{demo_file}"
    basename = os.path.basename(file_path)
    print(f"Fasta file to be loaded: {basename}")
    res = refget.build_seqcol_model(
        refget.fasta_to_seqcol(f"{fa_root}/{demo_file}"),
        inherent_attrs=["names", "sequences"],
    )
    demo_results[basename] = res

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
