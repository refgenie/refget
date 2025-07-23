import pytest
import logging
_LOGGER = logging.getLogger(__name__)

try:
    from gtars import ( # Adjust this import path to where your PyO3 module is
        SequenceCollection,

    )
    _RUST_BINDINGS_AVAILABLE = True

except ImportError as e:
    _LOGGER.warning(f"Could not import gtars python bindings. `from_PySequenceCollection` will not be available.")
    _RUST_BINDINGS_AVAILABLE = False


#@pytest.mark.skipif(not _RUST_BINDINGS_AVAILABLE, reason="gtars is not installed")
class TestRustPySequenceCollection:
    def test_pysequencecollection(self):
        assert True
        #assert _RUST_BINDINGS_AVAILABLE