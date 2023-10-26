import re
import requests
from config import Config

empty_metadata = {
    "title": "",
    "author": "",
    "issn": "",
    "url": "",
    "doi": "",
    "number": "",
    "journal": "",
    "publisher": "",
    "year": "",
    "month": "",
    "pages": "",
    "keywords": "",
}


class Metadata:
    def __init__(self, silent=True) -> None:
        config = Config()
        self.api_url_base = config.get_metadata_api_url()
        self.headers = config.get_metadata_api_headers()
        self.silent = silent

    def get_metadata_from_doi(self, doi: str) -> dict[str, str]:
        """`GET` method to fetch the metadata from the DOI of the paper"""
        url = self.api_url_base + doi
        try:
            res = requests.get(url, headers=self.headers, timeout=3000)
        except ConnectionError as err:
            print(err)
            # TODO handle this error
            return empty_metadata
        metadata = self._to_dict(res.text)

        return metadata

    def _to_dict(self, metadata: str):
        """Convert metadata do dictionary"""

        metadata_dict = {}

        # Use regular expressions to extract field values
        def search_field(field: str):
            field_pattern = f"{field}" + r"={(.*?)}"
            try:
                result = re.search(field_pattern, metadata).group(1)
            except Exception as err:
                if not self.silent:
                    print(
                        f"{err} of type {type(err)} - Error found trying to search {field} in the metadata: {metadata[:50]}..."
                    )
                result = ""
            return result

        metadata_dict["title"] = search_field("title")
        metadata_dict["volume"] = search_field("volume")
        metadata_dict["issn"] = search_field("ISSN")
        metadata_dict["url"] = search_field("url")
        metadata_dict["doi"] = search_field("DOI")
        metadata_dict["number"] = search_field("number")
        metadata_dict["journal"] = search_field("journal")
        metadata_dict["publisher"] = search_field("publisher")
        metadata_dict["author"] = [
            name.strip() for name in search_field("author").split("and")
        ]
        metadata_dict["year"] = search_field("year")
        metadata_dict["month"] = search_field("month")
        metadata_dict["pages"] = search_field("pages")
        metadata_dict["keywords"] = search_field("keywords")
        return metadata_dict
