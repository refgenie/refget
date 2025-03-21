import pytest
import requests

from tests.conftest import DEMO_FILES

REQ_SERVICE_MARK = "require_service"
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
    f"{API_TEST_DIR}/comparison/compare_base.fa_subset.fa.json",  # subset
    f"{API_TEST_DIR}/comparison/compare_base.fa_different_names.fa.json",  # same sequences, different names
    f"{API_TEST_DIR}/comparison/compare_base.fa_different_order.fa.json",  # same sequences, name order switch, but equivalent coordinate system
    f"{API_TEST_DIR}/comparison/compare_base.fa_pair_swap.fa.json",  # swapped name-length-pairs
    f"{API_TEST_DIR}/comparison/compare_base.fa_swap_wo_coords.fa.json",  # swapped name-length-pairs, but no coord system change
]


ATTRIBUTE_TESTS = [
    ("lengths", "7-_HdxYiRf-AJLBKOTaJUdxXrUkIXs6T", [8, 4]),
    ("names", "Fw1r9eRxfOZD98KKrhlYQNEdSRHoVxAG", ["chrX", "chr1", "chr2"]),
]

ATTRIBUTE_LIST_TESTS = [
    (
        "lengths",
        "cGRMZIb3AVgkcAfNv39RN7hnT5Chk7RX",
        f"{API_TEST_DIR}/attribute/cGRM.json",
    )
]

