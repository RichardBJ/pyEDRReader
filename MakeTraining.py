#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 30 17:15:12 2024

@author: richardbarrett-jolley
this is virtually a custom script for one job
simulated NOISY FREE (SLIGHTLY FILTERED) ion channel data produced in winEDR
The I layer on noise from real data recorded and saved to a Sam format file.
1) Open the simulated winEDR data
2) Open the noisy data.  It combines being sure any real channels are retained

"""

import numpy as np
import pandas as pd
import tkinter as tk
from tkinter.filedialog import askopenfilenames

#Use a default sample interval of
SI = 50e-6
# TODO: Display that and check!!
"""DANGER HERE WILL SCREW UP PROPER IF WRONG"""
UnitaryAmp = 1.0

def get_outname(file_path:str) -> str:
    if file_path.endswith('.csv'):
        # Read the CSV file with pandas
        return file_path.replace(".csv", "_training.csv")
    if file_path.endswith('.txt'):
        return file_path.replace(".txt", "_training.txt")
    elif file_path.endswith('.parquet'):
        # Read the Parquet file with pandas
        return file_path.replace(".parquet", "_training.parquet")
    else:
        return "ERROR.parquet"
    

def read_file(file_path:str) -> pd.DataFrame:
    # Determine the file type
    if file_path.endswith('.csv'):
        # Read the CSV file with pandas
        df = pd.read_csv(file_path)
    if file_path.endswith('.txt'):
        try:
            df = pd.read_csv(file_path, sep='\t')
        except:
            df = pd.read_csv(file_path, sep='\\s+')
    elif file_path.endswith('.parquet'):
        # Read the Parquet file with pandas
        df = pd.read_parquet(file_path)
        
    df.reset_index(drop=True, inplace=True)
    return df

# Create the root Tk window
root = tk.Tk()
# Update the root window to ensure proper initialization on macOS
root.update()
# Hide the root Tk window
root.withdraw()
# Bring the Tkinter window to the front
root.lift()
# Open a file dialog for CSV or Parquet files
file_paths = askopenfilenames(filetypes=[("CSV files", "*.csv"), ("Parquet files", "*.parquet"),("txt files", "*.txt")])
# Convert all file paths to lower case
file_paths = [fp.lower() for fp in file_paths]

# Check if files were selected
# Choose the continuous WinEDR simulated events file
if file_paths:
    for file_path in file_paths:
        #create data output filename
        outputname = get_outname(file_path)
        edrDF=read_file(file_path)
        edrDF["Channels"]= edrDF["Noisy Current"]
        print(file_path)
        print(edrDF.info())
        print(edrDF.head())
        
else:
    print("No events file selected.")
# Quit the Tkinter event loop
root.quit()
# Destroy the Tkinter window
root.destroy()

# Create the root Tk window
root = tk.Tk()
# Update the root window to ensure proper initialization on macOS
root.update()
# Hide the root Tk window
root.withdraw()
# Bring the Tkinter window to the front
root.lift()
# Open a file dialog for CSV or Parquet files
file_paths = askopenfilenames(filetypes=[("CSV files", "*.csv"), ("Parquet files", "*.parquet"),("txt files", "*.txt")])
# Convert all file paths to lower case
file_paths = [fp.lower() for fp in file_paths]

# Check if files were selected
# Choose the continuous WinEDR simulated events file
if file_paths:
    for file_path in file_paths:
        df=read_file(file_path)
        #Gltches at the start of Volgate command data... drop 100 points
        df=df.iloc[100:,:]
        print(file_path)
        print(df.info())
        print(df.head())


"""
No we gotta make copy after copy of the "raw" data in df until it the exact
same length as edrDF or longer then crop it.
In fact times are all wrong lets see what happens"""

"""Numpy array"""
noise_and_channels = df.loc[:,["Noisy Current", "Channels"]].values

while len(noise_and_channels)<len(edrDF):
    noise_and_channels = np.append(noise_and_channels, noise_and_channels, axis=0)
    print(f"noise shape {noise_and_channels.shape}")
noise_and_channels = noise_and_channels[:len(edrDF),:]
print(f"noise shape {noise_and_channels.shape}")

#Add the noise layer to the existing noisy current
edrDF["Noisy Current"] = noise_and_channels[:,0] + edrDF["Channels"]

#Remember the original noisy current still had associated events so don't loose those!
#BUT winWDR channel size was not necessarily 1.0 :-)
edrDF["Channels"] = edrDF["Channels"] / UnitaryAmp
edrDF["Channels"] = edrDF["Channels"].astype("int32")
edrDF["Channels"] = noise_and_channels[:,1] + edrDF["Channels"]

edrDF.loc[10000:15000,:].plot(x="Time", y=["Channels","Noisy Current"])
#edrDF.drop(columns=["Channel 0"], inplace=True)

edrDF.to_parquet(outputname, index=False)

