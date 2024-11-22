#!/usr/bin/env python3

import os
import subprocess as subp
import re
from typing import List, Dict

PATH = os.getcwd()

cmds = [
    f'{PATH}/simulator/Run.pl -db {PATH}/simulator/bench.db -dir {PATH}/simulator/results/gcc1 -benchmark gcc -sim {PATH}/simulator/ss3/sim-outorder -args "-bpred bimod -bpred:bimod 2048 -fastfwd 5000000 -max:inst 5000000" >& {PATH}/simulator/results/gcc1_bimod.out',
    f'{PATH}/simulator/Run.pl -db {PATH}/simulator/bench.db -dir {PATH}/simulator/results/gcc1 -benchmark gcc -sim {PATH}/simulator/ss3/sim-outorder -args "-bpred 2lev -bpred:2lev 1 1024 8 1 -fastfwd 5000000 -max:inst 5000000" >& {PATH}/simulator/results/gcc1_gshare.out',
    f'{PATH}/simulator/Run.pl -db {PATH}/simulator/bench.db -dir {PATH}/simulator/results/gcc1 -benchmark gcc -sim {PATH}/simulator/ss3/sim-outorder -args "-bpred 2lev -bpred:2lev 1 1024 8 2 -fastfwd 5000000 -max:inst 5000000" >& {PATH}/simulator/results/gcc1_gselect.out',
    f'{PATH}/simulator/Run.pl -db {PATH}/simulator/bench.db -dir {PATH}/simulator/results/gcc1 -benchmark gcc -sim {PATH}/simulator/ss3/sim-outorder -args "-bpred comb -bpred:2lev 1 1024 8 1 -fastfwd 5000000 -max:inst 5000000" >& {PATH}/simulator/results/gcc1_comb_gshare.out',
    f'{PATH}/simulator/Run.pl -db {PATH}/simulator/bench.db -dir {PATH}/simulator/results/gcc1 -benchmark gcc -sim {PATH}/simulator/ss3/sim-outorder -args "-bpred comb -bpred:2lev 1 1024 8 2 -fastfwd 5000000 -max:inst 5000000" >& {PATH}/simulator/results/gcc1_comb_gselect.out'
        ]


def log_command_and_output(cmd: str, stdout: str, stderr: str, log_filename: str) -> None:  # Open a log file to store commands and outputs
    with open(log_filename, 'a') as log_file:
        log_file.write(f"Executing Command: {cmd}\n")
        log_file.write(f"Standard Output:\n{stdout}\n")
        log_file.write(f"Standard Error:\n{stderr}\n")
        log_file.write("=" * 80 + "\n")

def setup () -> None:
    pattrn = r'\$exp_dir\s=\s.*?;'
    path   = f'$exp_dir = "{PATH}/simulator";'

    f_handle = open(os.path.join(PATH, 'simulator', 'Run.pl'), 'r')
    content = f_handle.read()
    f_handle.close()

    # CHECK if already set correctly as path var
    if path in content:
        print('run.py:setup(): path already set correctly in Run.pl')

    else:
        content = re.sub(pattrn, path, content)

        f_handle = open(os.path.join(PATH, 'simulator', 'Run.pl'), 'w')
        f_handle.write(content)
        f_handle.close()


def run() -> None:
    log_filename = 'logs/command_logs.txt'  # Log file to store commands and outputs
    for cmd in cmds:
        try:
            process = subp.run(cmd, shell=True, stdout=subp.PIPE, stderr=subp.PIPE, universal_newlines=True)  # Run the command, capture stdout and stderr
            log_command_and_output(cmd, process.stdout, process.stderr, log_filename)  # Log the command and its output

            # Check the return code to determine success/failure
            if process.returncode != 0:
                print(f'ERROR: {process.stderr}')
            else:
                print(process.stdout)

        except Exception as e:
            print(f"Exception occurred: {e}")


def main() -> None:
    os.makedirs('logs', exist_ok=True)  # creates the logs directory, if it already exists do nothing.
    setup()
    run()


if __name__ == '__main__':
    main()
