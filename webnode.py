# -*- coding: utf-8 -*-
"""
Created on Sun Feb  7 15:08:42 2016

@author: daniel
"""


class WebNode:
    _DEFAULT_IMPORTANCE = -1

    def __init__(self, urls, content, out_links, language, importance=_DEFAULT_IMPORTANCE):
        self.urls = urls
        self.content = content
        self.out_links = out_links
        self.language = language
        self.importance = importance
        if urls is None or content is None:
            raise ValueError("No urls or content given for WebNode!")
        print("Initialized WebNode:", urls, language, importance)

    def get_out_links(self):
        return self.out_links

    def __eq__(self, other):
        return any((url in other.urls for url in self.urls))

    def __hash__(self):
        return hash(self.content)

    class Builder:
        def __init__(self, link_constraint):
            self.link_constraint = link_constraint
            self.urls = None
            self.content = None
            self.out_links = None
            self.language = None
            self.importance = WebNode._DEFAULT_IMPORTANCE

        def init_from_webparser(self, webparser):
            self.urls = [webparser.get_url()]
            self.content = webparser.get_content()
            self.out_links = [self.link_constraint.get_valid(link) for link in webparser.get_web_links()]
            self.out_links = [link for link in self.out_links if link is not None]
            self.language = webparser.get_language()

        def make_node(self):
            return WebNode(self.urls, self.content, self.out_links, self.language, self.importance)

        def add_url(self, url):
            if url is None:
                return
            if self.urls is None:
                self.urls = []
            self.urls.append(url)
