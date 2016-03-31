
import sqlite3 as lite
import os

from .node import WebNode


VALID_KEYWORDS = ("OR", "AND", "NOT")


class WebNodeStore:
    _SEPARATOR = "<=_|_=>"
    _TABLE_NAME = "WebNodes"

    def __init__(self, database_path, clear=False):
        self.database_path = database_path
        exists = os.path.isfile(self.database_path)
        if exists and clear:
            os.remove(self.database_path)
            exists = False
        self.con = None
        self.create_db = not exists
        self.cur = None

    def _create(self):
        cur = self.con.cursor()
        cur.execute("CREATE TABLE {tn}(Id INTEGER PRIMARY KEY, Urls TEXT, Content TEXT, OutLinks TEXT, \
            Language TEXT, Importance INTEGER, Title TEXT)".
                    format(tn=WebNodeStore._TABLE_NAME))
        cur.close()

    def query(self, request_tree, language=None, start_url=None):
        with DictCursor(self.con) as cur:
            nodes = []
            where_clause = ' WHERE'
            use_where = False
            where_parameters = []
            where_join_word = ' '
            if language is not None and len(language) > 0:
                use_where = True
                where_clause += where_join_word + "Language like ?"
                where_parameters.append("%" + language + "%")
                where_join_word = " AND "
            if start_url is not None and len(start_url) > 0:
                use_where = True
                where_clause += where_join_word + "Urls like ?"
                where_parameters.append("%" + start_url + "%")
                where_join_word = " AND "
            if request_tree is not None and len(request_tree) > 0:
                use_where = True
                where_clause += where_join_word
                where_join_words = []

                def get_where_join(join_words):
                    count = len(join_words)
                    if count == 0 or count > 2:
                        return "OR"  # default
                    if count == 1:
                        if join_words[0] == "NOT":
                            return "AND NOT"
                        return join_words[0]
                    if count == 2:
                        result = " ".join(join_words)
                        if result == "AND NOT" or result == "OR NOT":
                            return result
                        return "OR"  # default

                def tree_to_where_clause(curr, needs_join):
                    nonlocal where_join_words
                    nonlocal where_clause
                    if isinstance(curr, list):
                        if needs_join:
                            where_clause += " " + get_where_join(where_join_words) + " "
                        where_clause += "("
                        where_join_words = []
                        for index, child in enumerate(curr):
                            tree_to_where_clause(child, index > 0)
                        where_clause += ")"
                    else:
                        if curr in VALID_KEYWORDS:
                            where_join_words.append(curr)
                        else:
                            if needs_join:
                                where_clause += " " + get_where_join(where_join_words) + " "
                            where_clause += "(Content like ? OR Title like ?)"
                            where_join_words = []
                            where_parameters.append("%" + curr + "%")
                            where_parameters.append("%" + curr + "%")
                tree_to_where_clause(request_tree, False)
                # noinspection PyUnusedLocal
                where_join_word = " AND "
            if not use_where:
                where_clause = ''

            command = "SELECT * from {tn}" + where_clause + " ORDER BY Importance Desc"
            print("Executing command", command, " with parameters", where_parameters)
            cur.execute(command.format(tn=WebNodeStore._TABLE_NAME), tuple(where_parameters))
            for row in cur.fetchall():
                nodes.append(WebNodeStore._build_node(row, True))
            return nodes

    def load_webnodes(self, load_content=True):
        with DictCursor(self.con) as cur:
            nodes = []
            if load_content:
                command = "SELECT * from {tn}"
            else:
                command = "SELECT Id, Urls, OutLinks, Language, Importance, Title from {tn}"
            cur.execute(command.format(tn=WebNodeStore._TABLE_NAME))
            for row in cur.fetchall():
                nodes.append(WebNodeStore._build_node(row, load_content))
            return nodes

    @staticmethod
    def _build_node(row, load_content):
        builder = WebNode.Builder(link_constraint=None,
                                  language=row["Language"], importance=row["Importance"], node_id=row["Id"],
                                  title=row["Title"])
        builder.urls = row["Urls"].split(WebNodeStore._SEPARATOR)
        if load_content:
            builder.content = row["Content"].split(WebNodeStore._SEPARATOR)
        builder.out_links = row["OutLinks"].split(WebNodeStore._SEPARATOR)
        return builder.make_node()

    def save_webnodes(self, nodes):
        try:
            nodes_iter = iter(nodes)
        except TypeError:
            # Not iterable, maybe a single node
            nodes_iter = [nodes]
        cur = self.con.cursor()
        for node in nodes_iter:
            self._save_node(cur, node)
        cur.close()

    @staticmethod
    def _save_node(cur, node):
        node_id = node.get_node_id()
        urls = WebNodeStore._SEPARATOR.join(node.get_urls())
        ctn = node.get_content()
        if ctn is not None:
            ctn = WebNodeStore._SEPARATOR.join(ctn)
        ol = WebNodeStore._SEPARATOR.join(node.get_out_links())
        l = node.get_language()
        imp = node.get_importance()
        title = node.get_title()
        # Insert or update depending on if there already is a valid id
        #  and only update content if valid
        try:
            if node_id is None:
                command = "INSERT INTO {tn} (Urls, Content, OutLinks, Language, Importance, Title)\
                        VALUES (?, ?, ?, ?, ?, ?)".format(tn=WebNodeStore._TABLE_NAME)
                cur.execute(command, (urls, ctn, ol, l, imp, title))
                node.set_node_id(cur.lastrowid)
            else:
                if ctn is None:
                    command = "UPDATE {tn} SET Urls=?, OutLinks=?, Language=?, Importance=?, Title=?\
                            WHERE Id=?".format(tn=WebNodeStore._TABLE_NAME)
                    cur.execute(command, (urls, ol, l, imp, title, node_id))
                else:
                    command = "UPDATE {tn} SET Urls=?, Content=?, OutLinks=?, Language=?, Importance=?, Title=?\
                            WHERE Id=?".format(tn=WebNodeStore._TABLE_NAME)
                    cur.execute(command, (urls, ctn, ol, l, imp, title, node_id))
        except lite.IntegrityError:
            print('ERROR: ID {} already exists in PRIMARY KEY column.'.format(node_id))

    def open(self):
        self.con = lite.connect(self.database_path)
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


# Handles closing of the cursor and allows accessing columns by named indices
class DictCursor:
    def __init__(self, con):
        self._old_factory = None
        self._con = con
        self._cur = None

    def __enter__(self):
        self._old_factory = self._con.row_factory
        self._con.row_factory = lite.Row  # Dictionary cursor
        self._cur = self._con.cursor()
        return self._cur

    # noinspection PyUnusedLocal
    def __exit__(self, exc_type=None, exc_val=None, exc_tb=None):
        self._cur.close()
        self._con.row_factory = self._old_factory
