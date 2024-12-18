import struct
import re
import sys
import pandas as pd
import numpy as np
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox

"""
VER=6.4 <cr><lf> EDR file version number
NC=2 <cr><lf> No. of analogue input channels 
NP=102400 <cr><lf> No. of A/D samples in data block
NBH=2048 <cr><lf> No. of bytes in file header block
AD=5.0000 <cr> <lf> A/D converter upper limit of voltage range (V)
ADCMAX=4095 <cr><lf> Maximum A/D sample value
DT=.1600 <cr><lf> A/D sampling interval (s)
YN0=Im <cr> <lf> Channel 0 name (n=0 .. NC-1)
YU0=nA <cr> <lf> Channel 0 units
YCF0=0.0001 <cr> <lf> Channel 0 calibration factor V/units
YAG0=10.0 <cr> <lf> Channel 0 gain factor 
YZ0=1024 <cr> <lf> Channel 0 zero level (A/D bits)
YO0=0 <cr> <lf> Channel 0 offset into sample group in data block
YN1=Im <cr> <lf> Channel 1 name (n=0 .. NC-1)
YU1=nA <cr> <lf> Channel 1 units
YCF1=0.01 <cr> <lf> Channel 1 calibration factor V/units
YAG1=1.0 <cr> <lf> Channel 1 gain factor 
YZ1=1024 <cr> <lf> Channel 1 zero level (A/D bits)
YO1=1 <cr> <lf> Channel 1 offset into sample group in data block
TU=ms <cr> <lf> Time units
ID= Cell 1 <cr> <lf> Experiment identification line
BAK=T1 <cr> <lf> BAK=T indicates a .BAK file exist

"""


def logger(message, verbose):
    if verbose:
        print(message)

def calibrate(raw, YZ, AD, YCF, YAG, ADCMAX):
    return list(map(lambda x: (x - YZ) * AD / (YCF * YAG * (ADCMAX + 1)), raw))

def read_edr(filename: str, verbose: bool) -> list:
    with open(filename, 'rb') as my_file:
        if verbose:
            print(f"Processing: {filename}")
        # Read the data file in its entirety and get the head and data contents.
        header = my_file.read(2048).decode('ASCII')

        # Find the conversion parameters from the header.
        YZn = re.findall(r'(?<=YZ\d=)\-?\d+\.?\d*E?\-?\d*', header)
        AD = re.findall(r'(?<=AD=)\-?\d+\.?\d*E?\-?\d*', header)
        YCFn = re.findall(r'(?<=YCF\d=)\-?\d+\.?\d*E?\-?\d*', header)
        YAGn = re.findall(r'(?<=YAG\d=)\-?\d+\.?\d*E?\-?\d*', header)
        ADCMAX = re.findall(r'(?<=ADCMAX=)\-?\d+\.?\d*E?\-?\d*', header)
        DT = re.findall(r'(?<=DT=)\-?\d+\.?\d*E?\-?\d*', header)

        # How many signals are there?
        num_signals = len(YZn)

        # RBJ coming in clutch?? Should = NC number of channels
        channels = [[] for _ in range(num_signals)]

        byte = my_file.read(2)
        counter = 0
        # What does this byte bit do!?
        # OK reading pair of bytes by pair of bytes to get each next value in each channel
        while byte:
            try:
				# 'h' is a signed short integer. Capital H would be unsigned.
                channels[counter % num_signals].append(struct.unpack('h', byte)[0])
            except:
                pass

            counter += 1
            byte = my_file.read(2)

        if verbose:
            print("Byte processing complete")
        # Get a clean time column
        timescale = int(DT[0][-3:]) + 1 if 'E' in DT[0] else len(DT[0])
        time = [[round(i * float(DT[0]), timescale) for i in range(len(channels[0]))]]
        #RBJ 11th March 2024: Small bug at start of some edrs throws everything. This seems to work
        for channel in range(num_signals):
            channels[channel][:10]=10*[np.mean(channels[channel][10:1000])]
        if verbose:
            print ("Calibrating Signal")
        # Convert raw signal to calibrated signal
        calibrated = time + [calibrate(channels[i], float(YZn[i]), float(AD[0]), float(YCFn[i]), float(YAGn[i]), float(ADCMAX[0])) for i in range(num_signals)]
        if verbose:
            print ("Conversion complete")
        return calibrated

def write_to_csv(listy: list, csv_filename: str, verbose: bool) -> int:
    if verbose:
        print ("Saving to csv")
    num_channels = len(listy)

    with open(csv_filename, 'w') as my_file:

        # Add headers to CSV file
        channel_list = [f'Channel {i}' for i in range(num_channels - 1)]
        my_file.write(','.join(['Time'] + channel_list) + '\n')

        # Write data into columns
        for i in range(len(listy[0])):
            my_file.write(','.join([str(listy[j][i]) for j in range(num_channels)]) + '\n')
    if verbose:
        print ("Saving complete")

    return 1

def write_to_parquet(listy: list, parquet_filename: str, verbose: bool) -> int:
    if verbose:
        print ("Preparing to parquet")
    num_channels = len(listy)

    # Create a DataFrame from the list data
    if verbose:
        print ("Reshaping")
    la = np.asarray(listy)
    al = la.T
    df = pd.DataFrame(al)
    if verbose:
        print ("Renaming")
    df.columns = [f'Channel {i-1}' for i in range(num_channels)]
    df.rename(columns={df.columns[0]: 'Time'}, inplace=True)
    # Write the DataFrame to a Parquet file
    num_channels = len(listy)
    if verbose:
        print ("Writing to parquet")
    df.to_parquet(parquet_filename, index=False)
    if verbose:
        print ("Saving complete")

    return 1

# Create a simple GUI for input
root = tk.Tk()
root.withdraw()

# Ask the user for the input file
input_files = filedialog.askopenfilenames(filetypes=[("WinEDR files", "*.edr")],title="Select input file")
if input_files == "":
    sys.exit("No Files selected or found")

# Ask the user if they want verbose output
verbose = messagebox.askyesno("Verbose output", "Do you want verbose output?")
root.update()

# Ask the user if they want to convert to parquet
parquet = messagebox.askyesno("Convert to Parquet", "Do you want to convert to Parquet?")
root.update()

for input_file in input_files:
    input_file = input_file.lower()
    # Parse values into list format
    to_list = read_edr(input_file, verbose)

    # Write data to new file
    if parquet:
        output_file = input_file.replace('.edr','.parquet')
        write_to_parquet(to_list, output_file, verbose)
    else:
        output_file = input_file.replace('.edr','.csv')
        write_to_csv(to_list, output_file, verbose)
