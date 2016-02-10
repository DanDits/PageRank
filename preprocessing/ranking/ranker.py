from scipy.sparse import lil_matrix


class Ranker:
    def __init__(self):
        self.webnet = None
        self.id_to_index = None
        self.index_to_id = None
        self.matrix = None

    def rank(self, webnet):
        self.webnet = webnet
        self._init_mappings()
        self._build_matrix()

    def _init_mappings(self):
        self.index_to_id = []
        self.id_to_index = {}
        for index, node in enumerate(self.webnet):
            node_id = node.get_node_id()
            self.id_to_index[node_id] = index
            self.index_to_id[index] = node_id

    def _build_matrix(self):
        self.matrix = None
        nodes_count = len(self.webnet)
        M = lil_matrix((nodes_count, nodes_count))
        for index, node in enumerate(self.webnet):
            pass #TODO implement

        return M.tocsr()