# pyEDRReader
Export .EDR electrophysiology files using Python

pyEDRReader is a Python tool for converting electrophysiology .EDR files into .csv files for processing with other tools. Converting a single file is as simple as running:

`python3 reader.py -i <input file(s)>`

This will read the input file and output it to another file in the same directory, with the same name, converted to CSV.

For batch conversion, use the `recurrent` flag:

`python3 reader.py -r -i <folder(s)>`

This will then read and convert all .EDR files in the directory and export them to an output folder.

For both single file and batch conversion, multiple input files can be entered in as arguments seperated by spaces.

To change the name of the output file, use the `output` flag:

`python3 read.py -i <input file(s)> -o <output file(s)>`

or

`python3 reader.py -r -i <input folder(s)> -o <output folder(s)>`

The `verbose` flag will print out progress to stdout, e.g.:

`python3 reader.py -rv -i <input folder(s)>`
