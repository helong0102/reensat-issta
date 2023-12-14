from crytic_compile import compile_all

from ast_walker import AstWalker
from block_type import ANodeType, ANode
from funciton import Function, link_underlying_nodes
from node import NodeType
from utils import contains_any_substring, get_sat_result_by_cnf, get_content_by_src, get_function_name_and_arguments, \
    change_first_line_clause_numbers, generate_binary_strings_with_spaces, sat_by_one_case


def get_function_body(input):
    matches = ['call.value', 'transferFrom']
    matched = []
    # 1. 定位调用关系，与转账操作对应的调用关系
    for call_function in input['source_map'].func_call_names:
        # 判断调用关系里面是否有call.value方法，以及transferFrom方法
        if contains_any_substring(call_function, matches):
            matched.append(call_function)
    # 2. 获取函数代码块。
    node = input['source_map'].ast_helper.contracts["contractsByName"][input['contract']]
    walker = AstWalker()
    func_def_nodes = []
    walker.walk(node, {"name":  "FunctionDefinition"}, func_def_nodes)
    func_body_contents = []
    func_node_and_bodys = []
    for func_def_node in func_def_nodes:
        src = func_def_node['src'].split(":")
        start = int(src[0])
        end = start + int(src[1])
        func_body_contents.append(input['source_map'].source.content[start:end])
        for match in matched:
            lines = input['source_map'].source.content[start:end].split("\n")
            for line in lines:
                if match in line.strip():
                    temp = {}
                    temp['AST'] = func_def_node
                    temp['body'] = input['source_map'].source.content[start:end]
                    func_node_and_bodys.append(temp)
                    break
    if func_body_contents:
        return func_node_and_bodys, matched
    return None, matched


def new_anode(node_type):
    anode = ANode(node_type)
    return anode


def parse_variables(node, source_code, call_function_names):
    pass
    body = node.unparsed_expression
    # 1. 判断nodeType属性
    if body['nodeType'] == 'BinaryOperation':
        anode = new_anode(ANodeType.CHECK_BLOCK)
        # 2. 获取left的变量名
        variable_name = get_content_by_src(source_code, body['leftExpression']['src'])
        anode.variable_names.append(variable_name)
        node.abstract_nodes.append(anode)
    if body['nodeType'] == 'Assignment':
        anode = new_anode(ANodeType.STATE_BLOCK)
        # 2. 获取赋值操作左边表达式的变量名
        variable_name = get_content_by_src(source_code, body['leftHandSide']['src'])
        anode.variable_names.append(variable_name)
        node.abstract_nodes.append(anode)
    if body['nodeType'] == 'FunctionCall':
        # 与call_function_names进行比较
        b = contains_any_substring(get_content_by_src(source_code, body['src']), call_function_names)
        if b: # 如果为转账操作则创建TRANSFER_BLOCK
            anode = new_anode(ANodeType.TRANSFER_BLOCK)
            node.abstract_nodes.append(anode)


def build_exCFG_and_abstract(function, source_code, call_function_names, ast):
    # 1. 抽象代码块
    node = function.nodes[0]
    while True:
        # 处理逻辑
        if node.node_type == NodeType.ENTRYPOINT or\
            node.node_type == NodeType.ENTRYPOINT or\
            node.node_type == NodeType.ENDIF or\
            node.node_type == NodeType.ENDLOOP:
                # 1.创建一个ANode,且ANodeType为BASIC_BLOCK
                anode = new_anode(ANodeType.BASIC_BLOCK)
                node.abstract_nodes.append(anode)
                # 2.解析ANode的变量关系（ANodeType为BASIC_BLOCK不需要解析）
        elif node.node_type == NodeType.IF:
            # 1.创建一个ANode,且ANodeType为BRANCH_BLOCK
            anode = new_anode(ANodeType.BRANCH_BLOCK)
            node.abstract_nodes.append(anode)
            # 2.解析ANode的变量关系（ANodeType为BASIC_BLOCK不需要解析）
            parse_variables(node, source_code, call_function_names)
        else:
            parse_variables(node, source_code, call_function_names)
        node = node.sons[0]
        if not node.sons != []:
            break

    # 2. 构建EXCFG
    for node in function.nodes:
        for abstract_node in node.abstract_nodes:
            if abstract_node.anode_type == ANodeType.TRANSFER_BLOCK:
                pass
                # 构建一个Node,然后构建ANode
                new_node = function.new_node(NodeType.FALLBACK, "0:0:0", "attacker", ast)
                # 对构建的new_node进行抽象节点的设置
                anode = new_anode(ANodeType.FALLBACK_BLOCK)
                new_node.abstract_nodes.append(anode)
                # 构建重入的CFG
                link_underlying_nodes(node, new_node)
                link_underlying_nodes(new_node, function.nodes[1])


