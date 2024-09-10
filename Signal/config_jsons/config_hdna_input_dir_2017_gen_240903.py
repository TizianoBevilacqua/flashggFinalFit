# Config file: options for signal fitting

_year = '2017'

signalScriptCfg = {
  
  # Setup
  'inputWSDir':'/work/bevila_t/HpC_Analysis/HiggsDNA/coffea/FinalFits/CMSSW_10_2_13/src/flashggFinalFit/input_dir_2017_gen_bdt',
  'procs': 'auto', # if auto: inferred automatically from filenames
  'cats':'auto', # if auto: inferred automatically from (0) workspace
  'ext':'hpc_2p0_2017',
  'analysis':'hpc_gen', # To specify which replacement dataset mapping (defined in ./python/replacementMap.py)
  'year':'%s'%_year, # Use 'combined' if merging all years: not recommended
  'massPoints':'125',

  #Photon shape systematics  
  'scales':'', # separate nuisance per year
  'scalesCorr':'ShowerShape,FNUF,Material,Scale,Smearing', # correlated across years
  'scalesGlobal':'', # affect all processes equally, correlated across years
  'smears':'', # separate nuisance per year

  # Job submission options
  'batch':'slurm', # [condor,SGE,IC,local,slurm]
  'queue':'standard', # for condor e.g. microcentury
  'wall':'12:00:00', # [condor,SGE,IC,local]
  'mem':'8000' # for condor e.g. microcentury

}
