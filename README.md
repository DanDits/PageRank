# Pyoogle
Google in python!

University course project that consists of the following tasks:

## Preprocessing
1. Write a Crawler that automatically follows links on a given start website and downloads the websites.
2. Parse the downloaded website to analyze outgoing links and the content.
3. Save the analyzed website as a node in a webgraph.
4. Use page ranking algorithm to rank the importances of websites in the graph.

## Searching
- Offer some command line or gui interface to search for key words
- Present some results and a preview based on metrics and page rank

## Requirements
Written for python 3.5. Requires the packages numpy, scipy for the ranking, the package BeautifulSoup for crawling and analyzing html websites.

## Usage
- Configure config.py so that the url is some absolute path valid for your machine and can be used implicitly by various files for default behavior.
- For configuring a link constraint on the crawler see the example function in preprocessing.crawl.crawler.py which only follows links on a certain domain and prevents downloading of urls that do likely do not represent a webpage.
- For starting a crawler invoke the start(start_url). By default, this will clear the associated webstore. To wait until it finished invoke join() or to cancel stop().
- For calculating page rank of a webnet use the ranker.py
- For a command line search invoke main() in pyoogle/search/main.py.