def parse_transfer_block(nodes, source_code):
    for node in nodes:
        for abstract_node in node.abstract_nodes:
            if abstract_node.anode_type == ANodeType.TRANSFER_BLOCK:
                # 对当前block进行解析
                unparsed_expression = node.unparsed_expression
                source_slice = get_content_by_src(source_code, unparsed_expression['src'])
                if "transferFrom" in source_slice:
                    # 判断transferFrom函数的第一个参数是否为this
                    function_name, arguments= get_function_name_and_arguments(source_slice)
                    if arguments[0] != "this":
                        return 3 # 代表不需要进行检测，合约的参数不会对合约造成资金损失
                else:
                    break # 默认一个函数里面只存在一次转账，发生重入只在第一次转账时发生
    return 4 # 代表不存在transferForm操作


def build_model_by_excfg(cnf_file_path, nodes):
    # 初始化操作
    node_ids = [1]
    current_node = nodes[1]

    while True:
        tag1 = 1
        for node in current_node.sons:
            if node.node_type == NodeType.FALLBACK and \
                    tag1 == 1:
                current_node = node
                tag1 = 0
                break
        if tag1:
            current_node = current_node.sons[0]

        node_ids.append(current_node.node_id)

        # 判断current_node的孩子节点是否包含索引为1的节点
        tag2 = 0
        for node in current_node.sons:
            if node.node_id == nodes[1].node_id:
                tag2 = 1
                break
        if tag2 == 1:
            break

    # 获取变量个数并设定hasRE的值
    variable_numbers = 1 # 作为cnf第一行的数 p cnf variable_numbers， 从1开始，后面还要考虑约束条件
    hasRE = 1
    for node in nodes:
        if node.node_type == NodeType.ENTRYPOINT or \
                node.node_type == NodeType.ENDIF or \
                node.node_type == NodeType.ENDLOOP:
            hasRE += 1
            pass
        else:
            variable_numbers += 1
            hasRE += 1

    # 对重入漏洞进行建模
    lines = "p cnf " + str(variable_numbers) + " " + str(len(node_ids) * 3 ) + "\n"
    for variable in node_ids:
        line1 = str(-hasRE) + " " + str(variable) + " " + str(0) + "\n"
        line2 = str(-hasRE) + " " + str(-variable) + " " + str(0) + "\n"
        line3 = str(hasRE) + " " + str(variable) + " " + str(0) + "\n"
        lines += line1
        lines += line2
        lines += line3

    with open(cnf_file_path, 'w') as f:
        f.write(lines)

    return hasRE

def add_constraints(cnf_file_path, nodes):
    # 找到state block 建立node_id 与 variable_names 之间的关系
    node_id_and_variable_names = {}
    for node in nodes:
        for anode in node.abstract_nodes:
            if anode.anode_type == ANodeType.STATE_BLOCK:
                node_id_and_variable_names[node.node_id] = anode.variable_names # 注意这是一个list

    # 找到check block 判断其variable_name, 并建立约束关系
    constrains = {}
    for node in nodes:
        for anode in node.abstract_nodes:
            if anode.anode_type == ANodeType.CHECK_BLOCK:
                variable_names = anode.variable_names # 注意这是一个list
                # 判断variable_names里面每个variable_name与state block变量之间的关系
                for key, values in node_id_and_variable_names.items():
                    constrains[key] = []
                    for value in values:
                        if contains_any_substring(value, variable_names):
                            constrains[key].append(node.node_id)

    # 根据约束建立cnf文件
    lines = ""
    count = 0 # 用于表示增加子句的数量
    for key, values in constrains.items():
        if len(values) > 0:
            count += 3
            for value in values:
                # key -> -value
                line1 = str(-key) + " " + str(-value) + " " + str(0) + "\n"
                line2 = str(-key) + " " + str(value) + " " + str(0) + "\n"
                line3 = str(key) + " " + str(value) + " " + str(0) + "\n"
                lines += line1
                lines += line2
                lines += line3

    # 将约束条件写入文件
    with open(cnf_file_path, "a") as f:
        f.write(lines)

    # 更改文件的第一行子句的个数
    change_first_line_clause_numbers(cnf_file_path, count)


