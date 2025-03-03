# %%
### CoreMS function
# This is the CoreMS script as a callable function, rather than just a script.
#
# This version includes the automatic correlation checker which should optimize the calibration
# process a bit.

# Routine libraries
import os  # noqa: E402
import re  # noqa: E402
import sys  # noqa: E402
import argparse #noqa:E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import itertools as it  # noqa: E402

# CoreMS functions
from corems.mass_spectrum.input.massList import ReadMassList, ReadBrukerXMLList  # noqa: E402
from corems.transient.input.brukerSolarix import ReadBrukerSolarix  # noqa: E402
from corems.molecular_id.search.molecularFormulaSearch import SearchMolecularFormulas  # noqa: E402
from corems.encapsulation.factory.parameters import MSParameters  # noqa: E402
from corems.mass_spectrum.factory.MassSpectrumClasses import MassSpecCentroid  # noqa: E402
from corems.mass_spectrum.calc.Calibration import MzDomainCalibration  # noqa: E402

# parsing arguments
parser = argparse.ArgumentParser(
                    prog='CoreMS (RC-SFA)',
                    description='This is an implementation of CoreMS developed by the River Corridor SFA at PNNL. This function accepts folders as inputs, assuming those folders are filled with compatible FTICR-MS files. We prefer using .d or .xml files, but additional versions are compatible (with some testing).')
parser.add_argument('-i', '--input_dir', help="Input directory that contains relevant FTICR-MS files.")
parser.add_argument('-o', '--output_dir', help="Specifies the output location.")
parser.add_argument('-t', '--threshold_method', default='log', help="Set the threshold used during peak analyses (e.g., how are peaks going to be quality controlled). Log is set as the default; signal-to-noise is automatically used for XML files regardless of setting.")
parser.add_argument('-c', '--calib_thresh', default=5, type=int, help="Set the number of points required for a calibration to be considered 'good'. By default, this is set to 5.")
args = parser.parse_args()

# Full path to directory containing Bruker XMLs or .d folders (e.g., )
path_to_dir = args.input_dir

# Adding in a (eventually flexible) output directory
path_to_out = args.output_dir

# Specify the type of thresholding (only for .d file types)
threshold_method = args.threshold_method # options are signal-to-noise (SN) or log; XMLs default to SN

# Importing calibration thresholds
min_cal_thresh = args.calib_thresh

# ##################################### #
### Load in Python functions/packages ###
# ##################################### #

# Switch to directory
os.chdir(path_to_dir)

# Define auto correlation checker
def auto_cal(mass_spectrum_in, ref_file_location):
    # set threshold ranges
    cal_range = pd.DataFrame(
        {"min": np.arange(-5, -0.5, 0.1), "max": -np.arange(-5, -0.5, 0.1)}
    )

    # load in reference mass list
    df_ref = pd.read_csv(ref_file_location, sep="\t", header=None, skiprows=1)
    df_ref = df_ref.rename({0: "Formula", 1: "m/z", 2: "Charge", 3: "Form2"}, axis=1)
    df_ref.sort_values(by="m/z", ascending=False)

    # count matching peaks via loop
    ref_peaks = []

    for i in cal_range.index:
        peaks_mz = np.asarray(mass_spectrum_in.mz_exp)
        cal_peaks_mz = []
        for mzref in df_ref["m/z"]:
            tmp_peaks_mz = peaks_mz[abs(peaks_mz - mzref) < 1]
            for mzmeas in tmp_peaks_mz:
                delta_mass = ((mzmeas - mzref) / mzref) * 1e6
                if delta_mass < cal_range["max"][i]:
                    if delta_mass > cal_range["min"][i]:
                        cal_peaks_mz.append(mzmeas)

        ref_peaks.append(
            {"Cal. Value": cal_range["max"][i], "Peak Count": len(cal_peaks_mz)}
        )

    ref_peaks = pd.DataFrame(ref_peaks)

    # loop and select the first under the calibration point threshold
    if ref_peaks["Peak Count"].max() > min_cal_thresh:
        val = pd.DataFrame(ref_peaks["Peak Count"] > min_cal_thresh)
        row_ind = max(val.index[val["Peak Count"] == True])
    else:
        row_ind = 0

    # return
    return ref_peaks, row_ind


