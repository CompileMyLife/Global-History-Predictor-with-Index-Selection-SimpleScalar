#!/usr/bin/env python3

import os
import subprocess as subp
import re
import logging as log
import matplotlib.pyplot as plt  # Add this import for plotting

from time import perf_counter
from multiprocessing import Pool
from math import log2
from copy import deepcopy
from typing import Dict, List, Optional


# Get current working directory path
PATH = os.getcwd()

# SPEC 2000
benchmarks = [
        # Comparable Benchmarks to McFarling's Paper
        'gcc',
        'li'
#        'tomcatv'
#        'fpppp'
        ]
#
#        # rest of SPEC2000 Benchmarks
#        'gzip',
#        'vpr',
#        'gcc2k',
#        'mcf',
#        'crafty',
#        'go',
#        'm88skim',
#        'compress',
#        'ijpeg',
#        'perl',
#        'vortex',
#        'swim',
#        'su2color',
#        'hydro2d',
#        'mgrid',
#        'applu',
#        'turb3d',
#        'apsi',
#        'wave5'
#        ]


# PHT sizes (total number of entries)
sizes = [
        '32',
        '64',
        '128',
        '256',
        '512',
        '1024',
        '2048',
        '4096',
        '8192',
        '16384',
        '32768',
        '65536'
        ]

# Performance Patterns
perf_pattrns = {
        'IPC': r'sim_IPC\s+([\d.]+)',

        # Total Branch Predicion Updates
        'bpred_updates': r'bpred_.+?\.updates\s+([^\s]+)\s#\s',

        # Total Address-Predicted Hits
        'bpred_addr_hits': r'bpred_.+?\.addr_hits\s+([^\s]+)\s#\s',

        # Total Direction-Predicted Hits (includes Address-Predicted Hits)
        'bpred_dir_hits': r'bpred_.+?\.dir_hits\s+([^\s]+)\s#\s',

        # Total Misses
        'bpred_misses': r'bpred_.+?\.misses\s+([^\s]+)\s#\s',

        # Branch Address-Prediction Rate
        'bpred_addr_rate': r'bpred_.+?\.bpred_addr_rate\s+([\d.]+)\s#\s',

        # Branch Direction-Prediction Rate
        'bpred_dir_rate': r'bpred_.+?\.bpred_dir_rate\s+([\d.]+)\s#\s'
        }

# Performance Data Parsed
perf_data = {
        'nottaken': {},
        'taken': {},
        'bimod': {},
        'gshare': {},
        'gselect': {},
        'comb_bimod_gshare': {},
        'comb_bimod_gselect': {}
        }


# Configure the Run.pl with current working directory path
def setup() -> None:
    # match the exp_dir variable line
    pattrn = r'\$exp_dir\s=\s.*?;'

    # full path
    path   = f'$exp_dir = "{PATH}/simulator";'

    # Read the Run.pl file
    f_handle = open(os.path.join(PATH, 'simulator', 'Run.pl'), 'r')
    content = f_handle.read()
    f_handle.close()

    # CHECK if already set correctly as path var
    if path in content:
        print('setup(): path already set correctly in Run.pl')

    # ELSE substitute with full path
    else:
        content = re.sub(pattrn, path, content)

        # Overwrite the Run.pl
        f_handle = open(os.path.join(PATH, 'simulator', 'Run.pl'), 'w')
        f_handle.write(content)
        f_handle.close()


# Configure Logger
def setup_logger(fpath: str) -> None:
    log.basicConfig(level=log.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M',
                    handlers=[
                        log.FileHandler(fpath, mode='w', encoding='utf-8'),
                        log.StreamHandler()
                        ]
                    )


