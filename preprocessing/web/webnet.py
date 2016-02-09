

class WebNet:
    def __init__(self):
        self.hash_to_nodes = {}  # Maps each node's hash to the node
        self.url_to_nodes = {}  # Maps urls to nodes, can contain nodes multiple times

    def __len__(self):
        return len(self.hash_to_nodes)

    def __iter__(self):
        return iter(self.get_nodes())

    def get_nodes(self):
        return self.hash_to_nodes.values()

    def add_node(self, webnode):
        self.hash_to_nodes[hash(webnode)] = webnode
        self.url_to_nodes[webnode.get_urls()[0]] = webnode

    def node_add_url(self, node_hash, link):
        if link is None:
            return
        node = self.hash_to_nodes[node_hash]
        node.add_url(link)

    def get_by_url(self, url):
        node = self.url_to_nodes.get(url)
        if node is not None:
            return node
        # Now brute force search
        for node in self.get_nodes():
            if url in node.get_urls():
                # Map url to node (maybe it is common)
                self.url_to_nodes[url] = node
                return node
