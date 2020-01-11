# Clariostar data processor

A program written for my girlfriend to process her PHD experiment results from a Clariostar machine.

# Instructions

[Install matplotlib](https://matplotlib.org/users/installing.html)

Run `process.py` with three arguments: the directory with the CSVs and the name of the control sample to be subtracted from the
others and the number of samples in each group e.g.

`python process.py C:\Users\user\Documents\data\csvs\ "Blank B"` 8

The CSVs should be in their own directory.

Will output normalised data grouped by sample in `samples/` in the same directory as the CSVs and graphs in `graphs/`.