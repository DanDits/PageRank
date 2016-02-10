# -*- coding: utf-8 -*-
"""
Created on Sun Feb  7 15:08:42 2016
Models a Website which is a node in the network("internet"). A WebNode is identified by one or more
urls that resolve to the same content. The content is a tuple of strings describing texts found on the website.
The WebNode can have zero or more links to other WebNodes; these are edges in the network. A WebNode can have a
language that describes the content. The importance of a WebNode is calculated by the PageRank algorithm describing
its importance in the total network.
@author: daniel
"""

_DEFAULT_IMPORTANCE = -1
class WebNode:

    def __init__(self, urls, content, out_links, language, node_id=None, importance=_DEFAULT_IMPORTANCE):
        self.urls = urls
        self.content = content
        self.out_links = out_links
        self.language = language
        self.importance = importance
        self.node_id = node_id
        if urls is None or len(urls) == 0 or content is None or len(content) == 0:
            raise ValueError("No urls or content given for WebNode!")
        print("Initialized WebNode:", urls, language, importance)

    def add_url(self, url):
        self.urls.append(url)

    def get_out_links(self):
        return self.out_links

    def set_node_id(self, node_id):
        self.node_id = node_id

    def get_node_id(self):
        return self.node_id

    def get_urls(self):
        return self.urls

    def get_language(self):
        return self.language

    def get_importance(self):
        return self.importance

    def get_content(self):
        return self.content

    def __eq__(self, other):
        return any((url in other.urls for url in self.urls))

    def __hash__(self):
        return hash(self.content)

    class Builder:
        def __init__(self, link_constraint, urls=None, content=None, out_links=None, language=None,
                     importance=_DEFAULT_IMPORTANCE, node_id = None):
            self.link_constraint = link_constraint
            self.urls = urls
            self.content = content
            self.out_links = out_links
            self.language = language
            self.importance = importance
            self.node_id = node_id

        def init_from_webparser(self, webparser):
            self.urls = [webparser.get_url()]
            self.content = webparser.get_content()
            self.out_links = [self.link_constraint.get_valid(link) for link in webparser.get_web_links()]
            self.out_links = [link for link in self.out_links if link is not None]
            self.language = webparser.get_language()

        def make_node(self):
            return WebNode(self.urls, self.content, self.out_links, self.language,
                           node_id=self.node_id, importance=self.importance)
