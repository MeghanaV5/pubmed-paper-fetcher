import requests
import pandas as pd
from xml.etree import ElementTree as ET

# List of keywords to identify pharmaceutical/biotech companies
pharma_keywords = [
    "pharma", "biotech", "pfizer", "novartis", "astrazeneca", "roche",
    "sanofi", "gsk", "johnson & johnson", "merck", "bayer", "abbvie",
    "amgen", "bristol-myers", "eli lilly", "genentech", "regeneron"
]

def is_pharma_affiliation(affiliation):
    if not affiliation:
        return False
    return any(keyword in affiliation.lower() for keyword in pharma_keywords)

def fetch_pubmed_ids(query, retmax=10):
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        "db": "pubmed",
        "term": query,
        "retmode": "json",
        "retmax": retmax
    }
    response = requests.get(base_url, params=params)
    data = response.json()
    return data["esearchresult"]["idlist"]

def fetch_pubmed_details(pmid_list):
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = {
        "db": "pubmed",
        "id": ",".join(pmid_list),
        "retmode": "xml"
    }
    response = requests.get(base_url, params=params)
    return ET.fromstring(response.content)

def parse_articles(xml_root):
    results = []
    for article in xml_root.findall(".//PubmedArticle"):
        pmid = article.findtext(".//PMID")
        title = article.findtext(".//ArticleTitle")
        affiliations = article.findall(".//Affiliation")
        authors = article.findall(".//Author")
        
        for affiliation in affiliations:
            if is_pharma_affiliation(affiliation.text):
                author_names = []
                for author in authors:
                    last = author.findtext("LastName") or ""
                    fore = author.findtext("ForeName") or ""
                    author_names.append(f"{fore} {last}".strip())
                results.append({
                    "PMID": pmid,
                    "Title": title,
                    "Authors": "; ".join(author_names),
                    "Affiliation": affiliation.text
                })
                break  # Only include one entry per article if any author is affiliated
    return results

def main():
    query = input("Enter your PubMed query: ")
    pmids = fetch_pubmed_ids(query)
    print(f"Found {len(pmids)} paper IDs.")

    if not pmids:
        print("No results found.")
        return

    xml_data = fetch_pubmed_details(pmids)
    results = parse_articles(xml_data)

    if results:
        df = pd.DataFrame(results)
        df.to_csv("filtered_papers.csv", index=False)
        print(f"\n✅ {len(results)} matching papers saved to filtered_papers.csv")
    else:
        print("\n❌ No papers found with pharmaceutical affiliations.")

if __name__ == "__main__":
    main()
