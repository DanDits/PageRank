from pyoogle.preprocessing.web.nodestore import VALID_KEYWORDS as JOIN_WORDS


def extract_keyword_parameter(tokens, keyword, callback):
    for index, token in enumerate(tokens):
        if token.startswith(keyword):
            if callback(token[len(keyword):]):
                del tokens[index]
                break


def _extract_tokens(raw_tokens):
    # Since brackets do not need to be separated from keywords with whitespace, we need to extract them
    # here we only check if opening brackets are prepended or if closing brackets are appended to the tokens
    tokens = []
    for token in raw_tokens:
        while len(token) > 1 and token.startswith("("):
            tokens.append("(")
            token = token[1:]
        post_token = []
        while len(token) > 1 and token.endswith(")"):
            post_token.append(")")
            token = token[:-1]
        tokens.append(token)
        tokens.extend(post_token)
    return tokens


def _resolve_tree(tree, index_stack):
    curr = tree
    for index in index_stack[:-1]:
        curr = curr[index]
    return curr


def make_keywords_tree(query):
    # First extract all tokens, that are user keywords, single brackets and join words
    tokens = _extract_tokens(query.split())
    # Build tree, be generous with grammar mistakes and ignore them
    tree = []
    curr_tree = tree
    keywords = set()  # holds all keywords that are not joining words
    index_stack = [0]
    depth = 0

    for token in tokens:
        if token == "(":
            depth += 1
            curr_tree.append(list())
            index_stack.append(0)
            curr_tree = _resolve_tree(tree, index_stack)

        elif token == ")" and depth > 0:
            depth -= 1
            index_stack.pop()
            index_stack[-1] += 1
            curr_tree = _resolve_tree(tree, index_stack)

        else:
            curr_tree.append(token)
            index_stack[-1] += 1

            if token not in JOIN_WORDS:
                keywords.add(token)

    return keywords, tree

if __name__ == "__main__":
    test_query = ") (NOT (this) Hi AND (HI OR What)) Bla (What is this) ((("
    test_keywords, test_tree = make_keywords_tree(test_query)
    print(test_keywords)
    print(test_tree)
