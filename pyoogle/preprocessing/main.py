from pyoogle.preprocessing.crawl.crawler import crawl_mathy
from pyoogle.preprocessing.web.nodestore import WebNodeStore


path, webnet = crawl_mathy()

if webnet is not None:
    from pyoogle.preprocessing.ranking.ranker import BaseRanker
    ranker = BaseRanker()
    print("Starting ranking webnet with", ranker)
    ranker.rank(webnet)
    with WebNodeStore(database_path=path) as store:
        store.save_webnodes(webnet.get_nodes())
