# Draft of a compliance suite for the API

import json
import pytest
import requests

# Collection endpoints
DEMO_FILES = [
    "demo0.fa",
    "demo1.fa.gz",
    "demo2.fa",
    "demo3.fa",
    "demo4.fa",
    "demo5.fa.gz",
    "demo6.fa",
]

API_TEST_DIR = "test_api"

COLLECTION_TESTS = [
    (DEMO_FILES[0], f"{API_TEST_DIR}/collection/demo0_collection.json"),
    (DEMO_FILES[1], f"{API_TEST_DIR}/collection/demo1_collection.json"),
    (DEMO_FILES[2], f"{API_TEST_DIR}/collection/demo2_collection.json"),
    (DEMO_FILES[3], f"{API_TEST_DIR}/collection/demo3_collection.json"),
    (DEMO_FILES[4], f"{API_TEST_DIR}/collection/demo4_collection.json"),
    (DEMO_FILES[5], f"{API_TEST_DIR}/collection/demo5_collection.json"),
    (DEMO_FILES[6], f"{API_TEST_DIR}/collection/demo6_collection.json"),
]

COMPARISON_TESTS = [
    f"{API_TEST_DIR}/comparison/compare_subset.json",  # subset
    f"{API_TEST_DIR}/comparison/compare_different_names.json",  # same sequences, different names
    f"{API_TEST_DIR}/comparison/compare_different_order.json",  # same sequences, name order switch, but equivalent coordinate system
    f"{API_TEST_DIR}/comparison/compare_pair_swap.json",  # swapped name-length-pairs
    f"{API_TEST_DIR}/comparison/compare_swap_wo_coords.json",  # swapped name-length-pairs, but no coord system change
]

# This is optional, so we could turn off for a compliance test
TEST_SORTED_NAME_LENGTH_PAIRS = True

# api_root = "http://0.0.0.0:8100"
demo_root = "/home/nsheff/code/refget/demo_fasta"
demo_file = "demo0.fa"
response_file = "tests/demo0_collection.json"
import refget


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
    print(text)
    return yaml.safe_load(text)


def check_collection(api_root, demo_file, response_file):

    # Need schema to make sure we eliminate inherent attributes correctly
    schema_path = "https://schema.databio.org/refget/SeqColArraySetInherent.yaml"

    schema = read_url(schema_path)
    print(f"Loading fasta file at '{demo_root}/{demo_file}'")
    digest = refget.fasta_file_to_digest(f"{demo_root}/{demo_file}", schema=schema)
    print(f"Checking digest: {digest}")
    res = requests.get(f"{api_root}/collection/{digest}")
    server_answer = json.loads(res.content)
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
    res = requests.get(
        f"{api_root}/comparison/{correct_answer['digests']['a']}/{correct_answer['digests']['b']}"
    )
    server_answer = json.loads(res.content)
    assert server_answer == correct_answer, "Comparison endpoint failed"


@pytest.mark.require_service
class TestAPI:

    @pytest.mark.parametrize("test_values", COLLECTION_TESTS)
    def test_collection_endpoint(self, api_root, test_values):
        # print("Service unavailable: ", SERVICE_UNAVAILABLE)
        check_collection(api_root, *test_values)

    @pytest.mark.parametrize("response_file", COMPARISON_TESTS)
    def test_comparison_endpoint(self, api_root, response_file):
        # print("Service unavailable: ", SERVICE_UNAVAILABLE)
        check_comparison(api_root, response_file)
