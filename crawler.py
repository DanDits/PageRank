# -*- coding: utf-8 -*-
"""
Created on Sat Feb  6 12:49:02 2016

@author: daniel
"""

import threading  # For main processing thread
import urllib  # For downloading websites
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor  # each downloads a website
from queue import Queue, Empty  # For processing downloaded websites

import linkconstraint as lc  # constraint to which links are allowed in the network
from webnode import WebNode
from webparser import WebParser  # parses the downloaded html site and extracts info


class Crawler:
    # Initializes the Crawler. If max_sites is greater than zero it will only
    # download this many sites and stop afterwards, else until no new site is found.
    def __init__(self, max_sites=0, max_workers=3, timeout=30, link_constraint=None):
        self.pending_links = Queue()
        self.link_constraint = link_constraint
        if self.link_constraint is None:
            self.link_constraint = lc.LinkConstraint()
        self.already_processed = set()
        self.is_crawling = False
        self.max_sites = max_sites
        self.processed_sites_count = 0
        self.max_workers = max_workers
        self.timeout = timeout
        self.processor = None
        self.executor = None

    def process_link(self, link):
        if self.is_finished():
            return
        website = Crawler.download_website(link, self.timeout)
        if website is None:
            print("Website", link, "not downloaded")
        return self, link, website

    @staticmethod
    def link_got_processed(future):
        if future.done() and future.result():
            self, link, website = future.result()
            if website is None:
                # revert and try later
                print("Website not downloaded, retrying later", link)
                self.already_processed.remove(link)
                self.add_link(link)
                return
            if not self.has_maximum_sites_processed():
                webparser = WebParser(link, website)
                web_hash = hash(webparser)
                if web_hash in self.already_processed:
                    print("Website", link, "already processed (with different url)!")
                    return
                print("Processed", (self.processed_sites_count + 1), ".link", link)
                self.already_processed.add(web_hash)
                self.processed_sites_count += 1
                self.process_new_website(webparser)

    def process_new_website(self, webparser):
        builder = WebNode.Builder(self.link_constraint)
        builder.init_from_webparser(webparser)
        webnode = builder.make_node()
        for link in webnode.get_out_links():
            self.add_link(link)

    def obtain_new_link(self):
        link = None
        while link is None and not self.is_finished():
            try:
                link = self.pending_links.get(timeout=self.timeout)
            except Empty:
                print("No more links found to process!")
                return
            if link in self.already_processed:
                link = None
                continue  # already processed
        if link:
            self.already_processed.add(link)
        return link

    def is_finished(self):
        return not self.is_crawling or self.has_maximum_sites_processed()

    def has_maximum_sites_processed(self):
        return 0 < self.max_sites <= self.processed_sites_count

    def process_links(self):
        try:
            self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
            while not self.is_finished():
                # TODO this will submit way too many futures when testing with maxsites>0!
                link = self.obtain_new_link()
                if link is None:
                    return

                future = self.executor.submit(self.process_link, link)
                future.add_done_callback(Crawler.link_got_processed)

        finally:
            self.stop()  # ensure crawler is really stopped

    def start(self, start_url):
        print("Starting crawling at", start_url)
        self.is_crawling = True
        self.add_link(self.link_constraint.normalize(start_url))
        self.processor = threading.Thread(target=self.process_links)
        self.processor.start()

    def add_link(self, link):
        if link is None or link in self.already_processed:
            return
        self.pending_links.put(link)

    def stop(self):
        print("Stopping crawling")
        self.is_crawling = False
        self.executor.shutdown(wait=False)

    @staticmethod
    def download_website(url, timeout):
        # Download and read website
        print("Downloading website", url)
        try:
            website = urllib.request.urlopen(url, timeout=timeout).read()
        except urllib.error.URLError:
            print("(Timeout) error when downloading", url)
            return
        return website


if __name__ == "__main__":
    constraint = lc.LinkConstraint('http', 'www.math.kit.edu')
    for prefix in ['.png', '.jpg', '.jpeg', '.pdf', '.ico', '.doc', '.txt']:
        constraint.add_rule(lambda link: not link.lower().endswith(prefix))

    c = Crawler(max_sites=5, link_constraint=constraint)
    c.start("http://www.math.kit.edu")

