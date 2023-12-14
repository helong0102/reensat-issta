from configparser import ParsingError
from typing import List

from node import NodeType, Node
from scope import Scope



def link_underlying_nodes(node1: Node, node2: Node):
    node1.add_son(node2)
    node2.add_father(node1)


class Function:
    def __init__(self):
        self._counter_nodes = 0
        self.nodes = []

    def new_node(self, node_type: NodeType, src, scope, ast):
        node = Node(node_type, self._counter_nodes, scope)
        node.set_offset(src, ast) # 通过它获取节点的信息
        node.set_function(scope)
        self.nodes.append(node)
        self._counter_nodes += 1
        return node

    def build_cfg(self, cfg, ast):
        node = self.new_node(NodeType.ENTRYPOINT, cfg.get("body", None)['src'], cfg['name'], ast)
        statements = cfg.get('body', None)['statements']
        if statements:
            new_scope = Scope(node.is_checked, False, cfg['name'])
            self._parse_block(cfg['body'], node, new_scope, ast)
            self._remove_incorrect_edges()
            self._remove_alone_endif()

    def _parse_block(self, block, node, scope, ast):
        statements = block['statements']
        new_scope = scope
        for statement in statements:
            node = self._parse_statement(statement, node, new_scope, ast)
        return node

    def _parse_statement(self, statement, node, scope, ast):
        name = statement['nodeType']
        # SimpleStatement = VariableDefinition | ExpressionStatement
        if name == "IfStatement":
            node = self._parse_if(statement, node, scope, ast)
        elif name == "ExpressionStatement":
            expression = statement['expression']
            new_node = self.new_node(NodeType.EXPRESSION, statement['src'], scope, ast)
            new_node.add_unparsed_expression(expression)
            link_underlying_nodes(node, new_node)
            node = new_node
        elif name == "WhileStatement":
            node = self._parse_while(statement, node, scope, ast)
        elif name == "ForStatement":
            node = self._parse_for(statement, node, scope, ast)
        elif name == "Block":
            node = self._parse_block(statement, node, scope, ast)
        elif name == "UncheckedBlock":
            node = self._parse_unchecked_block(statement, node, scope, ast)
        elif name == "DoWhileStatement":
            node = self._parse_dowhile(statement, node, scope, ast)
        elif name == "Continue":
            continue_node = self.new_node(NodeType.CONTINUE, statement['src'], scope, ast)
            link_underlying_nodes(node, continue_node)
            node = continue_node
        elif name == "Break":
            break_node = self.new_node(NodeType.BREAK, statement["src"], scope, ast)
            link_underlying_nodes(node, break_node)
            node = break_node
        elif name == "Return":
            return_node = self.new_node(NodeType.RETURN, statement["src"], scope, ast)
            link_underlying_nodes(node, return_node)
            if statement.get("expression", None):
                return_node.add_unparsed_expression(statement['expression'])
            node = return_node
        elif name == "Throw":
            throw_node = self.new_node(NodeType.THROW, statement["src"], scope, ast)
            link_underlying_nodes(node, throw_node)
            node = throw_node
        elif name == "EmitStatement":
            expression = statement["eventCall"]
            new_node = self.new_node(NodeType.EXPRESSION, statement['src'], scope, ast)
            new_node.add_unparsed_expression(expression)
            link_underlying_nodes(node, new_node)
            node = new_node
        elif name == "RevertStatement":
            expression = statement["errorCall"]
            new_node = self.new_node(NodeType.EXPRESSION, statement["src"], scope, ast)
            new_node.add_unparsed_expression(expression)
            link_underlying_nodes(node,  new_node)
            node = new_node
        else:
            raise ParsingError(f"Statement not parsed {name}")

        return node

    def _parse_if(self, if_statement, node, scope, ast):
        falseStatement = None

        condition = if_statement["condition"]
        condition_node = self.new_node(NodeType.IF, condition['src'], scope, ast)
        condition_node.add_unparsed_expression(condition)
        link_underlying_nodes(node, condition_node)
        true_scope = Scope(node.is_checked, False, "if")
        true_statement = self._parse_statement(if_statement["trueBody"], condition_node, true_scope, ast)
        if "falseBody" in if_statement and if_statement["falseBody"]:
            false_scope = scope
            falseStatement = self._parse_statement(if_statement["falseBody"], condition_node, false_scope, ast)

        endIf_node = self.new_node(NodeType.ENDIF, if_statement['src'], scope, ast)
        link_underlying_nodes(true_statement, endIf_node)

        if falseStatement:
            link_underlying_nodes(falseStatement, endIf_node)
        else:
            link_underlying_nodes(condition_node, endIf_node)
        return endIf_node

    def _parse_while(self, while_statement, node, scope, ast):
        node_startWihle = self.new_node(NodeType.STARTLOOP,while_statement['src'], scope, ast)
        body_scope =  Scope(node.is_checked, False, "while")
        node_condition = self.new_node(NodeType.IFLOOP, while_statement['condition']['src'], scope, ast)
        node_condition.add_unparsed_expression(while_statement['condition'])
        statement = self._parse_statement(while_statement["body"], node_condition, body_scope, ast)
        node_endWhile = self.new_node(NodeType.ENDLOOP, while_statement['src'], scope, ast)
        link_underlying_nodes(node, node_startWihle)
        link_underlying_nodes(node_startWihle, node_condition)
        link_underlying_nodes(statement, node_condition)
        link_underlying_nodes(node_condition, node_endWhile)

        return node_endWhile

    def _parse_for(self, statement, node, scope, ast):
        pre, cond, post, body = self._parse_for_compact_ast(statement)

        node_startLoop = self.new_node(NodeType.STARTLOOP, statement['src'], scope, ast)
        node_endLoop = self.new_node(NodeType.ENDLOOP, statement['src'], scope, ast)
        last_scope = Scope(node.is_checked, False, "for")

        if pre:
            pre_scope = Scope(node.is_checked, False, "for")
            last_scope = pre_scope
            node_init_expression = self._parse_statement(pre, node, pre_scope, ast)
            link_underlying_nodes(node_init_expression, node_startLoop)
        else:
            link_underlying_nodes(node, node_startLoop)

        if cond:
            cond_scope = Scope(node.is_checked, False, last_scope)
            last_scope = cond_scope
            node_condition = self.new_node(NodeType.IFLOOP, cond['src'], cond_scope, ast)
            node_condition.add_unparsed_expression(cond)
            link_underlying_nodes(node_startLoop, node_condition)

            node_beforeBody = node_condition
        else:
            node_condition = None
            node_beforeBody = node_startLoop

        body_scope = Scope(node.is_checked, False, last_scope)
        last_scope = body_scope
        node_body = self._parse_statement(body, node_beforeBody, body_scope, ast)

        if post:
            node_loopexpression = self._parse_statement(post, node_body, last_scope)
            link_underlying_nodes(node_loopexpression, node_beforeBody)
        else:
            link_underlying_nodes(node_body, node_beforeBody)

        if node_condition:
            link_underlying_nodes(node_condition, node_endLoop)
        else:
            link_underlying_nodes(node_startLoop, node_endLoop)

        return node_endLoop

    def _parse_for_compact_ast(self, statement):
        body = statement['body']
        init_expression = statement.get("initializationExpression", None)
        condition = statement.get("condition", None)
        loop_expression = statement.get("loopExpression", None)

        return init_expression, condition, loop_expression, body

    def _parse_unchecked_block(self, block, node, scope, ast):
        statements = block["statements"]
        new_scope = Scope(False, False, scope)
        for statement in statements:
            node = self._parse_statement(statement, node, new_scope, ast)
        return node

    def _parse_dowhile(self, do_while_statement, node, scope, ast):
        node_startDowhile = self.new_node(NodeType.STARTLOOP, do_while_statement['src'], scope, ast)
        condition_scope = Scope(node.is_checked, False, scope)
        node_condition = self.new_node(NodeType.IFLOOP, do_while_statement['condition']['src'], condition_scope, ast)
        node_condition.add_unparsed_expression(do_while_statement['condition'])
        statement = self._parse_statement(do_while_statement['body'], node_condition, condition_scope, ast)

        body_scope = Scope(node.is_checked, False, "do_while")
        node_endDoWhile = self.new_node(NodeType.ENDLOOP, do_while_statement['src'], body_scope, ast)

        link_underlying_nodes(node, node_startDowhile)

        if not node_condition.sons:
            link_underlying_nodes(node_startDowhile, node_condition)
        else:
            link_underlying_nodes(node_startDowhile, node_condition[0])
        link_underlying_nodes(statement, node_condition)
        link_underlying_nodes(node_condition, node_endDoWhile)

        return node_endDoWhile

    def _remove_incorrect_edges(self):
        for node in self.nodes:
            if node.node_type in [NodeType.RETURN, NodeType.THROW]:
                for son in node.sons:
                    son.remove_father(node)
                node.set_sons([])
            if node.node_type in [NodeType.BREAK]:
                self._fix_break_node(node)
            if node.node_type in [NodeType.CONTINUE]:
                self._fix_continue_node(node)
            if node.node_type in [NodeType.TRY]:
                self._fix_try(node)

    def _fix_break_node(self, node):
        end_node = self._find_end_loop(node, [], 0)
        if not end_node:
            end_node = self._find_end_loop(node, [], -1)
            if not end_node:
                raise ParsingError(f"Break in no-loop context {node.function_name}")
        for son in node.sons:
            son.remove_father(node)

        node.set_sons([end_node])

    def _find_end_loop(self, node, visited, counter):
        if node in visited:
            return None

        if node.node_type == NodeType.ENDLOOP:
            if counter == 0:
                return node
            counter -= 1

        if node.node_type == NodeType.STARTLOOP:
            counter += 1

        visited = visited + [node]
        for son in node.sons:
            ret = self._find_end_loop(son, visited, counter)
            if ret:
                return ret

        return None

    def _fix_continue_node(self, node):
        start_node = self._find_start_loop(node, [])

        if not start_node:
            raise ParsingError(f"Continue in no-loop context {node.node_id}")

        for son in node.sons:
            son.remove_father(node)
        node.set_sons([start_node])
        start_node.add_father(node)

    def _find_start_loop(self, node, visited):
        if node in visited:
            return None

        if node.type == NodeType.STARTLOOP:
            return node

        visited = visited + [node]

        for father in node.fathers:
            ret = self._find_start_loop(father, visited)
            if ret:
                return ret

        return None

    def _fix_try(self, node):
        end_node = next((son for son in node.sons if son.type != NodeType.CATCH), None)
        if end_node:
            for son in node.sons:
                if son.type == NodeType.CATCH:
                    self._fix_catch(son, end_node)

    def _fix_catch(self, node, end_node):
        if not node.sons:
            link_underlying_nodes(node, end_node)
        else:
            for son in node.sons:
                if son != end_node:
                    self._fix_catch(son, end_node)

    def _remove_alone_endif(self):
        prev_nodes = []
        while set(prev_nodes) != set(self.nodes):
            prev_nodes = self.nodes
            to_remove: List[Node] = []
            for node in self.nodes:
                if node.node_type == NodeType.ENDIF and not node.fathers:
                    for son in node.sons:
                        son.remove_father(node)
                        node.set_sons([])
                        to_remove.append(node)
            self.nodes = [n for n in self.nodes if n not in to_remove]
            for remove in to_remove:
                if remove in self.nodes:
                   self.nodes.remove(remove)

                