# Compliance suite for the GA4GH SeqCol API v1.0.0
#
# Endpoints tested:
#   - GET /service-info
#   - GET /collection/:digest (level 1 and level 2)
#   - GET /comparison/:digest1/:digest2
#   - POST /comparison/:digest
#   - GET /attribute/collection/:attr/:digest
#   - GET /list/collection (with pagination and filtering)
#   - GET /list/attributes/:attr
#
# Also validates:
#   - Level 1 returns digest strings, level 2 returns arrays
#   - Transient attributes (sorted_name_length_pairs) in level 1 only
#   - Pagination structure (results + pagination fields)
#
# Tests fall into two categories:
# 1. Content tests (collection, comparison, attribute): compare full responses to known fixtures
# 2. Structure tests (service-info, list endpoints): validate response structure only, since values vary by server

import json
import pytest
import requests
import refget

# Collection endpoints
from tests.api.conftest import (
    COLLECTION_TESTS,
    COMPARISON_TESTS,
    ATTRIBUTE_TESTS,
    ATTRIBUTE_LIST_TESTS,
)
from tests.conftest import DIGEST_TESTS

demo_file = "demo0.fa"
response_file = "tests/demo0_collection.json"

print("Testing Compliance")


def read_url(url):
    import requests
    import yaml

    try:
        response = requests.get(url, timeout=1)
    except requests.exceptions.ConnectionError:
        print(f"Connection error: {url}")
        raise e
    data = response.content
    return yaml.safe_load(data)


def check_collection(api_root, demo_file, response_file, data_root):

    # Need schema to make sure we eliminate inherent attributes correctly
    # schema_path = "https://schema.databio.org/refget/SeqColArraySetInherent.yaml"
    # schema = read_url(schema_path)
    # inherent_attrs = schema["inherent"]

    inherent_attrs = ["names", "sequences"]
    print(f"Loading fasta file at '{data_root}/{demo_file}'")
    digest = refget.fasta_to_digest(f"{data_root}/{demo_file}", inherent_attrs=inherent_attrs)
    print(f"Checking digest: {digest}")
    res = requests.get(f"{api_root}/collection/{digest}")

    client = refget.SequenceCollectionClient(urls=[api_root])

    srv_response = client.get_collection(digest, level=1)
    print("Server response:", srv_response)
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


def check_comparison(api_root, response_file):
    with open(response_file) as fp:
        correct_answer = json.load(fp)

    url = (
        f"{api_root}/comparison/{correct_answer['digests']['a']}/{correct_answer['digests']['b']}"
    )
    res = requests.get(url)
    try:
        server_answer = json.loads(res.content)
        print("Server answer:", refget.canonical_str(server_answer))
        print("Correct answer:", refget.canonical_str(correct_answer))
        assert refget.canonical_str(server_answer) == refget.canonical_str(
            correct_answer
        ), f"Comparison endpoint failed: {url}. File: {response_file}"
    except json.decoder.JSONDecodeError:
        print(f"Url: {url}")
        assert False, f"Comparison endpoint failed: {url}"


def check_attribute(api_root, attribute_type, attribute, correct_value):
    url = f"{api_root}/attribute/collection/{attribute_type}/{attribute}"
    res = requests.get(url)
    try:
        server_answer = json.loads(res.content)
        assert (
            server_answer == correct_value
        ), f"Attribute endpoint failed: {url}. Answer: {correct_value}"
    except json.decoder.JSONDecodeError:
        print(f"Url: {url}")
        assert False, f"Attribute endpoint failed: {url}"


def check_list_collections_by_attribute(api_root, attribute_type, attribute, response_file):
    with open(response_file) as fp:
        correct_answer = json.load(fp)

    url = f"{api_root}/list/collection?{attribute_type}={attribute}"
    res = requests.get(url)
    try:
        server_answer = json.loads(res.content)
        print("Server answer:", server_answer)
        for digest in correct_answer["results"]:
            print("Checking digest:", digest)
            assert (
                digest in server_answer["results"]
            ), f"Attribute endpoint failed: {url}. Missing: {digest}"
    except json.decoder.JSONDecodeError:
        print(f"Url: {url}")
        assert False, f"Attribute endpoint failed: {url}"


def check_service_info(api_root):
    url = f"{api_root}/service-info"
    res = requests.get(url)
    try:
        server_answer = json.loads(res.content)
        # Check required GA4GH service-info fields exist
        assert "id" in server_answer, "service-info missing 'id' field"
        assert "type" in server_answer, "service-info missing 'type' field"
        assert "group" in server_answer["type"], "service-info type missing 'group'"
        assert "artifact" in server_answer["type"], "service-info type missing 'artifact'"
        assert "version" in server_answer["type"], "service-info type missing 'version'"
    except json.decoder.JSONDecodeError:
        print(f"Url: {url}")
        assert False, f"Service-info endpoint failed: {url}"


def check_list_collections(api_root):
    url = f"{api_root}/list/collection"
    res = requests.get(url)
    try:
        server_answer = json.loads(res.content)
        assert "results" in server_answer, "list/collection missing 'results' field"
        assert isinstance(server_answer["results"], list), "list/collection 'results' should be a list"
        assert "pagination" in server_answer, "list/collection missing 'pagination' field"
        assert "page" in server_answer["pagination"], "pagination missing 'page'"
        assert "page_size" in server_answer["pagination"], "pagination missing 'page_size'"
    except json.decoder.JSONDecodeError:
        print(f"Url: {url}")
        assert False, f"List collections endpoint failed: {url}"


