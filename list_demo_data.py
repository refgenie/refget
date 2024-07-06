import json
from refget import SeqColClient

template = """
Filepath: {f}
Digest: {digest}
Object:
{pretty_str}
"""

scc = SeqColClient("http://127.0.0.1:8100")
scc.get_collection(digest)

for demo_file in DEMO_FILES:
    f = os.path.join(fa_root, demo_file)
    print("Fasta file to be loaded: {}".format(f))
    digest = refget.fasta_file_to_digest(f, dbc.inherent_attrs)
    seqcol = scc.get_collection(digest)
    pretty_str = json.dumps(
        seqcol,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        indent=2,
    )
    print(template.format(f=f, digest=digest, pretty_str=pretty_str))


# demo_results = {}
# for demo_file in DEMO_FILES:
#     f = os.path.join(fa_root, demo_file)
#     print("Fasta file to be loaded: {}".format(f))
#     demo_results[f] = dbc.seqcol.add_from_fasta_file(f)
