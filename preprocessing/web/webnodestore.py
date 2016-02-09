
import sqlite3 as lite
import os


class WebNodeStore:
    _SEPARATOR = "|||||"
    _DATABASE_PATH = "webnodes.db"
    _TABLE_NAME = "WebNodes"

    def __init__(self, clear=True):
        exists = os.path.isfile(WebNodeStore._DATABASE_PATH)
        if exists and clear:
            os.remove(WebNodeStore._DATABASE_PATH)
            exists = False
        self.con = None
        self.create_db = not exists
        self.cur = None

    def _create(self):
        cur = self.con.cursor()
        cur.execute("CREATE TABLE {tn}(Id INTEGER PRIMARY KEY, Urls TEXT, Content TEXT, OutLinks TEXT, \
            Language TEXT, Importance INTEGER)".
                    format(tn=WebNodeStore._TABLE_NAME))
        cur.close()

    # TODO allow loading of webnodes and building a webnet of loaded nodes
    def save_webnodes(self, nodes):
        try:
            nodes_iter = iter(nodes)
        except TypeError:
            # Not iterable
            nodes_iter = [nodes]
        cur = self.con.cursor()
        for node in nodes_iter:
            self._save_node(cur, node)
        cur.close()

    @staticmethod
    def _save_node(cur, node):
        node_id = node.get_node_id()
        urls = WebNodeStore._SEPARATOR.join(node.get_urls())
        ctn = WebNodeStore._SEPARATOR.join(node.get_content())
        ol = WebNodeStore._SEPARATOR.join(node.get_out_links())
        l = node.get_language()
        imp = node.get_importance()

        try:
            if node_id is None:
                command = "INSERT INTO {tn} (Urls, Content, OutLinks, Language, Importance)\
                        VALUES (?, ?, ?, ?, ?)".format(tn=WebNodeStore._TABLE_NAME)
                cur.execute(command, (urls, ctn, ol, l, imp))
            else:
                command = "UPDATE {tn} SET Urls=?, Content=?, OutLinks=?, Language=?, Importance=?\
                        WHERE Id=?".format(tn=WebNodeStore._TABLE_NAME)
                cur.execute(command, (WebNodeStore._TABLE_NAME, urls, ctn, ol, l, imp, node_id))
        except lite.IntegrityError:
            print('ERROR: ID {} already exists in PRIMARY KEY column.'.format(node_id))

    def open(self):
        self.con = lite.connect(WebNodeStore._DATABASE_PATH)
        if self.create_db:
            self._create()

    def __enter__(self):
        self.open()
        return self

    def close(self):
        if self.con is not None:
            self.con.commit()
            self.con.close()
            self.con = None

    # noinspection PyUnusedLocal
    def __exit__(self, exc_type=None, exc_val=None, exc_tb=None):
        self.close()

if __name__ == "__main__":

    with WebNodeStore(False) as store:
        print("Store open, db newly created:", store.create_db)
        pass
