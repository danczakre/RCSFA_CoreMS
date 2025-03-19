#!/bin/bash
# This shell script is meant to run the single file version of the RCSFA-CoreMS pipeline
# in a for loop to save researchers time in building their own.
#
# Inputs (All directories need to be full paths):
# $1 = path to CoreMS_Runner.py
# $2 = input directory
# $3 = output directory
# $4 = calibration reference location
# $5 = threshold option (default: log)
# $6 = number of points for automated calibration (default: 5)

date

## setup
# parsing inputs
corems_path="$1"
in_dir="$2"
out_dir="$3"
ref_loc="$4"
thresh="${5:-'log'}"
cal_pt="${6:-5}"

# switch to input directory
cd "$in_dir"

## run CoreMS_Runner.py
# loop
for file in *;
    do if [[ $file =~ \.(xml|txt|d)$ ]]; then
        python "$corems_path"/"CoreMS_Runner_Single.py" -i "$file" -d "$in_dir" -o "$out_dir" -r "$ref_loc" -t "$thresh" -c "$cal_pt"
        echo "Finished running" $file
    else
        echo $file "is not compatible with our CoreMS pipeline"
    fi
done

# print done date
date
