from .crawl.crawler import crawl_mathy
from .web.nodestore import WebNodeStore


path, webnet = crawl_mathy()

if webnet is not None and webnet.all_nodes_have_id():
    from pyoogle.preprocessing.ranking.ranker import BaseRanker
    ranker = BaseRanker()
    print("Starting ranking webnet.")
    ranker.rank(webnet)
    with WebNodeStore(database_path=path) as store:
        store.save_webnodes(webnet.get_nodes())
