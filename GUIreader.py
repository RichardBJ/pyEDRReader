import struct
import re
import os
import sys
import pandas as pd
import numpy as np
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox

def logger(message, verbose):
    if verbose:
        print(message)

def calibrate(raw, YZ, AD, YCF, YAG, ADCMAX):
    return list(map(lambda x: (x - YZ) * AD / (YCF * YAG * (ADCMAX + 1)), raw))

def read_edr(filename: str, verbose: bool) -> list:
    with open(filename, 'rb') as my_file:

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
                channels[counter % num_signals].append(struct.unpack('h', byte)[0])
            except:
                pass

            counter += 1
            byte = my_file.read(2)

        # Get a clean time column
        timescale = int(DT[0][-3:]) + 1 if 'E' in DT[0] else len(DT[0])
        time = [[round(i * float(DT[0]), timescale) for i in range(len(channels[0]))]]
        #RB 11th March 2024: Small bug at start of some edrs throws everything. This seems to work
        for channel in range(num_signals):
            channels[channel][:10]=10*[np.mean(channels[channel][10:1000])]

        # Convert raw signal to calibrated signal
        calibrated = time + [calibrate(channels[i], float(YZn[i]), float(AD[0]), float(YCFn[i]), float(YAGn[i]), float(ADCMAX[0])) for i in range(num_signals)]

        return calibrated

def write_to_csv(listy: list, csv_filename: str, verbose: bool) -> int:
    # ... rest of your code ...
    num_channels = len(listy)

    with open(csv_filename, 'w') as my_file:

        # Add headers to CSV file
        channel_list = [f'Channel {i}' for i in range(num_channels - 1)]
        my_file.write(','.join(['Time'] + channel_list) + '\n')

        # Write data into columns
        for i in range(len(listy[0])):
            my_file.write(','.join([str(listy[j][i]) for j in range(num_channels)]) + '\n')

    return 1

def write_to_parquet(listy: list, parquet_filename: str, verbose: bool) -> int:
    # ... rest of your code ...
    num_channels = len(listy)

    # Create a DataFrame from the list data
    df = pd.DataFrame(listy).T
    df.columns = [f'Channel {i}' for i in range(num_channels)]
    df.rename(columns={df.columns[0]: 'Time'}, inplace=True)
    # Write the DataFrame to a Parquet file
    df.to_parquet(parquet_filename, index=False)

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

# Ask the user if they want to convert to parquet
parquet = messagebox.askyesno("Convert to Parquet", "Do you want to convert to Parquet?")

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
