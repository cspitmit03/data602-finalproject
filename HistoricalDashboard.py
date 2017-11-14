from os.path import dirname, join
from datetime import datetime, date
import pandas as pd
from bokeh.layouts import row, widgetbox
from bokeh.models import ColumnDataSource,CheckboxButtonGroup, CustomJS, DatetimeTickFormatter, FuncTickFormatter
from bokeh.models.widgets import Select, DateRangeSlider, RangeSlider, Button, DataTable, TableColumn, DateFormatter
from bokeh.io import curdoc
from urllib.request import urlopen
from bokeh.plotting import figure
from bokeh.io import output_file, show
import numpy as np
from PullData import getSunsAndBools

# Colors for plotting Counters
colors = ['red', 'green', 'blue', 'orange', 'black', 'grey', 'brown',
                   'cyan', 'yellow', 'purple']

# Get dataframe of historical observations, weather, and daylight hours
histPath = "https://raw.githubusercontent.com/cspitmit03/data602-finalproject/master/histDF.csv"
weatherPath = "https://raw.githubusercontent.com/cspitmit03/data602-finalproject/master/weatherDF.csv"
daylightPath = "https://raw.githubusercontent.com/cspitmit03/data602-finalproject/master/daylightDF.csv"
jsPath = "https://raw.githubusercontent.com/cspitmit03/data602-finalproject/master/download.js"

histDF = pd.read_csv(histPath, index_col = 0) # From Seattle Data Portal
weatherDF = pd.read_csv(weatherPath, index_col = 0) # From WeatherUnderground
daylightDF = pd.read_csv(daylightPath, index_col = 0) # From jakevdp formula

# Set indices of hist and weather as datetime & date objects, respectively
Indx = [] # Index to house dates
for i in range(len(histDF)): 
    Indx.append(datetime.strptime(histDF.index[i], '%m/%d/%Y %H:%M'))
histDF.index = Indx

Indx = [] # Index to house dates
for i in range(len(weatherDF)): 
    Indx.append(datetime.strptime(weatherDF.index[i], '%Y-%m-%d').date())
weatherDF.index = Indx

Indx = [] # Index to house dates
for i in range(len(daylightDF)): 
    Indx.append(datetime.strptime(daylightDF.index[i], '%Y-%m-%d').date())
daylightDF.index = Indx

MyTools = "pan,wheel_zoom,box_zoom,reset,undo,save"

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

def subsetWeekday(daylist, df):
    # Return dataframe containing only the days of the week specified,
    # where 0 = Monday, 1 = Tuesday, etc.
    return df[df.index.weekday.isin(daylist)]

def subsetMonth(monthList, df):
    # Return dataframe containing only the days of the week specified,
    # where 0 = Monday, 1 = Tuesday, etc.
    return df[df.index.month.isin(monthList)]

def subsetRain(low = 0, high = 3, wdf = weatherDF, df = histDF):
    # Subset histDF by specified rain volume, inches per day
    
    dfDates = pd.Series(df.index.date) # All dates in dataset
    
    filterDates = [] # List to store dates meeting filters
    
    # Create list of lists of dates satisfying filters
    filterDates = wdf[(wdf.Precip >= low) & 
                      (wdf.Precip <= high)].index 
        
    # Obtain list of booleans indicating whether a date meets the filter criteria
    filterBools = list(dfDates.isin(filterDates))
    
    # Return dataframe containing only the dates that meet the filter criteria    
    return df[filterBools]

def subsetWeather(weatherList, wdf = weatherDF, df = histDF):
    # Return dataframe containing only dates where the specified weather events
    # occurred. Eg, subsetWeather(["Rain", "Snow"]) returns all counts from days
    # on which it rained or snowed. If no events, string should be "None"
    # 
    # Note, if there were also fog on a given day, 
    # that date would show up in the returned dataframe.
    
    # Set weather Events field null values to empty strings
    wdf.Events = wdf.Events.replace(np.nan, 'None', regex=True)
    
    # Dates with the specified weather conditions
    dfDates = pd.Series(df.index.date) # All dates in dataset
    
    filterDates = [] # List to store dates meeting filters
    
    # Create list of lists of dates satisfying filters
    for event in weatherList:
        filterDates.append(wdf.index[wdf['Events'].str.contains(event)])
    
    # Convert list of lists into flat list
    filterDates = [item for sublist in filterDates for item in sublist]
    
    # Sort dates list
    filterDates.sort()    
        
    # Obtain list of booleans indicating whether a date meets the filter criteria
    filterBools = list(dfDates.isin(filterDates))
    
    # Create new dataframe containing only the dates that meet the filter criteria
    filterDF = df[filterBools]
    
    return filterDF

def subsetDaylight(df = histDF, ddf = daylightDF, low=8, high=16):
    # Function for filtering dataset by hours of sunlight for each date
    
    # Create list of dates that meet filter criteria
    filterDates = ddf[(ddf.daylightHours >= low) & 
                      (ddf.daylightHours <= high)].index
    
    dfDates = pd.Series(df.index.date) # All dates in dataset
     
    # Obtain list of booleans indicating whether a date meets the filter criteria
    filterBools = list(dfDates.isin(filterDates))

    # Return dataframe containing only the dates that meet the filter criteria    
    return df[filterBools] 

