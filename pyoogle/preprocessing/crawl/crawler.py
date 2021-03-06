# -*- coding: utf-8 -*-
"""
Created on Sat Feb  6 12:49:02 2016

@author: daniel
"""

import logging
import threading  # For main processing thread
import urllib  # For downloading websites
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor  # each downloads a website
from http.client import RemoteDisconnected
from queue import Queue, Empty  # For processing downloaded websites
from socket import timeout as socket_timeout

from pyoogle.config import LOGGING_LEVEL
from pyoogle.preprocessing.crawl.linkconstraint import LinkConstraint  # constraint to which links are allowed
from pyoogle.preprocessing.web.net import WebNet
from pyoogle.preprocessing.web.node import WebNode
from pyoogle.preprocessing.web.nodestore import WebNodeStore  # for permanently saving created WebNodes
from pyoogle.preprocessing.web.parser import WebParser  # parses the downloaded html site and extracts info

logging.getLogger().setLevel(LOGGING_LEVEL)

NotResolvable = "NOT_RESOLVABLE_LINK"


class Crawler:
    # Initializes the Crawler. If max_sites is greater than zero it will only
    # download this many sites and stop afterwards, else until no new site is found.
    def __init__(self, store_path, link_constraint, max_sites=0, max_workers=2, timeout=30):
        self.store_path = store_path
        self.pending_links = Queue()
        self.pending_websites = Queue()
        self.web_net = None
        self.link_constraint = link_constraint
        if self.link_constraint is None:
            raise ValueError("No link constraint given!")
        self.already_processed_links = set()
        self.already_processed_websites = set()
        self.is_crawling = False
        self.max_sites = max_sites
        self.processed_sites_count = 0
        self.max_workers = max_workers
        self.timeout = timeout
        self.starting_processor = None
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
            logging.debug("Website %s not downloaded", link)
        if website is NotResolvable:
            logging.debug("Website %s not resolvable and not trying again.", link)
            return
        return self, link, website

    @staticmethod
    def link_got_processed(future):
        if future.done() and future.result() is not None:
            self, link, website = future.result()
            if self._is_finished():
                return
            if website is None:
                # revert and try later
                logging.debug("Website %s not downloaded, retrying later ", link)
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
                logging.info("No more links found to process!")
                return
            if link in self.already_processed_links:
                link = None
                continue  # already processed
        if link is not None:
            self.already_processed_links.add(link)
        return link

    def process_links(self):
        logging.info("Starting to process links")
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
        logging.debug("Starting to parse %s pending links %d", link, self.pending_links.qsize())
        try:
            webparser = WebParser(link, website)
        except ValueError:
            logging.debug("Website %s not parsable, ignored but out link kept", link)
            return
        web_hash = hash(webparser)
        if web_hash in self.already_processed_websites:
            # Already processed but with a different url, add this url to node so we know this in the future!
            logging.debug("Website %s already processed (with different url)!", link)
            node = self.web_net.get_by_content_hash(web_hash)
            if node is not None:
                node.add_url(link)
            return
        logging.info("Processed %d.link %s pending websites %d",
                     self.processed_sites_count + 1, link, self.pending_websites.qsize())
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
        logging.info("Starting to process websites")
        with WebNodeStore(self.store_path, clear_store) as node_store:
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

    def _init_net(self, clear_store):
        self.web_net = WebNet()
        if not clear_store:
                # Do not clear the store but add new nodes to it, load and add existing to webnet
            with WebNodeStore(self.store_path, clear=False) as node_store:
                for node in node_store.load_webnodes(True):
                    self.already_processed_websites.add(node.get_content_hash())
                    for link in node.get_urls():
                        self.already_processed_links.add(link)
                    self.web_net.add_node(node)

                # After we marked all already processed links, add new outgoings to restart
                restart_link_count = 0
                total_link_out = 0
                for node in self.web_net:
                    for link in node.get_out_links():
                        total_link_out += 1
                        if link not in self.already_processed_links:
                            self.add_link(link)
                            restart_link_count += 1
                logging.info("Restarting with %d links of %d", restart_link_count, total_link_out)

    def _start_async(self, clear_store):
        self._init_net(clear_store)
        self.links_processor = threading.Thread(target=self.process_links)
        self.links_processor.start()
        self.websites_processor = threading.Thread(target=Crawler.process_websites, args=[self, clear_store])
        self.websites_processor.start()

    def join(self):
        try:
            self.starting_processor.join()  # If this stops blocking, the other processors are valid
            self.websites_processor.join()
            self.links_processor.join()
        except KeyboardInterrupt:
            self.stop()

    def start(self, start_url, clear_store=True):
        logging.info("Starting crawling at %s", start_url)
        self.is_crawling = True
        self.add_link(start_url)
        self.starting_processor = threading.Thread(target=Crawler._start_async, args=[self, clear_store])
        self.starting_processor.start()

    def add_link(self, link):
        link = self.link_constraint.get_valid(link)
        if link is None:
            return
        self.pending_links.put(link)

    def stop(self):
        if self.is_crawling:  # Race condition safe (could be executed multiple times)
            logging.info("Stopping crawling")
            self.is_crawling = False
            self.pending_websites.put(None)  # Ensure threads do not wait forever and exit
            self.pending_links.put(None)

    @staticmethod
    def download_website(url, timeout):
        # Download and read website
        logging.debug("Downloading website %s", url)
        try:
            website = urllib.request.urlopen(url, timeout=timeout).read()
        except socket_timeout:
            logging.debug("Timeout error when downloading %s", url)
            website = None
        except urllib.error.HTTPError as err:
            if int(err.code / 100) == 4:
                logging.debug("Client http error when downloading %s %s", url, err)
                website = NotResolvable  # 404 Not Found or other Client Error, ignore link in future
            else:
                logging.debug("HTTP Error when downloading %d %s %s", err.code, url, err)
                website = None
        except urllib.error.URLError as err:
            logging.debug("Url error when downloading %s %s", url, err)
            website = None
        except RemoteDisconnected as disc:
            logging.debug("(RemoteDisconnect) error when downloading %s %s", url, disc)
            website = NotResolvable
        except UnicodeEncodeError:
            logging.debug("(UnicodeEncodeError) error when downloading %s", url)
            website = NotResolvable
        return website


