import urllib.request, json 
import pandas as pd
import datetime
# from pd.io.json import json_normalize

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

# Get JSON files of a single counter; 
# "counter" is the name of a counter, a string, like "BGT"
def getJSON(counter):
    with urllib.request.urlopen(urlDict[counter]) as url:
        data = json.loads(url.read().decode())
        df = pd.io.json.json_normalize(data, record_path = "data").iloc[:,8:]
    return df

# Download data for each counter, name columns and reorder
def getRawData():
    dfList = []
    for i in range(len(Counters)):
        dfList.append(getJSON(Counters[i]))
    return dfList



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

def subsetDate(begin, end, df):
    # Return dataframe that is within the date bounds specified, in m/D/Y 
    # format
    begin = datetime.strptime(begin, '%m/%d/%Y').date()
    begin = begin.strftime('%Y%m%d')
    end = datetime.strptime(end, '%m/%d/%Y').date()
    end = end.strftime('%Y%m%d')
    
    return df[begin:end]

def subsetTime(begin, end, df):
    # Return dataframe within the times specified, in 24 hour format
    # e.g. begin = '12:00', end = '13:00'
    df = df.between_time(begin, end)
    return df
    
def subsetWeather(weather, df):
    # Return dataframe that has the specified weather
    # Options: Sunny, cloudy, rain, storm
    if weather == "All":
        return df
    else:
        return df[df.Weather == weather]

'''def subsetSeason(season, df):
    # Return dataframe that has the specified season
    # Options: Spring, Summer, Fall, Winter, All
    return df'''

def subsetTemp(low, high, df):
    # Return dataframe containing only days where average temp is within bounds
    # specified
    return df[df.Temp >= low and df.Temp  <= high]

def subsetWeekday(daylist, df):
    # Return dataframe containing only the days of the week specified,
    # where 0 = Monday, 1 = Tuesday, etc.
    df[df.index.weekday.isin(daylist)]
    return df

raw = getRawData()
dfList = raw.copy()
dfList = modifyData(dfList)
totalDF = getTotalDF(dfList)
path = r"C:\Users\asher\Documents\GitHub\data602-finalproject\totalDF.csv"
totalDF.to_csv(path)