def init() -> None:
    print('init(): Initializing perf_data...')

    for benchmark in benchmarks:

        perf_data['taken'].update({benchmark : {}})
        perf_data['taken'][benchmark].update({
                'IPC': 0.0,
                'bpred_updates': 0,
                'bpred_addr_hits': 0,
                'bpred_dir_hits': 0,
                'bpred_misses': 0,
                'bpred_addr_rate': 0.0,
                'bpred_dir_rate': 0.0
                })

        perf_data['nottaken'].update({benchmark : {}})
        perf_data['nottaken'][benchmark].update({
                'IPC': 0.0,
                'bpred_updates': 0,
                'bpred_addr_hits': 0,
                'bpred_dir_hits': 0,
                'bpred_misses': 0,
                'bpred_addr_rate': 0.0,
                'bpred_dir_rate': 0.0
                })

        perf_data['bimod'].update({benchmark : {}})

        perf_data['gshare'].update({benchmark : {}})

        perf_data['gselect'].update({benchmark : {}})

        perf_data['comb_bimod_gshare'].update({benchmark : {}})

        perf_data['comb_bimod_gselect'].update({benchmark : {}})


        for size in sizes:

            perf_data['bimod'][benchmark].update({
                size : {
                    'IPC': 0.0,
                    'bpred_updates': 0,
                    'bpred_addr_hits': 0,
                    'bpred_dir_hits': 0,
                    'bpred_misses': 0,
                    'bpred_addr_rate': 0.0,
                    'bpred_dir_rate': 0.0
                    }})

            perf_data['gshare'][benchmark].update({
                size : {
                    'IPC': 0.0,
                    'bpred_updates': 0,
                    'bpred_addr_hits': 0,
                    'bpred_dir_hits': 0,
                    'bpred_misses': 0,
                    'bpred_addr_rate': 0.0,
                    'bpred_dir_rate': 0.0
                    }})

            perf_data['gselect'][benchmark].update({
                size : {
                    'IPC': 0.0,
                    'bpred_updates': 0,
                    'bpred_addr_hits': 0,
                    'bpred_dir_hits': 0,
                    'bpred_misses': 0,
                    'bpred_addr_rate': 0.0,
                    'bpred_dir_rate': 0.0
                    }})

            perf_data['comb_bimod_gshare'][benchmark].update({
                size : {
                    'IPC': 0.0,
                    'bpred_updates': 0,
                    'bpred_addr_hits': 0,
                    'bpred_dir_hits': 0,
                    'bpred_misses': 0,
                    'bpred_addr_rate': 0.0,
                    'bpred_dir_rate': 0.0
                    }})

            perf_data['comb_bimod_gselect'][benchmark].update({
                size : {
                    'IPC': 0.0,
                    'bpred_updates': 0,
                    'bpred_addr_hits': 0,
                    'bpred_dir_hits': 0,
                    'bpred_misses': 0,
                    'bpred_addr_rate': 0.0,
                    'bpred_dir_rate': 0.0
                    }})


def simulation(cmd: str, log_file: str) -> None:
    setup_logger(log_file)
    log.info(f'Executing {cmd}')

    try:
        process = subp.run(cmd, shell=True, stdout=subp.PIPE, stderr=subp.PIPE)

        if process.returncode != 0:
            log.err(f'{process.stderr}')

        else:
            log.info(f'Finished executing {cmd}\n{process.stdout}')

    except Exception as e:
        log.err(f'{e}')


def run_process_pool(cmds: List[str], logs: List[str]) -> None:
    t_start = perf_counter()
    with Pool() as pool:
        pool.starmap(simulation, zip(cmds, logs)) 
    t_end = perf_counter()
    t_duration = t_end - t_start
    print(f'Simulation Batch Duration: {t_duration:.2f}s')


