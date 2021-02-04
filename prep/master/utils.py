#!/usr/bin/python

NORM_NAMES = "defs/names.txt"
LABELS_FILE = "defs/labels.txt"
FIELDS_FILE = "defs/fields.txt"

# Normalized names are read from the dictionary
def getNormalizedNames():
    names = {}
    fin = open(NORM_NAMES, "r")
    while True:
        line = fin.readline()
        if not line:
            # The end of the file has been reached
            break
        # End of line and spaces on the sides are removed
        line = line.strip()
        if line == '' or line[0] == '#':
            # The line is empty or is a comment
            # So, ignore it
            continue
        # Extracting pairs
        try:
            key, value = line.split(':')
        except:
            print(line)
        key = key.strip()
        value = value.strip()
        # Creating entry in the dictionary
        names[key] = value
        continue
    fin.close()
    return names

def getLabels():
    with open(LABELS_FILE, 'r') as fin:
        lines = fin.readlines()
    labels = {}
    for line in lines:
        fields = line.strip().split(':')
        labels[fields[0]] = {'size': fields[1], 'kind': fields[2]}
    return labels

def getFieldNames():
    with open(FIELDS_FILE, "r") as fin:
        fields = [line.strip() for line in fin.readlines()]
    return fields

