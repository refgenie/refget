# Models
# Used for documentation examples in OpenAPI

from fastapi import Path, Body

example_digest = Path(
    ...,
    description="Sequence collection digest",
    pattern=r"^[-\w]+$",
    max_length=64,
    min_length=16,
    examples="a6748aa0f6a1e165f871dbed5e54ba62",
)

example_attribute_digest = Path(
    ...,
    description="Attribute digest",
    pattern=r"^[-\w]+$",
    max_length=64,
    min_length=16,
    examples="cGRMZIb3AVgkcAfNv39RN7hnT5Chk7RXCopy",
)

example_collection_digest = Path(
    ...,
    description="Sequence collection digest",
    pattern=r"^[-\w]+$",
    max_length=64,
    min_length=16,
    examples="a6748aa0f6a1e165f871dbed5e54ba62",
)


example_pangenome_digest = Path(
    ...,
    description="Pangenome digest",
    pattern=r"^[-\w]+$",
    max_length=64,
    min_length=8,
    examples="a6748aa0f6a1e165f871dbed5e54ba62",
)

example_digest_2 = Path(
    ...,
    description="Sequence collection digest",
    pattern=r"^[-\w]+$",
    max_length=64,
    min_length=32,
    examples="2786eb8a921aa97018c214f64b9960a0",
)

example_digest_hg38 = Path(
    ...,
    description="Sequence collection digest",
    pattern=r"^[-\w]+$",
    max_length=64,
    min_length=32,
    examples="514c871928a74885ce981faa61ccbb1a",
)

example_digest_hg38_primary = Path(
    ...,
    description="Sequence collection digest",
    pattern=r"^[-\w]+$",
    max_length=64,
    min_length=32,
    examples="c345e091cce0b1df78bfc124b03fba1c",
)

example_sequence = Path(
    ...,
    description="Refget sequence digest",
    pattern=r"^[-\w]+$",
    max_length=64,
    min_length=32,
    examples="SQ.iYtREV555dUFKg2_agSJW6suquUyPpMw",
)

example_hg38_sc = Body(
    {
        "lengths": [
            "248956422",
            "242193529",
            "198295559",
            "190214555",
            "181538259",
            "170805979",
            "159345973",
            "145138636",
            "138394717",
            "133797422",
            "135086622",
            "133275309",
            "114364328",
            "107043718",
            "101991189",
            "90338345",
            "83257441",
            "80373285",
            "58617616",
            "64444167",
            "46709983",
            "50818468",
            "16569",
            "156040895",
            "57227415",
        ],
        "names": [
            "chr1",
            "chr2",
            "chr3",
            "chr4",
            "chr5",
            "chr6",
            "chr7",
            "chr8",
            "chr9",
            "chr10",
            "chr11",
            "chr12",
            "chr13",
            "chr14",
            "chr15",
            "chr16",
            "chr17",
            "chr18",
            "chr19",
            "chr20",
            "chr21",
            "chr22",
            "chrM",
            "chrX",
            "chrY",
        ],
        "sequences": [
            "a004bc1b0bf05fc668cab6bbfd93d3eb",
            "0ccf3a67666ac53f99fcad19768f2dde",
            "bda7b228789169ae811dd8d676d517ca",
            "88a6091e2d9a609f4ea7eaef937cd4c2",
            "0f1725f15e8046a6a04e32de629b1e10",
            "08c3702d62a2c476a081d3ccd15ea30c",
            "cac9e313d08cdf40c9eeafe62b17879a",
            "9a2ebb88dc34c2af023d50219248c815",
            "41bbec590d36e711864dc6f030f0264b",
            "6b420cbb22daea77d7cc930c0a00f812",
            "0d4e0be5c4e5bc0f12912894f21a5dd8",
            "e1507ba70028a65b3f5a81b594e6f0fe",
            "7110500758388b169fe631b212b7e56c",
            "f37e77fdbacb1a0f1be5e2bf25df343d",
            "3f14ce1984dada290682eb1f564934ee",
            "88169bd58f0c5f9fd083030d1357d908",
            "0bbc162a7d963574b5989adab5651ac5",
            "388e8c7cd11a23eebf84a02d5e442bb7",
            "1c927775585df1cb09ec7c7dd1b32a6a",
            "c37960f60eff5e2cfbde87e53d262efa",
            "f0324d60ccf85288a26a47a7ca25a54a",
            "f7479d5a2a3169e2e44d97d7f2a13db1",
            "6ab1f3c8f4941e148463c40408c89e43",
            "6bdaf93397b486a58fd60b55aa2e21ca",
            "9bd609da53b41a50a724f2a0131ee9c1",
        ],
    }
)

reclimit_ex = Path(
    ...,
    description="Recursion limit, the number of times to recurse to populate digests in the structure",
    gt=-1,
    lt=2,
    examples=0,
)
