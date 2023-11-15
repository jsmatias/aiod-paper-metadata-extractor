"""
Reads a single paper or a bulk of paper
"""
import pandas as pd
from glob import glob
from .paper import Paper
from config import Config


class Reader:
    def __init__(self) -> None:
        config = Config()
        self.files_path = config.get_papers_path()

        self.paper_list: list[Paper] = []

    def reset(self):
        self.paper_list = []

    def extract_info(
        self,
        file_name: str,
        filename_has_doi: bool = True,
        pattern_to_replace: dict = {},
    ):
        """Instantiate Paper with the file_name"""
        # TODO check if the file exists
        self.paper_list.append(
            Paper(self.files_path, file_name, filename_has_doi, pattern_to_replace)
        )

    def extract_info_from_bulk(
        self, filename_has_doi: bool = False, pattern_to_replace: dict = {}
    ):
        """Extracts info for all pdf files in the files path"""

        papers = [
            paperPath.split("/")[-1] for paperPath in glob(self.files_path + "*.pdf")
        ]
        for paper in papers:
            print(f"--------- Extracting --------- {paper}")
            self.extract_info(paper, filename_has_doi, pattern_to_replace)

    def get_metadata(self, format: str = "dict") -> list[dict] | pd.DataFrame:
        """
        Args:
            format: accepts 'dict' or 'dataframe'
        returns: A list of dictionaries containing the metadata extracted from the
            paper of a pandas dataframe.
        """

        papers_details = []
        for paper in self.paper_list:
            papers_details.append(
                {
                    "file_name": paper.file_name,
                    "doi": paper.doi,
                    "title": paper.title,
                    "authors": ";".join(paper.author),
                    "journal": paper.journal,
                    "publisher": paper.publisher,
                    "year": paper.year,
                    "keywords": ";".join(paper.keywords),
                    "topics": ";".join(paper.topics),
                }
            )

        if format == "dict":
            return papers_details
        elif format == "dataframe":
            papers_df = pd.DataFrame(papers_details)
            return papers_df
        else:
            raise TypeError("format must be 'dict' or 'dataframe'")

    def get_data(self, raw=False) -> dict:
        """"""
        papers_content = []
        for paper in self.paper_list:
            papers_content.append(
                {
                    "doi": paper.doi,
                    "text": paper._raw_text if raw else paper.text,
                }
            )
        return papers_content

    def source(self) -> str:
        return self.files_path

    # def list_papers
