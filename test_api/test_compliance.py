# Draft of a compliance suite for the API

import json
import pytest
import requests
import refget

# Collection endpoints
# DEMO_FILES = [
#     "demo0.fa",
#     "demo1.fa.gz",
#     "demo2.fa",
#     "demo3.fa",
#     "demo4.fa",
#     "demo5.fa.gz",
#     "demo6.fa",
# ]

DEMO_FILES = [
    "base.fa",
    "different_names.fa",
    "different_order.fa",
    "pair_swap.fa",
    "subset.fa",
    "swap_wo_coords.fa",
]

API_TEST_DIR = "test_api"

COLLECTION_TESTS = [
    (DEMO_FILES[0], f"{API_TEST_DIR}/collection/base_collection.json"),
    (DEMO_FILES[1], f"{API_TEST_DIR}/collection/different_names_collection.json"),
    (DEMO_FILES[2], f"{API_TEST_DIR}/collection/different_order_collection.json"),
    (DEMO_FILES[3], f"{API_TEST_DIR}/collection/pair_swap_collection.json"),
    (DEMO_FILES[4], f"{API_TEST_DIR}/collection/subset_collection.json"),
    (DEMO_FILES[5], f"{API_TEST_DIR}/collection/swap_wo_coords_collection.json"),
]

COMPARISON_TESTS = [
    f"{API_TEST_DIR}/comparison/compare_subset.json",  # subset
    f"{API_TEST_DIR}/comparison/compare_different_names.json",  # same sequences, different names
    f"{API_TEST_DIR}/comparison/compare_different_order.json",  # same sequences, name order switch, but equivalent coordinate system
    f"{API_TEST_DIR}/comparison/compare_pair_swap.json",  # swapped name-length-pairs
    f"{API_TEST_DIR}/comparison/compare_swap_wo_coords.json",  # swapped name-length-pairs, but no coord system change
]

ATTRIBUTE_TESTS = [
    ("lengths", "7-_HdxYiRf-AJLBKOTaJUdxXrUkIXs6T", [8,4]),
    ("names", "Fw1r9eRxfOZD98KKrhlYQNEdSRHoVxAG", ["chrX","chr1","chr2"])
]

ATTRIBUTE_LIST_TESTS = [
    ("lengths", "cGRMZIb3AVgkcAfNv39RN7hnT5Chk7RX", f"{API_TEST_DIR}/attribute/cGRM.json",)
]


# This is optional, so we could turn off for a compliance test
TEST_SORTED_NAME_LENGTH_PAIRS = False

# api_root = "http://0.0.0.0:8100"
demo_root = "/home/nsheff/code/refget/test_fasta"
demo_file = "demo0.fa"
response_file = "tests/demo0_collection.json"



def read_url(url):
    import yaml
    print("Reading URL: {}".format(url))
    from urllib.request import urlopen
    from urllib.error import HTTPError
    try:
        response = urlopen(url)
    except HTTPError as e:
        raise e
    data = response.read()  # a `bytes` object
    text = data.decode("utf-8")
    return yaml.safe_load(text)


def check_collection(api_root, demo_file, response_file):

    # Need schema to make sure we eliminate inherent attributes correctly
    schema_path = "https://schema.databio.org/refget/SeqColArraySetInherent.yaml"

    schema = read_url(schema_path)
    inherent_attrs = schema["inherent"]
    print(f"Loading fasta file at '{demo_root}/{demo_file}'")
    digest = refget.fasta_file_to_digest(f"{demo_root}/{demo_file}", inherent_attrs=inherent_attrs)
    print(f"Checking digest: {digest}")
    res = requests.get(f"{api_root}/collection/{digest}")
    try:
        server_answer = json.loads(res.content)
    except json.decoder.JSONDecodeError:
        print(f"Url: {url}")

    with open(response_file) as fp:
        correct_answer = json.load(fp)

    assert (
        server_answer["sequences"] == correct_answer["sequences"]
    ), f"Collection endpoint failed: sequence mismatch for {demo_file}"
    assert (
        server_answer["names"] == correct_answer["names"]
    ), f"Collection endpoint failed: names mismatch for {demo_file}"
    assert (
        server_answer["lengths"] == correct_answer["lengths"]
    ), f"Collection endpoint failed: lengths mismatch for {demo_file}"
    if TEST_SORTED_NAME_LENGTH_PAIRS:
        assert (
            server_answer["sorted_name_length_pairs"] == correct_answer["sorted_name_length_pairs"]
        ), f"Collection endpoint failed: sorted_name_length_pairs mismatch for {demo_file}"


def check_comparison(api_root, response_file):
    with open(response_file) as fp:
        correct_answer = json.load(fp)

    url = f"{api_root}/comparison/{correct_answer['digests']['a']}/{correct_answer['digests']['b']}"
    res = requests.get(url)
    try:
        server_answer = json.loads(res.content)
        print("Server answer:", refget.canonical_str(server_answer))
        print("Correct answer:", refget.canonical_str(correct_answer))
        assert refget.canonical_str(server_answer) == refget.canonical_str(correct_answer), f"Comparison endpoint failed: {url}. File: {response_file}"
    except json.decoder.JSONDecodeError:
        print(f"Url: {url}")
        assert False, f"Comparison endpoint failed: {url}"


def check_attribute(api_root, attribute_type, attribute, correct_value):
    url = f"{api_root}/attribute/{attribute_type}/{attribute}"
    res = requests.get(url)
    try:
        server_answer = json.loads(res.content)
        assert server_answer == correct_value, f"Attribute endpoint failed: {url}. Answer: {correct_value}"
    except json.decoder.JSONDecodeError:
        print(f"Url: {url}")
        assert False, f"Attribute endpoint failed: {url}"

def check_attribute_list(api_root, attribute_type, attribute, response_file):
    with open(response_file) as fp:
        correct_answer = json.load(fp)

    url = f"{api_root}/attribute/{attribute_type}/{attribute}/list"
    res = requests.get(url)
    try:
        server_answer = json.loads(res.content)
        print("Server answer:", server_answer)
        for digest in correct_answer["items"]:
            print("Checking digest:", digest)
            assert digest in server_answer["items"], f"Attribute endpoint failed: {url}. Missing: {digest}"
    except json.decoder.JSONDecodeError:
        print(f"Url: {url}")
        assert False, f"Attribute endpoint failed: {url}"

@pytest.mark.require_service
class TestAPI:

    @pytest.mark.parametrize("test_values", COLLECTION_TESTS)
    def test_collection_endpoint(self, api_root, test_values):
        check_collection(api_root, *test_values)

    @pytest.mark.parametrize("response_file", COMPARISON_TESTS)
    def test_comparison_endpoint(self, api_root, response_file):
        check_comparison(api_root, response_file)

    @pytest.mark.parametrize("test_values", ATTRIBUTE_TESTS)
    def test_attribute_endpoint(self, api_root, test_values):
        check_attribute(api_root, *test_values)

    @pytest.mark.parametrize("test_values", ATTRIBUTE_LIST_TESTS)
    def test_attribute_list_endpoint(self, api_root, test_values):
        check_attribute_list(api_root, *test_values)