def crawl_mathy():

    # Build constraint that describes which outgoing WebNode links to follow
    constraint = LinkConstraint('http', 'www.math.kit.edu')

    # Prevent downloading links with these endings
    # Frequent candidates: '.png', '.jpg', '.jpeg', '.pdf', '.ico', '.doc', '.txt', '.gz', '.zip', '.tar','.ps',
    # '.docx', '.tex', 'gif', '.ppt', '.m', '.mw', '.mp3', '.wav', '.mp4'
    forbidden_endings = ['.pdf', '.png', '.ico', '#top']  # for fast exclusion
    constraint.add_rule(lambda link: all((not link.lower().endswith(ending) for ending in forbidden_endings)))

    # Forbid every point in the last path segment as this likely is a file and we are not interested in it
    def rule_no_point_in_last_path_segment(link_parsed):
        split = link_parsed.path.split("/")
        return len(split) == 0 or "." not in split[-1]
    constraint.add_rule(rule_no_point_in_last_path_segment, parsed_link=True)

    # Start the crawler from a start domain, optionally loading already existing nodes
    from pyoogle.config import DATABASE_PATH
    path = DATABASE_PATH
    c = Crawler(path, constraint)
    c.start("http://www.math.kit.edu", clear_store=False)

    # Wait for the crawler to finish
    c.join()
    webnet = c.web_net
    logging.info("DONE, webnet contains %d nodes", len(webnet))
    return path, webnet


def crawl_spon():
    constraint = LinkConstraint('', 'www.spiegel.de')

    # Forbid every point in the last path segment as this likely is a file and we are not interested in it
    def rule_no_point_in_last_path_segment(link_parsed):
        split = link_parsed.path.split("/")
        return len(split) == 0 or ("." not in split[-1] or
                                   split[-1].lower().endswith(".html") or split[-1].lower().endswith(".htm"))

    constraint.add_rule(rule_no_point_in_last_path_segment, parsed_link=True)
    path = "/home/daniel/PycharmProjects/PageRank/spon.db"
    c = Crawler(path, constraint)
    c.start("http://www.spiegel.de", clear_store=False)

    # Wait for the crawler to finish
    c.join()
    webnet = c.web_net
    logging.info("DONE, webnet contains %d nodes", len(webnet))
    return path, webnet


if __name__ == "__main__":
    crawl_spon()
