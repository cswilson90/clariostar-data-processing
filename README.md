# Clariostar data processor

A program written for my girlfriend to process her PHD experiment results from a Clariostar machine.

# Instructions

Run `process.py` with two arguments: the directory with the CSVs and the name of the control sample to be subtracted from the others e.g.

`python process.py C:\Users\user\Documents\data\csvs\ "Blank B"`

The CSVs should be in their own directory. Will output normalised data grouped by sample in `/samples/` in the same directory as the CSVs.