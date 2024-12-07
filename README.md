# Global History Predictor with Index Selection in SimpleScalar
An implementation of `gselect` branch predictor for the SimpleScalar simulator.
## Features
A cost effective (in terms of footprint) global branch predictor that competes with its counterpart `gshare`. The benchmark analysis is automated by the `run.py` script under Debian Linux machines. Please refer to the documents found in `docs/` for more information. Some setup is required to run the simulator.
## How To
The library modules are defined in the `requirements.txt`. To get started, setup your environment:
```console
$ python3 -m venv proj_env
$ source ./proj_env/bin/activate
$ pip3 install -r ./requirements.txt
```
**NOTE**: If your global installation of python3 does not have the module `virtualenv` installed. Look up how to install python3 modules for your Debian Linux based machine.
Now that you have your environment setup, you can start simulating by:
```console
$ ./run.py
```
## Benchmarks
The benchmarks that closely followed McFarling's paper that was available for the SPEC2000 benchmarks was the following:
* li
* gcc
* tomcatv
* fpppp
**NOTE**: fpppp took too long to run to show in our demo and tomcatv did not work unfortunately. These two benchmarks were excluded in our anaylsis. If more time was given for the project. Then can look in to including these benchmarks.
## Reference
* [WRL Technical Note TN-36:Combining Branch Predictors](docs/WRL_Technical_Note_TN-36_Combining-Branch-Predictors_Mcfarling.pdf), Scott McFarling, 1993
* [SimpleScalar Simulator](https://github.com/toddmaustin/simplesim-3.0)
## License
Please refer to the MIT license attached to this repository. We do not own SimpleScalar simulator. It was used only for the purpose for academic research and to further our understanding.