# Run simulation commands
def run_simulations() -> None:
    
    cmd_template = []
    print('run_simulations(): Running Simulations...') 

    # Loop through the benchmarks
    for benchmark in benchmarks:
        # Basic Branch predictors
        nottaken_log_file = os.path.join(PATH, 'logs', f'{benchmark}_nottaken')
        taken_log_file = os.path.join(PATH, 'logs', f'{benchmark}_taken')

        # Out of Order Not Taken
        cmd_template.append(f'{PATH}/simulator/Run.pl -db {PATH}/simulator/bench.db -dir {PATH}/simulator/results/{benchmark}0 -benchmark {benchmark} -sim {PATH}/simulator/ss3/sim-outorder -args "-bpred nottaken -fastfwd 10000000 -max:inst 10000000" >& {PATH}/simulator/results/{benchmark}_nottaken.out')

        # Out of Order Taken
        cmd_template.append(f'{PATH}/simulator/Run.pl -db {PATH}/simulator/bench.db -dir {PATH}/simulator/results/{benchmark}1 -benchmark {benchmark} -sim {PATH}/simulator/ss3/sim-outorder -args "-bpred taken -fastfwd 10000000 -max:inst 10000000" >& {PATH}/simulator/results/{benchmark}_taken.out')

        log_file_paths = [
                nottaken_log_file, 
                taken_log_file 
                ]

        t_start = perf_counter()
        run_process_pool(cmd_template, log_file_paths)

        # Loop through the sizes
        for size in sizes:
            # Bimodal Branch Predictor
            bimod_log_file = os.path.join(PATH, 'logs', f'{benchmark}_bimod_{size}')

            shift_reg_width = str(int(log2(int(size)) - 3))

            # gshare Branch Predictor
            gshare_log_file = os.path.join(PATH, 'logs', f'{benchmark}_gshare_{size}_{shift_reg_width}')

            # gselect Branch Predictor
            gselect_log_file = os.path.join(PATH, 'logs', f'{benchmark}_gselect_{size}_{shift_reg_width}')

            # Comb Bimod-gshare Branch Predictor
            comb_bimod_gshare_log_file = os.path.join(PATH, 'logs', f'{benchmark}_comb_bimod_gshare_{size}_{shift_reg_width}')

            # Comb Bimod-gselect Branch Predictor
            comb_bimod_gselect_log_file = os.path.join(PATH, 'logs', f'{benchmark}_comb_bimod_gselect_{size}_{shift_reg_width}')


            log_file_paths = [
                    bimod_log_file,
                    gshare_log_file,
                    gselect_log_file,
                    comb_bimod_gshare_log_file,
                    comb_bimod_gselect_log_file
                    ]

            cmd_template.clear()

            # Out of Order Bimodal
            cmd_template.append(f'{PATH}/simulator/Run.pl -db {PATH}/simulator/bench.db -dir {PATH}/simulator/results/{benchmark}3 -benchmark {benchmark} -sim {PATH}/simulator/ss3/sim-outorder -args "-bpred bimod -bpred:bimod {size} -fastfwd 10000000 -max:inst 10000000" >& {PATH}/simulator/results/{benchmark}_bimod_{size}.out')

            # Out of Order gshare
            cmd_template.append(f'{PATH}/simulator/Run.pl -db {PATH}/simulator/bench.db -dir {PATH}/simulator/results/{benchmark}4 -benchmark {benchmark} -sim {PATH}/simulator/ss3/sim-outorder -args "-bpred 2lev -bpred:2lev 1 {size} {shift_reg_width} 1 -fastfwd 10000000 -max:inst 10000000" >& {PATH}/simulator/results/{benchmark}_gshare_{size}_{shift_reg_width}.out')

            # Out of Order gselect
            cmd_template.append(f'{PATH}/simulator/Run.pl -db {PATH}/simulator/bench.db -dir {PATH}/simulator/results/{benchmark}5 -benchmark {benchmark} -sim {PATH}/simulator/ss3/sim-outorder -args "-bpred 2lev -bpred:2lev 1 {size} {shift_reg_width} 2 -fastfwd 10000000 -max:inst 10000000" >& {PATH}/simulator/results/{benchmark}_gselect_{size}_{shift_reg_width}.out')


            # May not use these as part of data set since this is not in the scope just for show
            ##################################################################################
            # Out of Order Bimodal-gshare
            cmd_template.append(f'{PATH}/simulator/Run.pl -db {PATH}/simulator/bench.db -dir {PATH}/simulator/results/{benchmark}6 -benchmark {benchmark} -sim {PATH}/simulator/ss3/sim-outorder -args "-bpred comb -bpred:bimod {size} -bpred:2lev 1 {size} {shift_reg_width} 1 -fastfwd 10000000 -max:inst 10000000" >& {PATH}/simulator/results/{benchmark}_comb_bimod_gshare_{size}_{shift_reg_width}.out')
            # Out of Order Bimodal-gselect
            cmd_template.append(f'{PATH}/simulator/Run.pl -db {PATH}/simulator/bench.db -dir {PATH}/simulator/results/{benchmark}7 -benchmark {benchmark} -sim {PATH}/simulator/ss3/sim-outorder -args "-bpred comb -bpred:bimod {size} -bpred:2lev 1 {size} {shift_reg_width} 2 -fastfwd 10000000 -max:inst 10000000" >& {PATH}/simulator/results/{benchmark}_comb_bimod_gselect_{size}_{shift_reg_width}.out')

            run_process_pool(cmd_template, log_file_paths)
            
        t_end = perf_counter()
        t_duration = t_end - t_start
        print(f'Simulation for {benchmark}, Total Duration: {t_duration:.2f}s')


