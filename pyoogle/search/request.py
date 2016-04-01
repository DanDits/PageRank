from urllib.parse import urlparse

from pyoogle.search.result import Result
import pyoogle.search.parse as parse


class Request:
    def __init__(self, node_store):
        self.node_store = node_store
        self.language = None
        self.start_url = None
        self.result = None
        self.request_tree = None

    def set_language(self, language):
        if language is None:
            language = ''
        print("Setting language to", language)
        self.language = language
        return True

    def set_start_url(self, start_url, scheme=''):
        if start_url is None or len(start_url) == 0:
            self.start_url = ''
            return True
        if start_url.startswith("www") and scheme != '':
            # would parse a valid url anyways (rfc conform) but with three backslashes which is not expected of store
            start_url = "//" + start_url
        self.start_url = urlparse(start_url, scheme).geturl()
        return True

    def _parse(self, query):
        tokens = query.split()
        parse.extract_keyword_parameter(tokens, "lang:", self.set_language)
        parse.extract_keyword_parameter(tokens, "site:", self.set_start_url)
        self.keywords, self.request_tree = parse.make_keywords_tree(" ".join(tokens))

    def _calculate_count_to_nodes(self, nodes, node_text_callback):
        count_to_nodes = {}
        for node in nodes:
            count = 0
            for keyword in self.keywords:
                # Do not take the amount of occurrences of a single keyword into account!
                if node_text_callback(node).lower().count(keyword.lower()) > 0:
                    count += 1
            nodes = count_to_nodes.get(count)
            if nodes is None:
                nodes = []
                count_to_nodes[count] = nodes
            nodes.append(node)
        return count_to_nodes

    def execute(self, query):
        self._parse(query)
        # Use the user query string to query the store, returns a list sorted descending by importance value
        query_nodes = self.node_store.query(self.request_tree, self.language, self.start_url)
        if query_nodes is None:
            raise ValueError("Joining parameters (AND/OR/NOT) in query misplaced:", query)

        # prioritize if keyword occurrence count in title, the more the better, if equal amount use importance
        count_to_nodes = self._calculate_count_to_nodes(query_nodes, lambda param_node: param_node.get_title())

        nodes = []
        for count in sorted(count_to_nodes.keys(), reverse=True):
            if count > 0:
                for node in count_to_nodes[count]:
                    nodes.append(node)

        nothing_in_title_nodes = count_to_nodes.get(0)
        if nothing_in_title_nodes is not None:
            # if not in title check keyword occurrence count in content, the more the better,
            # if equal amount use importance
            count_to_nodes = self._calculate_count_to_nodes(nothing_in_title_nodes,
                                                            lambda param_node: " ".join(param_node.get_content()))
            for count in sorted(count_to_nodes.keys(), reverse=True):
                for node in count_to_nodes[count]:
                    nodes.append(node)
        return Result(query, nodes, self.keywords)


if __name__ == "__main__":
    from pyoogle.preprocessing.web.nodestore import WebNodeStore
    from config import DATABASE_PATH
    with WebNodeStore(DATABASE_PATH) as store:
        request = Request(store)
        result = request.execute("IWRMM lang:de")
        for i in range(0, len(result)):
            print(result.get_context(i))
