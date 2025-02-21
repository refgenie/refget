import json
import logging
import requests

_LOGGER = logging.getLogger(__name__)




# Abstract class?
class RefgetClient(object):
    """
    A generic class, for any features used by any subclass of refget client.
    """

    def __repr__(self):
        service_info = self.service_info()
        return (
            f"<{self.__class__.__name__}>\n"
            f"  Service ID: {service_info['id']}\n"
            f"  Service Name: {service_info['name']}\n"
            f"  API URLs:    {', '.join(self.urls)}\n"
        )
        
    def service_info(self):
        """
        Retrieves information about the service.

        Returns:
            dict: The service information.
        """
        endpoint = "/service-info"
        # Sequences uses /service-info under `/sequences`, which should be changed, but for now...
        if self.__class__.__name__ == "SequencesClient":
            endpoint = "/sequence/service-info"
        return _try_urls(self.urls, endpoint)

class SequencesClient(RefgetClient):
    """
    A client for interacting with a refget sequences API.
    """

    def __init__(self, urls=["https://www.ebi.ac.uk/ena/cram"]):
        """
        Initializes the sequences client.

        Args:
            urls (list, optional): A list of base URLs of the sequences API. Defaults to ["https://www.ebi.ac.uk/ena/cram/sequence/"].

        Attributes:
            urls (list): The list of base URLs of the sequences API.
        """
        # Remove trailing slaches from input URLs
        self.urls = [url.rstrip("/") for url in urls]

    def get_sequence(self, accession, start=None, end=None):
        """
        Retrieves a sequence for a given accession.

        Args:
            accession (str): The accession of the sequence.

        Returns:
            str: The sequence.
        """
        query_params = {}
        if start is not None:
            query_params["start"] = start
        if end is not None:
            query_params["end"] = end

        endpoint = f"/sequence/{accession}"
        return _try_urls(self.urls, endpoint, params=query_params)
    
    def get_metadata(self, accession):
        """
        Retrieves metadata for a given accession.

        Args:
            accession (str): The accession of the sequence.

        Returns:
            dict: The metadata.
        """
        endpoint = f"/sequence/{accession}/metadata"
        return _try_urls(self.urls, endpoint)


class SequenceCollectionsClient(RefgetClient):
    """
    A client for interacting with a refget sequence collections API.
    """

    def __init__(self, urls=["https://seqcolapi.databio.org"]):
        """
        Initializes the sequence collection client.

        Args:
            urls (list, optional): A list of base URLs of the sequence collection API. Defaults to ["https://seqcolapi.databio.org"].

        Attributes:
            urls (list): The list of base URLs of the sequence collection API.
        """
        # Remove trailing slaches from input URLs
        self.urls = [url.rstrip("/") for url in urls]

    def get_collection(self, accession, level=2):
        """
        Retrieves a sequence collection for a given accession and detail level.

        Args:
            accession (str): The accession of the sequence collection.
            level (int, optional): The level of detail for the sequence collection. Defaults to 2.

        Returns:
            (dict): The JSON response containing the sequence collection.
        """
        endpoint = f"/collection/{accession}?level={level}"
        return _try_urls(self.urls, endpoint)

    def compare(self, accession1, accession2):
        """
        Compares two sequence collections.

        Args:
            accession1 (str): The accession of the first sequence collection.
            accession2 (str): The accession of the second sequence collection.

        Returns:
            (dict): The JSON response containing the comparison of the two sequence collections.
        """
        endpoint = f"/comparison/{accession1}/{accession2}"
        return _try_urls(self.urls, endpoint)

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
            params["page"] = page
        if page_size is not None:
            params["page_size"] = page_size

        if attribute and attribute_digest:
            endpoint = f"/list/collections/{attribute}/{attribute_digest}"
        else:
            endpoint = "/list/collections"

        return _try_urls(self.urls, endpoint, params=params)

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
            params["page"] = page
        if page_size is not None:
            params["page_size"] = page_size

        endpoint = f"/list/attributes/{attribute}"
        return _try_urls(self.urls, endpoint, params=params)
    
    def service_info(self):
        """
        Retrieves information about the service.

        Returns:
            dict: The service information.
        """
        endpoint = "/service-info"
        return _try_urls(self.urls, endpoint)


class PangenomesClient(RefgetClient):
    pass



# Utilities

import re
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
        content_type = response.headers.get("content-type")
        if re.search(r"application/(.*\+)?json", content_type):
            return response.json()
        else:
            return response.text
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
        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            requests.exceptions.RequestException,
        ) as e:
            _LOGGER.debug(f"Error from {base_url}: {e}")
            errors.append(f"Error from {base_url}: {e}")
    error_message = "All URLs failed:\n" + "\n".join(errors)
    raise ConnectionError(error_message)
