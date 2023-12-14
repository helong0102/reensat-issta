import re
from enum import Enum
from typing import List

from source_node import Source


class NodeType(Enum):
    ENTRYPOINT = "ENTRY_POINT"  # no expression

    # Nodes that may have an expression

    EXPRESSION = "EXPRESSION"  # normal case
    RETURN = "RETURN"  # RETURN may contain an expression
    IF = "IF"
    VARIABLE = "NEW VARIABLE"  # Variable declaration
    ASSEMBLY = "INLINE ASM"
    IFLOOP = "IF_LOOP"

    # Nodes where control flow merges
    # Can have phi IR operation
    ENDIF = "END_IF"  # ENDIF node source mapping points to the if/else "body"
    STARTLOOP = "BEGIN_LOOP"  # STARTLOOP node source mapping points to the entire loop "body"
    ENDLOOP = "END_LOOP"  # ENDLOOP node source mapping points to the entire loop "body"

    # Below the nodes do not have an expression but are used to expression CFG structure.

    # Absorbing node
    THROW = "THROW"

    # Loop related nodes
    BREAK = "BREAK"
    CONTINUE = "CONTINUE"

    # Only modifier node
    PLACEHOLDER = "_"

    TRY = "TRY"
    CATCH = "CATCH"

    # Node not related to the CFG
    # Use for state variable declaration
    OTHER_ENTRYPOINT = "OTHER_ENTRYPOINT"

    # 定义fallback block 类型
    FALLBACK = "FALLBACK"

    def __str__(self):
        if self == NodeType.ENTRYPOINT:
            return "ENTRY_POINT"
        if self == NodeType.EXPRESSION:
            return "EXPRESSION"
        if self == NodeType.RETURN:
            return "RETURN"
        if self == NodeType.IF:
            return "IF"
        if self == NodeType.VARIABLE:
            return "NEW VARIABLE"
        if self == NodeType.ASSEMBLY:
            return "INLINE ASM"
        if self == NodeType.IFLOOP:
            return "IF_LOOP"
        if self == NodeType.THROW:
            return "THROW"
        if self == NodeType.BREAK:
            return "BREAK"
        if self == NodeType.CONTINUE:
            return "CONTINUE"
        if self == NodeType.PLACEHOLDER:
            return "_"
        if self == NodeType.TRY:
            return "TRY"
        if self == NodeType.CATCH:
            return "CATCH"
        if self == NodeType.ENDIF:
            return "END_IF"
        if self == NodeType.STARTLOOP:
            return "BEGIN_LOOP"
        if self == NodeType.ENDLOOP:
            return "END_LOOP"
        if self == NodeType.OTHER_ENTRYPOINT:
            return "OTHER_ENTRYPOINT"
        if self == NodeType.FALLBACK:
            return "FALLBACK"
        return f"Unknown type {hex(self.value)}"

class Node:

    def __init__(self, node_type, node_id, scope):
        self.unparsed_expression = None
        self.node_type = node_type
        self.node_id = node_id
        self.scope = scope
        self.function_name = None
        self.is_checked = False
        self.sons: List["Node"] = []
        self.fathers: List["Node"] = []
        self.source = Source()
        self.abstract_nodes = []

    def set_offset(self, src, ast):
        position = re.findall("([0-9]*):([0-9]*):([-]?[0-9]*)", src)
        s ,l ,f = position[0]
        s = int(s)
        l = int(l)
        f = int(f)

        new_source = Source()
        new_source.start = s
        new_source.end  = f
        new_source.len = l
        self.source = new_source

        return new_source

    def set_function(self, scope):
        self.function_name = scope

    def add_unparsed_expression(self, expression):
        assert self.unparsed_expression is None
        self.unparsed_expression = expression

    def add_son(self, son: "Node"):
        self.sons.append(son)

    def add_father(self, father: "Node"):
        self.fathers.append(father)

    def remove_father(self, father: "Node"):
        self.fathers = [x for x in self.fathers if x.node_id != father.node_id]

    def set_sons(self, sons: List["Node"]):
        self.sons = sons