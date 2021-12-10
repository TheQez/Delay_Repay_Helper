import requests
import json
from datetime import datetime, timedelta
import os.path
from pathlib import Path
import time
import pandas as pd

class trainData:
    def __init__(self, startStation, endStation, initDate):
        self.startDate = initDate
        self.endDate = initDate
        self.startStation = startStation
        self.endStation = endStation
        self.trains = []
        self.addDay(initDate)
        if self.startStation in fixedTimes and self.endStation in fixedTimes[self.startStation]:
            self.isFixed = True
            self.fixedTime = int(fixedTimes[self.startStation][self.endStation][0])
        else:
            self.isFixed = False
            self.fixedTime = None

    def addDay(self, day):
        date = datetime.strftime(day, '%Y-%m-%d') #Temporary and bad, fix soon
        r = getMetrics(self.startStation, self.endStation, date)
        ridList = []
        for service in r['Services']:
            ridList.append(service['serviceAttributesMetrics']['rids'][0])

        for rid in ridList:
            r = getDetails(self.startStation, self.endStation, date, rid)

            locations = r['serviceAttributesDetails']['locations']
            desiredStations = [locations[i] for i in range(len(locations)) if
                               locations[i]['location'] == self.startStation or locations[i]['location'] == self.endStation]

            journeyPred = [
            formatTime(date, desiredStations[0]['gbtt_ptd']), formatTime(date, desiredStations[1]['gbtt_pta'])]
            if journeyPred[1] < journeyPred[0]:
                journeyPred[1] += timedelta(days=1)
            # TODO: Deal with cases where a train is cancelled halfway. Currently we just treat it as cancelled
            if (not desiredStations[0]['actual_td'] == '') and (not desiredStations[1]['actual_ta'] == ''):
                journeyAct = [
                formatTime(date, desiredStations[0]['actual_td']), formatTime(date, desiredStations[1]['actual_ta'])]
                if journeyAct[0] < journeyPred[0]-timedelta(hours=1):
                    journeyAct[0] += timedelta(days=1)
                if journeyAct[1] < journeyPred[0]-timedelta(hours=1):
                    journeyAct[1] += timedelta(days=1)
            else:
                journeyAct = (None, None)
            self.trains.append((rid, journeyPred[0], journeyPred[1], journeyAct[0], journeyAct[1]))

    def getTrainsInRange(self, startRange, endRange):
        if startRange < self.startDate:
            for date in pd.date_range(start=startRange, end=self.startDate-timedelta(days=1)):
                self.addDay(date)
        if endRange > self.endDate:
            for date in pd.date_range(start=self.endDate+timedelta(days=1), end=endRange):
                self.addDay(date)

        return [train for train in self.trains if train[1] >= startRange and train[1] <= endRange]

    def getTrainByRid(self, rid):
        return next((train for train in self.trains if train[0] == rid))

    def getNextTrainPredAfter(self, time):
        if self.isFixed:
            return ((None, time, time + timedelta(minutes=self.fixedTime), time, time + timedelta(minutes=self.fixedTime)))
        while True:
            nextTrain = min([train for train in self.trains if train[1] > time], key=lambda t: t[1], default=None)
            if nextTrain is not None:
                return nextTrain
            self.endDate += timedelta(days=1)
            self.addDay(self.endDate)
            #TODO: Deal with us hitting the current day

    def getNextTrainActAfter(self, time):
        if self.isFixed:
            return ((None, time, time + timedelta(minutes=self.fixedTime), time, time + timedelta(minutes=self.fixedTime)))
        while True:
            nextTrain = min([train for train in self.trains if train[3] is not None and train[3] > time], key=lambda t: t[3], default=None)
            if nextTrain is not None:
                return nextTrain
            self.endDate += timedelta(days=1)
            self.addDay(self.endDate)
            #TODO: Deal with us hitting the current day


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
        sleeptime = 1
        while True:
            try:
                r = requests.post('https://hsp-prod.rockshore.net/api/v1/serviceMetrics', headers=headers,
                                  json=jsonQuery,
                                  auth=credentials)
                rJson = r.json()
                break
            except json.decoder.JSONDecodeError:
                print('Got invalid response from API, trying again in ' + str(sleeptime) + ' seconds')
                time.sleep(sleeptime)
                sleeptime *= 2

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

def findMinPredJourney(trainDataList, firstTrain):
    journey = []
    nextAvailable = firstTrain[2] + timedelta(minutes=int(conTimes[trainDataList[0].endStation]))
    journey.append(firstTrain)
    for leg in trainDataList[1:]:
        nextTrain = leg.getNextTrainPredAfter(nextAvailable)
        journey.append(nextTrain)
        nextAvailable = nextTrain[2] + timedelta(minutes=int(conTimes[leg.endStation]))
    return journey

def findMinActJourney(trainDataList, predJourney):
    #Current behavior: If planned train is not makeable or cancelled, get the next train.
    #If current train is makeable but late and another train arrives in the meantime, take it
    journey = []
    nextAvailable = predJourney[0][1]
    for i in range(0, len(trainDataList)):
        if (not predJourney[i][3] is None) and (predJourney[i][3] >= nextAvailable) and (not predJourney[i][0] is None): #Makeable and not fixed:
            possibleTrain = trainDataList[i].getNextTrainActAfter(predJourney[i][1])
            if possibleTrain[3] < predJourney[i][3]:
                nextTrain = possibleTrain
            else:
                nextTrain = predJourney[i]
        else:
            nextTrain = trainDataList[i].getNextTrainActAfter(nextAvailable)

        journey.append(nextTrain)
        nextAvailable = nextTrain[4] + timedelta(minutes=int(conTimes[trainDataList[i].endStation]))
    return journey


if __name__ == '__main__':
    with open('auth.txt') as f:
        username = f.readline()
        password = f.readline()
        credentials = (username.strip(), password.strip())
    headers = {'content-type': 'application/json'}

    f1 = open('contimes.json', 'r')
    conTimes = json.load(f1)

    f2 = open('atocfixed.json', 'r')
    fixedTimes = json.load(f2)

    stations = ['CBG', 'KGX', 'EUS', 'BHM', 'CSY']

    startDate = datetime.strptime('21-12-01', '%y-%m-%d')
    endDate = datetime.strptime('21-12-06', '%y-%m-%d')

    trainDataList = []
    for i in range(1, len(stations)):
        trainDataList.append(trainData(stations[i-1], stations[i], startDate))
    firstTrainList = trainDataList[0].getTrainsInRange(startDate, endDate)

    for train in firstTrainList:
        p = findMinPredJourney(trainDataList, train)
        a = findMinActJourney(trainDataList, p)
        delay = a[-1][4] - p[-1][2]
        if p[-1][2] >= a[-1][4]:
            delay = timedelta(0)
        if delay.seconds // 60 >= 60:
            print('Date: ' + datetime.strftime(p[0][1], '%d-%m-%y'))
            strPredJourney = ''
            strActJourney = ''
            for i in range(len(p)):
                strPredJourney += datetime.strftime(p[i][1], '%H:%M') + '-' + datetime.strftime(
                    p[i][2], '%H:%M') + ', '
                strActJourney += datetime.strftime(a[i][3], '%H:%M') + '-' + datetime.strftime(
                    a[i][4], '%H:%M') + ', '

            print('Predicted journey: ' + strPredJourney)
            print('Actual journey: ' + strActJourney)
            print('Delay:' + str(delay.seconds // 60) + ' minutes')
            print('-------------')