import argparse
import csv
import glob
import os
import re

def processResults():
    """Process data from files and output graphs."""

    parser = argparse.ArgumentParser()
    parser.add_argument("dataDir", help="The directory containing the raw results files")
    parser.add_argument("controlValue", help="Name of control value content in data (row that will be subtracted from others)")
    args = parser.parse_args()

    rawData = readFiles(args.dataDir)
    normaliseValues(rawData, args.controlValue)
    
    outputNormalised(rawData, args.dataDir)

def readFiles(dataDir):
    """Read data files from the passed in data directory."""

    if not os.path.isdir(dataDir):
        raise ValueError("Directory " + dataDir + " does not exist")

    print("Reading data from: " + dataDir)

    # Get list of all CSV files
    csvFiles = glob.glob(dataDir + "/*.csv")

    rawData = {}
    hourPattern = re.compile(r"_(\d+)h[.]csv", re.I)
    for csvFile in csvFiles:
        fileMatch = hourPattern.search(csvFile)

        if not fileMatch:
            print("Found unexpected CSV file: " + csvFile)
            continue

        hour = fileMatch.group(1)

        with open(csvFile, newline='') as fileObject:
            dataReader = csv.reader(fileObject)

            # TODO check that this is always true
            firstUsefulRow = 8
            processedRows = 0

            hourData = {}
            hourData["samples"] = {}
            for dataRow in dataReader:
                processedRows += 1

                if processedRows < firstUsefulRow:
                    continue;

                # Check if this is wavelength row
                if dataRow[0] == '' and re.match(r"Wavelength", dataRow[1], re.I):
                    if "wavelengths" in hourData:
                        raise UserWarning("File" + csvFile + " contains multiple wavelength rows")

                    # Store wavelengths as ints
                    hourData["wavelengths"] = [int(wavelength) for wavelength in dataRow[2:]]
                else:
                    content = dataRow[1]
                    # Store values as ints
                    hourData["samples"][content] = [int(value) for value in dataRow[2:]]

            rawData[hour] = hourData

    return rawData


def normaliseValues(rawData, controlValue):
    """Subtract control values from raw data to get plottable values."""

    for hour in rawData:
        controlData = rawData[hour]["samples"][controlValue].copy()

        # For each sample for the hour, subtract the control values
        for sampleName in rawData[hour]["samples"]:
            for i in range(len(controlData)):
                rawData[hour]["samples"][sampleName][i] -= controlData[i]


def outputNormalised(rawData, dataDir):
    """Outputs normalised data back to CSVs."""
    
    outputDir = dataDir + "/normalised"
    if not os.path.isdir(outputDir):
        os.mkdir(outputDir)
        
    for hour in rawData:
        with open(outputDir + "/normalised_" + hour + "h.csv", "w", newline='') as csvFile:
            csvWriter = csv.writer(csvFile)
            
            csvWriter.writerow(["Wavelength"] + rawData[hour]["wavelengths"])
            
            for sample in rawData[hour]["samples"]:
                csvWriter.writerow([sample] + rawData[hour]["samples"][sample])
    
if __name__== "__main__":
    processResults()