def check_list_attributes(api_root, attribute_name):
    url = f"{api_root}/list/attributes/{attribute_name}"
    res = requests.get(url)
    try:
        server_answer = json.loads(res.content)
        assert "results" in server_answer, f"list/attributes/{attribute_name} missing 'results' field"
        assert isinstance(server_answer["results"], list), f"list/attributes/{attribute_name} 'results' should be a list"
    except json.decoder.JSONDecodeError:
        print(f"Url: {url}")
        assert False, f"List attributes endpoint failed: {url}"


def check_collection_structure(api_root, digest):
    # Level 1: inherent attributes should be digest strings
    level1 = requests.get(f"{api_root}/collection/{digest}?level=1").json()
    for attr in ["names", "lengths", "sequences"]:
        assert isinstance(level1[attr], str), f"Level 1 {attr} should be digest string"

    # Level 1 should include transient attribute
    assert "sorted_name_length_pairs" in level1, "Level 1 missing sorted_name_length_pairs"

    # Level 2: inherent attributes should be arrays
    level2 = requests.get(f"{api_root}/collection/{digest}?level=2").json()
    for attr in ["names", "lengths", "sequences"]:
        assert isinstance(level2[attr], list), f"Level 2 {attr} should be array"

    # Level 2 should NOT include transient attribute
    assert "sorted_name_length_pairs" not in level2, "Level 2 should not have sorted_name_length_pairs"


def check_comparison_post(api_root, response_file, test_data_root):
    with open(response_file) as fp:
        correct_answer = json.load(fp)

    # Get the local collection to POST
    digest_b = correct_answer["digests"]["b"]
    client = refget.SequenceCollectionClient(urls=[api_root])
    local_collection = client.get_collection(digest_b)

    # POST to compare with collection A on server
    digest_a = correct_answer["digests"]["a"]
    url = f"{api_root}/comparison/{digest_a}"
    res = requests.post(url, json=local_collection)
    try:
        server_answer = json.loads(res.content)
        # POST endpoint returns "POSTed seqcol" for digest b since it doesn't know the digest
        # So we compare everything except the digests.b field
        assert server_answer["digests"]["a"] == correct_answer["digests"]["a"], \
            f"Comparison POST: digest a mismatch"
        assert server_answer["attributes"] == correct_answer["attributes"], \
            f"Comparison POST: attributes mismatch"
        assert server_answer["array_elements"] == correct_answer["array_elements"], \
            f"Comparison POST: array_elements mismatch"
    except json.decoder.JSONDecodeError:
        print(f"Url: {url}")
        assert False, f"Comparison POST endpoint failed: {url}"


@pytest.mark.require_service
class TestAPI:
    print("Testing Compliance")

    @pytest.mark.parametrize("test_values", COLLECTION_TESTS)
    def test_collection_endpoint(self, api_root, test_values, test_data_root):
        print("Testing collection endpoint")
        check_collection(api_root, *test_values, test_data_root)

    @pytest.mark.parametrize("response_file", COMPARISON_TESTS)
    def test_comparison_endpoint(self, api_root, response_file):
        print("Testing comparison endpoint")
        check_comparison(api_root, response_file)

    @pytest.mark.parametrize("test_values", ATTRIBUTE_TESTS)
    def test_attribute_endpoint(self, api_root, test_values):
        check_attribute(api_root, *test_values)

    @pytest.mark.parametrize("test_values", ATTRIBUTE_LIST_TESTS)
    def test_attribute_list_endpoint(self, api_root, test_values):
        check_list_collections_by_attribute(api_root, *test_values)

    def test_service_info_endpoint(self, api_root):
        check_service_info(api_root)

    def test_list_collections_endpoint(self, api_root):
        check_list_collections(api_root)

    @pytest.mark.parametrize("attribute_name", ["lengths", "names", "sequences"])
    def test_list_attributes_endpoint(self, api_root, attribute_name):
        check_list_attributes(api_root, attribute_name)

    @pytest.mark.parametrize("response_file", COMPARISON_TESTS)
    def test_comparison_post_endpoint(self, api_root, response_file, test_data_root):
        check_comparison_post(api_root, response_file, test_data_root)

    @pytest.mark.parametrize("fa_file, fa_digest_bundle", DIGEST_TESTS)
    def test_collection_structure(self, api_root, fa_file, fa_digest_bundle):
        digest = fa_digest_bundle["top_level_digest"]
        check_collection_structure(api_root, digest)

    @pytest.mark.parametrize("fa_file, fa_digest_bundle", DIGEST_TESTS)
    def test_collections(self, api_root, fa_file, fa_digest_bundle):
        client = refget.SequenceCollectionClient(urls=[api_root])
        digest = fa_digest_bundle["top_level_digest"]
        srv_response = client.get_collection(digest, level=1)
        print("Server response:", srv_response)

    @pytest.mark.snlp
    @pytest.mark.parametrize("fa_file, fa_digest_bundle", DIGEST_TESTS)
    def test_sorted_name_length_pairs(self, api_root, fa_file, fa_digest_bundle):
        client = refget.SequenceCollectionClient(urls=[api_root])
        digest = fa_digest_bundle["top_level_digest"]
        srv_response = client.get_collection(digest, level=1)
        assert (
            srv_response["sorted_name_length_pairs"]
            == fa_digest_bundle["sorted_name_length_pairs_digest"]
        ), f"Collection endpoint failed: sorted_name_length_pairs mismatch for {demo_file}"
