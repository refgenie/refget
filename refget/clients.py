import logging
import re
import requests

from typing import Optional

_LOGGER = logging.getLogger(__name__)


# Abstract class
class RefgetClient(object):
    """
    A generic abstract class, for any features used by any subclass of refget client.
    """

    urls: list[str]

    def __repr__(self) -> str:
        service_info = self.service_info()
        return (
            f"<{self.__class__.__name__}>\n"
            f"  Service ID: {service_info['id']}\n"
            f"  Service Name: {service_info['name']}\n"
            f"  API URLs:    {', '.join(self.urls)}\n"
        )

    def service_info(self) -> dict:
        """
        Retrieves information about the service.

        Returns:
            dict: The service information.
        """
        endpoint = "/service-info"
        # Sequences uses /service-info under `/sequences`, which should be changed, but for now...
        if self.__class__.__name__ == "SequenceClient":
            endpoint = "/sequence/service-info"
        return _try_urls(self.urls, endpoint)


class SequenceClient(RefgetClient):
    """
    A client for interacting with a refget sequences API.
    """

    def __init__(
        self,
        urls: list[str] = ["https://www.ebi.ac.uk/ena/cram"],
        raise_errors: Optional[bool] = None,
    ) -> None:
        """
        Initializes the sequences client.

        Args:
            urls (list, optional): A list of base URLs of the sequences API. Defaults to ["https://www.ebi.ac.uk/ena/cram/sequence/"].
            raise_errors (bool, optional): Whether to raise errors or log them. Defaults to None, which will guess.
        Attributes:
            urls (list): The list of base URLs of the sequences API.
        """
        # Remove trailing slaches from input URLs
        self.urls = [url.rstrip("/") for url in urls]
        # If raise_errors is None, set it to True if the client is not being used as a library
        if raise_errors is None:
            raise_errors = __name__ == "__main__"
        self.raise_errors = raise_errors

    def get_sequence(
        self, digest: str, start: Optional[int] = None, end: Optional[int] = None
    ) -> Optional[str]:
        """
        Retrieves a sequence for a given digest.

        Args:
            digest (str): The digest of the sequence.

        Returns:
            (str): The sequence.
        """
        query_params = {}
        if start is not None:
            query_params["start"] = start
        if end is not None:
            query_params["end"] = end

        endpoint = f"/sequence/{digest}"
        return _try_urls(self.urls, endpoint, params=query_params, raise_errors=self.raise_errors)

    def get_metadata(self, digest: str) -> Optional[dict]:
        """
        Retrieves metadata for a given sequence digest.

        Args:
            digest (str): The digest of the sequence.

        Returns:
            (dict): The metadata.
        """
        endpoint = f"/sequence/{digest}/metadata"
        return _try_urls(self.urls, endpoint, raise_errors=self.raise_errors)


