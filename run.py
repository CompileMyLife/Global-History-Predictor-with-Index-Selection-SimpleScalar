#!/usr/bin/env python3

import os
import subprocess as subp
import re
from typing import Dict, Optional
import matplotlib.pyplot as plt  # Add this import for plotting

# Ensure necessary directories exist
os.makedirs('logs', exist_ok=True)
os.makedirs('../simulator/results', exist_ok=True)

# Simulation commands
cmds = [
    '''../simulator/Run.pl -db ../simulator/bench.db -dir ../simulator/results/gcc1 -benchmark gcc -sim /u/kunjan/ECE_587_hw2/simulator/ss3/sim-outorder -args "-fastfwd 1000000 -max:inst 1000000" >& ../simulator/results/gcc1_outorder.out ''',

    '''../simulator/Run.pl -db ../simulator/bench.db -dir ../simulator/results/gcc1 -benchmark gcc -sim /u/kunjan/ECE_587_hw2/simulator/ss3/sim-outorder -args "-issue:inorder -fastfwd 1000000 -max:inst 1000000" >& ../simulator/results/gcc1_inorder.out ''',
]

# Logging function
def log_command_and_output(cmd: str, stdout: str, stderr: str, log_filename: str) -> None:
    with open(log_filename, 'a') as log_file:
        log_file.write(f"Executing Command: {cmd}\n")
        log_file.write(f"Standard Output:\n{stdout}\n")
        log_file.write(f"Standard Error:\n{stderr}\n")
        log_file.write("=" * 80 + "\n")

# Run simulation commands
def run_simulations() -> None:
    log_filename = 'logs/command_logs.txt'
    for cmd in cmds:
        try:
            process = subp.run(cmd, shell=True, stdout=subp.PIPE, stderr=subp.PIPE, universal_newlines=True)
            log_command_and_output(cmd, process.stdout, process.stderr, log_filename)

            if process.returncode != 0:
                print(f"ERROR executing command: {cmd}\n{process.stderr}")
            else:
                print(f"Command executed successfully: {cmd}\n{process.stdout}")
        except Exception as e:
            print(f"Exception occurred while executing command: {cmd}\n{e}")

# Parse IPC from a result file
def parse_ipc_from_file(file_path: str) -> Optional[float]:
    ipc_pattern = r"sim_IPC\s+([\d.]+)"  # Adjust the pattern based on your result file format
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        match = re.search(ipc_pattern, content)
        if match:
            return float(match.group(1))
        else:
            print(f"IPC not found in file {file_path}")
            return None
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return None

# Parse performance data from result files
def parse_performance_data(results_dir: str) -> Dict[str, float]:
    performance_data = {}
    for file_name in os.listdir(results_dir):
        file_path = os.path.join(results_dir, file_name)
        if file_name.endswith(".out"):
            ipc = parse_ipc_from_file(file_path)
            if ipc is not None:
                performance_data[file_name] = ipc
    return performance_data

# Plot IPC values
def plot_ipc_values(performance_data: Dict[str, float]) -> None:
    if not performance_data:
        print("No performance data available for plotting.")
        return

    # Sort performance data for consistent plotting
    sorted_data = sorted(performance_data.items(), key=lambda x: x[0])
    labels, values = zip(*sorted_data)

    # Create the bar chart
    plt.figure(figsize=(10, 6))
    plt.bar(labels, values, color='skyblue')
    plt.xlabel('Result Files')
    plt.ylabel('IPC')
    plt.title('IPC Values from Simulation Results')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    # Save and display the plot
    plt.savefig('logs/ipc_plot.png')
    print("IPC plot saved to logs/ipc_plot.png")
    plt.show()

def main() -> None:
    # Run simulation commands
    run_simulations()

    # Parse performance data
    results_dir = '../simulator/results'
    performance_data = parse_performance_data(results_dir)

    # Log performance data
    with open('logs/performance_data.txt', 'w') as perf_log:
        for file, ipc in performance_data.items():
            perf_log.write(f"{file}: IPC = {ipc}\n")
    print("Performance data logged to logs/performance_data.txt")

    # Plot performance data
    plot_ipc_values(performance_data)

if __name__ == '__main__':
    main()
