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

# Colors for plotting Counters
colors = ['red', 'green', 'blue', 'orange', 'black', 'grey', 'brown',
                   'cyan', 'yellow', 'purple']

# Get dataframe of historical observations, weather, and daylight hours
#histPath = "https://raw.githubusercontent.com/cspitmit03/data602-finalproject/master/histDF.csv"
#weatherPath = "https://raw.githubusercontent.com/cspitmit03/data602-finalproject/master/weatherDF.csv"
#daylightPath = "https://raw.githubusercontent.com/cspitmit03/data602-finalproject/master/daylightDF.csv"

# Local path for testing
histPath = r"C:\Users\asher\Documents\GitHub\data602-finalproject/histDF.csv"
weatherPath = r"C:\Users\asher\Documents\GitHub\data602-finalproject/weatherDF.csv"
daylightPath = r"C:\Users\asher\Documents\GitHub\data602-finalproject/daylightDF.csv"

#jsPath = "https://raw.githubusercontent.com/cspitmit03/data602-finalproject/master/download.js"

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

def subsetDate(start, end, df):
    # Return dataframe that is within the date bounds specified, in m/D/Y 
    # format
    start = datetime.strptime(start, '%m/%d/%Y').date()
    start = start.strftime('%Y%m%d')
    end = datetime.strptime(end, '%m/%d/%Y').date()
    end = end.strftime('%Y%m%d')
    
    return df[start:end]

def subsetMonth(monthList, df=histDF):
    # Return dataframe containing only the days of the week specified,
    # where 0 = Monday, 1 = Tuesday, etc.
    return df[df.index.month.isin(monthList)]

def subsetWeekday(daylist, df=histDF):
    # Return dataframe containing only the days of the week specified,
    # where 0 = Monday, 1 = Tuesday, etc.
    return df[df.index.weekday.isin(daylist)]

def subsetHours(start, end, df=histDF):
    # Return dataframe within the times specified, in 24 hour format
    # e.g. start = '12:00', end = '13:00'
    start = str(start) + ":00"
    end = str(end) + ":00"
    df = df.between_time(start, end)
    return df

def subsetRain(low = 0, high = 2.5, wdf = weatherDF, df = histDF):
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
    
    # show(p)
    return p

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

def TypicalDay(df = histDF):
    return df.groupby([df.index.hour])[df.columns].mean()

# Set up data
x = list(range(24))
y = histDF.groupby([histDF.index.hour])[histDF.columns].mean().Fremont
source = ColumnDataSource(data=dict(x=x, y=y))

# Set up plot
plot = figure(plot_height=600, plot_width=800, title="Bicycle Counts",
              tools=MyTools,
              x_range=[0, 23], y_range=[0, 600])

plot.line('x', 'y', source=source, line_width=3, line_alpha=0.6)


show(plot)
# Widgets section

# Drop down for selecting viewing a typical week or typical day
ViewDropdown = Select(title = "View by...", value = "Daily",
              options = ["Day", "Week", "Year", "Historical"])

CounterBoxes = CheckboxButtonGroup(labels = list(histDF.columns), active = [0,9])

DateSlider = DateRangeSlider(title="Date range", value=(date(2013, 10, 3), 
                            date(2017, 10, 31)), start=date(2013, 10, 3), 
                            end=date(2017, 10, 31), step=1)

MonthBoxes = CheckboxButtonGroup(labels = ["Jan.", "Feb.", "March", "April", 
                                           "May", "June", "July", "Aug.", "Sep.",
                                           "Oct.", "Nov.", "Dec."], active = [0,11])
WeekdayBoxes = CheckboxButtonGroup(labels = ["Monday", "Tuesday", "Wednesday",
                                              "Thursday", "Friday", "Saturday",
                                              "Sunday"], active = [0,6])
HourSlider = RangeSlider(title="Time Range", start=0, end=23, value=(0, 23), step=1, format="0")

DaylightSlider = RangeSlider(title = "Hours of Daylight", start = 8, end = 16, 
                             value = (8,16), step = 1, format = "0")

WeatherBoxes = CheckboxButtonGroup(labels = ["None", "Fog", "Rain", "Snow", 
                                             "Thunderstorm"], active = [0,4])

RainSlider = RangeSlider(title="Inches of Rain per Day", start = 0, end = 2.5, 
                         value = (0,3), step = 0.05, format = "0.00")

# Set up callbacks
def update_data(attrname, old, new):

    # Get the current slider values
    view = ViewDropdown.value
    counters = CounterBoxes.active
    dates = DateSlider.value
    months = MonthBoxes.active
    weekdays = WeekdayBoxes.active
    hours = np.round(HourSlider.value)
    weather = WeatherBoxes.active
    light = DaylightSlider.value
    rain = RainSlider.value

    # Generate the new dataframe
    mydf = subsetHours(start = hours[0], end = hours[1]) # Hours
    mydf = subsetDaylight(df = mydf, low = light[0], high = light[1])
    
    
    x = range(hours[0],hours[1] + 1)
    y = TypicalDay(mydf).Fremont
    
    # Generate the new curve
    #x = np.linspace(0, 4*np.pi, N)
    #y = a*np.sin(k*x + w) + b

    source.data = dict(x=x, y=y)

for w in [HourSlider, DaylightSlider]:
    w.on_change('value', update_data)


# Set up layouts and add to document
inputs = widgetbox(HourSlider, DaylightSlider)

curdoc().add_root(row(inputs, plot, width=800))
curdoc().title = "Bicycle Counts"

