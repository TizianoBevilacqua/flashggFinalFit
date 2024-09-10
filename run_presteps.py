# Author Tiziano Bevilacqua (17/03/2023) 
# Script to run FlashggFinalFit Signal, Background and Datacard steps

import re, os, sys, glob, time, logging, multiprocessing, socket, subprocess, shlex, getpass, math, shutil
from optparse import OptionParser
import json
import inspect
import subprocess

# ---------------------- A few helping functions  ----------------------

def colored_text(txt, keys=[]):
    _tmp_out = ''
    for _i_tmp in keys:
        _tmp_out += '\033['+_i_tmp+'m'
    _tmp_out += txt
    if len(keys) > 0: _tmp_out += '\033[0m'

    return _tmp_out

color_dict = {
    "cyan": '\033[96m',
    "green": '\033[92m',
    "red": '\033[91m',
    "yellow": '\33[33m',
    "blue": '\33[34m',
    "white": '\033[37m',
    "bold": '\033[01m',
    "end": '\033[0m'
    
}

def KILL(log):
    raise RuntimeError('\n '+colored_text('@@@ FATAL', ['1','91'])+' -- '+log+'\n')

def WARNING(log):
    print ('\n '+colored_text('@@@ WARNING', ['1','93'])+' -- '+log+'\n')

def MKDIRP(dirpath, verbose=False, dry_run=False):
    if verbose: print ('\033[1m'+'>'+'\033[0m'+' os.mkdirs("'+dirpath+'")')
    if dry_run: return
    try:
      os.makedirs(dirpath)
    except OSError:
      if not os.path.isdir(dirpath):
        raise
    return

def EXE(cmd, suspend=True, verbose=False, dry_run=False):
    if verbose: print ('\033[1m'+'>'+'\033[0m'+' '+cmd)
    if dry_run: return

    _exitcode = os.system(cmd)
    _exitcode = min(255, _exitcode)

    if _exitcode and suspend:
       raise RuntimeError(_exitcode)

    return _exitcode

