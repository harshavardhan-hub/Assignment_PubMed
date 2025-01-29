## Research Paper Fetching Program
This Python program fetches research papers from the PubMed API based on a user-specified query. It identifies papers with at least one author affiliated with a pharmaceutical or biotech company and returns the results as a CSV file.

# Table of Contents
1.	Overview
2.	Features
3.	Requirements
4.	Installation
5.	Usage
6.	Code Organization
7.	Dependencies
8.	Tools Used

# Overview
This Python program uses the PubMed API to search for research papers based on a user-defined query. The program identifies papers where authors are affiliated with pharmaceutical or biotech companies and exports the results into a CSV file. The CSV contains key information, such as the PubMed ID, paper title, publication date, non-academic author names, company affiliations, and corresponding author email.

# Features
•	Fetches research papers using PubMed API.
•	Supports PubMed's full query syntax.
•	Identifies non-academic authors and pharmaceutical/biotech companies.
# Outputs results to a CSV file with the following columns:
•	PubMedID
•	Title
•	Publication Date
•	Non-academic Author(s)
•	Company Affiliation(s)
•	Corresponding Author Email
# Command-line interface with options:
  •	-h / --help: Display usage instructions.
  •	-d / --debug: Print debug information.
  •	-f / --file: Specify output filename (defaults to console output).

# Requirements
•	Python 3.x
•	Poetry for dependency management
•	Git for version control

# Installation
1.	Clone the repository:
- bash
- git clone https://github.com/yourusername/research-paper-fetcher.git
- cd research-paper-fetcher
2.	Install dependencies using Poetry:
Make sure you have Poetry installed. If not, install it from Poetry's official site.
- bash
- poetry install
3.	Set up the environment:
Poetry will install all the required dependencies for you. You can activate the virtual environment by running:
bash
- poetry shell

# Usage
1.	Basic command to fetch papers:
To fetch papers based on a query and print the results to the console, run:
- bash
- python get_papers.py "pharmaceutical industry"
2.	Save results to a CSV file:
To save the results in a CSV file:
- bash
- python get_papers.py "pharmaceutical industry" -f output.csv
3.	Enable debug mode for detailed output:
To see debug information, use the -d option:
- bash
- python get_papers.py "pharmaceutical industry" -d
4.	Get help and see all available options:
- bash
- python get_papers.py -h

# Code Organization
•	get_papers.py: The main script that handles the fetching of research papers from PubMed, parsing the results, and outputting them as a CSV file.
•	requirements.toml: Lists all dependencies for the project, managed by Poetry.
•	README.md: Documentation explaining the usage and setup of the project.
•	.gitignore: Specifies files/folders that should not be tracked by Git.

# Dependencies
•	requests: For making HTTP requests to the PubMed API.
•	csv: For writing the fetched results to a CSV file.
•	argparse: To handle command-line arguments.
•	logging: To provide detailed logs during execution, especially when debug mode is enabled.
These dependencies are automatically managed by Poetry and installed with the poetry install command.

# Tools Used
•	ChartGPT: Assisted in generating the structure and functionality of the program, including the logic for handling the PubMed API and CSV output.
•	Replit.ai: Used for testing and prototyping the code in an online IDE environment to quickly develop and iterate on the solution.
