# -*- coding: utf-8 -*-
"""
Created on Sat Feb  6 12:49:02 2016

@author: daniel
"""

import threading  # For main processing thread
import urllib  # For downloading websites
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor  # each downloads a website
from queue import Queue, Empty  # For processing downloaded websites

import preprocessing.crawl.linkconstraint as lc  # constraint to which links are allowed in the network
from preprocessing.web.net import WebNet
from preprocessing.web.node import WebNode
from preprocessing.web.nodestore import WebNodeStore  # for permanently saving created WebNodes
from preprocessing.web.parser import WebParser  # parses the downloaded html site and extracts info


class Crawler:
    # Initializes the Crawler. If max_sites is greater than zero it will only
    # download this many sites and stop afterwards, else until no new site is found.
    def __init__(self, max_sites=0, max_workers=2, timeout=30, link_constraint=None):
        self.pending_links = Queue()
        self.pending_websites = Queue()
        self.web_net = WebNet()
        self.link_constraint = link_constraint
        if self.link_constraint is None:
            self.link_constraint = lc.LinkConstraint()
        self.already_processed_links = set()
        self.already_processed_websites = set()
        self.is_crawling = False
        self.max_sites = max_sites
        self.processed_sites_count = 0
        self.max_workers = max_workers
        self.timeout = timeout
        self.links_processor = None
        self.websites_processor = None

    def _is_finished(self):
        return not self.is_crawling or self.has_maximum_sites_processed()

    def has_maximum_sites_processed(self):
        return 0 < self.max_sites <= self.processed_sites_count

    def process_link(self, link):
        if self._is_finished():
            return
        website = Crawler.download_website(link, self.timeout)
        if website is None:
            print("Website", link, "not downloaded")
        return self, link, website

    @staticmethod
    def link_got_processed(future):
        if future.done() and future.result() is not None:
            self, link, website = future.result()
            if self._is_finished():
                return
            if website is None:
                # revert and try later
                print("Website not downloaded, retrying later", link)
                self.add_link(link)
                return
            if not self.has_maximum_sites_processed():
                self.pending_websites.put((link, website))

    def obtain_new_link(self):
        link = None
        while link is None and not self._is_finished():
            try:
                link = self.pending_links.get(timeout=self.timeout)
            except Empty:
                print("No more links found to process!")
                return
            if link in self.already_processed_links:
                link = None
                continue  # already processed
        if link is not None:
            self.already_processed_links.add(link)
        return link

    def process_links(self):
        print("Starting to process links in thread", threading.current_thread())
        try:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                while not self._is_finished():
                    # this will submit many many futures when testing with limited maxsites(>0)
                    # but they will be ignored!
                    link = self.obtain_new_link()
                    if link is None:
                        return

                    future = executor.submit(self.process_link, link)
                    future.add_done_callback(Crawler.link_got_processed)

        finally:
            self.stop()  # ensure crawler is really stopped

    def process_website(self, link, website):
        webparser = WebParser(link, website)
        web_hash = hash(webparser)
        if web_hash in self.already_processed_websites:
            print("Website", link, "already processed (with different url)!")
            self.web_net.node_add_url(web_hash, link)
            return
        print("Processed", (self.processed_sites_count + 1), ".link", link)
        self.already_processed_websites.add(web_hash)
        self.processed_sites_count += 1

        builder = WebNode.Builder(self.link_constraint)
        builder.init_from_webparser(webparser)
        webnode = builder.make_node()
        self.web_net.add_node(webnode)
        for link in webnode.get_out_links():
            self.add_link(link)

    def process_websites(self, clear_store):
        # We are required to open the store in the same thread the store is modified in
        print("Starting to process websites in thread", threading.current_thread())
        with WebNodeStore(clear_store) as node_store:
            try:
                while not self._is_finished():
                    data = self.pending_websites.get(block=True)
                    if data is None:
                        break
                    link, website = data
                    self.process_website(link, website)
                node_store.save_webnodes(self.web_net.get_nodes())
            finally:
                self.stop()  # ensure crawler is really stopped

    def join(self):
        self.websites_processor.join()
        self.links_processor.join()

    def start(self, start_url, clear_store=True):
        print("Starting crawling at", start_url)
        self.is_crawling = True
        self.add_link(self.link_constraint.normalize(start_url))
        print("Starting program in thread", threading.current_thread())
        self.links_processor = threading.Thread(target=self.process_links)
        self.links_processor.start()
        self.websites_processor = threading.Thread(target=Crawler.process_websites, args=[self, clear_store])
        self.websites_processor.start()

    def add_link(self, link):
        if link is None:
            return
        self.pending_links.put(link)

    def stop(self):
        print("Stopping crawling")
        self.is_crawling = False
        self.pending_websites.put(None)  # Ensure thread does not wait forever and exits

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

    c = Crawler(max_sites=12, link_constraint=constraint)
    c.start("http://www.math.kit.edu")
    c.join()
    webnet = c.web_net
    print("DONE, webnet contains", len(webnet), "nodes")
