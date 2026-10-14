# version with pandas implementation for exporting data into excel

# import all libraries and requirements
import math
import matplotlib.pyplot as plt
from matplotlib import style
import numpy as np
import pandas as pd
import glob
import scipy.fft
from scipy.interpolate import make_interp_spline
from scipy.signal import detrend

meancoeff = []
sqfrequencybins = []
x_microns = []
y_microns = []

# List to collect processed DataFrames for each frame
excel_export_list = []

# function to perform fft and squaring for each frame
def analyze_and_plot_stripes(df, line_pairs, frame_idx):

    x_col, y_col = line_pairs[0][0], line_pairs[0][1]
    # drop NaNs and sort
    clean_df = df[[x_col, y_col]].dropna().sort_values(by=x_col).drop_duplicates(subset=[x_col])
    x_raw = clean_df[x_col].to_numpy()
    y_raw = clean_df[y_col].to_numpy()

    x_min = x_raw.min()
    x_max = x_raw.max()
    y_max = y_raw.max()
    y_min = y_raw.min()

    # wavelenINmicrons = (x_max - x_min)/ 4.5
    # wavewidINmicrons = (y_max - y_min)/ 4.5 # this only divides the wavelen & wid with 4.5 not all values
    # print(wavelenINmicrons)

    allxtoMicrons = x_raw / 4.5
    x_microns = allxtoMicrons
    allytoMicrons = y_raw / 4.5
    y_microns = allytoMicrons

    # x_microns = np.linspace(0, wavelenINmicrons, len(x_raw))
    # y_microns = np.linspace(0, wavewidINmicrons, len(y_raw))

    # print(x_microns, "xmicrons")
    # print(y_microns, "ymicrons")

    # if we keep it where all data is converted to microns, we'd probably have to change all calculations of x and y values of raw coordinates to the microns values, nearly everything below this line
    dx = 1.0
    srate = 1 / dx
    x_uniform = np.arange(x_min, x_max, dx)
    x_dense = np.arange(x_min, x_max, 0.001)
    num_samples = len(x_uniform)
    # print(num_samples)
    # print(x_uniform)

    spline = make_interp_spline(x_raw, y_raw, k=3)
    y_uniform = spline(x_uniform)
    y_detrended = detrend(y_uniform, type="constant")
    # y_dense = detrend(spline(x_dense), type='constant')
    y_dense = spline(x_dense)

    # x_micronsdetrended = np.linspace(0, wavelenINmicrons, len(y_detrended))

    # manual fft
    comp_fft = np.zeros(num_samples, dtype=complex)
    for bin in range(num_samples):
        freq_bin = bin / (num_samples * dx)
        csw = np.exp(-1j * 2 * np.pi * freq_bin * (x_uniform - x_uniform[0]))
        comp_fft[bin] = np.sum(np.multiply(y_detrended, csw))


    # for el in range(len(comp_fft)):
    #     print(comp_fft[el])
    # print("================================")
    print(comp_fft)

    realcompfft = np.real(comp_fft)

    coef_conjugate = np.conjugate(comp_fft)
    # print(coef_conjugate, 'conjugate')
    for el in range(len(coef_conjugate)):
        print(coef_conjugate[el])
    print("^conjugate")


    sqcoef = (comp_fft * coef_conjugate).real

    # print(sqcoef, 'sq')
    for el in range(len(sqcoef)):
        print(sqcoef[el])


    # mean (or mode?)
    tempmean = np.array(np.mean(sqcoef))# square again here?
    tempmeansq = tempmean * tempmean
    meancoeff.append(tempmeansq)


    Nyquist = srate / 2.0
    Hz = np.linspace(0.0, Nyquist, math.floor(num_samples / 2) + 1)
    amps2 = np.abs(sqcoef) / num_samples
    amps_single_sided2 = amps2[:len(Hz)].copy()
    amps_single_sided2[1:-1] *= 2.0

    bins = np.arange(0, len(sqcoef))
    print(bins)
    sqbins = bins * bins

    fig1 = plt.figure(1, figsize=(18, 10))


    # -------------------- PLOTTING FIGURE 1 -------------------
    plt.figure(1)

    # Subplot 1: Raw Coordinates
    plt.subplot(2, 3, 1)
    plt.scatter(x_raw, y_raw, s=12, alpha=0.6, label="Raw Coordinates")

    # Subplot 2: Interpolation
    plt.subplot(2, 3, 2)
    plt.scatter(x_uniform, y_uniform, s=12, alpha=0.6, label="Integer Points Rescaled")
    plt.plot(x_dense, y_dense, lw=1.2, label="Interpolation")
    # plt.scatter(x_raw, detrend(y_raw), color='r', s=12, alpha=0.6, label="Raw coordinates (Detrended)")
    plt.scatter(x_raw, y_raw, color='r', s=12, alpha=0.6, label="Raw Coordinates")

    # Subplot 3:
    plt.subplot(2, 3, 3)
    # plt.plot(Hz, np.abs(comp_fft_scaled[0:len(Hz)]) / num_samples, 'ys-', label='Amplitude Spectrum')
    # plt.plot(Hz, X_Power[0:len(Hz)], 'ms-', label='Power Spectrum')

    markerline, stemlines, baseline = plt.stem(amps2)
    plt.setp(stemlines, 'linewidth', 1.5)

    # Subplot 4:
    plt.subplot(2, 3, 4)
    markerline, stemlines, baseline = plt.stem(amps_single_sided2)
    plt.setp(stemlines, 'linewidth', 1.5)

    # Subplot 5: sqREAL against sqmode (full spectrum sq)
    plt.subplot(2, 3, 5)
    plt.scatter(sqbins, sqcoef, s=12, alpha=0.6, label="Sq Coefficients")

    # Subplot 6: sqREAL against sqmode (corrected then sq) // UNSURE HOW TO DO THIS UNFINISHED
    # plt.subplot(2, 3, 6)
    # ampsbins = np.arange(0, len(amps_single_sided2))
    # sqAmpsbins = ampsbins * ampsbins
    # print(len(sqAmpsbins), len(sqbins), len(sqcoef), "sizing")
    # plt.scatter(sqbins, sqcoef, s=12, alpha=0.6, label="Sq Coefficients")

    # ---------------- Format Figure 1 Subplots ----------------
    plt.figure(1)
    titles_fig1 = [
        "Raw Pixel Coordinates", "Rescaled Integer-Cycle Grid", "Spatial Fourier Transform (indices)",
        "Spatial Fourier Transform (0 to Nyquist)", "Sq Coefficients (Full)", "Corrected Sq Coefficients"
    ]
    x_labels_fig1 = [
        "White X (pixels)", "White X (pixels)", "Frequency Bin",
        "Spatial Frequency (cycles/px)", 'Frequency Bin', "Frequency Bin"
    ]
    y_labels_fig1 = [
        "White Y (pixels)", "White Y (pixels)", "Amplitude",
        "Normalized Amplitude", 'Amplitude', "Amplitude"
    ]

    for i in range(1, 7):
        plt.subplot(2, 3, i)
        plt.title(titles_fig1[i - 1])
        plt.xlabel(x_labels_fig1[i - 1])
        plt.ylabel(y_labels_fig1[i - 1])
        plt.grid(True, linestyle="--", alpha=0.5)
        plt.legend(fontsize=8)

        if i in [1, 2]:
            # plt.xticks(0, x_microns)
            # plt.yticks(0, y_microns)
            plt.gca().invert_yaxis()


    plt.tight_layout()

    plt.show()

    # Pandas (append data to excel)
    max_rows = len(bins)

    infoCol = pd.DataFrame({
        "mode": bins,
        "Sqmode": sqbins,
        "SqRealCon": sqcoef,
        "mean": [float(tempmean)] * max_rows,
        "meansq": [float(tempmeansq)] * max_rows
    })

    # Concatenate frame number and metrics side by side
    df_frame_combined = pd.concat([infoCol], axis=1)
    excel_export_list.append(df_frame_combined)

