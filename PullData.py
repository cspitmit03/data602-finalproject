import urllib.request, json 
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import calendar
# from pd.io.json import json_normalize

# Dictionary of Counters and their JSON file location
urlDict = {"BGT": "https://data.seattle.gov/api/views/2z5v-ecg8/rows.json?accessType=DOWNLOAD",
           "Broad": "https://data.seattle.gov/api/views/j4vh-b42a/rows.json?accessType=DOWNLOAD",
           "Elliot": "https://data.seattle.gov/api/views/4qej-qvrz/rows.json?accessType=DOWNLOAD",
           "Fremont": "https://data.seattle.gov/api/views/65db-xm6k/rows.json?accessType=DOWNLOAD",
           "MTS": "https://data.seattle.gov/api/views/u38e-ybnc/rows.json?accessType=DOWNLOAD",
           "NW58": "https://data.seattle.gov/api/views/47yq-6ugv/rows.json?accessType=DOWNLOAD",   
           "Second": "https://data.seattle.gov/api/views/avwm-i8ym/rows.json?accessType=DOWNLOAD",
           "Spokane": "https://data.seattle.gov/api/views/upms-nr8w/rows.json?accessType=DOWNLOAD",
           "Thirty": "https://data.seattle.gov/api/views/3h7e-f49s/rows.json?accessType=DOWNLOAD",
           "TwoSix": "https://data.seattle.gov/api/views/mefu-7eau/rows.json?accessType=DOWNLOAD"
           }
# Create an alphabetical list of counters
Counters = list(urlDict.keys())
Counters.sort()

# Column list for later use in reordering columns for ped & bike counters
PBColOrder = ["Date","BTotal", "PBTotal", "PedNB", "PedSB", "BikeNB", "BikeSB"]

# Grab the datasets
weatherPath = "https://raw.githubusercontent.com/cspitmit03/data602-finalproject/master/weatherDF.csv"
weatherDF = pd.read_csv(weatherPath, index_col = 0)
Indx = [] # Index to house dates
for i in range(len(weatherDF)): 
    Indx.append(datetime.strptime(weatherDF.index[i], '%Y-%m-%d').date())
weatherDF.index = Indx



totalPath = "https://raw.githubusercontent.com/cspitmit03/data602-finalproject/master/TotalDF.csv"
totalDF = pd.read_csv(totalPath)

dailyPath = "https://raw.githubusercontent.com/cspitmit03/data602-finalproject/master/dailyDF.csv"
dailyDF = pd.read_csv(dailyPath)
dailyDF.index = dailyDF["Date"]
del dailyDF["Date"]

Indx = [] # Index to house dates
for i in range(len(dailyDF)): 
    Indx.append(datetime.strptime(dailyDF.index[i], '%Y-%m-%d').date())
dailyDF.index = Indx

'''
sunsAndBoolsDF = getSunsAndBools()

FremontDF = pd.concat([dailyDF["Fre"], sunsAndBoolsDF, weatherDF], axis = 1)

FremontPath = r"C:\Users\asher\Documents\GitHub\data602-finalproject\FremontAndPredictors.csv"
        
FremontDF.to_csv(FremontPath)
'''


def getSunsAndBools(end = datetime(2017, 10, 31)):

    # Create a list containing all dates
    start = datetime(2012, 10, 3) # First day of data
    duration = (end - start).days + 1 # length of duration in days
    
    dateList = []
    for i in range(duration):
        dateList.append((start + timedelta(days=i)).date())
        
    axis = 23.44
    latitude = 47.61
    
    # Given start and end dates, return an array containing the hours of sunlight
    # for each date
    sunlight = []
    for i in range(duration):
        day = (dateList[i] - pd.datetime(2000, 12, 21).date()).days # difference in days
        day %= 365.25
        m = 1. - np.tan(np.radians(latitude)) * np.tan(np.radians(axis) * np.cos(day * np.pi / 182.625))
        m = max(0, min(m, 2))
        sunlight.append(24. * np.degrees(np.arccos(1 - m)) / 180.)
    
    # Create boolean columns for each day of the week
    weekdays = []
    for j in range(7):
        weekday = []
        for i in range(duration):
            weekday.append((dateList[i].weekday() == j))
        weekdays.append(weekday)
    
    # Create a boolean isMay, because May is bike to work month, and may have 
    # additional ridership as a result, aside from other factors    
    isMay = []
    for i in range(duration):
        isMay.append(dateList[i].month == 5) # True if in May, otherwise false
    
    SunsAndBools = pd.DataFrame({'Sunlight': sunlight,
                                'isMay': isMay,
                                'Monday': weekdays[0],
                                'Tuesday':weekdays[1],
                                'Wednesday': weekdays[2],
                                'Thursday': weekdays[3],
                                'Friday': weekdays[4],
                                'Saturday': weekdays[5],
                                'Sunday': weekdays[6]}, index = dateList)
    
    # Sunlight code is courtesy of Jake Vanderplas, an astronomy PHD who literally wrote 
    # the book on data science for Python, and also investigated Seattle cycling: 
    # http://jakevdp.github.io/blog/2014/06/10/is-seattle-really-seeing-an-uptick-in-cycling/
    
    return SunsAndBools
    

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
        if len(dfList[i].columns) == 3: #Fremont has no total column
            dfList[i].columns = ["Date", "BikeNB", "BikeSB"]
            dfList[i][Counters[i]] = dfList[i]["BikeNB"] + dfList[i]["BikeSB"]
        elif len(dfList[i].columns) == 4: # For bike only counters
            dfList[i].columns = ["Date", Counters[i], "BikeNB", "BikeSB"]
        elif len(dfList[i].columns) == 6: # For bike and ped counters
            dfList[i].columns = ["Date", "PBTotal", "PedNB", "PedSB", "BikeNB", "BikeSB"]
            dfList[i][Counters[i]] = dfList[i]["BikeNB"] + dfList[i]["BikeSB"]
             
        # Convert date strings to timestamp objects
        dfList[i].index = pd.to_datetime(dfList[i]["Date"], format = '%Y-%m-%dT%H:%M:%S')
        dfList[i] = dfList[i][[Counters[i]]]
    
    # Create a data frame whose index is the complete date list    
    totalDF = pd.DataFrame(index = dfList[3].index)
    
    # Join all the counter data on dates. Note, this counter data only includes bike totals
    totalDF = totalDF.join(dfList, how = 'outer')
    # Remove entries with null values, these are defective observations
    # For some reason, putting this in the main loop caused a crash every time
    #for i in range(len(Counters)):
    #    dfList[i] = dfList[i][pd.notnull(dfList[i]["BTotal"])]
    return totalDF

