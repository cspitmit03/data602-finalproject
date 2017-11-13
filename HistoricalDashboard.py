from os.path import dirname, join
from datetime import datetime
import pandas as pd
from bokeh.layouts import row, widgetbox
from bokeh.models import ColumnDataSource, CustomJS, DatetimeTickFormatter, FuncTickFormatter
from bokeh.models.widgets import DateRangeSlider, RangeSlider, Button, DataTable, TableColumn, DateFormatter
from bokeh.io import curdoc
from urllib.request import urlopen
from bokeh.plotting import figure
from bokeh.io import output_file, show


# Get dataframe of historical observations
histPath = "https://raw.githubusercontent.com/cspitmit03/data602-finalproject/master/histDF.csv"
jsPath = "https://raw.githubusercontent.com/cspitmit03/data602-finalproject/master/download.js"

histDF = pd.read_csv(histPath, index_col = 0)

Indx = [] # Index to house dates
for i in range(len(histDF)): 
    Indx.append(datetime.strptime(histDF.index[i], '%m/%d/%Y %H:%M'))
histDF.index = Indx

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

def plotTypicalDay(df): 
    
    # Aggregate data by hour of the day
    df = df.groupby([df.index.hour])[df.columns].mean()
    
    # Create Bokeh figure
    p = figure(plot_width = 800, tools = 'pan, box_zoom', 
               title = "Average Bicycle Count By Hour and Counter")

    # Create a list of x values (the hour), and the average count at that hour
    # for each counter selected
    #Hours = ["Midnight", "","","", "","","6 AM","","8 AM","","10 AM","",    
    #           "Noon", "","2 PM","", "4 PM","","6 PM","","9 PM","","",""]
    xs = []
    ys = []
    for i in range(len(df.columns)):
        ys.append(df.iloc[:,i])
        xs.append(df.index*1000*60*60)
        #xs.append(Hours)
    # Add x and y values to a multiple line graph
    p.multi_line(xs, ys, 
                 color = ['red', 'green', 'blue', 'orange', 'black', 'grey', 
                          'brown','cyan', 'yellow', 'purple'])
    p.xaxis[0].formatter = DatetimeTickFormatter(hours = '%I %p')
    #p.xaxis.formatter = FuncTickFormatter.from_py_func(HourTicker)
    #output_file('TypicalDay.html')
    show(p)
    return

plotTypicalDay(subsetWeekday([6], histDF))




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

HourSlider = RangeSlider(title="Time Range", start=0, end=23, value=(8, 16), step=1, format="0")
HourSlider.on_change('value', lambda attr, old, new: update())

button = Button(label="Download", button_type="success")
button.callback = CustomJS(args=dict(source=source), 
                           code=urlopen(jsPath).read())

controls = widgetbox(HourSlider, button)

curdoc().add_root(row(controls, table))
curdoc().title = "Export CSV"

update()