from bs4 import BeautifulSoup
from urllib.parse import urljoin
from itertools import chain
import re


class WebParser:
    _CONTENT_SEPARATOR = "__S_E_P_A_R_A_T_O_R__:)"

    def __init__(self, base_link, website_raw):
        self.base_link = base_link
        self.soup = BeautifulSoup(website_raw, "html.parser")
        self.check_valid()
        self.links_in_scripts = []
        self.content = self._parse_content()

    def check_valid(self):
        html = str(self.soup)
        if (html is None or html.find("<html") < 0 or
                not hasattr(self.soup, "body") or
                self.soup.body is None or not hasattr(self.soup, "html") or self.soup.html is None):
            raise ValueError("Given website is not valid html website.")

    def get_url(self):
        return self.base_link

    def get_content(self):
        return self.content

    def get_title(self):
        title = self.soup.html.title
        return title.getText() if title is not None else ''

    def get_language(self):
        lang_tag = self.soup.find(attrs={"lang": True})
        return lang_tag["lang"] if lang_tag is not None else ''

    def get_web_links(self):
        href_urls = (link.get("href") for link in self.soup.find_all("a"))
        href_urls = chain(href_urls, self.links_in_scripts)
        return [self._get_resolved_link(url) for url in href_urls if url is not None]  # filter NoneTypes and resolve

    def __hash__(self):
        return WebParser.hash_content(self.content)

    @staticmethod
    def hash_content(content):
        if content is None:
            return
        return hash("".join(content))

    def __eq__(self, other):
        return self.content == other.content

    def _parse_content(self):
        # Remove <style> tags, no real text content
        for elem in self.soup.findAll('style'):
            elem.extract()

        # Remove <script> tags, we do not want to parse and execute the javascript, but fetch the contained links!
        for elem in self.soup.findAll('script'):
            if elem.contents is not None:
                for script_line in elem.contents:
                    for link in WebParser.find_hrefs(script_line):
                        self.links_in_scripts.append(link)
            elem.extract()

        content = self.soup.getText(separator=WebParser._CONTENT_SEPARATOR, strip=True)
        return tuple(content.split(sep=WebParser._CONTENT_SEPARATOR))  # content must be static and hashable

    def _get_resolved_link(self, link):
        return urljoin(self.base_link, link)  # Resolve relative links

    # Match <a href="SOMELINK" >
    # allow ' instead of ", capture SOMELINK and allow and ignore other attributes of 'a'
    _REGEX_LINK = re.compile('''<a(?:.[^<>]+)href\s*=\s*['"](.[^'"]+)['"](?:.[^<>]*)>''')

    @staticmethod
    def find_hrefs(text):
        return WebParser._REGEX_LINK.findall(text)

if __name__ == "__main__":
    test_url = "http://www.math.kit.edu"
    from urllib.request import urlopen
    website = urlopen(test_url).read()
    parser = WebParser(test_url, website)
    print("Parser content:")
    for c in parser.get_content():
        print(c)
    print("Title:", parser.get_title())
    print("Parser web links:")
    for web_link in parser.get_web_links():
        print(web_link)
    print("Language:", parser.get_language())
