import json

f1 = open('../atocfixed.txt', 'r')

fixedDict = dict()
while True:
    line = f1.readline()
    if line.strip() == 'END':
        break

    words = line.split()
    type = words[2]
    first = words[4]
    end = words[6]
    time = words[8]

    if first not in fixedDict:
        fixedDict[first] = dict()
    if end not in fixedDict:
        fixedDict[end] = dict()

    fixedDict[first][end] = (time, type)
    fixedDict[end][first] = (time, type)

f2 = open('../atocfixed.json', 'w')
json.dump(fixedDict, f2)
