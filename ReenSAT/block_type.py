from enum import Enum


class ANodeType(Enum):
    BRANCH_BLOCK = "BRANCH_BLOCK"
    TRANSFER_BLOCK = "TRANSFER_BLOCK"
    FALLBACK_BLOCK = "FALLBACK_BLOCK"
    CHECK_BLOCK = "CHECK_BLOCK"
    STATE_BLOCK = "STATE_BLOCK"
    BASIC_BLOCK = "BASIC_BLOCK"

    def __str__(self):
        if self == ANodeType.BRANCH_BLOCK:
            return "BRANCH_BLOCK"
        if self == ANodeType.TRANSFER_BLOCK:
            return "TRANSFER_BLOCK"
        if self == ANodeType.FALLBACK_BLOCK:
            return "FALLBACK_BLOCK"
        if self == ANodeType.CHECK_BLOCK:
            return "CHECK_BLOCK"
        if self == ANodeType.STATE_BLOCK:
            return "STATE_BLOCK"
        if self == ANodeType.BASIC_BLOCK:
            return "BASIC_BLOCK"
        return f"Unknown type {hex(self.value)}"

class ANode:
    def __init__(self, anode_type):
        self.anode_type = anode_type
        self.variable_names = []
