# -*- coding: utf-8 -*-
"""
Created on Sun Feb  7 16:37:16 2016

@author: daniel
"""

from urllib.parse import urlparse


class LinkConstraint:
    def __init__(self, scheme='', netloc=''):
        self.netloc = netloc
        self.scheme = scheme
        self.rules = []

    def add_rule(self, rule):
        self.rules.append(rule)

    def get_valid(self, link):
        link_url = urlparse(link, scheme=self.scheme)
        if not self._is_in_netloc(link_url[1]):
            return
        if not self._is_scheme(link_url[0]):
            return
        if self._is_rule_broken(link):
            return
        return self.normalize(link)

    def _is_rule_broken(self, link):
        for rule in self.rules:
            matched = rule(link)
            if not matched:
                return True

    def _is_scheme(self, scheme):
        return not self.scheme or self.scheme == '' or self.scheme == scheme

    def _is_in_netloc(self, netloc):
        return not self.netloc or self.netloc == '' or self.netloc == netloc

    # noinspection PyMethodMayBeStatic
    def normalize(self, link):
        if link.endswith("/"):
            # empty url path, cut backslash!
            link = link[:-1]
        parsed = urlparse(link)
        return parsed.geturl()