# ----------------- Execution ----------------------

# find all excel files (filtering out temporary Excel lock files starting with ~$)
files = [f for f in glob.glob("*_pixel_coordinates_analysis.xlsx") if not f.startswith("~$")]

selectedFile = None
# prompt chosen file
if files:
    print("Detected _pixel_coordinates_analysis.xlsx Files in Directory:")
    for idx, file_name in enumerate(files, 1):
        print(f"[{idx}] {file_name}")
    choice = input("Select .xlsx File: ")
    selected_index = int(choice) - 1
    selectedFile = files[selected_index]
else:
    print("No valid _pixel_coordinates_analysis.xlsx files found in the directory.")
    exit()

# read entire file
excel_file = pd.ExcelFile(selectedFile)
print(str(len(excel_file.sheet_names)), "# of frames")
numframes = len(excel_file.sheet_names)

for i in range(numframes):
    df = pd.read_excel(selectedFile, sheet_name=i, usecols=["white x", "white y"])

    lines_to_plot = [('white x', 'white y')]

    # Run function passing frame index
    analyze_and_plot_stripes(df, lines_to_plot, frame_idx=i)

# Save concatenated DataFrames into a new Excel file (each frame in its own sheet)
run_tag = input("\nEnter a suffix name for this run (e.g. run1, expB): ").strip()
output_filename = f"{run_tag}_processed_frames_output.xlsx"
with pd.ExcelWriter(output_filename, engine="openpyxl") as writer:
    for idx, frame_df in enumerate(excel_export_list):
        sheet_name = f"Frame_{idx + 1}"
        frame_df.to_excel(writer, sheet_name=sheet_name, index=False)

print(f"Successfully saved all frames into separate sheets in '{output_filename}'")

print(meancoeff)

coefflength = len(meancoeff)

for el in range(0, coefflength):
    sqfrequencybins.append(el)
print(sqfrequencybins)

plt.figure()
plt.scatter(sqfrequencybins, meancoeff)
plt.show()