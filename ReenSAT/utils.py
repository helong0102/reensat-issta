import os
import shutil
import subprocess
import shlex
import re


def get_content_by_src(source, src):
    src = src.split(":")
    start = int(src[0])
    end = int(src[1]) + start
    return source[start:end]

def run_command(cmd):
    FNULL = open(os.devnull, 'w')
    solc_p = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=FNULL)
    return solc_p.communicate()[0].decode('utf-8', 'strict')


def replace_last(string, old, new):
    index = string.rfind(old)
    if index == -1:
        return string
    else:
        return string[:index] + new + string[index + len(old):]

def contains_any_substring(input_string, substrings):
    for substring in substrings:
        if substring in input_string:
            return True
    return False

def rm_file(path):
    if os.path.isfile(path):
        os.unlink(path)

def get_sat_result_by_cnf(cnf_file_path):
    sat_path = "/home/long/longhe/match_2/sat/minisat"
    cmd = "%s %s" % (sat_path, cnf_file_path)
    out = run_command(cmd)
    try:
        result = out.split("\n")[-2]
    except Exception as e:
        print("Sat Solver Error:", e)
        raise Exception("Sat Solver Error")
    return result

def get_function_name_and_arguments(str):
    # 匹配函数名和参数列表的正则表达式
    pattern = r'(\w+)\((.*?)\)'

    matches = re.findall(pattern, str)
    if matches:
        function_name, arguments = matches[0]
        argument_list = arguments.split(',')
        argument_list = [arg.strip() for arg in argument_list]
        return function_name, argument_list
    else:
        print("No match found.")
        raise Exception("匹配函数名和参数列表错误！")

def change_first_line_clause_numbers(cnf_file_path, count):
    with open(cnf_file_path, "r") as f:
        lines = f.readlines()
    temp = lines[0].split(" ")
    # 重新计算子句的数量
    clause_number = int(temp[-1]) + count
    # 重构第一行内容
    new_first_line = temp[0] + " " + temp[1] + " " + temp[2] + " " + str(clause_number)
    # 将第一行的内容写回到文件中
    lines[0] = new_first_line + "\n"

    # 将修改后的内容写回文件
    with open(cnf_file_path, "w") as file:
        file.writelines(lines)

def generate_binary_strings_with_spaces(length, prefix=""):
    if length == 0:
        return [" ".join(prefix)]
    else:
        results = []
        results.extend(generate_binary_strings_with_spaces(length - 1, prefix + "0"))
        results.extend(generate_binary_strings_with_spaces(length - 1, prefix + "1"))
        return results

def sat_by_one_case(cnf_file_path, lines, count):
    # 首先创建一个临时文件，复制一份cnf_file_path出来，进行测试
    temp_file = "./temp_file_copy.txt"  # 复制后的文件名
    shutil.copy2(cnf_file_path, temp_file)
    # 进行sat测试
    change_first_line_clause_numbers(temp_file, count)
    with open(temp_file, "a") as f:
        f.write(lines)
    is_sat = get_sat_result_by_cnf(temp_file)
    # 删除文件
    rm_file(temp_file)

    if is_sat == "SATISFIABLE":
        return 1
    else:
        return 0

def auto_get_solc_version(path):
    res = ""
    with open(path, 'r') as f:
        lines = f.readlines()
        for line in lines:
            if line.strip().startswith("pragma solidity"):
                res = line.strip().split(" ")[2].replace(";", "").replace(">", "").replace("=", "").replace("<",
                                                                                                            "").replace(
                    "^", "").replace("00", "0").strip()
                break
    if res.count(".") != 2:
        res = ""
    # if res == '0.4.2':
    #     res = ""
    # if res == '0.4.4':
    #     res = ""
    # if res == '0.4.0':
    #     res = ""
    # if res == "0.4.8":
    #     res = ""
    # if res == "0.4.9":
    #     res = ""
    return res