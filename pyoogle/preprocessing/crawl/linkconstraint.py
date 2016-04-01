# -*- coding: utf-8 -*-
"""
Created on Sun Feb  7 16:37:16 2016

@author: daniel
"""

from urllib.parse import urlparse
from urllib.parse import quote
import re


class LinkConstraint:
    def __init__(self, scheme='', netloc='', use_fragment=False):
        self.netloc = netloc
        self.scheme = scheme
        self.use_fragment = use_fragment  # if false can ignore fragment (# in url) as it only directs within a website
        self.rules = []
        self.rules_parsed_link = []

    def add_rule(self, rule, parsed_link=False):
        if parsed_link:
            self.rules_parsed_link.append(rule)
        else:
            self.rules.append(rule)

    def get_valid(self, link):
        parsed = urlparse(link, scheme=self.scheme)
        if not self._is_in_netloc(parsed[1]):
            return
        if not self._is_scheme(parsed[0]):
            return
        if (not all((rule(link) for rule in self.rules)) or
                not all((rule(parsed) for rule in self.rules_parsed_link))):
            return
        return self.normalize(link)

    def _is_scheme(self, scheme):
        return not self.scheme or self.scheme == '' or self.scheme == scheme

    def _is_in_netloc(self, netloc):
        return not self.netloc or self.netloc == '' or self.netloc == netloc

    _REGEX_VALID_URL = re.compile('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@\.&+#]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')

    # noinspection PyProtectedMember
    def normalize(self, link):
        # This normalize function must be a projection; that is for all valid links it holds
        # lc.normalize(lc.normalize(link))==lc.normalize(link)
        if link.endswith("/"):
            # empty url path, cut backslash!
            link = link[:-1]
        valid = LinkConstraint._REGEX_VALID_URL.fullmatch(link) is not None
        if valid and self.use_fragment:
            return link  # already a valid url

        # Else we need to parse...
        parsed = urlparse(link)
        if valid and not self.use_fragment:
            # Only remove fragment
            return parsed._replace(fragment='').geturl()

        # ... and quote the components
        frag_param = ''
        if self.use_fragment:
            frag_param = quote(parsed.fragment)
        parsed = parsed._replace(netloc=quote(parsed.netloc),
                                 path=quote(parsed.path),
                                 params=quote(parsed.params),
                                 query=quote(parsed.query),
                                 fragment=frag_param)
        return parsed.geturl()


if __name__ == "__main__":
    c = LinkConstraint()
    c.add_rule(lambda link : "math" in link)
    test_link = "http://www.math.kit.edu/iag2/~schwer/seite/yggt5/de#Physics"
    print("Gettin valid:", c.get_valid(test_link))
    print("To normalize:", test_link)
    test_link = c.normalize(test_link)
    print("Normalized:", test_link)
    test_link = "http://www.math.kit.edu/iag2/%7Eschwer/seite/yggt5/de#Physics"
    test_link = c.normalize(test_link)
    print("Normalized again:", test_link)