def get_variable_list(cnf_file_path, hasRE):
    variable_list = set()
    with open(cnf_file_path, "r") as f:
        lines = f.readlines()

    for line in lines[1:]:
        values = line.split(" ")
        for value in values:
            if abs(int(value.strip())) != int(hasRE) and\
                int(value) != 0:
                variable_list.add(abs(int(value)))

    return variable_list

def run_build_exCFG_and_analysis(CFG, AST, input, call_function_names):
    function = Function() # 构建函数层面的cfg
    function.build_cfg(CFG, AST)

    with open(input['source'][:input['source'].rindex("/") + 1] + "temp.sol", "r") as file:
        source_code = file.read()

    '''
    CFG: function.nodes
    AST: AST
    SOURCE_CODE: source_code
    CALL: call_function_name_list
    '''

    # 构建EXCFG并抽象
    build_exCFG_and_abstract(function, source_code, call_function_names, AST)

    # 对构建好的CFG的转账块进行解析，判断其转账是否会影响合约的balance，其中不包括有益于合约的操作
    res_code = parse_transfer_block(function.nodes, source_code)
    if res_code == 3:
        # print("转账操作不会对合约造成影响！")
        print("Reentrancy vulnerability: No")
        print("Description: Change state variable without finacial risk")
        return

    # 首先根据EXCFG对重入进行建模
    cnf_file_path = "/home/long/longhe/sat/sat_example.cnf"
    hasRE = build_model_by_excfg(cnf_file_path, function.nodes)

    # 考虑约束条件
    add_constraints(cnf_file_path, function.nodes)

    # 扫描文件读取变量个数，及取值
    variables = get_variable_list(cnf_file_path, hasRE)
    variables = list(variables)
    
    # 枚举所有情况并使用sat求解
    binary_strings = generate_binary_strings_with_spaces(len(variables))

    is_sat = 0
    for binary_string in binary_strings:
        temp_res = binary_string.strip().split(" ")
        lines = ""
        count = 0
        for index, value in enumerate(temp_res):
            if int(value) > 0:
                lines += str(variables[index]) + " " + "0" + "\n"
                count += 1
            else:
                lines += str(-variables[index]) + " " + "0" + "\n"
                count += 1
        # 将cnf文件拷贝一份，进行测试
        sat_res = sat_by_one_case(cnf_file_path, lines, count)
        if sat_res:
            is_sat = 1
            break # 只要存在一个可以满足重入，则提前停止，以减少时间消耗

    if is_sat == 1:
        # print("存在重入漏洞！")
        print("Reentrancy vulnerability: Yes")
        print("Description: Simple Reentrancy")
    else:
        # print("不存在重入漏洞！")
        print("Reentrancy vulnerability: No")
        print("Description: Non")


