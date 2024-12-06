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

    # Loop through benchmarks
    for benchmark in benchmarks:
        # Initialization
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

        # Initialize bpred keys with a subset dictionary 
        perf_data['bimod'].update({benchmark : {}})

        perf_data['gshare'].update({benchmark : {}})

        perf_data['gselect'].update({benchmark : {}})

        perf_data['comb_bimod_gshare'].update({benchmark : {}})

        perf_data['comb_bimod_gselect'].update({benchmark : {}})


        # Loop through sizes
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
    # Setup the logging file given
    setup_logger(log_file)
    log.info(f'Executing {cmd}')

    # Execute the cmd given
    try:
        process = subp.run(cmd, shell=True, stdout=subp.PIPE, stderr=subp.PIPE)

        # CHECK cmd executed sucessfully or not
        if process.returncode != 0:
            log.error(f'{process.stderr}')

        else:
            log.info(f'Finished executing {cmd}\n{process.stdout}')

    except Exception as e:
        log.error(f'{e}')


def run_process_pool(cmds: List[str], logs: List[str]) -> None:
    t_start = perf_counter()

    # Start pool with however many cores available on CPU
    with Pool() as pool:
        # Give workers simulation(cmds,logs) and finished in any order
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
        cmd_template.append(f'{PATH}/simulator/Run.pl -db {PATH}/simulator/bench.db -dir {PATH}/simulator/results/{benchmark}0 -benchmark {benchmark} -sim {PATH}/simulator/ss3/sim-outorder -args "-bpred nottaken -fastfwd 10000000 -max:inst 10000000" > {PATH}/simulator/results/{benchmark}_nottaken.out 2>&1')

        # Out of Order Taken
        cmd_template.append(f'{PATH}/simulator/Run.pl -db {PATH}/simulator/bench.db -dir {PATH}/simulator/results/{benchmark}1 -benchmark {benchmark} -sim {PATH}/simulator/ss3/sim-outorder -args "-bpred taken -fastfwd 10000000 -max:inst 10000000" > {PATH}/simulator/results/{benchmark}_taken.out 2>&1')

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

            # Calculate shift register width and subtract three due to PC 3 LSBs
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

            # Clear previous entries
            cmd_template.clear()

            # Out of Order Bimodal
            cmd_template.append(f'{PATH}/simulator/Run.pl -db {PATH}/simulator/bench.db -dir {PATH}/simulator/results/{benchmark}3 -benchmark {benchmark} -sim {PATH}/simulator/ss3/sim-outorder -args "-bpred bimod -bpred:bimod {size} -fastfwd 10000000 -max:inst 10000000" > {PATH}/simulator/results/{benchmark}_bimod_{size}.out 2>&1')

            # Out of Order gshare
            cmd_template.append(f'{PATH}/simulator/Run.pl -db {PATH}/simulator/bench.db -dir {PATH}/simulator/results/{benchmark}4 -benchmark {benchmark} -sim {PATH}/simulator/ss3/sim-outorder -args "-bpred 2lev -bpred:2lev 1 {size} {shift_reg_width} 1 -fastfwd 10000000 -max:inst 10000000" > {PATH}/simulator/results/{benchmark}_gshare_{size}_{shift_reg_width}.out 2>&1')

            # Out of Order gselect
            cmd_template.append(f'{PATH}/simulator/Run.pl -db {PATH}/simulator/bench.db -dir {PATH}/simulator/results/{benchmark}5 -benchmark {benchmark} -sim {PATH}/simulator/ss3/sim-outorder -args "-bpred 2lev -bpred:2lev 1 {size} {shift_reg_width} 2 -fastfwd 10000000 -max:inst 10000000" > {PATH}/simulator/results/{benchmark}_gselect_{size}_{shift_reg_width}.out 2>&1')

            # Out of Order Bimodal-gshare
            cmd_template.append(f'{PATH}/simulator/Run.pl -db {PATH}/simulator/bench.db -dir {PATH}/simulator/results/{benchmark}6 -benchmark {benchmark} -sim {PATH}/simulator/ss3/sim-outorder -args "-bpred comb -bpred:bimod {size} -bpred:2lev 1 {size} {shift_reg_width} 1 -fastfwd 10000000 -max:inst 10000000" > {PATH}/simulator/results/{benchmark}_comb_bimod_gshare_{size}_{shift_reg_width}.out 2>&1')

            # Out of Order Bimodal-gselect
            cmd_template.append(f'{PATH}/simulator/Run.pl -db {PATH}/simulator/bench.db -dir {PATH}/simulator/results/{benchmark}7 -benchmark {benchmark} -sim {PATH}/simulator/ss3/sim-outorder -args "-bpred comb -bpred:bimod {size} -bpred:2lev 1 {size} {shift_reg_width} 2 -fastfwd 10000000 -max:inst 10000000" > {PATH}/simulator/results/{benchmark}_comb_bimod_gselect_{size}_{shift_reg_width}.out 2>&1')

            # Run batch with cmds and log files paths setup
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

        # CHECK match and which bpred_type
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

    # Store in list all 'files' only and ignore directories
    files = [f for f in os.listdir(results_dir) if os.path.isfile(os.path.join(results_dir, f))]

    # Loop through filenames
    for filename in files:
        file_path = os.path.join(results_dir, filename) 
        
        # Parse out which bpred, benchmark, size if it exists from filename
        bpred = re.search(r'^[a-z]+_([^\d]+)(?:_\d+.+?|\.out)', filename).group(1)
        benchmark = re.search(r'^([a-z]+)_.+\.out$',filename).group(1)
        size_match = re.search(r'^[a-z]+_.+?_(\d+)(?:_\d+)?\.out', filename)
        size = size_match.group(1) if size_match != None else None
        
        parse(file_path, bpred, benchmark, size)


    # Loop through bpreds from global performance data
    for bpred in perf_data.keys():
        # Loop through benchmarks for a bpred
        for benchmark in perf_data[bpred].keys():
            # CHECK which type of bpreds
            if bpred in ('taken', 'nottaken'):
                # Loop through all metric and values for a bpred and benchmark
                for metric, val in perf_data[bpred][benchmark].items():
                    # CHECK metric does not exist in the perf_avg_data bpred dictionary
                    if metric not in perf_avg_data[bpred].keys():
                        # Create the metric entry with a list
                        perf_avg_data[bpred].update({
                            metric : []
                            })

                    # Append to end of list
                    perf_avg_data[bpred][metric].append(val)
            else:
                # Loop through sizes for a bpred and benchmark
                for size in perf_data[bpred][benchmark].keys():
                    # CHECK size does not exist in perf_avg_data bpred dictionary
                    if size not in perf_avg_data[bpred]:
                        # Create the size entry
                        perf_avg_data[bpred].update({size:{}})

                    # Loop through all metric and values for a brped, benchmark, and size
                    for metric, val in perf_data[bpred][benchmark][size].items():
                        # CHECK metric does not exist in the perf_avg_data bpred size dictionary
                        if metric not in perf_avg_data[bpred][size].keys():
                            # Create the metric entry with a list
                            perf_avg_data[bpred][size].update({
                                metric: [] 
                                })

                        # Append to end of list
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

    # Perfrmance of Taken or Not Taken per benchmark
    taken_bpred_gcc_acc = perf_data['taken']['gcc']['bpred_dir_rate']
    taken_bpred_li_acc = perf_data['taken']['li']['bpred_dir_rate']

    nottaken_bpred_gcc_acc = perf_data['nottaken']['gcc']['bpred_dir_rate']
    nottaken_bpred_li_acc = perf_data['nottaken']['li']['bpred_dir_rate']

    fig, ax = plt.subplots()

    fig.set_figheight(10)
    fig.set_figwidth(12)

    ax.bar(predictors, [taken_bpred_gcc_acc, nottaken_bpred_gcc_acc], width=0.25, align='center')
    ax.set_xticks(range(len(predictors)))
    ax.set_xlabel('Branch Predictors')
    ax.set_xticklabels(predictors)
    ax.set_ylabel('Branch Prediction Accuracy (%)')
    ax.set_title('Taken and Not Taken Peformance by gcc')
    ax.yaxis.grid(True)

    plt.tight_layout()
    plt.savefig(f'{PATH}/logs/taken_nottaken_perf_by_gcc.png')

    fig, ax = plt.subplots()

    fig.set_figheight(10)
    fig.set_figwidth(12)

    ax.bar(predictors, [taken_bpred_li_acc, nottaken_bpred_li_acc], width=0.25, align='center')
    ax.set_xticks(range(len(predictors)))
    ax.set_ylabel('Branch Prediction Accuracy (%)')
    ax.set_xlabel('Branch Predictors')
    ax.set_xticklabels(predictors)
    ax.set_title('Taken and Not Taken Peformance by li')
    ax.yaxis.grid(True)

    plt.tight_layout()
    plt.savefig(f'{PATH}/logs/taken_nottaken_perf_by_li.png')


    # Find the averaged accuracy for each bpred per benchmark
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


    bar_width = 0.10
    
    bpreds = ['bimod', 'gselect', 'gshare', 'comb_bimod_gselect', 'comb_bimod_gshare']

    # List of each averaged bpred per benchmark
    gcc_bpred = [bimod_bpred_avg_gcc_acc, gselect_bpred_avg_gcc_acc, gshare_bpred_avg_gcc_acc, comb_bimod_gselect_bpred_avg_gcc_acc, comb_bimod_gshare_bpred_avg_gcc_acc]
    li_bpred = [bimod_bpred_avg_li_acc, gselect_bpred_avg_li_acc, gshare_bpred_avg_li_acc, comb_bimod_gselect_bpred_avg_li_acc, comb_bimod_gshare_bpred_avg_li_acc]

    fig, ax = plt.subplots()

    fig.set_figheight(10)
    fig.set_figwidth(12)
    
    ax.bar(bpreds, gcc_bpred, width=bar_width, align='center')
    ax.set_ylabel('Branch Prediction Accuracy (%)')
    ax.set_xlabel('Branch Predictors')
    ax.set_xticks(range(len(bpreds)))
    ax.set_xticklabels(bpreds)
    ax.set_title('Average Performance using gcc')
    ax.yaxis.grid(True)

    plt.tight_layout()
    plt.savefig(f'{PATH}/logs/avg_gcc_perf.png')

    fig, ax = plt.subplots()

    fig.set_figheight(10)
    fig.set_figwidth(12)

    ax.bar(bpreds, li_bpred, width=bar_width, align='center')
    ax.set_ylabel('Branch Prediction Accuracy (%)')
    ax.set_xlabel('Branch Predictors')
    ax.set_xticks(range(len(bpreds)))
    ax.set_xticklabels(bpreds)
    ax.set_title('Average Performance using li')
    ax.yaxis.grid(True)
    
    plt.tight_layout()
    plt.savefig(f'{PATH}/logs/avg_li_perf.png')


    # Averaged accuracies for Taken and Not Taken
    taken_bpred_acc = performance_data['taken']['bpred_dir_rate']
    nottaken_bpred_acc = performance_data['nottaken']['bpred_dir_rate']


    fig, ax = plt.subplots()

    fig.set_figheight(10)
    fig.set_figwidth(12)

    ax.bar(range(len(predictors)), [taken_bpred_acc, nottaken_bpred_acc], width=0.25, align='center')
    ax.set_ylabel('Branch Prediction Accuracy (%)')
    ax.set_xlabel('Branch Predictors')
    ax.set_xticks(range(len(predictors)))
    ax.set_xticklabels(predictors)
    ax.set_title('Taken and Not Taken Average Peformance over Benchmarks')
    ax.yaxis.grid(True)

    plt.tight_layout()
    plt.savefig(f'{PATH}/logs/taken_nottaken_avg_perf.png')

    # Create a list of averaged accuracies for each bpred for all sizes
    bimod_bpred_acc = [performance_data['bimod'][size]['bpred_dir_rate'] for size in sizes]
    gselect_bpred_acc = [performance_data['gselect'][size]['bpred_dir_rate'] for size in sizes]
    gshare_bpred_acc = [performance_data['gshare'][size]['bpred_dir_rate'] for size in sizes]

    comb_bimod_gshare_bpred_acc = [performance_data['comb_bimod_gshare'][size]['bpred_dir_rate'] for size in sizes]
    comb_bimod_gselect_bpred_acc = [performance_data['comb_bimod_gselect'][size]['bpred_dir_rate'] for size in sizes]

    fig, ax = plt.subplots()

    fig.set_figheight(10)
    fig.set_figwidth(12)

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

    # IPC for Taken and Not Taken
    taken_bpred_ipc = performance_data['taken']['IPC']
    nottaken_bpred_ipc = performance_data['nottaken']['IPC']

    fig, ax = plt.subplots()

    fig.set_figheight(10)
    fig.set_figwidth(12)

    ax.bar(range(len(predictors)), [taken_bpred_ipc, nottaken_bpred_ipc], width=0.25, align='center')
    ax.set_ylabel('IPC')
    ax.set_xlabel('Branch Predictors')
    ax.set_xticks(range(len(predictors)))
    ax.set_xticklabels(predictors)
    ax.set_title('Taken and Not Taken Average IPC over Benchmarks')
    ax.yaxis.grid(True)
    
    plt.tight_layout()
    plt.savefig(f'{PATH}/logs/taken_nottaken_avg_ipc_perf.png')

    # Create list of IPC of each bpred for all sizes in order
    bimod_bpred_ipc = [performance_data['bimod'][size]['IPC'] for size in sizes]
    gselect_bpred_ipc = [performance_data['gselect'][size]['IPC'] for size in sizes]
    gshare_bpred_ipc = [performance_data['gshare'][size]['IPC'] for size in sizes]

    comb_bimod_gshare_bpred_ipc = [performance_data['comb_bimod_gshare'][size]['IPC'] for size in sizes]
    comb_bimod_gselect_bpred_ipc = [performance_data['comb_bimod_gselect'][size]['IPC'] for size in sizes]

    fig, ax = plt.subplots()

    fig.set_figheight(10)
    fig.set_figwidth(12)

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
    # Create if it does not exist
    os.makedirs(f'{PATH}/logs', exist_ok=True)

    # Create if it does not exist
    os.makedirs(f'{PATH}/simulator/results', exist_ok=True)

    # Set the Run.pl to specified paths
    setup()

    # Initialize perf_data
    init()

    # Run simulation commands
    run_simulations()

    # Parse performance data
    results_dir = f'{PATH}/simulator/results'
    performance_avg_data = parse_performance_data(results_dir)
    
    plot_performance(performance_avg_data)


if __name__ == '__main__':
    main()
