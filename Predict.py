import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from fbprophet import Prophet
import matplotlib.pyplot as plt
import seaborn as sns
from bokeh.plotting import figure, output_file #show
from bokeh.models import FuncTickFormatter, ColumnDataSource, DataRange1d, Plot, LinearAxis, Grid
from bokeh.layouts import widgetbox, layout
from bokeh.io import curdoc
from bokeh.models.widgets import Select
from bokeh.models.glyphs import VBar

import pickle


    


#predPath = r"C:\Users\asher\Documents\GitHub\data602-finalproject\predictorsDF.csv"
predPath = "https://raw.githubusercontent.com/cspitmit03/data602-finalproject/master/predictorsDF.csv"
predictorsDF = pd.read_csv(predPath, index_col = 0)
predictorsDF["logPrecip"] = np.log(predictorsDF["Precip"]+1) # Add a log(precipitation) column
WeekdayNames = ['Monday', 'Tuesday', 'Weds', 'Thursday', 'Friday', 'Saturday', 'Sunday']
counterNames = ["Burke Gilman Trail", "Broad", "Elliott", "Fremont Bridge",
                "MTS Trail", "NW 58th St", "2nd Ave", "Spokane St", 
                "39th Ave", "26th Ave", "Total"]

# Dictionary for converting full trail names to column numbers
counterDict = {"Burke Gilman Trail":0,
               "Broad": 1,
               "Elliot": 2,
               "Fremont Bridge": 3,
               "MTS Trail": 4,
               "NW 58th St": 5,
               "2nd Ave": 6,
               "Spokane St": 7,
               "39th Ave": 8,
               "26th Ave": 9}


Indx = [] # Index to hold dates
for i in range(len(predictorsDF)): 
    # Convert strings containing dates (eg '2012-10-03') to date objects
    Indx.append(datetime.strptime(predictorsDF.index[i], '%Y-%m-%d').date())
predictorsDF.index = Indx

def CreateModels():
# Create a list of Prophet forecasts, one series for each counter
    Models = []
    
    for i in range(11):
        # Start dataframe at each counter with first date counter was active.
        # All counters except Fremont and Second began on 1/1/2014
        if predictorsDF.columns[i] == 'Fremont': k = 0 # 10/3/2012
        elif (predictorsDF.columns[i] == 'Second') | (predictorsDF.columns[i] == 'Total') : 
            k = 820 # 1/1/2015
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

def CreatePickleModels():
    Models = CreateModels()
    for i in range(11):
        filename = 'Models' + str(i) + '.pkl'
        with open(filename, 'wb') as output:
            pickle.dump(Models[i], output, pickle.HIGHEST_PROTOCOL)
    return 

def LoadPickleModels():
    Models = []
    for i in range(11): 
        filename = 'Models' + str(i) + '.pkl'
        with open(filename, 'rb') as input:
            Models.append(pickle.load(input))
            
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
    pd.options.display.float_format = '{:,.0f}'.format
    
    #ForecastTable.columns = counterNames
    ForecastTable[ForecastTable < 0 ] = 0
    return ForecastTable, Forecasts

def PlotTrendAnalysis(Models, counterNumber = 10):
    # Plots the historical trends as detected by the model
    
    if counterNumber == 3: k = 0 # Fremont, started 10/3/2012
    elif (counterNumber == 6) | (counterNumber == 10): k = 820 # Second St, started 1/1/2015
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

def PlotHistoricalModel(Models, counterNumber = 10):
    # Plots the model against past data
    
    if counterNumber == 3: k = 0 # Fremont, started 10/3/2012
    elif (counterNumber == 6) | (counterNumber == 10): k = 820 # Second St, started 1/1/2015
    else: k = 455    # All others, started 1/1/2014
    
    future = pd.DataFrame({'TempHi': predictorsDF["TempHi"][k:],
                      'logPrecip': predictorsDF["logPrecip"][k:],
                      'ds': predictorsDF.index[k:],
                      'floor': 0,
                      'cap': max(predictorsDF.iloc[k:, counterNumber][k:])},
                     index = predictorsDF.index[k:])
    
    forecast = Models[counterNumber].predict(future)
    Models[counterNumber].plot(forecast)
    
    return


