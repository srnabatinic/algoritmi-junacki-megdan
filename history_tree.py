from game_state import GameState

class HistoryNode:
    def __init__(self, state: GameState):
        self.state = state
        self.children = []
        self.parent = None

    def add_child(self, node: 'HistoryNode'):
        node.parent = self
        self.children.append(node)
        return node


class HistoryTree:
    def __init__(self, initial_state: GameState):
        self.root = HistoryNode(initial_state)
        self.current_node = self.root

    def add_move(self, state: GameState) -> HistoryNode:
        new_node = HistoryNode(state)
        self.current_node.add_child(new_node)
        self.current_node = new_node
        return new_node

    def undo(self):
        if self.current_node.parent is not None:
            self.current_node = self.current_node.parent

    def get_full_history(self):
        """DFS obilazak - vraca sve putanje od korena do listova."""
        paths = []
        self._dfs(self.root, [], paths)
        return paths

    def _dfs(self, node, current_path, paths):
        current_path = current_path + [node.state]
        if not node.children:
            paths.append(current_path)
        for child in node.children:
            self._dfs(child, current_path, paths)