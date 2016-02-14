

class WebNet:
    def __init__(self):
        self.nodes = []  # All nodes
        self.url_to_nodes = {}  # Maps urls to nodes, can contain nodes multiple times
        self._all_nodes_have_id = True  # True if all nodes have a valid not None id

    def __len__(self):
        return len(self.nodes)

    def __iter__(self):
        return iter(self.get_nodes())

    def get_nodes(self):
        return self.nodes

    def all_nodes_have_id(self):
        return self._all_nodes_have_id

    def add_node(self, webnode):
        given_has_id = webnode.get_node_id() is not None
        if self._all_nodes_have_id and not given_has_id:
            self._all_nodes_have_id = False
        self.nodes.append(webnode)
        self.url_to_nodes[webnode.get_urls()[0]] = webnode

    def get_by_content_hash(self, content_hash):
        for node in self.nodes:
            if node.get_content_hash() == content_hash:
                return node

    def get_by_url(self, url):
        if url is None:
            return
        node = self.url_to_nodes.get(url)
        if node is not None:
            return node
        # Now brute force search
        for node in self.get_nodes():
            if url in node.get_urls():
                # Map url to node (maybe it is common)
                self.url_to_nodes[url] = node
                return node

    def refresh(self):
        self._all_nodes_have_id = True
        for node in self.nodes:
            if node.get_node_id() is None:
                self._all_nodes_have_id = False
                break
