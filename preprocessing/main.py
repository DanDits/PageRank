import preprocessing.crawl.crawler as cr
from preprocessing.web.nodestore import WebNodeStore


path, webnet = cr.crawl_mathy()

if webnet is not None and webnet.all_nodes_have_id():
    from preprocessing.ranking.ranker import BaseRanker
    ranker = BaseRanker()
    print("Starting ranking webnet.")
    ranker.rank(webnet)
    with WebNodeStore(database_path=path, clear=False) as store:
        store.save_webnodes(webnet.get_nodes())
