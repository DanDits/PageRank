from PyQt4 import uic
from PyQt4 import QtGui
from PyQt4.QtGui import QStandardItemModel
from PyQt4.QtGui import QStandardItem

from pyoogle.preprocessing.web.nodestore import WebNodeStore
from pyoogle.search.request import Request
import re


Ui_MainWindow, WindowBaseClass = uic.loadUiType("main_window.ui")


class MyDialog(WindowBaseClass, Ui_MainWindow):
    def __init__(self, store, parent=None):
        WindowBaseClass.__init__(self, parent)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        self.request = Request(store)
        self.max_results = 20

    def start_search(self):
        print("Starting search", self.text_query.text())
        result = self.request.execute(self.text_query.text())
        self.show_result(result)

    def show_result(self, result):
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
    from config import DATABASE_PATH
    create_and_run(DATABASE_PATH)