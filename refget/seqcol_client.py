import requests


class SeqColClient(object):
    """
    A client for interacting with a sequence collection API.

    Args:
        url (str, optional): The base URL of the sequence collection API. Defaults to "http://seqcolapi.databio.org".

    Attributes:
        url (str): The base URL of the sequence collection API.

    Methods:
        get_collection(accession, level=2): Retrieves a sequence collection for a given accession and level.
    """

    def __init__(self, url="http://seqcolapi.databio.org"):
        self.url = url

    def get_collection(self, accession, level=2):
        """
        Retrieves a sequence collection for a given accession and detail level.

        Args:
            accession (str): The accession of the sequence collection.
            level (int, optional): The level of detail for the sequence collection. Defaults to 2.

        Returns:
            dict: The JSON response containing the sequence collection.
        """
        url = f"{self.url}/collection/{accession}?level={level}"
        response = requests.get(url)
        return response.json()

    def compare(self, accession1, accession2):
        """
        Compares two sequence collections.

        Args:
            accession1 (str): The accession of the first sequence collection.
            accession2 (str): The accession of the second sequence collection.

        Returns:
            dict: The JSON response containing the comparison of the two sequence collections.
        """
        url = f"{self.url}/comparison/{accession1}/{accession2}"
        response = requests.get(url)
        return response.json()