# Define CoreMS function
def CoreMS_Run(file_path, threshold_method):
    # ############# #
    ### File load ###
    # ############# #

    # Load files
    if bool(re.search(".d$", file_path)):  # importing Bruker files
        print("Importing data from a Bruker output.")

        # Setting some parameters
        MSParameters.transient.apodization_method = "Full-Sine"  # ('Hamming', 'Hanning', 'Blackman','Full-Sine','Half-Sine','Kaiser','Half-Kaiser'); use sine per https://doi.org/10.1016/j.ijms.2014.08.030
        MSParameters.transient.kaiser_beta = (
            3  # 8.6 is the default value; only matters if using Kaiser apodization
        )
        MSParameters.transient.number_of_truncations = 0
        MSParameters.transient.number_of_zero_fills = 1

        if bool(re.search("SN", threshold_method)):  # threshold is signal-to-noise
            print("Using signal-to-noise thresholding")
        # MSParameters.mass_spectrum.noise_threshold_method = "signal_noise"
        # MSParameters.mass_spectrum.noise_threshold_min_s2n = 7

        elif bool(re.search("log", threshold_method)):  # threshold is log
            print("Using log thresholding")
            MSParameters.mass_spectrum.noise_threshold_method = "log"
            MSParameters.mass_spectrum.noise_threshold_log_nsigma = 20

        else:
            sys.exit(
                "Threshold option not recommended and/or supported and/or spelled correctly."
            )

        # If file is Bruker, use Bruker reader to read in file
        bruker_reader = ReadBrukerSolarix(file_path)

        # Collect transient information
        bruker_transient_obj = bruker_reader.get_transient()

        # Calculates the transient duration time
        T = bruker_transient_obj.transient_time  # noqa: F841

        # Access the mass spectrum object
        mass_spectrum_obj = bruker_transient_obj.get_mass_spectrum(
            plot_result=False, auto_process=True
        )

        # S2N filter
        if bool(re.search("SN", threshold_method)):
            mass_spectrum_obj.filter_by_s2n(7)

    elif bool(re.search(".xml", file_path)):  # importing .xml files
        print("Importing data from a Bruker XML.")

        # Load XML
        with open(file_path, "r") as f:
            data = f.read()

        # Pull variables
        mz = re.findall("pk mz=.*i=", data)  # m/z values
        intens = re.findall("i=.*sn=", data)  # intensity values
        res = re.findall("res=.*algo=", data)  # resolution
        sn = re.findall("sn=.*a=", data)  # signal-to-noise

        # Clean m/z values
        mz = [re.sub('pk mz="', "", i) for i in mz]
        mz = [re.sub('" i=', "", i) for i in mz]

        # Clean intensity values
        intens = [re.sub('i="', "", i) for i in intens]
        intens = [re.sub('".*$', "", i) for i in intens]

        # Clean resolution values
        res = [re.sub('res="', "", i) for i in res]
        res = [re.sub('".*$', "", i) for i in res]

        # Clean signal-to-noise
        sn = [re.sub('sn="', "", i) for i in sn]
        sn = [re.sub('".*$', "", i) for i in sn]

        # Merge objects into a dataframe
        df = pd.DataFrame(
            {
                "m/z": pd.to_numeric(mz),
                "I": pd.to_numeric(intens),
                "Res.": pd.to_numeric(res),
                "S/N": pd.to_numeric(sn),
            }
        )

        # Create relative intensity column
        df["I %"] = df["I"] / df["I"].sum()

        # Setting threshold preferences (fixed for peak picked files here)
        MSParameters.mass_spectrum.noise_threshold_method = "absolute_abundance"
        MSParameters.mass_spectrum.noise_threshold_absolute_abundance = 1

        # Extracting output parameters
        output_parameters = ReadBrukerXMLList(file_path).get_output_parameters(-1)

        # Rename columns
        df.rename(
            columns=ReadBrukerXMLList(file_path).parameters.header_translate,
            inplace=True,
        )

        # Getting mass spectrum object
        mass_spectrum_obj = MassSpecCentroid(
            df.to_dict(orient="list"), output_parameters
        )

        # Filtering by SN
        mass_spectrum_obj.filter_by_s2n(12)

    elif bool(
        re.search(".processed.csv", file_path)
    ):  # importing files with intensity + SN
        print(
            "This is a non-standard file - but should be imported well given the presence of SN + Intensity."
        )

        # Setting threshold preferences
        MSParameters.mass_spectrum.noise_threshold_method = "absolute_abundance"
        MSParameters.mass_spectrum.noise_threshold_absolute_abundance = 1

        # load in data frame (columns should already be addressed by preprocessing script)
        df = pd.read_csv(file_path)

        # Gather output parameters (e.g., A term, B term, etc.)
        output_parameters = ReadMassList(file_path).get_output_parameters(-1)

        # Convert data frame to mass spectrum object
        mass_spectrum_obj = MassSpecCentroid(
            df.to_dict(orient="list"), output_parameters
        )

    elif bool(
        re.search(".thermo.csv", file_path)
    ):  # importing files with only mass (far from ideal)
        print(
            "This is a non-standard file - I recommend finding a raw or barely processed version of the file."
        )

        # Setting threshold preferences (fixed for .csv files)
        MSParameters.mass_spectrum.noise_threshold_method = "absolute_abundance"
        MSParameters.mass_spectrum.noise_threshold_absolute_abundance = 0.000001  # data is in relative abundance already; need to be aggressively vague

        # curr_file = [path_to_dir, file_path] # this is used for testing specific files rather than the whole function
        # curr_file = "/".join(curr_file)

        # load in data frame (columns should already be addressed by preprocessing script)
        df = pd.read_csv(file_path)

        # Gather output parameters (e.g., A term, B term, etc.)
        output_parameters = ReadMassList(
            file_path, isThermoProfile=True
        ).get_output_parameters(-1)

        # Convert data frame to mass spectrum object
        mass_spectrum_obj = MassSpecCentroid(
            df.to_dict(orient="list"), output_parameters
        )

    else:
        sys.exit("File type not supported!")

    # Store file name for output
    out_name = re.sub("\.xml|\.d|\.thermo.csv|\.processed.csv", "", file_path)

    print(out_name)

    # ############### #
    ### Calibration ###
    # ############### #

    # Load in calibration list
    ref_file_location = "/Users/danc808/Documents/Miscellaneous/Hawkes_neg.ref"

    # Run auto-cal checker
    ref_peaks, row_ind = auto_cal(mass_spectrum_obj, ref_file_location)

    # Calibrate mass spectrum
    mass_spectrum_obj.settings.max_calib_ppm_error = ref_peaks["Cal. Value"][row_ind]
    mass_spectrum_obj.settings.min_calib_ppm_error = -ref_peaks["Cal. Value"][row_ind]
    mass_spectrum_obj.settings.calib_pol_order = 1  # 1 = linear, 2 = quadratic

    # Run calibration
    MzDomainCalibration(mass_spectrum_obj, ref_file_location).run()

    # Calibration output
    cal_df = pd.DataFrame(
        {
            "Sample": out_name,
            "Cal. Points": pd.to_numeric(mass_spectrum_obj.calibration_points),
            "Cal. Thresh.": pd.to_numeric(ref_peaks["Cal. Value"][row_ind]),
            "Cal. RMS Error (ppm)": pd.to_numeric(mass_spectrum_obj.calibration_RMS),
            "Cal. Order": pd.to_numeric(mass_spectrum_obj.calibration_order),
        },
        index=[0],
    )

    # write calibration information
    cal_df.to_csv(f"{path_to_out}{out_name}.corems.cal", sep="\t", index=False)

    # ############################ #
    ### Molecular Formula Search ###
    # ############################ #

    # Set up database URL
    mass_spectrum_obj.molecular_search_settings.url_database = (
        "postgresql+psycopg2://coremsappdb:coremsapppnnl@localhost:5432/coremsapp"
    )

    # Molecular formula error settings
    mass_spectrum_obj.molecular_search_settings.min_ppm_error = -1
    mass_spectrum_obj.molecular_search_settings.max_ppm_error = 1

    # Molecular formula additional options
    mass_spectrum_obj.molecular_search_settings.isProtonated = True  # ionized
    mass_spectrum_obj.molecular_search_settings.isRadical = False  # radical elements
    mass_spectrum_obj.molecular_search_settings.isAdduct = False  # e.g., chloride

    # Filtering by ratios
    mass_spectrum_obj.molecular_search_settings.max_hc_filter = 2.5
    mass_spectrum_obj.molecular_search_settings.min_hc_filter = 0.3
    mass_spectrum_obj.molecular_search_settings.max_oc_filter = 1
    mass_spectrum_obj.molecular_search_settings.min_op_filter = 4

    # Molecular formula search space
    mass_spectrum_obj.molecular_search_settings.usedAtoms["C"] = (1, 90)
    mass_spectrum_obj.molecular_search_settings.usedAtoms["H"] = (4, 200)
    mass_spectrum_obj.molecular_search_settings.usedAtoms["O"] = (1, 25)
    mass_spectrum_obj.molecular_search_settings.usedAtoms["N"] = (0, 4)
    mass_spectrum_obj.molecular_search_settings.usedAtoms["S"] = (0, 2)
    mass_spectrum_obj.molecular_search_settings.usedAtoms["P"] = (0, 1)
    mass_spectrum_obj.molecular_search_settings.usedAtoms["Cl"] = (0, 0)

    # Specify adduct
    mass_spectrum_obj.molecular_search_settings.adduct_atoms_neg = ["Cl"]

    # Setting scoring method
    mass_spectrum_obj.molecular_search_settings.score_method = "N_S_P_lowest_error"

    # Search for molecular formulas
    SearchMolecularFormulas(
        mass_spectrum_obj, first_hit=False
    ).run_worker_mass_spectrum()

    # Export file
    mass_spectrum_obj.to_csv(f"{path_to_out}{out_name}.corems.csv")

    #### end of function


