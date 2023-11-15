import requests
from bs4 import BeautifulSoup


def get_classification(doi: str) -> list:
    classification = []
    url = f"https://dl.acm.org/doi/{doi}"
    try:
        res = requests.get(url, timeout=30)
    except ConnectionError as err:
        print(err)
        return classification
    soup = BeautifulSoup(res.text, "html.parser")
    kw_tree_elements = soup.find_all("ol", class_="rlist organizational-chart")

    if kw_tree_elements:
        root = kw_tree_elements[0].find("h6")
        classification.append(root.text)

        keywords = kw_tree_elements[0].find_all("p")
        if keywords:
            for kw in keywords:
                classification.append(kw.text)
    if classification:
        classification = [topic.lower() for topic in classification]
    return classification