class SequenceCollectionClient(RefgetClient):
    """
    A client for interacting with a refget sequence collections API.
    """

    def __init__(
        self,
        urls: list[str] = ["https://seqcolapi.databio.org"],
        raise_errors: Optional[bool] = None,
    ) -> None:
        """
        Initializes the sequence collection client.

        Args:
            urls (list, optional): A list of base URLs of the sequence collection API. Defaults to ["https://seqcolapi.databio.org"].

        Attributes:
            urls (list): The list of base URLs of the sequence collection API.
        """
        # Remove trailing slaches from input URLs
        self.urls = [url.rstrip("/") for url in urls]
        # If raise_errors is None, set it to True if the client is not being used as a library
        if raise_errors is None:
            raise_errors = __name__ == "__main__"
        self.raise_errors = raise_errors
        self._fasta_client = None

    def _get_fasta_helper(self) -> "FastaDrsClient":
        """Get or create the internal FASTA DRS helper."""
        if self._fasta_client is None:
            fasta_urls = [f"{url}/fasta" for url in self.urls]
            self._fasta_client = FastaDrsClient(urls=fasta_urls, raise_errors=self.raise_errors)
            self._fasta_client._seqcol_client = self
        return self._fasta_client

    def get_fasta(self, digest: str) -> Optional[dict]:
        """
        Get DRS object metadata for a FASTA file.

        Args:
            digest (str): The sequence collection digest (which is also the DRS object ID)

        Returns:
            (dict): DRS object with id, self_uri, size, checksums, access_methods, etc.
        """
        return self._get_fasta_helper().get_object(digest)

    def get_fasta_index(self, digest: str) -> Optional[dict]:
        """
        Get FAI index data for a FASTA file.

        Args:
            digest (str): The sequence collection digest

        Returns:
            (dict): Dict with line_bases, extra_line_bytes, offsets
        """
        return self._get_fasta_helper().get_index(digest)

    def download_fasta(self, digest: str, dest_path: str = None, access_id: str = None) -> str:
        """
        Download the FASTA file to a local path.

        Args:
            digest (str): The sequence collection digest
            dest_path (str, optional): Destination file path. If None, uses object name.
            access_id (str, optional): Specific access method to use. If None, tries all.

        Returns:
            (str): Path to downloaded file

        Raises:
            ValueError: If no access methods available or specified access_id not found
        """
        return self._get_fasta_helper().download(digest, dest_path, access_id)

    def download_fasta_to_store(
        self, digest: str, store: "GlobalRefgetStore", access_id: str = None, temp_dir: str = None
    ) -> str:
        """
        Download the FASTA file and import it into a GlobalRefgetStore.

        This method downloads the FASTA file from the DRS endpoint and immediately
        imports it into the provided RefgetStore, enabling local sequence retrieval
        by digest without re-downloading.

        Args:
            digest (str): The sequence collection digest
            store (GlobalRefgetStore): The GlobalRefgetStore instance to import into
            access_id (str, optional): Specific access method to use. If None, tries all.
            temp_dir (str, optional): Directory for temporary download. If None, uses system temp.

        Returns:
            (str): The collection digest of the imported sequences

        Raises:
            ValueError: If no access methods available or specified access_id not found
            ImportError: If gtars/GlobalRefgetStore is not available

        Example:
            >>> from refget.refget_store import GlobalRefgetStore, StorageMode
            >>> from refget.clients import SequenceCollectionClient
            >>> store = GlobalRefgetStore(StorageMode.Encoded)
            >>> client = SequenceCollectionClient()
            >>> collection_digest = client.download_fasta_to_store("abc123", store)
            >>> # Now you can retrieve sequences by digest from the local store
            >>> seq = store.get_substring(sequence_digest, 0, 100)
        """
        return self._get_fasta_helper().download_to_store(digest, store, access_id, temp_dir)

    def build_fai(self, digest: str) -> str:
        """
        Build a complete .fai index file content for a FASTA.

        FAI format per line: NAME\\tLENGTH\\tOFFSET\\tLINEBASES\\tLINEWIDTH

        Args:
            digest (str): The sequence collection digest

        Returns:
            (str): String content of the .fai file
        """
        return self._get_fasta_helper().build_fai(digest, seqcol_client=self)

    def write_fai(self, digest: str, dest_path: str) -> str:
        """
        Write a .fai index file for a FASTA.

        Args:
            digest (str): The sequence collection digest
            dest_path (str): Path to write the .fai file

        Returns:
            (str): Path to the written file
        """
        return self._get_fasta_helper().write_fai(digest, dest_path, seqcol_client=self)

    def build_chrom_sizes(self, digest: str) -> str:
        """
        Build a chrom.sizes file content for a sequence collection.

        Format per line: NAME\\tLENGTH

        Args:
            digest (str): The sequence collection digest

        Returns:
            (str): String content of the chrom.sizes file
        """
        collection = self.get_collection(digest, level=2)
        if not collection:
            raise ValueError(f"No collection found for {digest}")

        names = collection["names"]
        lengths = collection["lengths"]

        lines = []
        for name, length in zip(names, lengths):
            lines.append(f"{name}\t{length}")

        return "\n".join(lines) + "\n"

    def write_chrom_sizes(self, digest: str, dest_path: str) -> str:
        """
        Write a chrom.sizes file for a sequence collection.

        Args:
            digest (str): The sequence collection digest
            dest_path (str): Path to write the chrom.sizes file

        Returns:
            (str): Path to the written file
        """
        content = self.build_chrom_sizes(digest)
        with open(dest_path, "w") as f:
            f.write(content)
        return dest_path

    def get_collection(self, digest: str, level: int = 2) -> Optional[dict]:
        """
        Retrieves a sequence collection for a given digest and detail level.

        Args:
            digest (str): The digest of the sequence collection.
            level (int, optional): The level of detail for the sequence collection. Defaults to 2.

        Returns:
            (dict): The JSON response containing the sequence collection.
        """
        endpoint = f"/collection/{digest}?level={level}"
        return _try_urls(self.urls, endpoint)

    def get_attribute(self, attribute: str, digest: str) -> Optional[dict]:
        """
        Retrieves a specific attribute value by its digest.

        Args:
            attribute (str): The attribute name (e.g., "names", "lengths", "sequences").
            digest (str): The level 1 digest of the attribute.

        Returns:
            (dict): The JSON response containing the attribute value.
        """
        endpoint = f"/attribute/collection/{attribute}/{digest}"
        return _try_urls(self.urls, endpoint)

    def compare(self, digest1: str, digest2: str) -> Optional[dict]:
        """
        Compares two sequence collections hosted on the server.

        Args:
            digest1 (str): The digest of the first sequence collection.
            digest2 (str): The digest of the second sequence collection.

        Returns:
            (dict): The JSON response containing the comparison of the two sequence collections.
        """
        endpoint = f"/comparison/{digest1}/{digest2}"
        return _try_urls(self.urls, endpoint)

    def compare_local(self, digest: str, local_collection: dict) -> Optional[dict]:
        """
        Compares a server-hosted sequence collection with a local collection.

        Args:
            digest (str): The digest of the server-hosted sequence collection.
            local_collection (dict): A level 2 sequence collection representation.

        Returns:
            (dict): The JSON response containing the comparison.
        """
        endpoint = f"/comparison/{digest}"
        return _try_urls(self.urls, endpoint, method="POST", json=local_collection)

    def list_collections(
        self,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
        **filters,
    ) -> Optional[dict]:
        """
        Lists all available sequence collections with optional paging and attribute filtering support.

        Args:
            page (int, optional): The page number to retrieve. Defaults to None.
            page_size (int, optional): The number of items per page. Defaults to None.
            **filters: Optional attribute filters (e.g., names="abc123", lengths="def456").
                      Values should be level 1 digests of the attributes.

        Returns:
            (dict): The JSON response containing the list of available sequence collections.
        """
        params = {}
        if page is not None:
            params["page"] = page
        if page_size is not None:
            params["page_size"] = page_size
        params.update(filters)

        endpoint = "/list/collection"
        return _try_urls(self.urls, endpoint, params=params)

    def list_attributes(
        self, attribute: str, page: Optional[int] = None, page_size: Optional[int] = None
    ) -> Optional[dict]:
        """
        Lists all available values for a given attribute with optional paging support.

        Args:
            attribute (str): The attribute to list values for.
            page (int, optional): The page number to retrieve. Defaults to None.
            page_size (int, optional): The number of items per page. Defaults to None.

        Returns:
            (dict): The JSON response containing the list of available values for the attribute.
        """
        params = {}
        if page is not None:
            params["page"] = page
        if page_size is not None:
            params["page_size"] = page_size

        endpoint = f"/list/attributes/{attribute}"
        return _try_urls(self.urls, endpoint, params=params)

    def service_info(self) -> Optional[dict]:
        """
        Retrieves information about the service.

        Returns:
            (dict): The service information.
        """
        endpoint = "/service-info"
        return _try_urls(self.urls, endpoint)


