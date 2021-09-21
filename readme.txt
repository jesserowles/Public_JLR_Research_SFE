This repository performs the analyses in my MS thesis. This includes:
1.	Calculation of IFTs - each of the Instream Flow Target (IFT) calculation methods has its own script in the IFT Calculation folder. 
2.	SEWAM Results Analyses - each of the types of plots presented in the thesis (plus some others) can be generated using the python scripts in the SEWAM Results Analyses folder.

The folders are as follows:
- IFT Calculation Scripts: This folder contains python scripts for calculating IFTs
	- The scripts are numbered in the order they should be run. 
		- "00_": these contain functions that are called by the other scripts and are not designed to be run by themselves
		- "01_": determine MAF at each location, and WMT and WYT (these should be run before WEAP is run so WEAP knows what the current WMT/WYT is so it can determine which IFT to use). 
		- "02_": These actually calculate IFTs using results of "01_" scripts.
	- Each IFT method has its own script with the name of the method (e.g., EPP, FFM, MPOF, etc.) in the script filename.
	- "determine_paradigm_maf" calculates mean annual flow (MAF) from unimpaired flow and saves into Reference Files table.
	- "get_wmt..." and "get_wyt..." scripts determine water month type (WMT) and water year types(WYT) respectively.
	- "get_all_sfe_lois" obtains list of LOIs and some geographic characteristics from Reference Files
	- "read_loi_paradigm_flows" reads in unimpaired flow data as a dataframe.
- IFT Results: This folder contains results of the IFT calculation scripts. Specific method results are stored in subfolders.
- Reference Files: Contains lookup tables and other files with information used in processing.
- SEWAM Results Analyses: Resulting plots of scripts that process SEWAM results
- SEWAM Results Scripts: This folder contains python and R scripts for processing and plotting SEWAM results
	- The scripts are numbered in the order they should be run. 
		- "00_": these contain functions that are called by the other scripts and are not designed to be run by themselves
		- "01_": should be run first to fix scenario numbers in results, and calculate demand-based Reach Setting Parameters.
		- "02_": the only scripts in this level are ones that process WEAP results
		- "03_": only after weap results are processed ("02_") can result plots be generated
	- "q1_...", "q2a_...", etc.: the script to answer each research question is labeled by that question number. The research question intended to be answered by the plot is in the comments in each python file
	- lookup_scenarios: functions to take scenario number and turn it into text
	- plot_performance: each function to create plots is defined here. q1_..., q2a..., etc. scripts process data for use in these functions to create plots.
	- process_upstream_demands: calculates demand-based RSPs from 'SFER_Results_BaselineMGMT_NoIFT_Criteria.csv' which is SEWAM results in the baseline/no IFT scenario.
	- 'weap_results_v1' and '..._v2': these take WEAP results (v1 - Sept 2020 results, v2 - April 2021 results), process them and fix some things like rounding flow values to 0.001 and dates that have 0 flow because of WEAP errors, and calculates performance values for each location/scenario combination.
- Unimpaired Flow: This folder contains data sheets that represent unimpaired flow for each location.

Notes:
	1.	The scripts in the two 'Scripts' folders are numbered in order to be run. 
	2.	Due to data sharing restrictions, complete model results cannot be shared at this time. Due to this, dummy data was provided for Unimpaired Flow and Model Results. Dummy data is provided for 3 locations with LOI numbers 1111, 5555, and 9999. Each LOI number corresponds with a COMID number that is twice the number of digits of the LOI number (i.e., LOI 1111 is COMID 11111111, LOI 5555 is COMID 55555555, and LOI 9999 is COMID 99999999). These LOIs do not correspond with any point in space and are only provided so the scripts can be run.
	3.	All of the scripts rely on the current working directory being the Public_JLR_Research_Repo location. The folders and files that must be loaded are specified in the scripts relative to this path.
		- When running R scripts, the code specifies the absolute path since R does not automatically open to the working directory of interest. So, when you download this repository, change the line in the R scripts where the current directory is specified [look for "setwd(...)" in the script)] 
		- When running python scripts, the current working directory should be set as the Public_JLR_Research_Repo location if the python console is initiated in the project location. The location of the current working directory can be checked by running "import os;os.getcwd()". If it is not automatically set to the Public_JLR_Research_Repo location, the line "import os; os.chdir(path)" (where 'path' is the absolute path to Public_JLR_Research_Repo on your machine) will need to be run to change the working directory. 

Python toolboxes (and versions, if applicable) that need to be installed for these scripts to work are as follows:
numpy - 1.16.4
pandas - 0.24.2
simpledbf 
datetime
matplotlib - 3.3.4
calendar
statsmodels - 0.10.0
scipy - 1.2.1
seaborn - 0.9.0
mpl_toolkits

If you encounter any problems or have any questions, please email me at jesserowles@gmail.com