'''def getTotalDF(dfList):
    totalDFf = pd.DataFrame({})
    
    #for i in range(len(dfList)):
        
        # Rename BTotal column to Counter name, and remove columns after
    #    dfList[i] = dfList[i].rename(columns = {'BTotal':Counters[i]})
    #    dfList[i] = dfList[i].iloc[:, 0:2]
    
    # Use longest-running counter (Fremont, i = 3) to create a dates column    
    result = pd.DataFrame(index = dfList[3].Date)
    
    
    
    # Merge values into date dataframe
    for i in range(len(dfList)):    
        #totalDFf[Counters[i]] = dfList[i][Counters[i]]
        #df = pd.merge(totalDFf, dfList[i], how='outer', on=[totalDFf.index, dfList[i]["Date"])
        df = dfList[i].copy()
        df.index = df["Date"]
        del df["Date"]
        result.join(df, how = "outer")
        
    # Sort entries by date
    totalDF = totalDF.sort_values('Date')
    
    # Convert date column to index
    totalDF.index = totalDF["Date"]
    del totalDF["Date"]
    
    return totalDF'''

def getDailyDF(df):
    # Create dataframe that displays daily totals by counter
    #Convert date and time to just date
    df.index = pd.DatetimeIndex(df.index).normalize()
    # Aggregate total rides for each day and counter
    df = df.groupby(pd.DatetimeIndex(df.index)).sum()
    
    return df

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
    return df

def subsetCounter(counters):
    # Remove specified counters from dataset'''

def subsetTemp(low, high, df):
    # Return dataframe containing only days where average temp is within bounds
    # specified
    return df[df.Temp >= low and df.Temp  <= high]

def subsetWeekday(daylist, df):
    # Return dataframe containing only the days of the week specified,
    # where 0 = Monday, 1 = Tuesday, etc.
    df[df.index.weekday.isin(daylist)]
    return df

def addWeatherDummies(df):
    df.Events = weatherDF.Events.replace(np.nan, '', regex=True)
    df["DidRain"] = df['Events'].str.contains("Rain")
    df["DidFog"] = df['Events'].str.contains("Fog")
    df["DidSnow"] = df['Events'].str.contains("Snow")
    df["DidThunder"] = df['Events'].str.contains("Thunderstorm")
    
    return df

# Update Bike Counts (to be performed monthly, followed by a push to github)
def updateData():
    
    # Pull data from Seattle data portal, then write to local Github repo
    raw = getRawData()
    dfList = raw.copy()
    totalDF = modifyData(dfList)
    dailyDF = getDailyDF(totalDF)
    
    totalPath = r"C:\Users\asher\Documents\GitHub\data602-finalproject\totalDF.csv"
    dailyPath = r"C:\Users\asher\Documents\GitHub\data602-finalproject\dailyDF.csv"
    
    totalDF.to_csv(totalPath)
    dailyDF.to_csv(dailyPath)
    
    # Update weatherCSV manually, then add dummy variables
    '''Manually scrape WeatherUndeground for most recent full month 
    from WeatherURL'''
    now = datetime.now()
    if now.month == 1: 
        lastMonth = 12
        year = now.year - 1
    else: 
        lastMonth = now.month - 1
        year = now.year
    daysInMonth = calendar.monthrange(year, lastMonth)[1]
    WeatherURL =  "https://www.wunderground.com/history/airport/KBFI/" + str(year) + "/" + str(lastMonth) + "/1/CustomHistory.html?dayend=" + str(daysInMonth) + "&monthend=" + str(lastMonth) + "&yearend=" + str(year) + "&req_city=&req_state=&req_statename=&reqdb.zip=&reqdb.magic=&reqdb.wmo="
    print(WeatherURL)
    
    weatherPath = r"C:\Users\asher\Documents\GitHub\data602-finalproject\weatherDF.csv"
    weatherDF = pd.read_csv(weatherPath, index_col = 0)
    weatherDF = addWeatherDummies(weatherDF) # Create new Weather DF with dummy variables, like DidRain
    weatherDummyPath = r"C:\Users\asher\Documents\GitHub\data602-finalproject\weatherDummyDF.csv"
    weatherDF.to_csv(weatherDummyPath)
    
    return

def get10DayForecast():
    URL = "http://api.wunderground.com/api/91468d8e9a46ecc5/forecast10day/q/WA/Seattle.json"
    with urllib.request.urlopen(URL) as url:
        forecastList = json.loads(url.read().decode())["forecast"]["simpleforecast"]["forecastday"]
    
    
    for i in range(len(forecastList)):
        del forecastList[i]["date"]
    

