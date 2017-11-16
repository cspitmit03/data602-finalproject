import urllib.request, json 
import pandas as pd
import datetime
from pymongo import MongoClient
from bson import json_util
import os, time, glob
import socket
# from pd.io.json import json_normalize

#setup MongoDB to store all information

#client = MongoClient(os.environ['DB_PORT_27017_TCP_ADDR'],27017)
client = MongoClient('localhost:27017')
db = client.bike
blotters = db.blotter #Select the collection

# Dictionary of Counters and their JSON file location
urlDict = {"BGT": "https://data.seattle.gov/api/views/2z5v-ecg8/rows.json?accessType=DOWNLOAD",
           "Broad": "https://data.seattle.gov/api/views/j4vh-b42a/rows.json?accessType=DOWNLOAD",
           "Ell": "https://data.seattle.gov/api/views/4qej-qvrz/rows.json?accessType=DOWNLOAD",
           "Fre": "https://data.seattle.gov/api/views/65db-xm6k/rows.json?accessType=DOWNLOAD",
           "MTS": "https://data.seattle.gov/api/views/u38e-ybnc/rows.json?accessType=DOWNLOAD",
           "NW58": "https://data.seattle.gov/api/views/47yq-6ugv/rows.json?accessType=DOWNLOAD",   
           "Sec": "https://data.seattle.gov/api/views/avwm-i8ym/rows.json?accessType=DOWNLOAD",
           "Spok": "https://data.seattle.gov/api/views/upms-nr8w/rows.json?accessType=DOWNLOAD",
           "Thirty": "https://data.seattle.gov/api/views/3h7e-f49s/rows.json?accessType=DOWNLOAD",
           "TwoSix": "https://data.seattle.gov/api/views/mefu-7eau/rows.json?accessType=DOWNLOAD"
           }
# Create an alphabetical list of counters
Counters = list(urlDict.keys())
Counters.sort()

# Column names for Pedestrian + Bike Counters, and Bike-only counters
PedBikeCols = ["Date", "PBTotal", "PedNB", "PedSB", "BikeNB", "BikeSB"]
BikeOnlyCols = ["Date", "BTotal", "BikeNB", "BikeSB"]

# Column list for later use in reordering columns for ped & bike counters
PBColOrder = ["Date","BTotal", "PBTotal", "PedNB", "PedSB", "BikeNB", "BikeSB"]

DB_NAME = 'seattlebikes'
DB_HOST = 'ds243055.mlab.com'
DB_PORT = 43055
DB_USER = 'jamiel'
DB_PASS = 'Data602'

client = MongoClient(DB_HOST, DB_PORT)
db = client[DB_NAME]
db.authenticate(DB_USER, DB_PASS)
bikes = db.bike #Select the collection

# Get JSON files of a single counter; 
# "counter" is the name of a counter, a string, like "BGT"
def getJSON(counter):
    with urllib.request.urlopen(urlDict[counter]) as url:
        data = json.loads(url.read().decode())
        df = pd.io.json.json_normalize(data, record_path = "data").iloc[:,8:]
    return df

def getJSON2(counter):
    with urllib.request.urlopen(urlDict[counter]) as url:
        data = json.loads(url.read().decode())
    return data


# Download data for each counter, name columns and reorder
def getRawData():
    dfList = []
    for i in range(len(Counters)):
        dfList.append(getJSON(Counters[i]))
    return dfList

blotters.insert_many(json.loads(url.read().decode())).inserted_id

def modifyData(dfList):
    for i in range(len(Counters)):
  
        # Remove entries with null values (these were defective observations)
        #dfList[i] = dfList[i][pd.notnull(dfList[i].iloc[:, 1])]
        
        # Convert counts from strings to numerics
        for col in dfList[i].columns[1:]:
            dfList[i][col] = pd.to_numeric(dfList[i][col])
        
        # Rename columns, according to whether they are bike-only or ped & bike
        # counters; Fremont Bridge (i = 3) lacked a total column, so is treated 
        # separately here
        if len(dfList[i].columns) == 3:
            dfList[i].columns = ["Date", "BikeNB", "BikeSB"]
            dfList[i]["BTotal"] = dfList[i]["BikeNB"] + dfList[i]["BikeSB"]
            dfList[i] = dfList[i][["Date", "BTotal", "BikeNB", "BikeSB"]]
        elif len(dfList[i].columns) == 4:
            dfList[i].columns = BikeOnlyCols
        elif len(dfList[i].columns) == 6:
            dfList[i].columns = PedBikeCols
            dfList[i]["BTotal"] = dfList[i]["BikeNB"] + dfList[i]["BikeSB"]
            dfList[i] = dfList[i][PBColOrder]
        
        # Convert date strings to timestamp objects
        dfList[i].Date = pd.Series(
                [pd.to_datetime(date, 
                format = '%Y-%m-%dT%H:%M:%S') for date in dfList[i].Date])
    # Remove entries with null values, these are defective observations
    # For some reason, putting this in the main loop caused a crash every time
    for i in range(len(Counters)):
        dfList[i] = dfList[i][pd.notnull(dfList[i].iloc[:, 1])]
    return dfList

def getTotalDF(dfList):
    totalDF = pd.DataFrame({})
    for i in range(len(dfList)):
        
        # Rename BTotal column to Counter name, and remove columns after
        dfList[i] = dfList[i].rename(columns = {'BTotal':Counters[i]})
        dfList[i] = dfList[i].iloc[:, 0:2]
    
    # Use longest-running counter (Fremont, i = 3) to create a dates column    
    totalDF = pd.DataFrame({'Date': dfList[3].Date})
    
    # Merge values into date dataframe
    for i in range(len(dfList)):    
        totalDF = pd.merge(totalDF, dfList[i], on='Date', how='outer') 
    
    # Sort entries by date
    totalDF = totalDF.sort_values('Date')
    
    return totalDF

raw = getRawData()
dfList = raw.copy()
dfList = modifyData(dfList)
totalDF = getTotalDF(dfList)
totalDF = totalDF.fillna(0)

for i in range(len(totalDF)):
    Date = (totalDF.iloc[i,0]).to_pydatetime()
    BGT = totalDF.iloc[i,1]
    Broad = totalDF.iloc[i,2]
    Ell = totalDF.iloc[i,3]
    Fre = totalDF.iloc[i,4]
    MTS = totalDF.iloc[i,5]
    NW58 = totalDF.iloc[i,6]
    Sec = totalDF.iloc[i,7]
    Spok = totalDF.iloc[i,8]
    Thirty = totalDF.iloc[i,9]
    TwoSix = totalDF.iloc[i,10]
    k = db.bike.count()
    newentry = ()
    
    myrecord = {
        "_id": k,
        "Date": Date,
        "BGT": BGT,
        "Broad": Broad,
        "Ell": Ell,
        "Fre": Fre,
        "MTS": MTS,
        "NW58": NW58,
        "Sec": Sec,
        "Spok": Spok,
        "Thirty": Thirty,
        "TwoSix": TwoSix
        }
    
    db.bike.insert_one(myrecord)
    
    bikes.insert_one(totalDF.iloc[i].to_dict())
    
    d = db.bike.find()
import json
    df = ps.DataFrame(list(d))
    
    for item in data['data']['Date']:
        timestamp_millis = int(item['Date'])
        utc_time = datetime(1970, 1, 1) + timedelta(milliseconds=timestamp_millis)
        print(utc_time.isoformat() + 'Z')
    

path = r"C:\Users\asher\Documents\Classes\CUNY\DATA 602\Final Project\TotalDF.csv"
totalDF.to_csv(path)
