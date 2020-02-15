# This import registers the 3D projection, but is otherwise unused.
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 unused import

import argparse
import csv
import glob
import numpy
import matplotlib.pyplot as plt
import os
import re

def processResults():
    """Process data from files and output graphs."""

    parser = argparse.ArgumentParser()
    parser.add_argument("dataDir", help="The directory containing the raw results files")
    parser.add_argument("controlValue", help="Name of control value content in data (row that will be subtracted from others)")
    parser.add_argument("resultGrouping", help="Number of results to group together", type=int)
    parser.add_argument("--graphTest", help="Don't save results or graphs, instead show an example graph", action='store_true')
    args = parser.parse_args()

    rawData = readFiles(args.dataDir)
    # TODO validate raw data is all same wavelengths etc.?

    normaliseValues(rawData, args.controlValue)

    sampleData, groupMaxes = convertToSampleOriented(rawData, args.controlValue, args.resultGrouping)

    if not args.graphTest:
        outputSampleData(sampleData, args.dataDir)

    plotGraphs(sampleData, args.dataDir, args.resultGrouping, groupMaxes, args.graphTest)

def readFiles(dataDir):
    """Read data files from the passed in data directory."""

    if not os.path.isdir(dataDir):
        raise ValueError("Directory " + dataDir + " does not exist")

    print("Reading data from: " + dataDir)

    # Get list of all CSV files
    csvFiles = glob.glob(dataDir + "/*.csv")

    if len(csvFiles) == 0:
        sys.exit("No csv files found in " + dataDir)
    elif len(csvFiles) == 1:
        print("Found only one CSV file, assuming all data is in there")
        return readSingleFile(csvFiles[0])

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


def readSingleFile (csvFile):
    """Reads data from a single CSV file"""

    hours = []
    wavelengths = []
    samples = {}
    with open(csvFile, newline='') as fileObject:
        dataReader = csv.reader(fileObject)

        # TODO check that this is always true
        hourRow = 7
        wavelengthRow = 8
        processedRows = 0

        for dataRow in dataReader:
            processedRows += 1

            # Ignore rows before the hour row as they aren't needed
            if processedRows < hourRow:
                continue

            if processedRows == hourRow:
                # Parse hour out of "X h" string
                hours = [hour.split(' ')[0] for hour in dataRow[3:]]
            elif processedRows == wavelengthRow:
                # Store wavelengths as ints
                wavelengths = [int(wavelength) for wavelength in dataRow[3:]]
            else:
                sampleName = dataRow[2]
                # Store values as ints
                sampleValues = [int(value) for value in dataRow[3:]]
                samples[sampleName] = sampleValues

    # Get a sorted list of unique wavelength values
    uniqueWavelengths = sorted(set(wavelengths))

    rawData = {}
    # Iterate over every column from the CSV and insert into the correct place in the results
    for i in range(len(hours)):
        hour = hours[i]
        wavelength = wavelengths[i]

        if not hour in rawData:
            rawData[hour] = {}
            rawData[hour]["samples"] = {}
            rawData[hour]["wavelengths"] = uniqueWavelengths

        for sample in samples:
            if not sample in rawData[hour]["samples"]:
                rawData[hour]["samples"][sample] = []

            rawData[hour]["samples"][sample].append(samples[sample][i])

    return rawData

def normaliseValues(rawData, controlValue):
    """Subtract control values from raw data to get plottable values."""

    for hour in rawData:
        controlData = rawData[hour]["samples"][controlValue].copy()

        # For each sample for the hour, subtract the control values
        for sampleName in rawData[hour]["samples"]:
            for i in range(len(controlData)):
                rawData[hour]["samples"][sampleName][i] -= controlData[i]


def convertToSampleOriented(rawData, controlValue, resultGrouping):
    """Takes raw data split by hour and converts to be split by sample."""

    sampleData = {}
    wavelengths = rawData["0"]["wavelengths"]
    groupMaxes = {}

    for hour in rawData:
        for sample in rawData[hour]["samples"]:
            # Ignore control sample as values will now all be 0
            if sample == controlValue:
                continue

            if not(sample in sampleData):
                sampleData[sample] = {"wavelengths": wavelengths.copy(), "hours": {}}

            sampleData[sample]["hours"][hour] = rawData[hour]["samples"][sample]

            groupNum = sampleGroupNum(sample, resultGrouping)
            if not groupNum in groupMaxes:
                groupMaxes[groupNum] = max(rawData[hour]["samples"][sample])
            else:
                groupMaxes[groupNum] = max(groupMaxes[groupNum], max(rawData[hour]["samples"][sample]))

    return sampleData, groupMaxes


def outputSampleData(sampleData, dataDir):
    """Outputs sample oriented data to CSV"""

    outputDir = dataDir + "/samples"
    if not os.path.isdir(outputDir):
        os.mkdir(outputDir)

    for sample in sampleData:
        with open(outputDir + "/" + sample + ".csv", "w", newline='') as csvFile:
            csvWriter = csv.writer(csvFile)

            csvWriter.writerow(["Hour/Wavelength"] + sampleData[sample]["wavelengths"])

            for hour in sorted(sampleData[sample]["hours"], key=int):
                csvWriter.writerow([hour] + sampleData[sample]["hours"][hour])


def plotGraphs(sampleData, dataDir, resultGrouping, groupMaxes, graphTest):
    """Plots graphs from the smaple oriented data"""

    outputDir = dataDir + "/graphs"
    if not os.path.isdir(outputDir):
        os.mkdir(outputDir)

    for sample in sampleData:
        groupNum = sampleGroupNum(sample, resultGrouping)
        maxValue = groupMaxes[groupNum]

        fig = plt.figure()
        ax = fig.gca(projection='3d')

        ax.set_xlabel("Wavelength (nm)")
        ax.set_ylabel("Time (hr)")

        ax.set_zlabel("")
        ax.set_zlim([0, maxValue])

        ax.grid(False)

        # Plot graphs with back line first otherwise lines in front are written over it
        for hour in sorted(sampleData[sample]["hours"], key=int, reverse=True):
            wavelengths = sampleData[sample]["wavelengths"]
            magnitudes = sampleData[sample]["hours"][hour]
            ax.plot(wavelengths, magnitudes, zs=int(hour), zdir='y', linewidth=0.8)

        if graphTest:
            plt.show()
            return

        fileName = outputDir + "/" + sample
        fig.savefig(fileName)
        plt.close()

def sampleGroupNum(sample, resultGrouping):
    samplePattern = re.compile(r"Sample X(\d+)", re.I)

    sampleMatch = samplePattern.search(sample)
    if not sampleMatch:
        print("Found unexpected sample name " + sample)
        return 0

    return (int(sampleMatch.group(1)) - 1) // resultGrouping

if __name__== "__main__":
    processResults()
