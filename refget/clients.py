import logging
import requests

_LOGGER = logging.getLogger(__name__)

class SequencesClient(object):
    """
    A client for interacting with a refget sequences API.
    """
    def __init__(self, seq_urls=["https://www.ebi.ac.uk/ena/cram/sequence/"]):
        self.seq_urls = seq_urls

    def get_sequence(self, accession):
        """
        Retrieves a sequence for a given accession.

        Args:
            accession (str): The accession of the sequence.

        Returns:
            str: The sequence.
        """
        endpoint = f"{self.seq_url}/{accession}"
        return _try_urls(self.seq_urls, endpoint)


class SeqColClient(object):
    """
    A client for interacting with a refget sequence collections API.

    Args:
        urls (list, optional): A list of base URLs of the sequence collection API. Defaults to ["https://seqcolapi.databio.org"].

    Attributes:
        urls (list): The list of base URLs of the sequence collection API.

    Methods:
        get_collection(accession, level=2): Retrieves a sequence collection for a given accession and level.
    """

    def __init__(self, urls=["https://seqcolapi.databio.org"]):
        self.seqcol_api_urls = urls

    def get_collection(self, accession, level=2):
        """
        Retrieves a sequence collection for a given accession and detail level.

        Args:
            accession (str): The accession of the sequence collection.
            level (int, optional): The level of detail for the sequence collection. Defaults to 2.

        Returns:
            dict: The JSON response containing the sequence collection.
        """
        endpoint = f"/collection/{accession}?level={level}"
        return _try_urls(self.seqcol_api_urls, endpoint)

    def compare(self, accession1, accession2):
        """
        Compares two sequence collections.

        Args:
            accession1 (str): The accession of the first sequence collection.
            accession2 (str): The accession of the second sequence collection.

        Returns:
            dict: The JSON response containing the comparison of the two sequence collections.
        """
        endpoint = f"/comparison/{accession1}/{accession2}"
        return _try_urls(self.seqcol_api_urls, endpoint)

    def list_collections(self, page=None, page_size=None, attribute=None, attribute_digest=None):
        """
        Lists all available sequence collections with optional paging and attribute filtering support.

        Args:
            page (int, optional): The page number to retrieve. Defaults to None.
            page_size (int, optional): The number of items per page. Defaults to None.
            attribute (str, optional): The attribute to filter by. Defaults to None.
            attribute_digest (str, optional): The attribute digest to filter by. Defaults to None.

        Returns:
            dict: The JSON response containing the list of available sequence collections.
        """
        params = {}
        if page is not None:
            params['page'] = page
        if page_size is not None:
            params['page_size'] = page_size

        if attribute and attribute_digest:
            endpoint = f"/list/collections/{attribute}/{attribute_digest}"
        else:
            endpoint = "/list/collections"

        return _try_urls(self.seqcol_api_urls, endpoint, params=params)
    
    def list_attributes(self, attribute, page=None, page_size=None):
        """
        Lists all available values for a given attribute with optional paging support.

        Args:
            attribute (str): The attribute to list values for.
            page (int, optional): The page number to retrieve. Defaults to None.
            page_size (int, optional): The number of items per page. Defaults to None.
            
        Returns:
            dict: The JSON response containing the list of available values for the attribute.
        """
        params = {}
        if page is not None:
            params['page'] = page
        if page_size is not None:
            params['page_size'] = page_size

        endpoint = f"/list/attributes/{attribute}"
        return _try_urls(self.seqcol_api_urls, endpoint, params=params)


class RefGetClient(SequencesClient, SeqColClient):
    """
    A client for interacting with a refget API, for either 
    sequences or sequence collections, or both.
    """

    def __init__(self,
                 seq_api_urls=["https://www.ebi.ac.uk/ena/cram/sequence"],
                 seqcol_api_urls=["https://seqcolapi.databio.org"]):
        if seq_api_urls:
            SequencesClient.__init__(self, seq_api_urls)
        if seqcol_api_urls:
            SeqColClient.__init__(self, seqcol_api_urls)

    def __repr__(self):
        return f"<RefGetClient(seq_api_urls={self.seq_api_urls}, seqcol_api_urls={self.seqcol_api_urls})>"
    

# Utilities

def _wrap_response(response):
    """
    Wraps a response in a try/except block to catch any exceptions.

    Args:
        response (requests.Response): The response to wrap.

    Returns:
        dict: The JSON response.
    """
    try:
        response.raise_for_status()  # Raise an HTTPError for bad responses
        return response.json()
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"An error occurred: {e}")
    
def _try_urls(urls, endpoint, params=None):
    """
    Tries the list of URLs in succession until a successful response is received.

    Args:
        urls (list): A list of base URLs to try.
        endpoint (str): The endpoint to append to the base URL.
        params (dict, optional): The query parameters to include in the request.

    Returns:
        dict: The JSON response or None if all URLs fail.
    """
    errors = []
    for base_url in urls:
        url = f"{base_url}{endpoint}"
        try:
            response = requests.get(url, params=params)
            result = _wrap_response(response)
            _LOGGER.info(f"Successful response from {base_url}")
            return result
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.RequestException) as e:
            _LOGGER.debug(f"Error from {base_url}: {e}")
            errors.append(f"Error from {base_url}: {e}")
    error_message = "All URLs failed:\n" + "\n".join(errors)
    raise ConnectionError(error_message)