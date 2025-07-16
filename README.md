# RC SFA CoreMS Pipeline
This repository will walk you through the installation of CoreMS and necessary pre-requisites, and will also provide all of the necessary files to replicate the pipeline which the River Corridor Hydrobiogeochemistry Science Focus Area (RC SFA) from PNNL uses to process FTICR-MS data.

## Contents
1) [Installing](https://github.com/danczakre/WHONDRS_CoreMS/edit/main/README.md#instructions-for-installing-corems)
2) [Running](https://github.com/danczakre/WHONDRS_CoreMS/edit/main/README.md#running-the-corems-pipeline)
3) [Troubleshooting](https://github.com/danczakre/WHONDRS_CoreMS/edit/main/README.md#troubleshooting)
4) [Acknowledgments](https://github.com/danczakre/WHONDRS_CoreMS/edit/main/README.md#acknowledgements)

## Instructions for installing CoreMS
### Overview
Due to recent efforts from researchers at EMSL to improve formula assignment and overall processing of high-resolution mass spectrometry data, we are moving away from using Formularity/Formultitude to generate accessible FTICR-MS data and towards **CoreMS**. **CoreMS** is a framework used to analyze many types of mass spectrometry data and there is no single right way to use it (though there are plenty of wrong ways…). **CoreMS** provides several benefits over our previous workflow: 

1)	We have finer control over each step of the analytical process from peak calling to formula assignment
2)	It is open-source and non-proprietary, 
3)	It is agnostic towards operating system because it is written using Python. 

This instruction set will walk you through how to install CoreMS and all prerequisites, run our SFA’s CoreMS script, and regenerate our published datasets (or apply these methods to your own datasets). By default, our CoreMS-based pipeline accepts a variety of data types including raw FIDs from Bruker instruments, XML/mass lists generated using Bruker Data Analysis, and a series of miscellaneous mass lists; the script will identify the data type using the extension. This instruction set assumes limited knowledge of Python, conda/mamba, and similar programs – if you have experience with these, some of this information might be redundant!

<ins>**Disclaimer:**</ins> We are not affiliated with the CoreMS development team and any issues with this instruction set are not associated with them. Please submit an issue to this repository if you run into any problems.

<ins>**Important Note:**</ins> We set this signal-to-noise threshold to **12** for filtering peaks picked by Bruker's Data Analysis; this is fairly conservative. Feel free to change this to your needs (e.g., search for *filter_by_s2n* in the CoreMS_Runner.py file) and keep an eye out for an option that might be added down the road (we don't change it often on our end for standardization - but instrumental changes often merit changes).