def plotTypicalDay(df = histDF): 
    
    # Aggregate data by hour of the day
    df = df.groupby([df.index.hour])[df.columns].mean()
    
    # Create x-axis values from index which contains hours
    xs = df.index*1000*60*60 # Convert milliseconds to hours
        
    p = figure(plot_width = 800, tools = MyTools, 
               title = "Average Bicycle Count By Hour for One Day")
    for i in range(len(df.columns)):
        p.line(xs, df.iloc[:,i], color= colors[i], legend= df.columns[i])
        p.xaxis[0].formatter = DatetimeTickFormatter(hours = '%a %-I %p')
    
    show(p)
    return

def plotTypicalWeek(df = histDF): 
    # Plots average count by hour and day of week
    
    # Aggregate data by day of the week and hour
    df = df.groupby([df.index.weekday, df.index.hour])[df.columns].mean()

    # Create x-axis values from index which contains hours
    #xs = pd.Series(range(len(df)))*1000*60*60 # Convert milliseconds to hours
    xs = (np.array(range(len(df))) + 4*24)*1000*60*60
    p = figure(plot_width = 800, tools = MyTools, 
               title = "Average Bicycle Count By Hour, for One Week")
    for i in range(len(df.columns)):
        p.line(xs, df.iloc[:,i], color= colors[i], legend= df.columns[i])
        p.xaxis[0].formatter = DatetimeTickFormatter(hours = '%a %-I %p',
                                                     days = '%a')
    
    show(p)
    return

def plotTypicalYear(df = histDF):
    # Plots average count of one full typical year

    # Aggregate data by day of the week and hour
    df = df.groupby([df.index.week])[df.columns].mean()

    # Create x-axis values from index which contains hours
    xs = (df.index - 1) * 1000*60*60*24*7

    p = figure(plot_width = 800, tools = MyTools, 
               title = "Average Bicycle Counts By Week, for One Year")
    for i in range(len(df.columns)):
        p.line(xs, df.iloc[:,i], color= colors[i], legend= df.columns[i])
        p.xaxis[0].formatter = DatetimeTickFormatter(months = '%B')
    show(p)
    return

def plotHistory(df = histDF):
    # Plots entire history
    
    # Downsample into one week segments
    df = df.resample('7d').sum()

    p = figure(plot_width = 800, tools = MyTools, 
               title = "Historical Bicycle Counts By Week")
    for i in range(len(df.columns)):
        p.line(x = df.index,y = df.iloc[:,i], color= colors[i], legend= df.columns[i])
        p.xaxis[0].formatter = DatetimeTickFormatter(months = '%B',
                                                     years = '%Y')
    show(p)
    return


    


'''
def HourTicker():
    return "{:.0f} + {:.2f}".format(tick, tick % 1)
'''

source = ColumnDataSource(data=dict())

def update():
    current = histDF[(Hour >= HourSlider.value[0]) & (Hour <= HourSlider.value[1])]
    source.data = {
        'Date': current.index,
        'BGT': current.BGT,
        'Broad': current.Broad,
        'Elliot': current.Elliot,
        'Fremont': current.Fremont,
        'MTS': current.MTS,
        'NW58': current.NW58,
        'Second': current.Second,
        'Spokane': current.Spokane,
        'Thirty': current.Thirty,
        'TwoSix': current.TwoSix                
    }
    
# Widgets section

HourSlider = RangeSlider(title="Time Range", start=0, end=23, value=(8, 17), step=1, format="0")
HourSlider.on_change('value', lambda attr, old, new: update())

DateSlider = DateRangeSlider(title="Date range", 
                             value=(date(2013, 10, 3), 
                            date(2017, 10, 31)), 
                            start=date(2013, 10, 3), 
                            end=date(2017, 10, 31), 
                            step=1)

# Drop down for selecting viewing a typical week or typical day
ViewDropdown = Select(title = "View by...", value = "Daily",
              options = ["Day", "Week", "Annual", "Historical"])

DaylightSlider = RangeSlider(title = "Hours of Daylight", start = 8, end = 16, 
                             value = (8,16), step = 1, format = "0")

WeekdayBoxes = CheckboxButtonGroup(title = "Days of the Week",
                                   labels = ["Monday", "Tuesday", "Wednesday",
                                              "Thursday", "Friday", "Saturday",
                                              "Sunday"],
                                    active = [0,1])

MonthBoxes = CheckboxButtonGroup(title = "Months",
                                 labels = ["Jan.", "Feb.", "March", "April", 
                                           "May", "June", "July", "Aug.", "Sep.",
                                           "Oct.", "Nov.", "Dec."],
                                    active = [0,1])

WeatherBoxes = CheckboxButtonGroup(title = "Weather Events",
                                   labels = ["None", "Fog", "Rain", "Snow", 
                                             "Thunderstorm"],
                                    active = [0,1])


button = Button(label="Download", button_type="success")
button.callback = CustomJS(args=dict(source=source), 
                           code=urlopen(jsPath).read())

controls = widgetbox(HourSlider, button)

curdoc().add_root(row(controls, table))
curdoc().title = "Export CSV"

update()