def PlotCounterForecast(CounterNumber, ForecastTable):
    objects = []
    for i in range(ForecastTable.shape[0]): 
        objects.append(WeekdayNames[ForecastTable.index[i].weekday()])
    objects 
    #objects = ('Python', 'C++', 'Java', 'Perl', 'Scala', 'Lisp')
    y_pos = np.arange(len(objects))
    performance = ForecastTable.iloc[:, CounterNumber]

    plt.bar(y_pos, performance, align='center', alpha=0.5)
    plt.xticks(y_pos, objects)
    plt.ylabel('Bicycle Count')
    plt.title('Seven Day Forecast of Counter ' + ForecastTable.columns[CounterNumber])

    plt.show()
    
def PlotSecularTrend(Models, counterNumber):
    if counterNumber == 3: k = 0 # Fremont, started 10/3/2012
    elif (counterNumber == 6) | (counterNumber == 10): k = 820 # Second St, started 1/1/2015
    else: k = 455    # All others, started 1/1/2014
    
    future = pd.DataFrame({'TempHi': predictorsDF["TempHi"][k:],
                      'logPrecip': predictorsDF["logPrecip"][k:],
                      'ds': predictorsDF.index[k:],
                      'floor': 0,
                      'cap': max(predictorsDF.iloc[k:, counterNumber][k:])},
                     index = predictorsDF.index[k:])
    
    forecast = Models[counterNumber].predict(future)
    
    # Calculate Rate of Change for the last 365 days
    GrowthRate = 1000*(forecast.trend[-1:].values/forecast.trend[-365:-364].values) - 1000
    GrowthRate = int(GrowthRate)/10
    
    
    sns.set_style("darkgrid")
    sns.set(font_scale = 1.5)
    plt.plot_date(forecast.ds, forecast.trend)
    plt.suptitle(counterNames[counterNumber] + " Counter: " 
                  + str(GrowthRate) + "% Trailing Annual Growth Rate")
    plt.show()
    return


def plotForecast(ForecastTable, counterNumber): 
    
    dayNames = []
    for i in range(ForecastTable.shape[0]): 
        dayNames.append(WeekdayNames[ForecastTable.index[i].weekday()])

    output_file("ForecastBarPlot.html")


    p = figure(plot_width=600, plot_height=400, 
               title = "7 Day Bicycle Count Forecast for " + counterNames[counterNumber])
    p.vbar(x=[0,1,2,3,4,5,6], width=0.5, bottom=0,
       top=ForecastTable.iloc[:, counterNumber], color="DeepSkyBlue")
    
    label_dict = {}
    for i, s in enumerate(dayNames):
        label_dict[i] = s

    p.xaxis.formatter = FuncTickFormatter(code="""
        var labels = %s;
        return labels[tick];
    """ % label_dict)

    #show(p)
    
    return p



Models = LoadPickleModels()
ForecastTable, Forecasts = GetForecastTable(Models, days = 7)



# Set up data
x =  [0,1,2,3,4,5,6]
top = ForecastTable.iloc[:, 3]
source = ColumnDataSource(data=dict(x=x, top=top))

def plotBokeh(ymax = 800):
    
    dayNames = []
    for i in range(ForecastTable.shape[0]): 
        dayNames.append(WeekdayNames[ForecastTable.index[i].weekday()])

    p = figure(plot_width=600, plot_height=400, 
               title = "7 Day Bicycle Count Forecast")
    glyph = VBar(x="x", top = "top", width=0.5, bottom=0,
                 fill_color="DeepSkyBlue")
    
    p.add_glyph(source, glyph)
    
    label_dict = {}
    for i, s in enumerate(dayNames):
        label_dict[i] = s

    p.xaxis.formatter = FuncTickFormatter(code="""
        var labels = %s;
        return labels[tick];
    """ % label_dict)
    
    return p

plot = plotBokeh()

# Widgets section

# Drop down for selecting viewing a typical week or typical day

CounterDropdown = Select(title = "Select Counter", value = "Fremont Bridge", 
                             options = counterNames)

# Set up callbacks
def update_data(attrname, old, new):

    # Get the current slider values
    counter = counterDict[CounterDropdown.value]
    x =  [0,1,2,3,4,5,6] 
    
    top = ForecastTable.iloc[:, counter].astype(float)
   
    source.data = dict(x=x, top=top)
    
for w in [CounterDropdown]:
    w.on_change('value', update_data)

# Set up layouts and add to document
inputs = widgetbox(CounterDropdown)


lay = layout([
        [inputs], 
        [plot]
        ])#, sizing_mode = 'fixed')
#curdoc().add_root(row(inputs, plot, width=800))
curdoc().add_root(lay)    
curdoc().title = "7 Day Forecast"