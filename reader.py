import struct
import re
import argparse
import os
import sys

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

        # RBJ coming in clutch 
        channels = [[] for _ in range(num_signals)]

        byte = my_file.read(2)
        counter = 0
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

        # Convert raw signal to calibrated signal
        calibrated = time + [calibrate(channels[i], float(YZn[i]), float(AD[0]), float(YCFn[i]), float(YAGn[i]), float(ADCMAX[0])) for i in range(num_signals)]
        
        return calibrated

def write_to_csv(listy: list, csv_filename: str, verbose: bool) -> int:
    
    num_channels = len(listy)

    with open(csv_filename, 'w') as my_file:

        # Add headers to CSV file
        channel_list = [f'Channel {i}' for i in range(num_channels - 1)]
        my_file.write(','.join(['Time'] + channel_list) + '\n') 
        
        # Write data into columns
        for i in range(len(listy[0])):
            my_file.write(','.join([str(listy[j][i]) for j in range(num_channels)]) + '\n')

    return 1
    
import pandas as pd

def write_to_parquet(listy: list, parquet_filename: str, verbose: bool) -> int:
    num_channels = len(listy)

    # Create a DataFrame from the list data
    df = pd.DataFrame(listy).T
    df.columns = [f'Channel {i}' for i in range(num_channels)]

    # Write the DataFrame to a Parquet file
    df.to_parquet(parquet_filename, index=False)

    return 1

# Argument parsing
parser = argparse.ArgumentParser()

# Verbose argument
parser.add_argument("-v", "--verbose", help="Increase output verbosity", action="store_true")
# Recurrent arguement
parser.add_argument("-r", "--recurrent", help="Targets a folder and converts all EDR files within to CSV files. Creates new folder for CSV files.", action="store_true")

# I/O arguements
parser.add_argument("-i", "--input", help="Location of file(s) or folder(s) for conversion. If the recurrent flag is set, this refers to a list of folder paths", nargs='+', default=[sys.stdin], required=True)
parser.add_argument("-o", "--output", help="Name of output file(s) or folder(s). If left blank, files will be converted with the same name. If the recurrent flag is set, this refers to the name of the output folders", nargs='*')
parser.add_argument("-p", "--parquet", help="creates .parquet instead of csv", action="store_true")

args = parser.parse_args()

# Check to see if the number of output files is equal to the number of input files, or is equal to 0.
if args.output:
    if len(args.output) != len(args.input):
        raise IOError('Length of output flag must equal length of input flag, or not exist')

if args.recurrent:
    # Operate on folders
    for folder in args.input:
        for filename in os.listdir(folder):
            if len(filename) < 4:
                logger(f'{filename} Invalid, skipping...', args.verbose)
                continue
            elif filename[-4:].upper() != '.EDR':
                logger(f'{filename} Invalid, skipping...', args.verbose)
                continue
            else:
                # Parse values into list format
                #Need to use os.path.join(folder, filename) or wont find the file if not root!
                #to_list = read_edr(filename, args.verbose )clde              
                to_list = read_edr(os.path.join(folder, filename), args.verbose ) 
                logger(f'Reading filename: {filename}', args.verbose)

                # Get new folder name
                if not args.output:
                    # If no output flag is set, create output subfolder in input directory
                    if not os.path.exists(f'{folder}/output'):
                        logger('Output folder not found. Creating...', args.verbose) 
                        os.mkdir(f'{folder}/output')
                    
                    new_filename = f'{folder}/output/{filename[:-4]}.csv'
                else:
                    # Otherwise make folder with name of output flag
                    if not os.path.exists(f'{folder}/output'):
                        logger('Output folder not found. Creating...', args.verbose)
                        os.mkdir(f'{folder}/{args.output}')

                    
                    new_filename = f'{folder}/{args.output}/{filename[:-4]}.csv'

                # Write data to file
                if args.parquet:
                    new_filename = new_filename.replace(".csv",".parquet")
                    logger(f'Writing to file: {new_filename}...', args.verbose)
                    write_to_parquet( to_list, new_filename, args.verbose )
                else:
                    logger(f'Writing to file: {new_filename}...', args.verbose)
                    write_to_csv( to_list, new_filename, args.verbose )
    pass
else:
    # Operate on files
    for idx, filename in enumerate(args.input):
        
        # Parse values into list format
        to_list = read_edr( filename, args.verbose )
        
        # Get the new file name
        if not args.output:
            new_filename = f'{filename[:-4]}.csv'
        else:
            new_filename = args.output[idx]
        
        # Write data to new file
            if args.parquet:
                write_to_parquet( to_list,
                        new_filename.replace(".csv",".parquet"), args.verbose)
            else:
                write_to_csv( to_list, new_filename, args.verbose )
