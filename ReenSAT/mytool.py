import argparse
import os

import analysis
from input_helper import InputHelper
from utils import rm_file


def run_solidity_analysis(inputs):
    exit_code = 0
    print("Vulnerability Report:\n")
    for input in inputs:
        file_name_contract = input['contract'][input['contract'].rindex("/") + 1:]
        file_infos = file_name_contract.split(":")
        print("File path: " + file_infos[0])
        print("Contract name: " + file_infos[1])
        return_code = analysis.run(input)

        # 删除临时文件
        temp_file_name = input['source'][:input['source'].rindex("/") + 1] + "temp.sol"
        rm_file(temp_file_name)

    if return_code == 1:
        exit_code = 1

    return exit_code


def analysis_solidity():
    global args
    helper = InputHelper(source=args.source)
    inputs = helper.get_inputs()
    exit_code = run_solidity_analysis(inputs)

    return exit_code


def main():
    global args

    parser = argparse.ArgumentParser()

    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument("-s", "--source", type=str, help="local source file name. Solidity by default.")

    args = parser.parse_args()

    exit_code = analysis_solidity()

    return exit_code


if __name__ == '__main__':
    # 设置环境变量，conda环境都需要
    # os.environ['PATH'] += os.pathsep + '/root/anaconda3/envs/mytool/bin'
    # os.environ['PATH'] += os.pathsep + '/root/helong/go-ethereum-1.7.3/build/bin'

    exit_code = main()
