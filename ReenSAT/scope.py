from typing import List

from node import Node


class Scope:
    def __init__(self, is_checked, is_yul, scope):
        self.nodes: List["Node"] = []
        self.is_checked = is_checked
        self.is_yul = is_yul
        self.father = scope
