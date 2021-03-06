import re
import webbrowser
import time

from PyQt4 import QtGui
from PyQt4 import uic
from PyQt4.QtGui import QStandardItem
from PyQt4.QtGui import QStandardItemModel

from pyoogle.preprocessing.web.nodestore import WebNodeStore
from pyoogle.search.request import Request

Ui_MainWindow, WindowBaseClass = uic.loadUiType("main_window.ui")


class MyDialog(WindowBaseClass, Ui_MainWindow):
    def __init__(self, store, parent=None):
        WindowBaseClass.__init__(self, parent)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        self.text_store.setText(store.get_path_name())
        self.request = Request(store)
        self.list_language.setCurrentIndex(self.list_language.model().index(2))
        self.max_results = 20
        self.result = None

    def node_selected(self, model_index):
        index = model_index.row()
        if self.result is None or index >= len(self.result):
            return
        node = self.result.get_node(index)
        webbrowser.open(node.get_urls()[0])

    def start_search(self):
        start_time = time.time()
        try:
            self.result = self.request.execute(self.text_query.text())
        except ValueError:
            self.show_query_error()
            self.result = None
            return
        if self.result is None or len(self.result) == 0:
            self.show_no_results()
            return
        self.show_result(time.time() - start_time)

    def show_no_results(self):
        self.set_results_heading_text("Keine Ergebnisse. Versuche es mit einfachen Stichwörtern "
                                      "getrennt durch Leerzeichen.")
        self.list_results.hide()

    def show_query_error(self):
        self.set_results_heading_text("Verbindungswörter (AND/OR/NOT) in Suche falsch gesetzt.")
        self.list_results.hide()

    def set_results_heading_text(self, text):
        self.text_results_heading.setText(text)

    def show_result(self, search_time):
        self.set_results_heading_text("{} Ergebnisse in {:.2f} Sekunden".format(len(self.result), search_time))
        result = self.result
        model = QStandardItemModel(self.list_results)
        for index in range(min(len(result), self.max_results)):
            node = result.get_node(index)
            context = result.get_context(index)
            item_text = [str(index + 1) + ". " + node.get_title(),
                         node.get_urls()[0],
                         "\t" + context]
            item = QStandardItem("\n".join(item_text))
            model.appendRow(item)
        self.list_results.setModel(model)
        self.list_results.show()

    def set_start_url(self, text):
        self.request.set_start_url(text)

    def update_language(self):
        item = self.list_language.currentItem()
        if item is None:
            return
        lang = ''
        index = self.list_language.currentRow()
        if index == 1:
            lang = item.text()  # Custom language
        elif index > 0:
            # Extract language shortcut from text, so "de" from "Deutsch(de)"
            # Capture all expressions in brackets but only retrieve the one inside the last one
            lang = re.findall(".*(\(.+\))", item.text())
            lang = lang[-1]
            lang = lang[1:-1]
        self.request.set_language(lang)


def create_and_run(database_path):
    app = QtGui.QApplication([])
    with WebNodeStore(database_path) as store:
        dialog = MyDialog(store)
        dialog.show()
        app.exec_()

if __name__ == "__main__":
    from pyoogle.config import DATABASE_PATH
    create_and_run(DATABASE_PATH)