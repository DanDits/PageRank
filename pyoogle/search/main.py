from pyoogle.preprocessing.web.nodestore import WebNodeStore

from pyoogle.search.request import Request
from config import DATABASE_PATH


def safe_to_int(text, default_value):
    try:
        return int(text)
    except ValueError:
        return default_value


def search(store, query, language, starturl, max_output):
    request = Request(store)
    request.set_language(language)
    request.set_start_url(starturl)
    result = request.execute(query)
    print("Exactly", len(result), "results for", "'" + query + "'", "[lang:", language, ", url:", starturl + "]")
    for index in range(0, min(len(result), max_output)):
        print(str(index + 1) + ".", result.get_node(index).get_title())
        print(result.get_node(index).get_urls()[0])
        print("\t" + result.get_context(index))
        print("\n")


def start(database_path=DATABASE_PATH):

    command = ''
    max_output = 10
    language = ''
    starturl = ''
    with WebNodeStore(database_path) as store:
        while command != 'E':
            try:
                command = input("Enter command: E(xit), S(earch:) text, M(ax output:) number,"
                                " L(anguage:) text, W(ebsite:) url\n>>")
            except KeyboardInterrupt:
                command = 'E'
            if command.startswith('S '):
                print("Hint: in query use 'lang:de site:www.math.kit.edu/lehre' to only show german results "
                      "and from the given domain\n\tUse 'AND'/'OR' to connect keywords")
                search(store, command[2:], language, starturl, max_output)
            elif command.startswith('M '):
                max_output = safe_to_int(command[2:], max_output)
            elif command.startswith('L '):
                language = command[2:]
            elif command.startswith('W '):
                starturl = command[2:]
            elif command == 'E':
                print("\nThank you for trying Pyoogle! Come back anytime")

if __name__ == "__main__":
    start()