import re
import fitz
import numpy as np
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
import warnings

# from config import Config
from .metadata import Metadata
from acm.classification_extractor import get_classification


class Paper:
    """A simple abstraction layer for working on the paper object"""

    def __init__(self, files_path: str, file_name: str, silent=True) -> None:
        """
        Args:
            files_path: "/path/to/files/"
            file_name: "my-paper.pdf"
        """
        self.silent = silent
        self.file_name = file_name
        # config = Config()
        # self.full_path = config.get_papers_path() + self.file_name
        self.full_path = files_path + self.file_name

        self._pdf_info = []
        self._raw_text = ""
        self.text = ""

        self.title = ""
        self.author = []
        self.issn = ""
        self.url = ""
        self.doi = ""
        self.number = ""
        self.journal = ""
        self.publisher = ""
        self.year = ""
        self.month = ""
        self.pages = ""
        self.keywords = []
        self.topics = []

        self.load()

    def load(self):
        """Set up the paper parameters"""
        self._pdf_info = self.extract_pdf_info()
        self._raw_text = self.extract_pdf_text()
        self.text = self.clean_text()

        self.doi = self.extract_doi()
        if self.doi:
            metadata = Metadata().get_metadata_from_doi(self.doi)

            if not self.silent:
                print("Correct DOI? ", self.cross_validate_doi(metadata))

            self.title = metadata["title"]
            self.author = metadata["author"]
            self.issn = metadata["issn"]
            self.url = metadata["url"]
            self.doi = metadata["doi"]
            self.number = metadata["number"]
            self.journal = metadata["journal"]
            self.publisher = metadata["publisher"]
            self.year = metadata["year"]
            self.month = metadata["month"]
            self.pages = metadata["pages"]
            self.keywords = metadata["keywords"]

            self.topics = self.extract_topics()

        self.keywords = self.extract_keywords()

    def extract_topics(self) -> list:
        """Gets the topics from ontology classification.
        At the moment it's only implemented for ACM publisher.
        """
        topics = self.topics
        if self.doi:
            publisher = self.publisher.lower().strip()
            if publisher == "acm":
                topics = get_classification(self.doi)
                if topics and (topics[0].strip().lower() != self.title.lower().strip()):
                    if not self.silent:
                        msg = f"The title in the topics extracted from '{publisher}' didn't match with '{self.title}'"
                        warnings.warn(msg)
            else:
                if not self.silent:
                    msg = f"Logic not implemented to extract topics from publisher: '{self.publisher}'"
                    warnings.warn(msg)
        return topics

    def extract_keywords(self) -> list:
        """Calls the extract_raw_keywords method and format the keywords"""

        keywords_list = [
            keyword.strip().lower() for keyword in self.extract_raw_keywords()
        ]
        return keywords_list

    def extract_raw_keywords(self) -> list:
        """Searches for keywords in the metadata of pdf file first.
        If nothing is found it searches in the text.
        """
        if self._pdf_info:
            if "Keywords" in self._pdf_info[0].keys():
                keywords_str = self._pdf_info[0]["Keywords"]
                if isinstance(keywords_str, bytes) and keywords_str:
                    try:
                        keywords_str = str(keywords_str, encoding="utf-8")
                        keywords_list = re.split(r"[^\s\w]", keywords_str)
                    except Exception as err:
                        keywords_list = []
                        if not self.silent:
                            print(
                                f"Error {err} of type {type(err)} - Variable with type: {type(keywords_str)}; and value: {keywords_str}",
                            )

                elif isinstance(keywords_str, str) and keywords_str:
                    keywords_list = keywords_str.split(",")
                else:
                    keywords_list = []
                if keywords_list:
                    return keywords_list

        # join words that are separated at the end of the line: e.g. dis-\parate
        text = self._raw_text.replace("-\n", "")
        text = re.sub(r" {2,3}", " ", text)
        text = re.sub(r"\n{2,}", "\n", text)
        text = re.sub(r"(?<=[^ \w])\s|\s(?=[^ \w])", "", text)
        text = text.lower().strip()
        keywords_list = self.extract_keywords_from_text(text)
        return keywords_list

    def extract_keywords_from_text(self, text: str) -> list:
        r"""Tries to extract keywords from the text.
        It assumes that the pattern is a list of words after the flag 'keywords' or 'key words'
        separated by any non-word character, excluding "\s" and "-".
        Full pattern:
          "(?:Keywords|Key words)[:\s]((?:(?:\w+(?:[-\s]\w+){,3},)){1,6}(?:\w+(?:[-\s]\w+){0,3})(?:[^\s,\w]|\n\w+[^ \w]))"
        Ex.: keywords: test-word1, test-word2 word1, word2, last composed.
        """

        min_words = 1
        max_words = 4

        min_keywords = 1
        max_keywords = 7

        start_pattern = r"(?:keywords|key words)[:\s]"
        keyword_pattern = rf"\w+(?:[-\s]\w+){{{min_words-1},{max_words-1}}}"
        separator_pattern = r"[^\s\w-]"  # e.g. ",", ";", "|", etc.
        separator = re.findall(
            rf"{start_pattern}(?:{keyword_pattern})({separator_pattern})", text
        )
        if separator:
            # separator must have just one element
            separator = separator[0]
        else:
            keywords_list = []
            return keywords_list

        keyword_sep_pattern = f"{keyword_pattern}{separator}"
        end_pattern = rf"(?=[^\s\w{separator}]|\n\w+[^ \w])"  # full stop or a word wrapped around \n

        keywords_group_pattern = f"(?:{keyword_sep_pattern}){{{min_keywords},{max_keywords-1}}}(?:{keyword_pattern})"
        keywords_match_pattern = (
            rf"{start_pattern}({keywords_group_pattern}{end_pattern})"
        )

        keywords_group = re.findall(keywords_match_pattern, text)
        if not keywords_group:
            return self.keywords or []
        keywords_string = keywords_group[0]

        keywords_list = [
            keyword.strip().replace("\n", " ")
            for keyword in keywords_string.split(separator)
        ]

        if keywords_list and (keywords_list[-1] in ["acm reference format"]):
            del keywords_list[-1]

        if self.keywords and (self.keywords != keywords_list):
            print(
                "Keywords found from the metadata of the pdf differs from the ones found in the text."
            )

        return keywords_list

    def extract_keywords_from_text_(self, text: str) -> list:
        r"""Tries to extract keywords from the text.
        It assumes that the pattern is a list of at least 3 words separated by
        any non-word character, excluding "\s" and "\.".
        Full pattern:
          "(?:Keywords|Key words)[:\s]+((?:(?:\w+\-?\w+)?[\r\f\t ]?(?:\w+\-?\w+))(?:[^\s\.\w][\r\f\t ]?(?:(?:\w+\-?\w+)?[\r\f\t ]?(?:\w+\-?\w+))){2,})"
        Ex.: keywords: test-word1, test-word2 word1, word2, last composed.
        """

        "(((?:(?:[\w\-?]+)?[\s]?(?:\w+\-?\w+))(?:([^\s\.\w])[\r\f\t\n ]?)){1,}(?:(?:\w+\-?\w+)?[\r\f\t ]?(?:\w+\-?\w+)))"

        flag_pattern = r"(?:keywords|key words)[:\s]+"
        single_word_pattern = r"(?:\w+\-?\w+)"
        composed_word_pattern = r"[\r\f\t ]?".join(
            [single_word_pattern + "?", single_word_pattern]
        )
        separator_pattern = r"[^\s\.\w][\r\f\t ]?"  # e.g. ", ", ";", "|", etc.
        keywords_group_pattern = f"((?:{composed_word_pattern})(?:{separator_pattern}(?:{composed_word_pattern})){{2,}})"

        keywords_pattern = f"{flag_pattern}{keywords_group_pattern}"

        keywords_groups = re.findall(keywords_pattern, text)
        if not keywords_groups:
            return self.keywords or []
        keywords_string = keywords_groups[0]
        separators = np.array(re.findall(r"[^\s\w\-]", keywords_string))
        unique_separators, counts = np.unique(separators, return_counts=True)
        if len(unique_separators) > 1:
            print(f"Multiple separators found for paper {self.title}")
            idx_of_most_frequent = counts.argmax()
            separator = unique_separators[idx_of_most_frequent]
        else:
            separator = unique_separators[0]

        keywords_list = [
            keyword.strip() for keyword in keywords_string.split(separator)
        ]

        if self.keywords and (self.keywords != keywords_list):
            print(
                "Keywords found from the metadata of the pdf differs from the ones found in the text."
            )

        return keywords_list

    def cross_validate_doi(self, metadata: dict) -> bool:
        """Check if title from metadata is in the text"""
        # print(f"{self.doi=}")
        # print(f"{metadata['doi']=}")
        # print(f"{metadata['title']=}")
        text = re.sub(r"\n", " ", self.text)
        text = re.sub(r"\s\s", " ", text)

        assertion = (self.doi == metadata["doi"]) and (
            re.sub(r"(?!\s)\W", "", metadata["title"]).lower().strip() in text
        )
        return assertion

    def clean_text(self):
        """Remove punctuation and special characters from the text"""

        # join words that are separated at the end of the line: e.g. dis-\parate
        text = self._raw_text.replace("-\n", "\n")
        # remove line breaks
        text = text.replace(r"\n", " ")
        text = re.sub(r"\s\s", " ", text)
        # remove any non-word character, excluding empty spaces.
        text = re.sub(r"(?!\s)\W", "", text).lower().strip()
        return text

    def extract_pdf_info(self) -> str:
        """
        Extracts the metadata information of the PDF file if available.
        """

        fp = open(self.full_path, "rb")
        parser = PDFParser(fp)
        doc = PDFDocument(parser)
        info = doc.info
        return info

    def extract_pdf_text(self) -> str:
        """
        Extract the text from the pdf file.
        """
        doc = fitz.open(self.full_path)
        text = ""
        for page in doc:
            text += page.get_text()
        return text

    def extract_doi_from_str(self, string: str) -> list:
        """Extract all DOIs matches from a string using a regular expression"""
        doi_pattern = r"\b10\.\d{4,}/[-._;()/:a-zA-Z0-9]+\b"
        # Find all matches in the text
        doi_list = re.findall(doi_pattern, string)
        return doi_list

    def extract_doi(self) -> str:
        """Extract DOI"""
        doi_list = self.extract_doi_from_str(str(self._pdf_info))
        if not doi_list:
            doi_list = self.extract_doi_from_str(self._raw_text)

        return doi_list[0] if doi_list else ""