class PangenomeClient(RefgetClient):
    pass


class FastaDrsClient(RefgetClient):
    """
    A client for interacting with FASTA files via GA4GH DRS endpoints.
    """

    def __init__(
        self,
        urls: list[str] = ["https://seqcolapi.databio.org/fasta"],
        raise_errors: Optional[bool] = None,
    ) -> None:
        """
        Initializes the FASTA DRS client.

        Args:
            urls (list, optional): A list of base URLs of the FASTA DRS API.
                Defaults to ["https://seqcolapi.databio.org/fasta"].
            raise_errors (bool, optional): Whether to raise errors or log them.
                Defaults to None, which will guess.

        Attributes:
            urls (list): The list of base URLs of the FASTA DRS API.
        """
        self.urls = [url.rstrip("/") for url in urls]
        if raise_errors is None:
            raise_errors = __name__ == "__main__"
        self.raise_errors = raise_errors

    def get_object(self, digest: str) -> Optional[dict]:
        """
        Get DRS object metadata for a FASTA file.

        Args:
            digest (str): The sequence collection digest (which is also the DRS object ID)

        Returns:
            (dict): DRS object with id, self_uri, size, checksums, access_methods, etc.
        """
        endpoint = f"/objects/{digest}"
        return _try_urls(self.urls, endpoint, raise_errors=self.raise_errors)

    def get_index(self, digest: str) -> Optional[dict]:
        """
        Get FAI index data for a FASTA file.

        Args:
            digest (str): The sequence collection digest

        Returns:
            (dict): Dict with line_bases, extra_line_bytes, offsets
        """
        endpoint = f"/objects/{digest}/index"
        return _try_urls(self.urls, endpoint, raise_errors=self.raise_errors)

    def get_access_url(self, digest: str, access_id: str) -> Optional[dict]:
        """
        Get access URL for a specific access method.

        Args:
            digest (str): The sequence collection digest
            access_id (str): The access ID from the access method

        Returns:
            (dict): Access URL object
        """
        endpoint = f"/objects/{digest}/access/{access_id}"
        return _try_urls(self.urls, endpoint, raise_errors=self.raise_errors)

    def service_info(self) -> Optional[dict]:
        """
        Get DRS service info.

        Returns:
            (dict): The service information.
        """
        endpoint = "/service-info"
        return _try_urls(self.urls, endpoint)

    def download(self, digest: str, dest_path: str = None, access_id: str = None) -> str:
        """
        Download the FASTA file to a local path.

        Args:
            digest (str): The sequence collection digest
            dest_path (str, optional): Destination file path. If None, uses object name.
            access_id (str, optional): Specific access method to use. If None, tries all.

        Returns:
            (str): Path to downloaded file

        Raises:
            ValueError: If no access methods available or specified access_id not found
        """
        drs_obj = self.get_object(digest)
        if not drs_obj or not drs_obj.get("access_methods"):
            raise ValueError(f"No access methods for {digest}")

        # Filter to specific access method if requested
        methods = drs_obj["access_methods"]
        if access_id:
            methods = [m for m in methods if m.get("access_id") == access_id]
            if not methods:
                raise ValueError(f"Access method '{access_id}' not found for {digest}")

        # Find first accessible URL
        for method in methods:
            url = None
            if method.get("access_url"):
                access_url = method["access_url"]
                url = access_url.get("url") if isinstance(access_url, dict) else access_url
            elif method.get("access_id"):
                access_info = self.get_access_url(digest, method["access_id"])
                url = access_info.get("url") if access_info else None

            if url:
                if dest_path is None:
                    dest_path = drs_obj.get("name", f"{digest}.fa")

                response = requests.get(url, stream=True)
                response.raise_for_status()
                with open(dest_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                return dest_path

        raise ValueError(f"No accessible URLs for {digest}")

    def download_to_store(
        self, digest: str, store: "GlobalRefgetStore", access_id: str = None, temp_dir: str = None
    ) -> str:
        """
        Download the FASTA file and import it into a GlobalRefgetStore.

        This method downloads the FASTA file from the DRS endpoint and immediately
        imports it into the provided RefgetStore, enabling local sequence retrieval
        by digest without re-downloading.

        Args:
            digest (str): The sequence collection digest
            store (GlobalRefgetStore): The GlobalRefgetStore instance to import into
            access_id (str, optional): Specific access method to use. If None, tries all.
            temp_dir (str, optional): Directory for temporary download. If None, uses system temp.

        Returns:
            (str): The collection digest of the imported sequences

        Raises:
            ValueError: If no access methods available or specified access_id not found
            ImportError: If gtars/GlobalRefgetStore is not available

        Example:
            >>> from refget.refget_store import GlobalRefgetStore, StorageMode
            >>> store = GlobalRefgetStore(StorageMode.Encoded)
            >>> client = FastaDrsClient()
            >>> collection_digest = client.download_to_store("abc123", store)
        """
        import tempfile
        import os

        # Verify store is available
        try:
            from .refget_store import GlobalRefgetStore as RefgetStoreClass
        except ImportError:
            raise ImportError("gtars is required for download_to_store functionality")

        # Download to temporary location
        temp_file = None
        try:
            if temp_dir:
                os.makedirs(temp_dir, exist_ok=True)
                temp_file = os.path.join(temp_dir, f"{digest}.fa")
            else:
                # Create a named temporary file
                fd, temp_file = tempfile.mkstemp(suffix=".fa", prefix=f"{digest}_")
                os.close(fd)  # Close the file descriptor

            # Download the FASTA
            downloaded_path = self.download(digest, dest_path=temp_file, access_id=access_id)
            _LOGGER.info(f"Downloaded FASTA to {downloaded_path}")

            # Import into store
            store.import_fasta(downloaded_path)
            _LOGGER.info(f"Imported FASTA into RefgetStore: {digest}")

            return digest

        finally:
            # Clean up temporary file if we created it in system temp
            if temp_file and not temp_dir and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception as e:
                    _LOGGER.warning(f"Could not remove temporary file {temp_file}: {e}")

    def build_fai(self, digest: str, seqcol_client: "SequenceCollectionClient" = None) -> str:
        """
        Build a complete .fai index file content for a FASTA.

        FAI format per line: NAME\tLENGTH\tOFFSET\tLINEBASES\tLINEWIDTH

        Args:
            digest (str): The sequence collection digest
            seqcol_client (SequenceCollectionClient, optional): SequenceCollectionClient
                to use. If None, uses parent client or creates one.

        Returns:
            (str): String content of the .fai file
        """
        # Get FAI index data
        index = self.get_index(digest)
        if not index:
            raise ValueError(f"No FAI index for {digest}")

        # Get sequence collection for names/lengths
        if seqcol_client is None:
            # Use parent client if we were created via SequenceCollectionClient.fasta
            if hasattr(self, "_seqcol_client") and self._seqcol_client is not None:
                seqcol_client = self._seqcol_client
            else:
                # Derive seqcol URL from fasta URL (strip /fasta suffix)
                base_urls = [url.rsplit("/fasta", 1)[0] for url in self.urls]
                seqcol_client = SequenceCollectionClient(urls=base_urls)

        collection = seqcol_client.get_collection(digest, level=2)
        if not collection:
            raise ValueError(f"No collection found for {digest}")

        names = collection["names"]
        lengths = collection["lengths"]
        offsets = index["offsets"]
        line_bases = index["line_bases"]
        line_width = line_bases + index["extra_line_bytes"]

        # Build FAI lines
        lines = []
        for name, length, offset in zip(names, lengths, offsets):
            # FAI format: NAME LENGTH OFFSET LINEBASES LINEWIDTH
            lines.append(f"{name}\t{length}\t{offset}\t{line_bases}\t{line_width}")

        return "\n".join(lines) + "\n"

    def write_fai(
        self, digest: str, dest_path: str, seqcol_client: "SequenceCollectionClient" = None
    ) -> str:
        """
        Write a .fai index file for a FASTA.

        Args:
            digest (str): The sequence collection digest
            dest_path (str): Path to write the .fai file
            seqcol_client (SequenceCollectionClient, optional): SequenceCollectionClient to use

        Returns:
            (str): Path to the written file
        """
        fai_content = self.build_fai(digest, seqcol_client)
        with open(dest_path, "w") as f:
            f.write(fai_content)
        return dest_path


# Utilities


def _wrap_response(response: requests.Response) -> dict | str:
    """
    Handles the response from a request, unwrapping the content as either
    text or json, depending on the content type.

    Args:
        response (requests.Response): The response to wrap.

    Returns:
        (dict): The JSON response.
    """
    try:
        response.raise_for_status()  # Raise an HTTPError for bad responses
        content_type = response.headers.get("content-type")
        if re.search(r"application/(.*\+)?json", content_type):
            return response.json()
        else:
            return response.text
    except requests.exceptions.RequestException as e:
        raise e


def _try_urls(
    urls: list[str],
    endpoint: str,
    method: str = "GET",
    params: Optional[dict] = None,
    json: Optional[dict] = None,
    raise_errors: bool = True,
) -> Optional[dict | str]:
    """
    Tries the list of URLs in succession until a successful response is received.

    Args:
        urls (list): A list of base URLs to try.
        endpoint (str): The endpoint to append to the base URL.
        method (str): HTTP method ("GET" or "POST"). Defaults to "GET".
        params (dict, optional): Query parameters for GET requests.
        json (dict, optional): JSON body for POST requests.
        raise_errors (bool): Whether to raise errors or log them.

    Returns:
        (dict): The JSON response or None if all URLs fail.
    """
    errors = []
    for base_url in urls:
        url = f"{base_url}{endpoint}"
        try:
            if method.upper() == "POST":
                response = requests.post(url, json=json)
            else:
                response = requests.get(url, params=params)
            result = _wrap_response(response)
            _LOGGER.debug(f"Response received from {base_url}")
            return result
        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            requests.exceptions.RequestException,
        ) as e:
            _LOGGER.debug(f"Error from {base_url}: {e}")
            errors.append(f"Error from {base_url}: {e}")
    error_message = "All URLs failed:\n" + "\n".join(errors)
    if raise_errors:
        raise ConnectionError(error_message)
    else:
        _LOGGER.error(error_message)
        return None