# Create output folder if it doesn't exist
if not os.path.exists(path_to_out):
    print("Creating the specified output directory")
    os.makedirs(
        path_to_out, exist_ok=True
    )  # exist_ok should handle things, but I want a manual trigger

# List all files in specified directory
file_list = [
    f
    for f in os.listdir(path_to_dir)
    if re.match(".*\.xml$|.*\.d$|.*\.thermo.csv$|.*\.processed.csv$", f)
]  # list files from directory

# Check to see if the pipe has been run before, but broke
run_list = [
    f for f in os.listdir(path_to_out) if re.match(".*\.corems.csv$", f)
]  # list files if any already run

if bool(len(run_list) > 0):
    # temporary rename to make matching work
    temp_file = [re.sub(".d$|.thermo.csv$|.processed.csv$", "", f) for f in file_list]
    temp_run = [re.sub(".corems.csv$", "", f) for f in run_list]

    # finding true/false indices for matches
    fil_val = [i in temp_run for i in temp_file]
    fil_val = [
        not i for i in fil_val
    ]  # inverting matches (we want files that haven't been run)

    # filtering down file list
    file_list = list(
        it.compress(file_list, fil_val)
    )  # use itertools to filter based on boolean values

else:
    print("No previously run samples detected")

for file in file_list:
    os.chdir(path_to_dir)
    CoreMS_Run(file, threshold_method)
