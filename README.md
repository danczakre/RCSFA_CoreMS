# WHONDRS CoreMS Pipeline
This repository will walk you through the installation of CoreMS and necessary pre-requisites, and will also provide all of the necessary files to replicate the pipeline which the River Corridor Hydrobiogeochemistry Science Focus Area (RC SFA) from PNNL uses to process FTICR-MS data.


## Instructions for installing CoreMS
### Overview
Due to recent efforts from researchers at EMSL to improve formula assignment and overall processing of high-resolution mass spectrometry data, we are moving away from using Formularity/Formultitude to generate accessible FTICR-MS data and towards **CoreMS**. **CoreMS** is a framework used to analyze many types of mass spectrometry data and there is no single right way to use it (though there are plenty of wrong ways…). **CoreMS** provides several benefits over our previous workflow: 

1)	We have finer control over each step of the analytical process from peak calling to formula assignment
2)	It is open-source and non-proprietary, 
3)	It is agnostic towards operating system because it is written using Python. 

This instruction set will walk you through how to install CoreMS and all prerequisites, run our SFA’s CoreMS script, and regenerate our published datasets (or apply these methods to your own datasets). By default, our CoreMS-based pipeline accepts a variety of data types including raw FIDs from Bruker instruments, XML/mass lists generated using Bruker Data Analysis, and a series of miscellaneous mass lists; the script will identify the data type using the extension. This instruction set assumes limited knowledge of Python, conda/mamba, and similar programs – if you have experience with these, some of this information might be redundant!

<ins>**Disclaimer:**</ins> We are not affiliated with the CoreMS development team and any issues with this instruction set are not associated with them. Please reach out to us with any issues that arise if you are using our instructions.

### Requirements
- Reading through the CoreMS GitHub page (https://github.com/EMSL-Computing/CoreMS)
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
   -	Make sure you store it somewhere memorable and intentional where you won’t accidentally delete it – let’s call this location **/Documents/CoreMS-[current date or version]/**
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
mamba create -n corems-[current date or version]
```

5) Activate your virtual environment and install Python v3.10 by running the following commands in your terminal
```
mamba activate corems-[current date or version]
mamba install python=3.10
```

6) Install dependencies by running the following command in your terminal
```
mamba install pip git pythonnet psycopg2-binary
# I suspect we're safe without the psycopg2-binary, but I have yet to do A/B testing
```

7) Deactivate and reactivate the virtual environment to ensure it loads correctly
```
mamba deactivate
mamba activate corems-[current date or version]
```

9) Install CoreMS into your virtual environment from the git repo
```
pip install git+https://github.com/EMSL-Computing/CoreMS
# This will download and install the current version of CoreMS, regardless of the version you downloaded above
```

10) Install Podman, an open-source alternative to Docker
    - **On Windows:** Follow the instructions from Podman’s own documentation (https://podman-desktop.io/docs/installation/windows-install)
      - You will also need to ensure you have “Compose” setup (https://podman-desktop.io/docs/compose/setting-up-compose)
    - **On macOS:** Use homebrew to install Podman
```
brew install podman
brew install podman-compose
```

11) Load CoreMS’s database Docker image into Podman
    - On Windows: Open Command Prompt instead of Miniforge Prompt for this section
```
cd /Documents/CoreMS-[current date or version]/
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
      - ```mamba activate corems-[current date or version]```
    - Run the “CoreMS_Runner.py” script on the provided example data
      - ```python CoreMS_Runner.py /Documents/CoreMS-[current date or version]/tests/tests_data/ftms/srfa_neg_xml_example.xml /Documents/Output```
    - If you see an output in your chosen output folder, everything worked correctly!

**Podman Troubleshooting**
- Windows: On occasion, Podman will appear running but ultimately any command you try to run will fail (e.g., Step 10d doesn’t work). This appears to be the result of a file not generating correctly.
  - Navigate to C:\Users\[current user]
  - If you do not see a folder named .ssh, please create it
  - Navigate into that folder
  - Create a new, empty text file named ‘known_hosts’ without any extension
  - Run podman ps -a in your Command Prompt; if you see an output, this fix has succeeded, if not, please send us a message