# Parse data from results files
def parse(file_path: str, bpred: str, benchmark: str, size: Optional[str] = None) -> None:
    # Read file
    with open(file_path, 'r') as f:
        content = f.read()

    # 0 for basic types and 1 for bimod and etc
    bpred_type = 0 if bpred in ('nottaken', 'taken') else 1
    
    # Loop through patterns
    for metric, pattrn in perf_pattrns.items():
        match = re.search(pattrn, content)

        if match and bpred_type == 0:
            perf_data[bpred][benchmark][metric] = float(match.group(1))

        elif match and bpred_type:
            perf_data[bpred][benchmark][size][metric] = float(match.group(1))

        else:
            print(f'{file_path} does not contain metric: {metric}')


# Parse performance data from result files
def parse_performance_data(results_dir: str) -> Dict[str, float]:
    # Store the averages across all benchmarks per predictor type
    perf_avg_data = {
            'nottaken': {},
            'taken': {},
            'bimod': {},
            'gshare': {},
            'gselect': {},
            'comb_bimod_gshare': {},
            'comb_bimod_gselect': {}
            }

    files = [f for f in os.listdir(results_dir) if os.path.isfile(os.path.join(results_dir, f))]

    for filename in files:
        file_path = os.path.join(results_dir, filename) 
        
        bpred = re.search(r'^[a-z]+_([^\d]+)(?:_\d+.+?|\.out)', filename).group(1)
        benchmark = re.search(r'^([a-z]+)_.+\.out$',filename).group(1)
        size_match = re.search(r'^[a-z]+_.+?_(\d+)(?:_\d+)?\.out', filename)
        size = size_match.group(1) if size_match != None else None
        
        parse(file_path, bpred, benchmark, size)


    for bpred in perf_data.keys():
        for benchmark in perf_data[bpred].keys():
            if bpred in ('taken', 'nottaken'):
                for metric, val in perf_data[bpred][benchmark].items():
                    if metric not in perf_avg_data[bpred].keys():
                        perf_avg_data[bpred].update({
                            metric : []
                            })
                    perf_avg_data[bpred][metric].append(val)
            else:
                for size in perf_data[bpred][benchmark].keys():
                    if size not in perf_avg_data[bpred]:
                        perf_avg_data[bpred].update({size:{}})
                    for metric, val in perf_data[bpred][benchmark][size].items():
                        if metric not in perf_avg_data[bpred][size].keys():
                            perf_avg_data[bpred][size].update({
                                metric: [] 
                                })
                        perf_avg_data[bpred][size][metric].append(val)

    # Calculate average
    for bpred in perf_avg_data.keys():
        if bpred in ('taken', 'nottaken'):
            # Average % Accuracy
            perf_avg_data[bpred]['bpred_addr_rate'] = sum(perf_avg_data[bpred]['bpred_addr_hits']) / sum(perf_avg_data[bpred]['bpred_updates'])
            perf_avg_data[bpred]['bpred_dir_rate'] = sum(perf_avg_data[bpred]['bpred_dir_hits']) / sum(perf_avg_data[bpred]['bpred_updates'])

            # Average Hits
            perf_avg_data[bpred]['bpred_addr_hits'] = sum(perf_avg_data[bpred]['bpred_addr_hits']) / len(perf_avg_data[bpred]['bpred_addr_hits'])
            perf_avg_data[bpred]['bpred_dir_hits'] = sum(perf_avg_data[bpred]['bpred_dir_hits']) / len(perf_avg_data[bpred]['bpred_dir_hits'])

            # Average Misses
            perf_avg_data[bpred]['bpred_misses'] = sum(perf_avg_data[bpred]['bpred_misses']) / len(perf_avg_data[bpred]['bpred_misses'])

            # Average IPC
            perf_avg_data[bpred]['IPC'] = sum(perf_avg_data[bpred]['IPC']) / len(perf_avg_data[bpred]['IPC'])

        else:
            for size in perf_avg_data[bpred].keys():
                # Average % Accuracy
                perf_avg_data[bpred][size]['bpred_addr_rate'] = sum(perf_avg_data[bpred][size]['bpred_addr_hits']) / sum(perf_avg_data[bpred][size]['bpred_updates'])
                perf_avg_data[bpred][size]['bpred_dir_rate'] = sum(perf_avg_data[bpred][size]['bpred_dir_hits']) / sum(perf_avg_data[bpred][size]['bpred_updates'])

                # Average Hits
                perf_avg_data[bpred][size]['bpred_addr_hits'] = sum(perf_avg_data[bpred][size]['bpred_addr_hits']) / len(perf_avg_data[bpred][size]['bpred_addr_hits'])
                perf_avg_data[bpred][size]['bpred_dir_hits'] = sum(perf_avg_data[bpred][size]['bpred_dir_hits']) / len(perf_avg_data[bpred][size]['bpred_dir_hits'])

                # Average Misses
                perf_avg_data[bpred][size]['bpred_misses'] = sum(perf_avg_data[bpred][size]['bpred_misses']) / len(perf_avg_data[bpred][size]['bpred_misses'])

                # Average IPC
                perf_avg_data[bpred][size]['IPC'] = sum(perf_avg_data[bpred][size]['IPC']) / len(perf_avg_data[bpred][size]['IPC'])


    return perf_avg_data