def get_modifier_body_block(input, func_node_and_body):
    # 判断是否含有函数修改器
    walk = AstWalker()
    block_modifier_node = []
    walk.walk(func_node_and_body['AST'], {"name": "ModifierInvocation"}, block_modifier_node)
    if block_modifier_node: # 如果存在函数修改器，则获取函数修改器的body_block
        block_temp_modifier_name = []
        # 这个位置只考虑了使用一个函数修改器的情况，实际情况大多数也只是使用了一个函数修改器
        walk.walk(block_modifier_node[0], {"name": "Identifier"}, block_temp_modifier_name)
        modifier_name = block_temp_modifier_name[0]['attributes']['value']
        # {"name":  "ModifierDefinition"} 获取modifier的定义是（需要查全局，所以要用到input）
        block_modifier_node_temps = [] # 查出来的结果可能不止一个
        walk.walk(input['source_map'].ast_helper.contracts['contractsByName'][input['source_map'].cname],
                   {"name": "ModifierDefinition"}, block_modifier_node_temps)
        # 获取函数修改器的name，并匹配到对应的modifier block
        for block_modifier_node_temp in block_modifier_node_temps:
            block_modifier_name = block_modifier_node_temp['attributes']['name']
            if modifier_name == block_modifier_name:
                # 获取当前block_modifier_node_tmp的src
                temp_block = []
                walk.walk(block_modifier_node_temp, {"name": "Block"}, temp_block)
                src = temp_block[0]['src'].split(":")
                start = int(src[0])
                end = start + int(src[1])
                modifier_body_block = input['source_map'].source.content[start:end]
                return modifier_body_block
    else:
        return None


def get_function_body_block(input, func_node_and_body):
    # 获取函数body，即node,以及其AST,作为构建CFG的输入
    walker = AstWalker()
    block_node = []
    walker.walk(func_node_and_body['AST'], {"name": "Block"}, block_node)
    src = block_node[0]['src'].split(":")
    start = int(src[0])
    end = start + int(src[1])
    function_body = input['source_map'].source.content[start:end]
    if function_body:
        return function_body
    return None


def extract_function_definitions(nodes):
    for node in nodes:
        if isinstance(node, dict):
            if "nodeType" in node and node["nodeType"] == "FunctionDefinition":
                yield node
            if "nodes" in node and isinstance(node["nodes"], list):
                yield from extract_function_definitions(node["nodes"])


def get_cfg_body(block, function_body_block, function_name, input):
    body = None
    new_source_code = input['source_map'].source.content.replace(function_body_block, block)
    temp_file_name = input['source'][:input['source'].rindex("/") + 1] + "temp.sol"
    with open(temp_file_name, 'w') as of:
        of.write(new_source_code)
    compilations = compile_all(temp_file_name)
    contract_ast = compilations[0].asts[temp_file_name]
    function_asts =list(extract_function_definitions(contract_ast.get("nodes", [])))
    for function_ast in function_asts:
        if function_ast['name'] == function_name:
            body = function_ast
    return body, contract_ast


def run(input):
    # 根据合约中的调用关系，定位存在转账操作的函数代码片段，作为构建CFG的输入
    func_node_and_bodys, call_function_name_list = get_function_body(input)
    if len(func_node_and_bodys) == 0:
        # print("不存在转账函数。")
        print("Reentrancy vulnerability: No")
        print("Description: None")
        return 1 # 返回1代表不存在函数调用，所以不用检测（该合约无漏洞）。
    for func_node_and_body in func_node_and_bodys:
        # 判断函数修饰符
        visibility = func_node_and_body['AST']['attributes']['visibility']
        if visibility == 'internal':
            # print("存在转账函数，但是不可外部调用。")
            print("Reentrancy vulnerability: No")
            print("Description: Non-callable function")
            return 2 # 如果为internal则直接返回2，代表该函数不能被外部调用。
        modifier_body_block = get_modifier_body_block(input, func_node_and_body)
        function_body_block = get_function_body_block(input, func_node_and_body)
        # 重构block
        block = function_body_block
        if modifier_body_block:
            block = block.strip('{}')
            block = modifier_body_block.replace("_;", block.strip())
        # 将得到的block进行替换重新得到合约代码，然后再通过solidity-parser获得AST，便于后续构建cfg
        body, contract_ast = get_cfg_body(block, function_body_block, func_node_and_body['AST']['attributes']['name'], input)
        # 构建exCFG
        # 如果这个位置contract_ast的信息不足的话，那么就用dict进行传值
        run_build_exCFG_and_analysis(body, contract_ast, input, call_function_name_list)
    return None