import urllib.request, json 
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
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
    # average of the datapoints one week before and after on Fremont
        
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

def updatePredictorsDF():
    raw = getRawData()
    dfList = []
    for i in range(len(raw)):
        dfList.append(raw[i].copy(deep = True)) # Put raw counter data into list of lists
    totalDF = modifyData(dfList) # Put list of lists into single dataframe
    totalDF = markNulls(totalDF) # Replace nulls with imputed values
    dailyDF = getDailyDF(totalDF) # Convert hourly to weekly data
    
    weatherPath = "https://raw.githubusercontent.com/cspitmit03/data602-finalproject/master/weatherDF.csv"
    weatherDF = pd.read_csv(weatherPath, index_col = 0)
    Indx = [] # Index to house dates
    for i in range(len(weatherDF)): 
        Indx.append(datetime.strptime(weatherDF.index[i], '%Y-%m-%d').date())
    weatherDF.index = Indx
    
    predictorsDF = pd.concat([dailyDF, weatherDF], axis = 1)
           
    predPath = r"C:\Users\asher\Documents\GitHub\data602-finalproject\predictorsDF.csv"
    predictorsDF.to_csv(predPath)
    
    return

# Update Bike Counts (to be performed monthly, followed by a push to github)
def updateHistDF():
    
    # Pull data from Seattle data portal, then write to local Github repo
    # Counts in this DF are not edited; they are used for historical viewing
    raw = getRawData()
    dfList = []
    for i in range(len(raw)):
        dfList.append(raw[i].copy(deep = True))
    histDF = modifyData(dfList)
    histPath = r"C:\Users\asher\Documents\GitHub\data602-finalproject\histDF.csv"
    histDF.to_csv(histPath)
 
    return

def getDaylightList(end = datetime(2017, 11, 30)):
    # ^Put in last day of previous month
    
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
        
    return daylight

def addDaylightToWeatherCSV():
    # Get weatherDF
    weatherPath = r"https://raw.githubusercontent.com/cspitmit03/data602-finalproject/master/weatherDF.csv"
    weatherDF = pd.read_csv(weatherPath, index_col = 0)
    
    # Replace index with datestamps
    Indx = [] # Index to house dates
    for i in range(len(weatherDF)): 
        Indx.append(datetime.strptime(weatherDF.index[i], '%Y-%m-%d').date())
    weatherDF.index = Indx

    # Put in hours of daylight per day column
    daylightHours = getDaylightList()
    weatherDF["daylightHours"] = daylightHours
    
    # Write to hard drive
    weatherPath = r"C:\Users\asher\Documents\GitHub\data602-finalproject\weatherDF.csv"
    weatherDF.to_csv(weatherPath)
    
    return

def updateAll():
    
    # To update code:
    
    # Manually update the weather CSV using URL below, and adjust for month
    # https://www.wunderground.com/history/airport/KBFI/2017/12/4/CustomHistory.html?&reqdb.zip=&reqdb.magic=&reqdb.wmo=
    
    # Add the daylight hours
    addDaylightToWeatherCSV()
    
    updateHistDF()
    updatePredictorsDF()
    
    return