# Plot IPC values
def plot_performance(performance_data: Dict[str, float]) -> None:
    if not performance_data:
        print("No performance data available for plotting.")
        return

    predictors = ['taken', 'nottaken']
    taken_bpred_gcc_acc = perf_data['taken']['gcc']['bpred_dir_rate']
    taken_bpred_li_acc = perf_data['taken']['li']['bpred_dir_rate']

    nottaken_bpred_gcc_acc = perf_data['nottaken']['gcc']['bpred_dir_rate']
    nottaken_bpred_li_acc = perf_data['nottaken']['li']['bpred_dir_rate']

    fig, ax = plt.subplots()

    ax.barh('gcc', taken_bpred_gcc_acc, height=0.25, label='taken', color='lightgray')
    ax.barh('li', taken_bpred_li_acc, height=0.25, label='taken', color='lightgray')
    ax.barh('gcc', nottaken_bpred_gcc_acc, height=0.25, label='nottaken', color='darkgray')
    ax.barh('li', nottaken_bpred_li_acc, height=0.25, label='nottaken', color='darkgray')
    ax.set_yticks(range(len(benchmarks)), benchmarks)
    ax.set_xlabel('Branch Prediction Accuracy (%)')
    ax.set_title('Taken and Not Taken Peformance by Benchmark')
    ax.xaxis.grid(True)
    ax.legend()

    plt.tight_layout()
    plt.savefig(f'{PATH}/logs/taken_nottaken_perf_by_bench.png')
    

    bimod_bpred_gcc_dir_hits = [perf_data['bimod']['gcc'][size]['bpred_dir_hits'] for size in sizes]
    bimod_bpred_gcc_updates = [perf_data['bimod']['gcc'][size]['bpred_updates'] for size in sizes]
    bimod_bpred_avg_gcc_acc = sum(bimod_bpred_gcc_dir_hits) / sum(bimod_bpred_gcc_updates)

    bimod_bpred_li_dir_hits = [perf_data['bimod']['li'][size]['bpred_dir_hits'] for size in sizes]
    bimod_bpred_li_updates= [perf_data['bimod']['li'][size]['bpred_updates'] for size in sizes]
    bimod_bpred_avg_li_acc = sum(bimod_bpred_li_dir_hits) / sum(bimod_bpred_li_updates)

    gselect_bpred_gcc_dir_hits = [perf_data['gselect']['gcc'][size]['bpred_dir_hits'] for size in sizes]
    gselect_bpred_gcc_updates = [perf_data['gselect']['gcc'][size]['bpred_updates'] for size in sizes]
    gselect_bpred_avg_gcc_acc = sum(gselect_bpred_gcc_dir_hits) / sum(gselect_bpred_gcc_updates)

    gselect_bpred_li_dir_hits = [perf_data['gselect']['li'][size]['bpred_dir_hits'] for size in sizes]
    gselect_bpred_li_updates = [perf_data['gselect']['li'][size]['bpred_updates'] for size in sizes]
    gselect_bpred_avg_li_acc = sum(gselect_bpred_li_dir_hits) / sum(gselect_bpred_li_updates)

    gshare_bpred_gcc_dir_hits = [perf_data['gshare']['gcc'][size]['bpred_dir_hits'] for size in sizes]
    gshare_bpred_gcc_updates = [perf_data['gshare']['gcc'][size]['bpred_updates'] for size in sizes]
    gshare_bpred_avg_gcc_acc = sum(gshare_bpred_gcc_dir_hits) / sum(gshare_bpred_gcc_updates)

    gshare_bpred_li_dir_hits = [perf_data['gshare']['li'][size]['bpred_dir_hits'] for size in sizes]
    gshare_bpred_li_updates = [perf_data['gshare']['li'][size]['bpred_updates'] for size in sizes]
    gshare_bpred_avg_li_acc = sum(gshare_bpred_li_dir_hits) / sum(gshare_bpred_li_updates)

    comb_bimod_gshare_bpred_gcc_dir_hits = [perf_data['comb_bimod_gshare']['gcc'][size]['bpred_dir_hits'] for size in sizes]
    comb_bimod_gshare_bpred_gcc_updates = [perf_data['comb_bimod_gshare']['gcc'][size]['bpred_updates'] for size in sizes]
    comb_bimod_gshare_bpred_avg_gcc_acc = sum(comb_bimod_gshare_bpred_gcc_dir_hits) / sum(comb_bimod_gshare_bpred_gcc_updates)

    comb_bimod_gshare_bpred_li_dir_hits = [perf_data['comb_bimod_gshare']['li'][size]['bpred_dir_hits'] for size in sizes]
    comb_bimod_gshare_bpred_li_updates = [perf_data['comb_bimod_gshare']['li'][size]['bpred_updates'] for size in sizes]
    comb_bimod_gshare_bpred_avg_li_acc = sum(comb_bimod_gshare_bpred_li_dir_hits) / sum(comb_bimod_gshare_bpred_li_updates)

    comb_bimod_gselect_bpred_gcc_dir_hits = [perf_data['comb_bimod_gselect']['gcc'][size]['bpred_dir_hits'] for size in sizes]
    comb_bimod_gselect_bpred_gcc_updates = [perf_data['comb_bimod_gselect']['gcc'][size]['bpred_updates'] for size in sizes]
    comb_bimod_gselect_bpred_avg_gcc_acc = sum(comb_bimod_gselect_bpred_gcc_dir_hits) / sum(comb_bimod_gselect_bpred_gcc_updates)

    comb_bimod_gselect_bpred_li_dir_hits = [perf_data['comb_bimod_gselect']['li'][size]['bpred_dir_hits'] for size in sizes]
    comb_bimod_gselect_bpred_li_updates = [perf_data['comb_bimod_gselect']['li'][size]['bpred_updates'] for size in sizes]
    comb_bimod_gselect_bpred_avg_li_acc = sum(comb_bimod_gselect_bpred_li_dir_hits) / sum(comb_bimod_gselect_bpred_li_updates)

    fig, ax = plt.subplots()

    bar_width = 0.10
    y_pos = range(len(benchmarks))

    ax.barh(y_pos + 5, bimod_bpred_avg_gcc_acc, height=bar_width, label='bimod', color='k')
    ax.barh(y_pos - 5, bimod_bpred_avg_li_acc, height=bar_width, label='bimod', color='k')
    ax.barh(y_pos + 4, gselect_bpred_avg_gcc_acc, height=bar_width, label='gselect', color='r')
    ax.barh(y_pos - 4, gselect_bpred_avg_li_acc, height=bar_width, label='gselect', color='r')
    ax.barh(y_pos + 3, gshare_bpred_avg_gcc_acc, height=bar_width, label='gshare', color='c')
    ax.barh(y_pos - 3, gshare_bpred_avg_li_acc, height=bar_width, label='gshare', color='c')
    ax.barh(y_pos + 2, comb_bimod_gselect_bpred_avg_gcc_acc, height=bar_width, label='comb_bimod_gselect', color='m')
    ax.barh(y_pos - 2, comb_bimod_gselect_bpred_avg_li_acc, height=bar_width, label='comb_bimod_gselect', color='m')
    ax.barh(y_pos + 1, comb_bimod_gshare_bpred_avg_gcc_acc, height=bar_width, label='comb_bimod_gshare', color='b')
    ax.barh(y_pos - 1, comb_bimod_gshare_bpred_avg_li_acc, height=bar_width, label='comb_bimod_gshare', color='b')
    ax.set_yticks(y_pos)
    ax.set_yticklabels(benchmarks)
    ax.set_xlabel('Branch Prediction Accuracy (%)')
    ax.set_title('Predictors Peformance by Benchmark')
    ax.xaxis.grid(True)
    ax.legend()

    plt.tight_layout()
    plt.savefig(f'{PATH}/logs/avg_perf_by_bench.png')


    taken_bpred_acc = performance_data['taken']['bpred_dir_rate']
    nottaken_bpred_acc = performance_data['nottaken']['bpred_dir_rate']


    fig, ax = plt.subplots()

    ax.bar(range(len(predictors)), [taken_bpred_acc, nottaken_bpred_acc], align='center')
    ax.set_ylabel('Branch Prediction Accuracy (%)')
    ax.set_xlabel('Branch Predictors')
    ax.set_xticks(range(len(predictors)))
    ax.set_xticklabels(predictors)
    ax.set_title('Taken and Not Taken Average Peformance over Benchmarks')
    ax.yaxis.grid(True)

    plt.tight_layout()
    plt.savefig(f'{PATH}/logs/taken_nottaken_avg_perf.png')

    bimod_bpred_acc = [performance_data['bimod'][size]['bpred_dir_rate'] for size in sizes]
    gselect_bpred_acc = [performance_data['gselect'][size]['bpred_dir_rate'] for size in sizes]
    gshare_bpred_acc = [performance_data['gshare'][size]['bpred_dir_rate'] for size in sizes]

    comb_bimod_gshare_bpred_acc = [performance_data['comb_bimod_gshare'][size]['bpred_dir_rate'] for size in sizes]
    comb_bimod_gselect_bpred_acc = [performance_data['comb_bimod_gselect'][size]['bpred_dir_rate'] for size in sizes]

    fig, ax = plt.subplots()

    ax.plot(sizes, bimod_bpred_acc, label='bimod', linewidth=0.8, color='k', marker='^')
    ax.plot(sizes, gselect_bpred_acc, label='gselect', linewidth=0.8, color='r', marker='o')
    ax.plot(sizes, gshare_bpred_acc, label='gshare', linewidth=0.8, color='b', marker='v')
    ax.plot(sizes, comb_bimod_gselect_bpred_acc, label='comb_bimod_gselect', linewidth=0.8, color='m', marker='d')
    ax.plot(sizes, comb_bimod_gshare_bpred_acc, label='comb_bimod_gshare', linewidth=0.8, color='c', marker='p')
    ax.set_ylabel('Conditional Branch Prediction Accuracy (%)')
    ax.set_xlabel('Predictor Size (Bytes)')
    ax.set_title('Average Peformance over all Benchmarks')
    ax.legend()
    ax.yaxis.grid(True)

    plt.tight_layout()
    plt.savefig(f'{PATH}/logs/avg_accuracy_perf.png')

    taken_bpred_ipc = performance_data['taken']['IPC']
    nottaken_bpred_ipc = performance_data['nottaken']['IPC']

    fig, ax = plt.subplots()

    ax.bar(range(len(predictors)), [taken_bpred_ipc, nottaken_bpred_ipc], align='center')
    ax.set_ylabel('IPC')
    ax.set_xlabel('Branch Predictors')
    ax.set_xticks(range(len(predictors)))
    ax.set_xticklabels(predictors)
    ax.set_title('Taken and Not Taken Average IPC over Benchmarks')
    ax.yaxis.grid(True)

    plt.tight_layout()
    plt.savefig(f'{PATH}/logs/taken_nottaken_avg_ipc_perf.png')

    bimod_bpred_ipc = [performance_data['bimod'][size]['IPC'] for size in sizes]
    gselect_bpred_ipc = [performance_data['gselect'][size]['IPC'] for size in sizes]
    gshare_bpred_ipc = [performance_data['gshare'][size]['IPC'] for size in sizes]

    comb_bimod_gshare_bpred_ipc = [performance_data['comb_bimod_gshare'][size]['IPC'] for size in sizes]
    comb_bimod_gselect_bpred_ipc = [performance_data['comb_bimod_gselect'][size]['IPC'] for size in sizes]

    fig, ax = plt.subplots()

    ax.plot(sizes, bimod_bpred_ipc, label='bimod', linewidth=0.8, color='k', marker='^')
    ax.plot(sizes, gselect_bpred_ipc, label='gselect', linewidth=0.8, color='r', marker='o')
    ax.plot(sizes, gshare_bpred_ipc, label='gshare', linewidth=0.8, color='b', marker='v')
    ax.plot(sizes, comb_bimod_gselect_bpred_ipc, label='comb_bimod_gselect', linewidth=0.8, color='m', marker='d')
    ax.plot(sizes, comb_bimod_gshare_bpred_ipc, label='comb_bimod_gshare', linewidth=0.8, color='c', marker='p')
    ax.set_ylabel('IPC')
    ax.set_xlabel('Predictor Size (Bytes)')
    ax.set_title('Average IPC over all Benchmarks')
    ax.legend()
    ax.yaxis.grid(True)

    plt.tight_layout()
    plt.savefig(f'{PATH}/logs/avg_ipc_perf.png')

def main() -> None:
    os.makedirs(f'{PATH}/logs', exist_ok=True)

    # Set the Run.pl to specified paths
    setup()

    init()

    # Run simulation commands
    #run_simulations()

    # Parse performance data
    results_dir = f'{PATH}/simulator/results'
    performance_avg_data = parse_performance_data(results_dir)
    
    plot_performance(performance_avg_data)

if __name__ == '__main__':
    main()
