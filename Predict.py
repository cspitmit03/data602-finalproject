import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from fbprophet import Prophet

#predPath = r"C:\Users\asher\Documents\GitHub\data602-finalproject\predictorsDF.csv"
predPath = "https://raw.githubusercontent.com/cspitmit03/data602-finalproject/master/predictorsDF.csv"
predictorsDF = pd.read_csv(predPath, index_col = 0)
predictorsDF["logPrecip"] = np.log(predictorsDF["Precip"]+1) # Add a log(precipitation) column

Indx = [] # Index to hold dates
for i in range(len(predictorsDF)): 
    # Convert strings containing dates (eg '2012-10-03') to date objects
    Indx.append(datetime.strptime(predictorsDF.index[i], '%Y-%m-%d').date())
predictorsDF.index = Indx

def CreateModels():
# Create a list of Prophet forecasts, one series for each counter
    Models = []
    
    for i in range(10):
        # Start dataframe at each counter with first date counter was active.
        # All counters except Fremont and Second began on 1/1/2014
        if predictorsDF.columns[i] == 'Fremont': k = 0 # 10/3/2012
        elif predictorsDF.columns[i] == 'Second': k = 820 # 1/1/2015
        else: k = 455    #1/1/2014
        
        df = pd.DataFrame(data = {'ds': predictorsDF.index[k:], # dates
                              'y': predictorsDF.iloc[k:, i], # Counts
                              'logPrecip': predictorsDF['logPrecip'][k:], # log of rainfall in inches
                                 'TempHi': predictorsDF['TempHi'][k:],  # Daily high temperature, Fahrenheit
                                 'cap': max(predictorsDF.iloc[k:, i]),
                                 'floor': min(predictorsDF.iloc[k:, i])}) # Maximum value = maximum observed in dataset
    
        # Create the Prophet Model
        m = Prophet(growth='linear', yearly_seasonality=True, daily_seasonality = False, 
                    weekly_seasonality = True)
        m.add_regressor('logPrecip')
        m.add_regressor('TempHi')
    
        # Fit the Prpohet Model
        m.fit(df)
        Models.append(m)
        
    return Models
    
# Create the dataframe to house the dates to predict, and their forecasted weather

# Get a table of forecasts for the next X days, where x is an integer between 1
# and 10 inclusive
def GetForecastTable(Models, days = 7):

    thisDay = datetime.today()
    date_list = [(thisDay + timedelta(days=x)).date() for x in range(0, days)]
    
    # Compute number of days since last date of actuals, in this case October 31, 2017
    #delt = (datetime.today().date() - datetime(2017, 10, 31).date()).days
    
    # Get weather forecast data, to predict upcoming bike counts using weatherbit API, in Imperial measures.
    ForecastURL= 'http://api.wunderground.com/api/91468d8e9a46ecc5/forecast10day/q/WA/Seattle.json'
    forecastJSON = pd.read_json(ForecastURL) # Read in the JSON data from API call
    logPrecip = [] # list to house rainfall forecasts
    TempHi = []
    for i in range(days): 
        DayDict = forecastJSON.iloc[1, 0]['forecastday'][i] # Identify location in JSON where data appears
        logPrecip.append(np.log(DayDict['qpf_allday']['in'] + 1)) # Add 1 to avoid log of zero
        TempHi.append(int(DayDict['high']['fahrenheit'])) 
        
    # Create dataframe
    future = pd.DataFrame({'TempHi': TempHi,
                          'logPrecip': logPrecip,
                          'ds': date_list,
                          'floor': 0,
                          'cap': max(predictorsDF["Fremont"])},
                         index = list(range(days)))
    
    # Create table of forecasts
    # Forecasts contains the point estimate forecast, as well as the confidence 
    # interval, trend components, and other statistical information about the model
    Forecasts = []
    ForecastTable = pd.DataFrame({}, index = date_list)
    for i in range(10):
        Forecasts.append(Models[i].predict(future))
        ForecastTable[predictorsDF.columns[i]] = Forecasts[i]['yhat'].values# Create column for each counter forecast
        
    ForecastTable = round(ForecastTable)
    ForecastTable[ForecastTable < 0 ] = 0
    return ForecastTable, Forecasts

def PlotTrendAnalysis(Models, counterNumber = 3):
    # Plots the historical trends as detected by the model
    
    if counterNumber == 3: k = 0 # Fremont, started 10/3/2012
    elif counterNumber == 6: k = 820 # Second St, started 1/1/2015
    else: k = 455    # All others, started 1/1/2014
    
    future = pd.DataFrame({'TempHi': predictorsDF["TempHi"][k:],
                      'logPrecip': predictorsDF["logPrecip"][k:],
                      'ds': predictorsDF.index[k:],
                      'floor': 0,
                      'cap': max(predictorsDF.iloc[k:, counterNumber][k:])},
                     index = predictorsDF.index[k:])
    
    forecast = Models[counterNumber].predict(future)
    Models[counterNumber].plot_components(forecast)
    
    return

Models = CreateModels()
ForecastTable, Forecasts = GetForecastTable(Models, days = 7)
PlotTrendAnalysis(Models, counterNumber = 3)