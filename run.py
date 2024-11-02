#!/usr/bin/env python3

import os
import subprocess as subp
from typing import List, Dict


cmds = [
        ['''
        simulator/Run.pl -db simulator/bench.db -dir simulator/results/gcc1
        -benchmark gcc -sim $HOME/workspace/ECE-587_Proj/simulator/ss3/sim-outorder
        -args "-fastfwd 1000000 -max:inst 1000000" >& simulator/results/gcc1_outorder.out
         '''],

        ['''
        simulator/Run.pl -db simulator/bench.db -dir simulator/results/gcc1
        -benchmark gcc -sim $HOME/workspace/ECE-587_Proj/simulator/ss3/sim-outorder
        -args "-issue:inorder -fastfwd 1000000 -max:inst 1000000" >& simulator/results/gcc1_inorder.out
        '''],
        ]


def run() -> None:
    for cmd in cmds:
        process = subp.run(cmd)

        if process.returncode != 0:
            print(f'ERROR: {process.stderr}')

        else:
            print(process.output)


def main() -> None:
    run()


if __name__ == '__main__':
    main()
