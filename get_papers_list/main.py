import argparse
import csv
import logging
import re
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
from Bio import Entrez
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class PubMedScraper:
    def __init__(self, email: str = "your_email@example.com"):
        """Initialize the PubMed scraper with configuration."""
        self.email = email
        Entrez.email = email

    def parse_publication_date(self, article_data: Dict) -> str:
        """Extract and format publication date from article data."""
        try:
            pub_date = article_data.get("Journal", {}).get("JournalIssue", {}).get("PubDate", {})
            if "Year" in pub_date:
                year = pub_date.get("Year", "")
                month = pub_date.get("Month", "01")
                day = pub_date.get("Day", "01")

                # Convert month name to number if needed
                if month.isalpha():
                    try:
                        month = str(datetime.strptime(month, "%B").month).zfill(2)
                    except ValueError:
                        month = "01"

                month = month.zfill(2)
                day = day.zfill(2)

                return f"{year}-{month}-{day}"
            elif "MedlineDate" in pub_date:
                medline_date = pub_date["MedlineDate"]
                match = re.search(r'(\d{4})', medline_date)
                if match:
                    return f"{match.group(1)}-01-01"
        except Exception as e:
            logging.warning(f"Error parsing publication date: {e}")

        return "Unknown"

    def extract_emails(self, text: str) -> Set[str]:
        """Extract all valid email addresses from text using simplified patterns."""
        email_patterns = [
            # Basic email pattern
            re.compile(r'[\w\.-]+@[\w\.-]+\.\w+'),
            # Emails with common prefixes
            re.compile(r'[Ee]mail:\s*([\w\.-]+@[\w\.-]+\.\w+)'),
            re.compile(r'[Ee]-mail:\s*([\w\.-]+@[\w\.-]+\.\w+)'),
            # Emails in brackets or parentheses
            re.compile(r'\[([\w\.-]+@[\w\.-]+\.\w+)\]'),
            re.compile(r'\(([\w\.-]+@[\w\.-]+\.\w+)\)'),
            re.compile(r'\<([\w\.-]+@[\w\.-]+\.\w+)\>')
        ]
        emails = set()
        for pattern in email_patterns:
            try:
                matches = pattern.finditer(text)
                for match in matches:
                    email = match.group(1) if len(match.groups()) > 0 else match.group(0)
                    email = email.strip('.,()<>[]{}').lower()
                    if re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
                        emails.add(email)
            except Exception as e:
                logging.debug(f"Error matching email pattern {pattern}: {e}")
                continue

        return emails

    def is_company_affiliation(self, affiliation: str) -> bool:
        """Determine if an affiliation is from a company."""
        academic_indicators = [
            r'\b(?:university|college|institut|academy|school)\b',
            r'\b(?:hospital|medical center|clinic)\b',
            r'\b(?:research center|laboratory|department)\b',
            r'\b(?:faculty|division)\b'
        ]
        clean_affiliation = ' '.join(affiliation.lower().split())
        for indicator in academic_indicators:
            if re.search(indicator, clean_affiliation, re.IGNORECASE):
                return False
        company_indicators = [
            r'\b(?:pharma|pharmaceutical|biotech|biotechnology)\b',
            r'\b(?:therapeutics|biosciences|biologics)\b',
            r'\b(?:inc|corp|ltd|gmbh|s\.a\.|llc|co\.|company|plc)\b',
            r'\b(?:drug discovery|r&d)\b',
            r'\b(?:labs|laboratories)\b',
            r'\b(?:research|development)\b'
        ]
        return any(re.search(indicator, clean_affiliation, re.IGNORECASE) 
                  for indicator in company_indicators)

    def fetch_pubmed_articles(self, query: str, max_results: int = 100) -> List[Dict[str, Any]]:
        """Fetch articles from PubMed based on query."""
        try:
            handle = Entrez.esearch(db="pubmed", term=query, retmax=max_results)
            record = Entrez.read(handle)
            handle.close()

            pmids = record["IdList"]
            if not pmids:
                logging.info("No results found for the query.")
                return []

            logging.info(f"Found {len(pmids)} articles. Fetching details...")

            handle = Entrez.efetch(db="pubmed", id=",".join(pmids), rettype="xml")
            articles = Entrez.read(handle)
            handle.close()

            return articles["PubmedArticle"]

        except Exception as e:
            logging.error(f"Error fetching PubMed articles: {e}")
            return []

    def extract_article_info(self, article: Dict) -> Optional[Dict[str, Any]]:
        """Extract and validate article information."""
        try:
            medline = article["MedlineCitation"]
            article_data = medline["Article"]
            pmid = str(medline["PMID"])
            if not pmid:
                return None

            title = article_data.get("ArticleTitle", "").strip()
            if not title:
                return None

            pub_date = self.parse_publication_date(article_data)
            if pub_date == "Unknown":
                return None

            non_academic_authors = []
            company_affiliations = set()
            all_emails = set()

            if "Electronic_Mail_Address" in article_data:
                emails = self.extract_emails(article_data["Electronic_Mail_Address"])
                all_emails.update(emails)

            authors = article_data.get("AuthorList", [])
            for author in authors:
                if not all(author.get(field) for field in ["ForeName", "LastName"]):
                    continue

                author_name = f"{author.get('ForeName', '')} {author.get('LastName', '')}".strip()

                if "AffiliationInfo" in author:
                    author_has_company = False
                    for aff in author["AffiliationInfo"]:
                        affiliation = aff.get("Affiliation", "").strip()
                        if not affiliation:
                            continue
                        emails = self.extract_emails(affiliation)
                        all_emails.update(emails)
                        if self.is_company_affiliation(affiliation):
                            author_has_company = True
                            company_affiliations.add(affiliation)

                    if author_has_company:
                        non_academic_authors.append(author_name)

            if non_academic_authors and company_affiliations:
                result = {
                    "PubmedID": pmid,
                    "Title": title,
                    "Publication Date": pub_date,
                    "Non-academic Authors": "; ".join(non_academic_authors),
                    "Company Affiliations": "; ".join(company_affiliations),
                    "Corresponding Author Email": "; ".join(all_emails) if all_emails else "Not available"
                }
                return result

            return None
        except Exception as e:
            logging.error(f"Error extracting info for PMID {article.get('MedlineCitation', {}).get('PMID', 'unknown')}: {e}")
            return None

    def save_to_csv(self, data: List[Dict[str, Any]], filename: str):
        """Save extracted data to CSV with validation."""
        if not data:
            logging.warning("No data to save.")
            return

        valid_data = [
            entry for entry in data 
            if all(entry.get(field) and entry[field] not in ["Unknown", "None", "", None] 
                  for field in ["PubmedID", "Title", "Publication Date", "Non-academic Authors", 
                              "Company Affiliations"])
        ]

        if not valid_data:
            logging.warning("No valid entries found after filtering.")
            return

        try:
            with open(filename, "w", newline="", encoding="utf-8") as csvfile:
                fieldnames = ["PubmedID", "Title", "Publication Date", 
                            "Non-academic Authors", "Company Affiliations", 
                            "Corresponding Author Email"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(valid_data)
            logging.info(f"Results saved to {filename} with {len(valid_data)} valid entries")
        except Exception as e:
            logging.error(f"Error saving to CSV: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Enhanced PubMed scraper for articles with pharmaceutical/biotech affiliations."
    )
    parser.add_argument("query", type=str, help="PubMed search query")
    parser.add_argument(
        "-f", "--file", type=str, default="pubmed_results.csv",
        help="CSV filename to save results (default: pubmed_results.csv)"
    )
    parser.add_argument(
        "-e", "--email", type=str, default="your_email@example.com",
        help="Email address for PubMed API access"
    )
    parser.add_argument(
        "-d", "--debug", action="store_true",
        help="Enable debug logging"
    )

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    scraper = PubMedScraper(email=args.email)
    logging.info(f"Starting PubMed search with query: {args.query}")

    articles = scraper.fetch_pubmed_articles(args.query)
    extracted_data = []

    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(scraper.extract_article_info, article): article for article in articles}
        for future in as_completed(futures):
            article_info = future.result()
            if article_info:
                extracted_data.append(article_info)

    if extracted_data:
        scraper.save_to_csv(extracted_data, args.file)
        logging.info(f"Processed {len(extracted_data)} articles successfully")
    else:
        logging.warning("No valid articles found to process")

if __name__ == "__main__":
    main()