def is_job_finished(prev_step):
    submit_command = f'squeue -o "%.10i %.9P %.48j %.8u %.8T %.10M %.9l %.6D %R" -u bevila_t | grep {prev_step} | wc -l'
    result = subprocess.run(submit_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    output = result.stdout.strip()

    return output == "0"

#--------------------------------------------------------------------------------------------------------------------------#
#- USAGE: -----------------------------------------------------------------------------------------------------------------#
#- python33 run_presteps.py --input ../out_dir_syst_090323/ --sig --bkg --data --sig_config config_hdna_input_dir_16cats_diophotonID_newggHBDT_260423_2017.py -#
#--------------------------------------------------------------------------------------------------------------------------#

# Read options from command line
usage = "Usage: python3 %prog filelists [options]"
parser = OptionParser(usage=usage)
parser.add_option("--input", dest="input", type="string", default="higgs_dna_signals_2017_cats", help="input dir")
parser.add_option("--sig", dest="signal", action="store_true", default=False, help="Do Signal steps")
parser.add_option("--skip", dest="skip", type="string", default="", help="Comma separated steps to skip during run.")
parser.add_option("--skip_vtx_split", dest="skip_vtx_split", action="store_true", default=False, help="Skip vertex splitting scenario")
parser.add_option("--doEffAccFromJson", dest="doEffAccFromJson", action="store_true", default=False, help="do EffxAcc calculation from json")
parser.add_option("--prune", dest="prune", action="store_true", default=False, help="do pruning of datacard")
parser.add_option("--bkg", dest="background", action="store_true", default=False, help="Do Background step")
parser.add_option("--data", dest="datacard", action="store_true", default=False, help="Do Datacard step")
parser.add_option("--sig_config", dest="sconfig", type="string", default="config_hdna_2017.py", help="configuration file for Signal steps, as it is now it must be stored in Signal directory in FinalFit")
parser.add_option("--bkg_config", dest="bconfig", type="string", default="config_hdna_2017.py", help="configuration file for Background steps, as it is now it must be stored in Background directory in FinalFit")
parser.add_option("--dc_config", dest="dconfig", type="string", default="config_hdna.py", help="configuration file for Datacard steps, as it is now it must be stored in Datacard directory in FinalFit")
parser.add_option("--syst", dest="syst", action="store_true", default=False, help="Do systematics variation treatment")
parser.add_option("--ext", dest="ext", type="string", default="test_hdna", help="extension to attach to names")
parser.add_option("--verbose", dest="verbose", type="string", default="INFO", help="verbose lefer for the logger: INFO (default), DEBUG")
parser.add_option("--year", dest="year", type="string", default="2017", help="year")
(opt,args) = parser.parse_args()

skip = opt.skip.split(",")
opt.input = os.path.abspath(opt.input)
if opt.signal:
    print("Running signal steps...")
    print("-"*120)
    print(f"input signal config {opt.sconfig}")
    os.chdir("Signal")
    with open(opt.sconfig) as f:
        exec(f.read())
    _cfg = signalScriptCfg

    if opt.skip_vtx_split: 
        skip_vtx = "--skipVertexScenarioSplit" 
    else:
         skip_vtx = ""
    if "ftest" not in skip:
        if opt.skip_vtx_split: skip_vtx = "--skipWV" 
        else: skip_vtx = ""
        os.system(f"python3 RunSignalScripts.py --inputConfig {opt.sconfig} --mode fTest --modeOpts \"--doPlots {skip_vtx}\"")
    if "syst" not in skip:
        if _cfg["batch"] == "slurm":
            # Wait for the job to finish
            while not is_job_finished("fTest"):
                print(f"fTest Jobs are still running...")
                time.sleep(30) 
            print(f"fTest Jobs are finished, continuing with systematics")
        os.system(f"python3 RunSignalScripts.py --inputConfig {opt.sconfig} --mode calcPhotonSyst")

    if "fit" not in skip:
        if _cfg["batch"] == "slurm":
            # Wait for the job to finish
            while not is_job_finished("Syst"):
                print(f"Syst Jobs are still running...")
                time.sleep(30) 
            print(f"Systematics Jobs are finished, continuing with fit")
        if opt.doEffAccFromJson: 
            print("Using eff x acceptance from json file file, have you set it up properly?")
            doEffAccFromJson = "--doEffAccFromJson"
        else:
            print("Using eff x acceptance from input file, I suppose you have normilised it properly, did you?")
            doEffAccFromJson = ""
        if opt.skip_vtx_split: 
            skip_vtx = "--skipVertexScenarioSplit" 
        else: 
            skip_vtx = ""
        os.system(f"python3 RunSignalScripts.py --inputConfig {opt.sconfig} --mode signalFit --modeOpts \"{skip_vtx} --doPlots {doEffAccFromJson}\"")
    if "package" not in skip:
        if _cfg["batch"] == "slurm":
            # Wait for the job to finish
            while not is_job_finished("signalFit"):
                print(f"Fit Jobs are still running...")
                time.sleep(30) 
            print(f"Fit Jobs are finished, continuing with fit")
        os.system(f"python3 RunPackager.py --cats {_cfg['cats']} --inputWSDir {_cfg['input']} --ext {_cfg['ext']} --batch local --massPoints {_cfg['massPoints']} --year {_cfg['year']}")
    os.chdir("..")
    print("Signal steps done.")
    print("-"*120)

if opt.background:
    print("Running background steps...")
    print("-"*120)
    os.chdir("Background")
    if "ftest" not in skip:
        os.system(f"python3 RunBackgroundScripts.py --inputConfig {opt.bconfig} --mode fTestParallel")
    os.chdir("..")
    print("Background steps done.")
    print("-"*120)

if opt.datacard:
    print("Running datacard steps...")
    print("-"*120)
    os.chdir("Datacard")
    if "syst" not in skip:
        print("|---> doing systematic step")
        doSystematics = "--doSystematics"
    else:
        doSystematics = ""
    os.system(f"python3 RunYields.py --inputWSDirMap {opt.year}={opt.input} --cats auto --procs auto --batch local --ext {opt.ext} {doSystematics} --skipZeroes")
    if opt.prune:
        os.system(f"python3 makeDatacard.py --years {opt.year} --ext {opt.ext} {doSystematics} --prune")
    else:
        os.system(f"python3 makeDatacard.py --years {opt.year} --ext {opt.ext} {doSystematics}")
    os.chdir("..")
    print("datacard steps done.")
    print("-"*120)
