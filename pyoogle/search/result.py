class Result:

    def __init__(self, user_query, nodes, keywords):
        self.user_query = user_query
        self.nodes = nodes
        self.keywords = keywords

    def __len__(self):
        return len(self.nodes)

    def get_node(self, index):
        return self.nodes[index]

    # noinspection PyMethodMayBeStatic
    def _get_nice_content(self, node):
        content = list(node.get_content())
        index = 0
        while index < len(content):
            line = content[index].strip()
            content[index] = " ".join(content[index].split())
            if ' ' not in line and index > 0:
                # Add single words to previous content line
                content[index - 1] += ' ' + line
                del content[index]
                # Keep index the same as we removed the entry at this index
            else:
                index += 1
        return content

    def get_context(self, index):
        node = self.nodes[index]
        node_content = self._get_nice_content(node)

        separator = " "
        chars_delta = 80
        content = separator.join(node_content)
        if len(content) == 0:
            return ''
        content_index = -1
        for word in self.keywords:
            content_index = content.lower().find(word.lower())
            if content_index >= 0:
                break
        if content_index == -1:
            # Did not find any keyword in content, so simply get first content line (after title) or nothing
            if len(node_content) > 1:
                return node_content[1]
            return ''
        start_index = max(content_index - chars_delta, 0)
        end_index = min(len(content), content_index + chars_delta)
        prefix = ''
        if start_index > 0:
            prefix = "..."
        return prefix + content[start_index:end_index]
