# this program is the same as p4fitline but with micron converted numbers, I want to compare the two results.

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

# Main

# import the file from p3computeFFT.py
# IN THE FUTURE, IMPLEMENT A WAY TO DETECT SPECIFIC NAMED FILES to distinguish excel files needed for this file and previous one
files = [f for f in glob.glob("*_processed_frames_output.xlsx") if not f.startswith("~$")]

# select excel file containing sq coefficients
selectedFile = None
if files:
    print("Detected _processed_frames_output.xlsx Files in Directory:")
    for idx, file_name in enumerate(files, 1):
        print(f"[{idx}] {file_name}")
    choice = input("Select .xlsx File: ")
    selected_index = int(choice) - 1
    selectedFile = files[selected_index]
else:
    print("No valid .xlsx files found in the directory.")
    exit()

# read entire file
excel_file = pd.ExcelFile(selectedFile)
# print(str(len(excel_file.sheet_names)), "# of frames")
numframes = len(excel_file.sheet_names)

# Initialize # of rows to pick out our idx
getrows_df = pd.read_excel(selectedFile, sheet_name=0, usecols=["mode"])
rows = len(getrows_df)
# print(str(rows), "# of rows")

# specify range of indicies
lowMode = int(input("Select lowest range of your mode 0 - " + str(rows - 1) + ": "))
highMode = int(input("Select highest range of your mode " + str(lowMode) + " - " + str(rows - 1) + ": "))

# initialize two arrays for method 1 and 2 avgs
m1_m = []
m1_b = []

# initialize variables for method 2
selectedsqrealcons = [] # store all the sqrealcons
selectedmode = []

plt.figure(figsize = (10,5))
plt.suptitle(f"Best Fit Averaging Amongst Indices of {lowMode} - {highMode}", fontsize=16)

# For loop, looping through each frame/sheet within that range
for i in range(numframes): # only -1 for test sheet since an extra sheet is added
    global mode
    df = pd.read_excel(selectedFile, sheet_name=i, usecols=["Sqmode", "SqRealCon"])

    df2 = df.iloc[lowMode:highMode + 1]
    # print("df2", df2)

    lines_to_plot = [('Sqmode', 'SqRealCon')]
    sqmode, sqcoeff = lines_to_plot[0][0], lines_to_plot[0][1]

    clean_df = df2[[sqmode, sqcoeff]].dropna().sort_values(by=sqmode)

    mode = clean_df[sqmode].to_numpy()
    coeff = clean_df[sqcoeff].to_numpy()
    # print(coeff, 'coeff')
    modemin = np.min(mode)
    modemax = np.max(mode)


    # Run line fitting function for Method 1
    m, b = np.polyfit(mode, coeff, 1)
    m1_m.append(m)
    m1_b.append(b)

    plt.figure(1)
    plt.subplot(2,2,1)
    plt.scatter(mode, coeff)
    plt.plot(m)

    # For method 2: append all the same indicies into one array, then combine into an arraylist?
    selectedsqrealcons.append(coeff)

# Averaging Method 1:
addSlope = 0
addB = 0

for i in range(len(m1_m)):
    # print(m1_m[i])
    addSlope += m1_m[i]
    addB += m1_b[i]

# print(addSlope, addB)
mslope = addSlope / len(m1_m)
bintercept = addB / len(m1_b)
# print(mslope, bintercept)
xaxis = np.linspace(modemin, modemax, 100)

yaxis = mslope * xaxis + bintercept
# print(xaxis, yaxis)

m1_frameAve = f'y = {mslope:.3}x + {bintercept:.3}'


# Averaging Method 2:

# initialize num of samples
samples = len(selectedsqrealcons[0]) # might be an issue because not all frames have the same amount of idx...
# print(samples, 'samples')
currentTotal = 0
allAddedIdx = []
allAvgIdx = []

# print(selectedsqrealcons, 'selectedsqrealcons')

for n in range(samples):
    for i in range(len(selectedsqrealcons)):
        currentvalue = selectedsqrealcons[i][n]
        currentTotal += currentvalue
    allAddedIdx.append(currentTotal)
    currentTotal = 0

# print(allAddedIdx, 'allAddedIdx')

# print(allAddedIdx, 'before')
for i in range(len(allAddedIdx)):
    allAvgIdx.append(allAddedIdx[i]/samples)

# print(allAvgIdx, ' after allAvgIdx')

# poly fit line for method 2:
m, b = np.polyfit(mode, allAvgIdx, 1)

# yaxis = m * xaxis + b


m2_slope = f'y = {m:.3}x + {b:.3}'


# Plot avg slope - Method 1
plt.figure(1)
plt.subplot(2, 2, 1)
plt.plot(xaxis, mslope * xaxis + bintercept, color = "red", label = m1_frameAve)
plt.xlabel("Squared Indicies")
plt.ylabel("Coefficients")
plt.title("Averaging Amongst Frames")
plt.grid(True)
plt.legend()


# Plot avg numbers and polyfit/slope line - Method 2
plt.figure(1)
plt.subplot(2, 2, 2)

plt.scatter(mode, allAvgIdx)
plt.plot(xaxis, m * xaxis + b, color = "red", label = m2_slope)
plt.xlabel("Squared Indicies")
plt.ylabel("Coefficients")
plt.title("After Idx Averaging")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()

# plot microns 1 method
# Convert units to microns
# micronsX = np.linspace(0, ((modemax - modemin)/4.5))
# print(micronsX)