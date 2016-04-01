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
from .parser import WebParser

_DEFAULT_IMPORTANCE = -1


class WebNode:

    def __init__(self, urls, content, out_links, language, title, node_id=None, importance=_DEFAULT_IMPORTANCE):
        self.urls = urls
        self.content = content
        self.out_links = out_links
        self.language = language
        self.title = title
        self.importance = importance
        self.node_id = node_id
        if urls is None or len(urls) == 0:
            raise ValueError("No urls given for WebNode!")
        if node_id is None and (content is None or len(content) == 0):
            raise ValueError("No node id and no content, node cannot be valid!")
        self._content_hash = WebParser.hash_content(self.content)

    def add_url(self, url):
        self.urls.append(url)

    def get_out_links(self):
        return self.out_links

    def has_node_id(self):
        return self.node_id is not None

    def set_node_id(self, node_id):
        self.node_id = node_id

    def get_node_id(self):
        return self.node_id

    def get_urls(self):
        return self.urls

    def get_title(self):
        return self.title

    def get_language(self):
        return self.language

    def get_importance(self):
        return self.importance

    def set_importance(self, importance):
        self.importance = min(1., max(0., importance))

    def get_content_hash(self):
        return self._content_hash

    def get_content(self):
        return self.content

    def __eq__(self, other):
        return any((url in other.urls for url in self.urls))

    def __hash__(self):
        if not self.has_node_id():
            return self.get_content_hash()
        return self.node_id

    def __str__(self):
        return ("id: " + str(self.node_id) + ", urls: " + str(self.urls) +
                ", lang: " + str(self.language) + ", importance: " + str(self.importance))

    def __repr__(self):
        return "id: " + str(self.node_id) + ",  url:" + str(self.urls[0]) + ", importance: " + str(self.importance)

    class Builder:
        def __init__(self, link_constraint, urls=None, content=None, out_links=None, language=None,
                     importance=_DEFAULT_IMPORTANCE, title=None, node_id=None):
            self.link_constraint = link_constraint
            self.urls = urls
            self.content = content
            self.out_links = out_links
            self.language = language
            self.importance = importance
            self.node_id = node_id
            self.title = title

        def init_from_webparser(self, webparser):
            self.urls = [webparser.get_url()]
            self.content = webparser.get_content()
            self.out_links = [self.link_constraint.get_valid(link) for link in webparser.get_web_links()]
            self.out_links = [link for link in self.out_links if link is not None]
            self.title = webparser.get_title()
            self.language = webparser.get_language()

        def make_node(self):
            if self.link_constraint is not None:
                self.urls = [self.link_constraint.normalize(url) for url in self.urls]
            return WebNode(self.urls, self.content, self.out_links, self.language, self.title,
                           node_id=self.node_id, importance=self.importance)
