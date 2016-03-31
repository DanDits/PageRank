import numpy as np
from scipy.sparse import lil_matrix


class BaseRanker:
    def __init__(self):
        self.webnet = None
        self.id_to_index = None
        self.matrix = None
        self.importances = None

    def rank(self, webnet, eps=1e-8, max_iter=100):
        if not webnet.all_nodes_have_id():
            raise ValueError("Cannot rank webnet where not all nodes have a valid id.")
        if len(webnet) == 0:
            print("Nothing to rank!")
            return  # We ranked all in net perfectly!
        self.webnet = webnet
        self._init_mapping()
        self._build_matrix()
        self._calculate_importances(eps=eps, max_iter=max_iter)
        self._apply_importances()

    def _init_mapping(self):
        self.id_to_index = {}
        for index, node in enumerate(self.webnet):
            node_id = node.get_node_id()
            self.id_to_index[node_id] = index

    def _build_matrix(self):
        # Build adjacency matrix for the WebNet graph where a WebNode is a node and an out going url is an edge
        # and normalize so that we get the probability matrix to travel to a random adjacent node.
        self.matrix = None
        nodes_count = len(self.webnet)
        # noinspection PyPep8Naming
        M = lil_matrix((nodes_count, nodes_count))
        rows_without_out_links = []
        for index, node in enumerate(self.webnet):
            out_links = node.get_out_links()
            if out_links is not None:
                out_count = 0
                for out_link in out_links:
                    out_node = self.webnet.get_by_url(out_link)
                    if out_node is not None:
                        out_id = out_node.get_node_id()
                        M[index, self.id_to_index[out_id]] = 1
                        out_count += 1
                if out_count > 0:
                    M[index, :] /= out_count
                else:
                    rows_without_out_links.append(index)

        # In case some nodes do not have any edges there is a zero row in the matrix which we do not want.
        # Therefore teleport to a random node by filling this row with ones
        for row in rows_without_out_links:
            M[row, :] = 1. / nodes_count

        # Ultimately we want to have the edge values for a node in a column, but it was cheaper to build
        # the lil-matrix row based.
        self.matrix = M.tocsr().transpose()

    def _calculate_importances(self, eps, max_iter):
        # Calculate greatest eigenvalue of matrix using the power method.
        # In each step ensure that the current (probability!) distribution x is normalized in the sum (1) norm.
        self.importances = None
        n = self.matrix.shape[1]
        x = np.ones((n, 1)) / n  # Normalized start vector with equally distributed importances
        print("Calculating importances for size", n)
        for index in range(0, max_iter):
            next_x = self._power_method_step(x)
            # noinspection PyTypeChecker
            norm_next_x = np.linalg.norm(next_x, 1)
            if norm_next_x < eps:
                break  # Matrix singular and we go towards null vector, better stop!
            next_x /= norm_next_x
            diff = np.linalg.norm(x - next_x)
            x = next_x
            if diff < eps:
                print("Converged at step", index, "with eps=", eps)
                break  # Converged, stop
        self.importances = x

    def _power_method_step(self, x):
        return self.matrix.dot(x)

    def _apply_importances(self):
        for node in self.webnet:
            node.set_importance(self.importances[self.id_to_index[node.get_node_id()], 0])


class TeleportRanker(BaseRanker):

    def __init__(self, teleport_prop=0.):
        super().__init__()
        self.teleport_prop = min(1., max(0., teleport_prop))
        self._matrix_size = 1

    # noinspection PyUnresolvedReferences
    def _build_matrix(self):
        super()._build_matrix()
        if self.teleport_prop > 0.:
            self._matrix_size = self.matrix.shape[0]  # Matrix is square

    def _power_method_step(self, x):
        next_x = super()._power_method_step(x)
        if self.teleport_prop > 0.:
            # The teleport matrix the ones((k, k)) matrix scaled by (self.teleport_prop / k)
            # where k = self._matrix_size.
            # We do not compute this full rank 1 matrix for performance reasons and use the fact that
            # norm(x,1)=sum(x)=1
            next_x = (1. - self.teleport_prop) * next_x + self.teleport_prop / self._matrix_size
        return next_x


if __name__ == "__main__":
    ranker = TeleportRanker(0.1)
    print("Starting ranking webnet.")
    from pyoogle.preprocessing.web.nodestore import WebNodeStore
    from pyoogle.preprocessing.web.net import WebNet
    from config import DATABASE_PATH
    with WebNodeStore(database_path=DATABASE_PATH) as store:
        loaded_webnet = WebNet()
        for loaded_node in store.load_webnodes(load_content=False):
            loaded_webnet.add_node(loaded_node)
        ranker.rank(loaded_webnet)
        store.save_webnodes(loaded_webnet.get_nodes())