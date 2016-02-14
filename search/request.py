from urllib.parse import urlparse
from preprocessing.web.nodestore import VALID_KEYWORDS
from search.result import Result


class Request:
    def __init__(self, node_store):
        self.node_store = node_store
        self.language = None
        self.start_url = None
        self.result = None
        self.keywords = []
        self.keyword_joins = []

    def set_language(self, language):
        if language is None:
            language = ''
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
        self.keywords = query.split()
        self._parse_query_keyword_parameter("lang:", self.set_language)
        self._parse_query_keyword_parameter("site:", self.set_start_url)
        self._parse_keyword_joins()

    def _parse_query_keyword_parameter(self, keyword, callback):
        for index, word in enumerate(self.keywords):
            if word.startswith(keyword):
                if callback(word[len(keyword):]):
                    del self.keywords[index]
                    break

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
        query_nodes = self.node_store.query(self.keywords, self.keyword_joins, self.language, self.start_url)

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
                                                            lambda param_node: param_node.get_title())
            for count in sorted(count_to_nodes.keys(), reverse=True):
                for node in count_to_nodes[count]:
                    nodes.append(node)
        return Result(query, nodes, self.keywords)

    def _parse_keyword_joins(self):
        self.keyword_joins = []
        join_possible = False
        index = 0
        while index < len(self.keywords):
            word = self.keywords[index]
            if word in VALID_KEYWORDS:
                del self.keywords[index]
                if join_possible:
                    join_possible = False
                    self.keyword_joins.append(word)
                    # Keep index as we removed the one with the same index
                else:
                    index += 1
                    # Remove keyword and proceed
            else:
                if join_possible:
                    self.keyword_joins.append(None)
                join_possible = True
                index += 1


if __name__ == "__main__":
    from preprocessing.web.nodestore import WebNodeStore
    with WebNodeStore("/home/daniel/PycharmProjects/PageRank/webnodes.db") as store:
        request = Request(store)
        result = request.execute("IWRMM lang:de")
        for index in range(0, len(result)):
            print(result.get_context(index))