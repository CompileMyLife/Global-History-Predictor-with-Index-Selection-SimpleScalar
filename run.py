#!/usr/bin/env python3

import os
import subprocess as subp
from typing import List, Dict

os.makedirs('logs', exist_ok=True) #creates the logs directory, if it already exists do nothing.

cmds = [
        ['''
        simulator/Run.pl -db simulator/bench.db -dir simulator/results/gcc1
        -benchmark gcc -sim $HOME/workspace/ECE-587_Proj/simulator/ss3/sim-outorder
        -args "-fastfwd 1000000 -max:inst 1000000" >& simulator/results/gcc1_outorder.out
         ''',
         '''
        simulator/Run.pl -db simulator/bench.db -dir simulator/results/gcc1
        -benchmark gcc -sim $HOME/workspace/ECE-587_Proj/simulator/ss3/sim-outorder
        -args "-issue:inorder -fastfwd 1000000 -max:inst 1000000" >& simulator/results/gcc1_inorder.out
        '''
        ]

def log_command_and_output(cmd: str, stdout: str, stderr: str, log_filename: str) -> None: # Open a log file to store commands and outputs
    with open(log_filename, 'a') as log_file:  
        log_file.write(f"Executing Command: {cmd}\n")
        log_file.write(f"Standard Output:\n{stdout}\n")
        log_file.write(f"Standard Error:\n{stderr}\n")
        log_file.write("=" * 80 + "\n") 


def run() -> None:
    log_filename = 'logs/command_logs.txt'  # Log file to store commands and outputs
    for cmd in cmds:
      try: 
          process = subp.run(cmd, shell=True, capture_output=True, text=True) # Run the command, capture stdout and stderr
            log_command_and_output(cmd, process.stdout, process.stderr, log_filename) # Log the command and its output

            # Check the return code to determine success/failure

          if process.returncode != 0:
            print(f'ERROR: {process.stderr}')

          else:
            print(process.output)


def main() -> None:
    run()


if __name__ == '__main__':
    main()
