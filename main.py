import requests
import json
from datetime import datetime, timedelta
import os.path
from pathlib import Path

def formatTime(date, time):
    return datetime.strptime(date[2:] + ' ' + time, '%y-%m-%d %H%M')

def getMetrics(start, end, date):
    day = datetime.strptime(date[2:], '%y-%m-%d').weekday()
    if day == 5:
        days = 'SATURDAY'
    elif day == 6:
        days = 'SUNDAY'
    else:
        days = 'WEEKDAY'

    if os.path.exists('cache/' + start + '-' + end + '/' + date + '/metrics.json'):
        f = open('cache/' + start + '-' + end + '/' + date + '/metrics.json')
        return json.loads(f.read())
    else:
        Path('cache/' + start + '-' + end + '/' + date).mkdir(parents=True, exist_ok=True)
        query = {"from_loc": start,
                 'to_loc': end,
                 'from_time': '0000',
                 'to_time': '2359',
                 'from_date': date,
                 'to_date': date,
                 'days': days}
        jsonQuery = json.loads(json.dumps(query))
        r = requests.post('https://hsp-prod.rockshore.net/api/v1/serviceMetrics', headers=headers, json=jsonQuery,
                          auth=credentials)
        rJson = r.json()
        f = open('cache/' + start + '-' + end + '/' + date + '/metrics.json', 'w')
        json.dump(rJson, f)
        return rJson

def getDetails(start, end, date, rid):
    if os.path.exists('cache/' + start + '-' + end + '/' + date + '/' + rid + '.json'):
        f = open('cache/' + start + '-' + end + '/' + date + '/' + rid + '.json')
        return json.loads(f.read())
    else:
        ridJson = json.loads(json.dumps({'rid': rid}))
        r = requests.post('https://hsp-prod.rockshore.net/api/v1/serviceDetails', headers=headers, json=ridJson,
                          auth=credentials)
        rJson = r.json()
        f = open('cache/' + start + '-' + end + '/' + date + '/' + rid + '.json', 'w')
        json.dump(rJson, f)
        return rJson

def getData(start, end, date):
    rDict = getMetrics(start, end, date)

    ridList = []
    for service in rDict['Services']:
        ridList.append(service['serviceAttributesMetrics']['rids'][0])

    journeyPreds = []
    journeyActs = []
    for rid in ridList:
        r = getDetails(start, end, date, rid)

        locations = r['serviceAttributesDetails']['locations']
        desiredStations = [locations[i] for i in range(len(locations)) if
                           locations[i]['location'] == start or locations[i]['location'] == end]

        journeyPred = (formatTime(date, desiredStations[0]['gbtt_ptd']), formatTime(date, desiredStations[1]['gbtt_pta']))
        #TODO: Deal with cases where a train is cancelled halfway. Currently we just treat it as cancelled
        if (not desiredStations[0]['actual_td'] == '') and (not desiredStations[1]['actual_ta'] == ''):
            journeyAct = (formatTime(date, desiredStations[0]['actual_td']), formatTime(date, desiredStations[1]['actual_ta']))
        else:
            journeyAct = (None, None)
        journeyPreds.append(journeyPred)
        journeyActs.append(journeyAct)
    return (journeyPreds, journeyActs)

def findMinimalJourney(legs, firstTrainIndex, stations, isPredicted):
    #TODO: Deal with cancelled trains
    journey = []
    for i in range(firstTrainIndex, len(legs[0][0])):
        firstTrain = legs[0][isPredicted][i]
        if not firstTrain == (None, None):
            break
    if firstTrain == (None, None):
        return []

    nextAvailable = firstTrain[1] + timedelta(minutes=int(conTimes[stations[1]]))
    journey.append((firstTrain[0], firstTrain[1]))
    for i in range(1, len(legs)):
        for j in range(0, len(legs[i][isPredicted])):
            if legs[i][isPredicted][j][0] is None:
                continue
            if legs[i][isPredicted][j][0] >= nextAvailable:
                nextAvailable = legs[i][isPredicted][j][1] + timedelta(minutes=int(conTimes[stations[i+1]]))
                journey.append((legs[i][isPredicted][j][0], legs[i][isPredicted][j][1]))
                break
    return journey

if __name__ == '__main__':
    with open('auth.txt') as f:
        username = f.readline()
        password = f.readline()
        credentials = (username.strip(), password.strip())
    headers = {'content-type': 'application/json'}

    f = open('contimes.json', 'r')
    conTimes = json.load(f)

    for day in range(25, 29+1):
        date = '2021-11-' + str(day)
        legs = []
        stations = ['CBG', 'BHM', 'CSY']
        for i in range(len(stations)-1):
            legs.append(getData(stations[i], stations[i+1], date))

        for k in range(len(legs[0][0])):
            predJourney = findMinimalJourney(legs, k, stations, 0)
            actJourney = findMinimalJourney(legs, k, stations, 1)
            if not ((len(predJourney) == 2) and (len(actJourney) == 2)):
                continue
            delay = actJourney[-1][1] - predJourney[-1][1]
            if predJourney[-1][1] >= actJourney[-1][1]:
                delay = timedelta(0)
            if delay.seconds//60 >= 20:
                print('Date: ' + datetime.strftime(predJourney[0][0], '%d-%m-%y'))
                print('Journey: ' + datetime.strftime(predJourney[0][0], '%H:%M') + '-' + datetime.strftime(predJourney[-1][1], '%H:%M'))
                print('Delay:' + str(delay.seconds//60) + ' minutes')
                print('-------------')




