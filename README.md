# AIoD Paper Metadata Extractor

Extracts metadata from PDF files.

1. First it gets the DOI from the text using regex
2. Makes a get request to an API to retrieve the metadata of this specific paper.
3. Cross validates the DOI by matching the retrieved title with the text content of the PDF
4. Tries to extract the key words from different sources in this order:
   a. From the PDF metadata
   b. From the text itself using a regex pattern

   