#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 30 17:15:12 2024

@author: richardbarrett-jolley
df is your real raw
edrDF is your slightly filtered ideal out of winEDR

so create an idealisation out of edrDF which is just the integer version of
Channel 0
"""
df.columns=["Time","Noise"]
edrDF["Channels"] = edrDF["Channel 0"].astype("int32")
edrDF.head()

"""
No we gotta make copy after copy of the "raw" data in df until it the exact
same length as edrDF or longer then crop it.
In fact times are all wrong lets see what happens"""

"""Numpy array"""
noise=df.loc[:,"Noise"].values

while len(noise)<len(edrDF):
    noise = np.append(noise, noise)
    print(f"noise shape {noise.shape}")
noise = noise[:len(edrDF)]

edrDF["Noisy Current"] = noise + edrDF["Channels"]
from matplotlib import pyplot as plt
edrDF.loc[20000:25000,:].plot(x="Time", y="Channels")
edrDF.drop(columns=["Channel 0"], inplace=True)

edrDF.to_parquet("/Users/richardbarrett-jolley/Library/CloudStorage/OneDrive-TheUniversityofLiverpool/Data/WinEDR simulated/TRAINING240513_001[LP=5000Hz RD=1].parquet",
                 index=False)

