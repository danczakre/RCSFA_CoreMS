@echo off
:: This batch script is meant to run the single file version of the RCSFA-CoreMS pipeline
:: in a for loop to save researchers time in building their own.
::
:: Inputs (All directories need to be full paths):
:: %1 = path to CoreMS_Runner.py
:: %2 = input directory
:: %3 = output directory
:: %4 = calibration reference location
:: %5 = threshold option (default: log)
:: %6 = number of points for automated calibration (default: 5)

echo %date% %time%

:: setup
:: parsing inputs
set corems_path=%1
set in_dir=%2
set out_dir=%3
set ref_loc=%4
if "%5"=="" (set thresh=log) else (set thresh=%5)
if "%6"=="" (set cal_pt=5) else (set cal_pt=%6)

:: switch to input directory
pushd "%in_dir%"

:: run CoreMS_Runner.py
:: loops
for %%f in (*.xml) do (
    python "%corems_path%\CoreMS_Runner_Single_CoreMSv3-3.py" -i "%%f" -d "%in_dir%" -o "%out_dir%" -r "%ref_loc%" -t "%thresh%" -c "%cal_pt%"
)

for %%f in (*.txt) do (
    python "%corems_path%\CoreMS_Runner_Single_CoreMSv3-3.py" -i "%%f" -d "%in_dir%" -o "%out_dir%" -r "%ref_loc%" -t "%thresh%" -c "%cal_pt%"
)

for %%f in (*.d) do (
    python "%corems_path%\CoreMS_Runner_Single_CoreMSv3-3.py" -i "%%f" -d "%in_dir%" -o "%out_dir%" -r "%ref_loc%" -t "%thresh%" -c "%cal_pt%"
)

:: return to original directory
popd

:: print done date
echo %date% %time%
