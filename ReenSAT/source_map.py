import json
import re

import six

from ast_helper import AstHelper
from utils import run_command, replace_last
from solidity_parser import parser


class Source:
    def __init__(self, filename):
        self.filename = filename
        self.content = self._load_content()
        self.line_break_positions = self._load_line_break_positions()

    def _load_content(self):
        with open(self.filename, 'rb') as f:
            content = f.read().decode('UTF-8')
        return content

    def _load_line_break_positions(self):
        return [i for i, letter in enumerate(self.content) if letter == '\n']


class SourceMap:
    parent_filename = ""
    position_groups = {}
    sources = {}
    ast_helper = None
    func_to_sig_by_contract = {}
    contract_infos = {}  # 保存当前合约的信息(一个文件可能有多个contract)
    parse_contract = {} # 保存合约源代码和逻辑相关信息（使用solidity_parse）

    def __init__(self, cname, parent_filename):
        self.cname = cname
        # 这样写的目的是为了遍历一个文件中有多个contract
        if not SourceMap.parent_filename:
            SourceMap.parent_filename = parent_filename
            SourceMap.ast_helper = AstHelper(SourceMap.parent_filename)
            SourceMap.func_to_sig_by_contract = SourceMap._get_sig_to_func_by_contract()
            SourceMap.parse_contract = parser.parse(self._get_source().content)
        self.source = self._get_source()
        self.var_names = self._get_var_names()  # 全局变量名
        self.func_call_names = self._get_func_call_names()
        self.callee_src_pairs = self._get_callee_src_pairs()
        self.func_name_to_params = self._get_func_name_to_params()
        self.sig_to_func = self._get_sig_to_func()
        self.contract_infos = self._parse_smart_contract()

        # 后面需要什么东西再在这个位置增加
        print()

    @classmethod
    def _get_sig_to_func_by_contract(cls):
        cmd = 'solc --combined-json hashes %s' % cls.parent_filename
        out = run_command(cmd)
        out = json.loads(out)
        return out['contracts']

    def _get_source(self):
        fname = self.get_filename()
        if fname not in SourceMap.sources:
            SourceMap.sources[fname] = Source(fname)
        return SourceMap.sources[fname]

    def get_filename(self):
        return self.cname.split(":")[0]

    def _get_var_names(self):
        return SourceMap.ast_helper.extract_state_variable_names(self.cname)

    def _get_func_call_names(self):
        func_call_srcs = SourceMap.ast_helper.extract_func_call_srcs(self.cname)
        func_call_names = []
        for src in func_call_srcs:
            src = src.split(":")
            start = int(src[0])
            end = start + int(src[1])
            func_call_names.append(self.source.content[start:end])
        return func_call_names

    def _get_callee_src_pairs(self):
        return SourceMap.ast_helper.get_callee_src_pairs(self.cname)

    def _get_func_name_to_params(self):
        func_name_to_params = SourceMap.ast_helper.get_func_name_to_params(self.cname)
        for func_name in func_name_to_params:
            calldataload_position = 0
            for param in func_name_to_params[func_name]:
                if param['type'] == 'ArrayTypeName':
                    param['position'] = calldataload_position
                    calldataload_position += param['value']
                else:
                    param['position'] = calldataload_position
                    calldataload_position += 1
        return func_name_to_params

    def _get_sig_to_func(self):
        func_to_sig = SourceMap.func_to_sig_by_contract[self.cname]['hashes']
        return dict((sig, func) for func, sig in six.iteritems(func_to_sig))

    def _get_smart_contract_functions_and_bodys(self):
        function_bodys = {}
        # alist = self.source.content.split('function')
        alist = re.split(r'function|modifier', self._get_contract_body(self.cname.split(":")[-1]))
        for i in range(1, len(alist)):
            function_name = alist[i].split("(")[0].strip()
            # XXX{XX{XX}XX}XXX
            start = alist[i].split("{")[0]
            end = alist[i].split("}")[-1]
            function_body = replace_last(alist[i].replace(start, "", 1), end, "")
            function_bodys[f"{function_name}"] = function_body
        return function_bodys

    def _get_global_variable_body(self, variable_name):
        # lines = self.source.content.split("\n")
        lines = self._get_contract_body(self.cname.split(":")[-1]).split("\n")
        for line in lines:
            # 换一种写法
            pattern = r".*" + variable_name +  r".*;"
            match = re.findall(pattern, line.strip())
            if match:
                return line.strip()
            # if variable_name in line:
            #     return line.strip()

    def _get_contract_body(self, contract_name):
        # alist = self.source.content.split("contract").split("library") # 这种方式直接弃用
        alist = re.split(r'contract|library|interface',self.source.content)
        for i in range(1, len(alist)):
            # 更改一种匹配方式
            pattern = '^' + contract_name + r'\s*{'
            match = re.findall(pattern, alist[i].strip())
            if match:
                return alist[i].strip()

    """
    {
    	"contract SimpleDao": {
    		"gloabl_variables": ["mapping (address => uint) public credit;", "sting public data;"],
    		"functions": [{
    			"function deposit() public payable": ["credit[msg.sender] += msg.value;"]
    		}, {
    			"function withdraw(uint amount)": ["require(credit[msg.sender] >= amount);", "// <yes> <report> REENTRANCY", "require(msg.sender.call.value(amount)());", "credit[msg.sender]-=amount;"]
    		}, {
    			"function getBalance() returns (uint)": ["return address(this).balance;"]
    		}]
    	},
    	"DAO": {
    		"gloabl_variables": ["sting public data1;"],
    		"functions": [ {
    			"function getBalance() returns (uint)": ["return address(this).balance;"]
    		}]
    	}
    }
    """

    def _parse_smart_contract(self):  # 提取合约信息
        contract_infos_temp = {}
        function_and_bodys = self._get_smart_contract_functions_and_bodys()

        # 提取合约名
        contract_name = self.cname.split(":")[-1]
        contract_infos_temp[f'{contract_name}'] = {
            "global_variables": [],
            "functions": [],
            "modifiers": []
        }

        # 提取全局变量所在行信息
        # 1. 找到当前合约所在的代码片段
        # current_contract_body = self._get_contract_body(contract_name)
        # 2.查找全局变量的body
        for var_name in self.var_names:
            current_variable_body = self._get_global_variable_body(var_name)
            if current_variable_body:
                contract_infos_temp[f"{contract_name}"]["global_variables"].append(current_variable_body)

        # 提取函数和函数体信息
        # 1.获取当前合约所对应的函数名
        # 通过 func_to_sig_by_contract[f'{cname}'] 来获取所有的函数签名，但是其中存在public变量所对应的名字~
        function_names = SourceMap.func_to_sig_by_contract[f'{self.cname}']['hashes']
        # 2.遍历所函数名，判断其是否在function_and_bodys里面，在则添加，否则跳过
        for function_name in function_names:
            function_name = function_name.strip().split("(")[0]
            if function_name in function_and_bodys: # 存在该函数，而非public变量函数
                function_title = self._get_function_title_by_name(function_name)
                temp_body = self._get_function_body_list(function_and_bodys[function_name])
                temp_info = {f'{function_title}': temp_body}
                contract_infos_temp[f'{contract_name}']['functions'].append(temp_info)
            else: # 不存在该函数，是public变量函数
                pass

        # 提取modifier函数修改器信息
        # 1. 获取函数修改器名称
        modifier_names = self._get_modifier_names()
        # 2. 获取合约的所有modifier title
        for modifier_name in modifier_names:
            modifier_title = self._get_modifer_titile_by_name(modifier_name)
            modifier_temp_body = self._get_modifier_body_list(function_and_bodys[modifier_name])
            temp_info = {f'{modifier_title}':modifier_temp_body}
            contract_infos_temp[f'{contract_name}']['modifiers'].append(temp_info)

        return contract_infos_temp

    def _get_function_title_by_name(self, function_name):
        # lines = self.source.content.split("\n")
        lines = self._get_contract_body(self.cname.split(":")[-1]).split("\n")
        for line in lines:
            # ^function.*deposit.*{
            pattern = r"^function.*" + function_name + ".*(;|{)"
            result = re.compile(pattern).search(line.strip())
            # match = re.findall(pattern, line.strip())
            if result:
                return result.string.replace("{", "")

    def _get_function_body_list(self, function_body_content):
        lines = []
        lines_content = function_body_content.split("\n")
        for i in range(1, len(lines_content) - 1):
            if lines_content[i].strip() != "" and \
                    not re.findall(r"^//", lines_content[i].strip()): # 这个位置还需要修改~ 还要考虑‘}’括号
                lines.append(lines_content[i].strip())
        return lines

    def _get_modifier_names(self):
        modifier_names = []
        lines = self._get_contract_body(self.cname.split(":")[-1]).split("\n")
        for line in lines:
            if "modifier" in line:
                temp =re.findall("^modifier\s*(.*?)\w*\s*{", line.strip())
                temp = temp[0].split('(')[0]
                if temp:
                    modifier_names.append(temp.strip())
        return modifier_names

    def _get_modifer_titile_by_name(self, modifier_name):
        lines = self._get_contract_body(self.cname.split(":")[-1]).split("\n")
        for line in lines:
            pattern = r"^modifier.*" + modifier_name + ".*{"
            match = re.findall(pattern, line.strip())
            if match:
                return match[0].replace("{", "").strip()

    def _get_modifier_body_list(self, modifier_body_content):
        lines = []
        lines_content = modifier_body_content.split("\n")
        for i in range(1, len(lines_content) - 1):
            if lines_content[i].strip() != "" and \
                    not re.findall(r"^//", lines_content[i].strip()):
                lines.append(lines_content[i].strip())
        return lines
