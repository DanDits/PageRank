from bs4 import BeautifulSoup
from urllib.parse import urljoin


class WebParser:
    _CONTENT_SEPARATOR = "__S_E_P_A_R_A_T_O_R__:)"

    def __init__(self, base_link, website_raw):
        self.base_link = base_link
        self.soup = BeautifulSoup(website_raw, "html.parser")
        self.content = self.parse_content()

    def get_url(self):
        return self.base_link

    def get_content(self):
        return self.content

    def get_language(self):
        return self.soup.find(attrs={"lang": True})["lang"]

    def get_web_links(self):
        href_urls = (link.get("href") for link in self.soup.find_all("a"))
        return [self._get_resolved_link(url) for url in href_urls if url is not None]  # filter NoneTypes and resolve

    def __hash__(self):
        return hash(self.content)

    def __eq__(self, other):
        return self.content == other.content

    def parse_content(self):
        content = self.soup.getText(separator=WebParser._CONTENT_SEPARATOR, strip=True)
        return tuple(content.split(sep=WebParser._CONTENT_SEPARATOR))

    def _get_resolved_link(self, link):
        return urljoin(self.base_link, link)  # Resolve relative links

if __name__ == "__main__":
    test_url = "http://www.math.kit.edu"
    from urllib.request import urlopen
    website = urlopen(test_url).read()
    parser = WebParser(test_url, website)
    print(parser.get_web_links())
