import urllib.request, json 
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import calendar
from fbprophet import Prophet
import matplotlib.pyplot as plt
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

plt.style.use('fivethirtyeight')

'''
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


sunsAndBoolsDF = getSunsAndBools()

FremontDF = pd.concat([dailyDF["Fremont"], sunsAndBoolsDF, weatherDF], axis = 1)

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
    
    newList = []
    for i in range(len(Counters)):
        df = dfList[i]
        # Remove entries with null values (these were defective observations)
        #dfList[i] = dfList[i][pd.notnull(dfList[i].iloc[:, 1])]
        
        # Convert counts from strings to numerics
        for col in df.columns[1:]:
            df[col] = pd.to_numeric(df[col])
        
        # Rename columns, according to whether they are bike-only or ped & bike
        # counters; Fremont Bridge (i = 3) lacked a total column, so is treated 
        # separately here

        if len(df.columns) == 4: # For bike only counters
            df.columns = ["Date", Counters[i], "BikeNB", "BikeSB"]
        elif len(df.columns) == 6: # For bike and ped counters
            df.columns = ["Date", "PBTotal", "PedNB", "PedSB", "BikeNB", "BikeSB"]
            df[Counters[i]] = df["BikeNB"] + df["BikeSB"]
        else: #Fremont has no total column
            df.columns = ["Date", "BikeNB", "BikeSB"]
            df[Counters[i]] = df["BikeNB"] + df["BikeSB"]
             
        # Convert date strings to timestamp objects
        df.index = pd.to_datetime(df["Date"], format = '%Y-%m-%dT%H:%M:%S')
        df = df[[Counters[i]]]
        newList.append(df)
    
    # Create a data frame whose index is the complete date list    
    totalDF = pd.DataFrame(index = dfList[3].index)
        
    # Join all the counter data on dates. Note, this counter data only includes bike totals
    totalDF = totalDF.join(newList)
    totalDF = totalDF[~totalDF.index.duplicated(keep='first')]
    totalDF.index = dfList[3].index
    
    return totalDF

def markNulls(totalDF):
    
    # This function marks hourly entries as null when they seem defective
    # They seem defective when a) they have zeros or values close to zero when
    # other counters have positive counts and b) when in a long anomalous chain
    # of zero or near-zero values
    
    # These nulls are then replaced by imputed values calculated as a ratio to 
    # the Fremont values. For missing Fremont values, these are imputed by the 
    # average of the datapoints one week before and after
        
    # Impute Missing Fremont values: Average of t - 1 week, t + 1 week
    totalDF.loc["6/14/2013 9:00", "Fremont"] = (totalDF.loc["6/7/2013 9:00", "Fremont"] + totalDF.loc["6/21/2013 9:00", "Fremont"])/2 
    totalDF.loc["6/14/2013 10:00", "Fremont"] = (totalDF.loc["6/7/2013 10:00", "Fremont"] + totalDF.loc["6/21/2013 10:00", "Fremont"])/2 
    totalDF.loc["3/9/2014 2:00", "Fremont"] = (totalDF.loc["3/2/2014 2:00", "Fremont"] + totalDF.loc["3/16/2014 2:00", "Fremont"])/2 
    totalDF.loc["3/8/2015 2:00", "Fremont"] = (totalDF.loc["3/1/2015 2:00", "Fremont"] + totalDF.loc["3/15/2015 2:00", "Fremont"])/2 
    totalDF.loc["4/21/2015 11:00", "Fremont"] = (totalDF.loc["4/14/2015 11:00", "Fremont"] + totalDF.loc["4/28/2015 11:00", "Fremont"])/2 
    totalDF.loc["4/21/2015 12:00", "Fremont"] = (totalDF.loc["4/14/2015 12:00", "Fremont"] + totalDF.loc["4/28/2015 12:00", "Fremont"])/2 
    totalDF.loc["3/13/2016 2:00", "Fremont"] = (totalDF.loc["3/6/2016 2:00", "Fremont"] + totalDF.loc["3/20/2016 2:00", "Fremont"])/2 
    totalDF.loc["3/12/2017 2:00", "Fremont"] = (totalDF.loc["3/5/2017 2:00", "Fremont"] + totalDF.loc["3/19/2017 2:00", "Fremont"])/2     
    
    # Calculate ratios for imputing values
    ratios = []
    # Non-Null Fremont Entries
    Fremonts = totalDF["Fremont"][totalDF["Fremont"].notnull()]
    
    for i in range(10):
        
        # Counter name
        name = Counters[i]
        
        # Non-Null Counter i entries
        Counter = totalDF[totalDF[name].notnull()][name]
        
        #Join on rows where they both have values (i.e. have identical indexes)
        Both = Fremonts.align(Counter, axis = 0, join = 'inner')
        
        # Store the ratio of Counter sum / Fremont Sum, which empirically
        # is 8%-41%
        ratios.append(sum(Both[1])/sum(Both[0]))
    
    
    # Identify probable defective values as null, then impute them
    
    #BGT - 0
    totalDF.loc["11/14/2015 9:00":"12/7/2015 11:00","BGT"] = None
    
    #Broad - 1
    totalDF.loc["11/29/2014 18:00":"11/30/2014 23:00","Broad"] = None
    totalDF.loc["6/1/2015 0:00":"6/1/2015 10:00","Broad"] = None
    totalDF.loc["9/4/2015 12:00":"9/18/2015 13:00","Broad"] = None  
    totalDF.loc["7/24/2017 3:00":"8/1/2017 11:00","Broad"] = None
    
    #Elliot - 2
    totalDF.loc["3/1/2015 12:00":"4/2/2015 12:00","Elliot"] = None 

    #MTS - 4
    totalDF.loc["2/20/2015 20:00":"3/3/2015 9:00","MTS"] = None
    
    #NW58 - 5
    totalDF.loc["8/25/2014 16:00":"8/28/2014 13:00","NW58"] = None
    totalDF.loc["12/30/2014 2:00":"1/1/2015 12:00","NW58"] = None
    totalDF.loc["4/11/2015 0:00":"4/12/2015 23:00","NW58"] = None
    totalDF.loc["5/15/2015 18:00":"5/17/2015 6:00","NW58"] = None
    totalDF.loc["4/21/2017 12:00":"4/25/2017 11:00","NW58"] = None
    totalDF.loc["4/28/2017 14:00":"5/3/2017 12:00","NW58"] = None
    totalDF.loc["5/12/2017 9:00":"6/2/2017 12:00","NW58"] = None

    #Second - 6
    totalDF.loc["6/11/2015 23:00":"6/18/2015 10:00","Second"] = None   
    totalDF.loc["4/2/2016 3:00":"4/4/2016 10:00","Second"] = None
    totalDF.loc["11/1/2016 9:00":"11/28/2016 13:00","Second"] = None 
    
    # Spokane - 7
    
    # Thirty - 8
    
    # TwoSix - 9
    totalDF.loc["1/30/2015 11:00":"2/3/2015 9:00","TwoSix"] = None
    totalDF.loc["11/16/2015 18:00":"12/2/2015 10:00","TwoSix"] = None
    totalDF.loc["11/1/2016 9:00":"11/28/2016 13:00","TwoSix"] = None
    
    
    # Pseudocode: impute values to null using ratios
    for i in range(10):
        name = Counters[i]
        Counts = totalDF[name]
        totalDF.loc[Counts.isnull(), name] = ratios[i]*totalDF.loc[Counts.isnull()]["Fremont"]
    
    
    return totalDF

def getDailyDF(df):
    # Create dataframe that displays daily totals by counter
    #Convert date and time to just date
    df.index = pd.DatetimeIndex(df.index).normalize()
    # Aggregate total rides for each day and counter
    df = df.groupby(pd.DatetimeIndex(df.index)).sum()
    
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
    dfList = []
    for i in range(len(raw)):
        dfList.append(raw[i].copy(deep = True))
    totalDF = modifyData(dfList)
    dailyDF = getDailyDF(totalDF)
    
    totalPath = r"C:\Users\asher\Documents\GitHub\data602-finalproject\totalDF.csv"
    dailyPath = r"C:\Users\asher\Documents\GitHub\data602-finalproject\dailyDF.csv"
    
    totalDF.to_csv(totalPath)
    dailyDF.to_csv(dailyPath)
    
    totalDF = pd.read_csv(totalPath)
    
    # Update weatherCSV manually, then add dummy variables
    # Manually scrape WeatherUndeground for most recent full month 
    # from WeatherURL
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
    
def weeklyDF(dailyDF):
    # Converts dataframe of daily counts to rolling weekly average
    return dailyDF.rolling(window = 7).mean()

def updateDaylightCSV(end = datetime(2017, 10, 31)):

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
    daylight = []
    for i in range(duration):
        day = (dateList[i] - pd.datetime(2000, 12, 21).date()).days # difference in days
        day %= 365.25
        m = 1. - np.tan(np.radians(latitude)) * np.tan(np.radians(axis) * np.cos(day * np.pi / 182.625))
        m = max(0, min(m, 2))
        daylight.append(24. * np.degrees(np.arccos(1 - m)) / 180.)
    
    daylightDF =  pd.DataFrame(data = {'daylightHours': daylight}, 
                               index = dateList)
    daylightDF.index.name = "Date"
    daylightDF.to_csv("daylightDF.csv")
        
    return 
        
        
weeklyDF = dailyDF.rolling(window = 30).mean()
ax = weeklyDF.plot(figsize=(12, 8))
ax.set_ylabel('Monthly Number of Airline Passengers')
ax.set_xlabel('Date')

plt.show()