### Requirements
- Reading through the CoreMS GitHub page (https://github.com/EMSL-Computing/CoreMS)
- Download this repository - store is somewhere memorable!
- Any computer
  - These instructions are written for Windows and macOS; if you are using Linux, the macOS instructions should be equivalent
  - Some computers will likely run through the analyses slower than others, so the computer should be recent (newer than 2020-2021)
- mamba installed via Miniforge
  - Please read through and follow the instructions that corresponds to your device on their GitHub: https://github.com/conda-forge/miniforge
  - mamba allows us to use “virtual environments” which give us complete control of versioning (e.g., things installed into one virtual environment don’t impact the rest of your computer or other environments)
  - There are other virtual environment tools, but (virtualenv, etc.) but mamba has had great reproducibility and isolation for us.
- R and RStudio
  - Download and install R: https://www.r-project.org/
  - Download and install RStudio: https://posit.co/download/rstudio-desktop/
- _Recommended, but optional:_ An integrated development environment (IDE) of your choice – we recommend using VS Code (https://code.visualstudio.com/)
  - An IDE is a program that allows you to have a bit more control over scripting and coding that simply writing in a simple text editor. This is useful if you plan on editing the script and want to do some testing on your own.
  - VS Code is compatible with many different languages and, notably, interfaces well with virtual environments
  - Each IDE will need to be configured differently so please look up how to configure VS Code if you desire
  - RStudio is an IDE made specifically for R, but can also be configured to work with other languages.

### Instructions
1) Download CoreMS repo from GitHub (either via the website or using git clone)
   -	Make sure you store it somewhere memorable and intentional where you won’t accidentally delete it – let’s call this location **/Documents/CoreMS-3.1.0/**
2) Open your terminal
   - **On Windows** – open Miniforge Prompt
   - **On macOS** – open Terminal
3) **If on macOS**: Install mono via homebrew
   - Please see https://brew.sh/ for information about homebrew, how to install it, and why you should use it on macOS
   - Run the following commands in Terminal
```
brew update
brew upgrade
brew install mono
```

4) Create new virtual environment by running the following commands in your terminal
   - One of the advantages of virtual environments is the control of software versions. By naming this environment after the date that you install (or the version of CoreMS you are using), you can always ensure you can go back to a known working and good version.
```
mamba update --all
mamba create -n corems-3.1.0
```

5) Activate your virtual environment and install Python v3.10 by running the following commands in your terminal
```
conda activate corems-3.1.0
mamba install python=3.10
```

6) Install dependencies by running the following command in your terminal
```
mamba install pip git pythonnet psycopg2-binary
# CoreMS v3.3.0 has psycopg2-binary listed as a requirement, so psycopg2-binary is no longer necessary if you deploy the most recent version
```

7) Deactivate and reactivate the virtual environment to ensure it loads correctly
```
conda deactivate
mamba activate corems-3.1.0
```

9) Install CoreMS into your virtual environment from the git repo
```
pip install git+https://github.com/EMSL-Computing/CoreMS.git@c77d0ae14287a69e3c2cee410267ed63ab479bca
# This will download and install CoreMS-3.1.0 based on CoreMS's commit history
# Our single file branch is experimenting with more recent versions of CoreMS
```

10) Install Podman, an open-source alternative to Docker
    - **On Windows:** Follow the instructions from Podman’s own documentation (https://podman-desktop.io/docs/installation/windows-install)
      - You will also need to ensure you have “Compose” setup (https://podman-desktop.io/docs/compose/setting-up-compose). There should be an option during the Podman Desktop installation process.
      - **Important:** After you install Podman and it asks if you want to initialize a machine, press the "Skip" button in the upper right corner of the window to move onto the Compose installation.
    - **On macOS:** Use homebrew to install Podman
```
brew install podman
brew install podman-compose
```

11) Load CoreMS’s database Docker image into Podman
    - **On Windows:** Open Command Prompt instead of Miniforge Prompt for this section
```
cd /Documents/CoreMS-3.1.0/
podman machine init
podman machine start
podman-compose up -d
podman container list
# Listing the containers just confirms everything is running – you should see a single entry including “corems” in the name
```
```
# Occasionally, the database generation can fail but no error will appear.
# You'll be able to tell by 1) the scripts running very fast, and 2) no formulas being assigned.
# To fix this, you need to remove volumes in podman; from there, you should be good!
podman volume ls
podman volume rm [volume name]
```

12) Test your CoreMS installation using the provided Python script and test data
    - In your terminal, make sure that you have started your CoreMS environment
      - ```mamba activate corems-3.1.0```
    - Run the “CoreMS_Runner.py” script on the provided example data (be sure that you are running CoreMS_Runner.py from the downloaded RCSFA_CoreMS repository)
      - ```python CoreMS_Runner.py -i [path-to-CoreMS-repo]/tests/tests_data/ftms -o [path-to-RCSFA-repo]/Output -r [path-to-Hawkes_neg.ref]```
    - If you see an output in your chosen output folder, everything worked correctly!
   
## Running the CoreMS Pipeline
Assuming everything above worked (or that you had CoreMS installed through another mechanism), you are ready to run our pipeline. In principle, there are two steps to run data through CoreMS and we’ve provided example data for you to test each step.

1) Run the CoreMS_Runner.py script on your data or the example data (*Test_Raw*). To run this script, you will need to change your directory to the downloaded RCSFA_CoreMS repository location and you need to ensure you have your corems-3.1.0 environment activated through conda.
```
python CoreMS_Runner.py -i /Documents/Input_Data -o /Documents/Processed_Data -r /Documents/CoreMS-3.1.0/db/Hawkes_neg.ref

Required Options:
-i = input folder (please specify the full path)
-o = output directory (please specify the full path)
-r = location of reference for calibration; feel free to move the reference file elsewhere [found in the CoreMS repo by default]

Optional Options:
-t = threshold method used in peak identification when run on a raw data file; xmls are always run using SN (default: log)
-c = calibration value used for selecting points (default: 5)
-sn = set the signal-to-noise threshold if you do not want the default; I recommend either 7 or 12 (default: 12)
```

2) Run the CoreMS_MergeProcess.Rmd script in RStudio.
   - Install all the required packages in R
```
install.packages(c(“devtools”, “tidyverse”))
devtools::install_github("bogind/easycsv") # easycsv was on CRAN but removed...
devtools::install_github("EMSL-Computing/ftmsRanalysis@1.0.0") # make sure you use version #1 for now
```
   - Change your input directory to your processed data or our example data (*Test_Processed*)
     - Currently, the script is configured to use easycsv (an OS agnostic package) to prompt the user to input their desired directory, though sometimes this can fail. In this case, you can set path_to_dir to your input directory. 
   - Click “Knit” at the top of the RStudio window

## Troubleshooting
**mamba/conda Troubleshooting**
- Removing a conda environment
  - Sometimes, our environments break (an inevitiblity it seems sometimes). Fortunately, we can remove them and restart from the beginning.
  - List your environments to find the name of interest: ```mamba env list```
  - Remove your environment (assuming it's the CoreMS environment): ```mamba env remove -n CoreMS-3.1.0```
- conda/mamba confusion
  - These commands are virtually interchangable though there are some instances where they shouldn't be substituted
  - Given some inconsistencies in behavior that would lead to confusion, following the patterns above should serve you well. Specifically, use **conda to activate/deactivate environments** and use **mamba to install packages and create environments**.

**CoreMS Troubleshooting**
- This should only occur if you've updated macOS from Sonoma to Sequoia while you already had a CoreMS environment, but it is possible that you run into an error associated with Fortran. To resolve this, please run: ```mamba install "libgfortran5>=14"```


**Podman Troubleshooting**
- **Windows:** On occasion, Podman will appear running but ultimately any command you try to run will fail (e.g., Step 10d doesn’t work). This appears to be the result of a file not generating correctly.
  - Navigate to C:\Users\[current user]
  - If you do not see a folder named .ssh, please create it
  - Navigate into that folder
  - Create a new, empty text file named ‘known_hosts’ without any extension
  - Run podman ps -a in your Command Prompt; if you see an output, this fix has succeeded, if not, please send us a message
- **Windows:** Podman requires that your system has the necessary virtualization subsystems enabled. For most installations of Windows 10/11, these features will be enabled by default (for example, many newer security features require virtualization). Some Windows systems may not be completely configurated and require a couple extra steps.
  - After installing Podman (Step 9), you’ll see a message about virtualization not being enabled. This message will have an accompanying link with instructions - if you follow the instructions, you should be able to enable virtualization and proceed to Step 10. 
- **Windows:** In limited situations, communication with the Docker image server is impossible resulting in Step 10d failing with an error message like “Temporary failure in name resolution”. 
  - This is likely a result of your corporate security infrastructure blocking communication with the necessary server. Please reach out to IT to see if access to the necessary servers (registry-1.docker.io).
  - If you are still having issues, please let us know.
 
## Acknowledgements
This pipeline leverages tools made by lots of talented folks. If you are using this repo for any reason, please cite at least each of the following (though look at our manuscripts for a more complete list of common FTICR-MS related citations):
1) **CoreMS** - [GitHub Link](https://github.com/EMSL-Computing/CoreMS)
2) **ftmsRanalysis** - [GitHub Link](https://github.com/EMSL-Computing/ftmsRanalysis) and [Manuscript](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1007654)
3) **lambda** - [GitHub Link](https://github.com/hyunseobsong/lambda) and [Manuscript](https://doi.org/10.3389/fmicb.2020.531756)

