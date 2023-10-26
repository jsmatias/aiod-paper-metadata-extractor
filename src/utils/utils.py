import re


def extract_doi_from_str(string: str) -> list:
    """Extract all DOIs matches from a string using a regular expression"""
    doi_pattern = r"\b10\.\d{4,}/[-._;()/:a-zA-Z0-9]+\b"
    # Find all matches in the text
    doi_list = re.findall(doi_pattern, string)
    return doi_list
