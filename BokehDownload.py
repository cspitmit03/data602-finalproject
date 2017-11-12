from os.path import dirname, join
from datetime import datetime
import pandas as pd
from bokeh.layouts import row, widgetbox
from bokeh.models import ColumnDataSource, CustomJS
from bokeh.models.widgets import RangeSlider, Button, DataTable, TableColumn, DateFormatter
from bokeh.io import curdoc
from urllib.request import urlopen

totalPath = "https://raw.githubusercontent.com/cspitmit03/data602-finalproject/master/histDF.csv"
jsPath = "https://raw.githubusercontent.com/cspitmit03/data602-finalproject/master/download.js"
#filepath = r"C:\Users\asher\Documents\GitHub\data602-finalproject"

totalDF = pd.read_csv(totalPath)
totalDF.index = totalDF.Date
Indx = [] # Index to house dates
for i in range(len(totalDF)): 
    Indx.append(datetime.strptime(totalDF.index[i], '%m/%d/%Y %H:%M'))
totalDF.index = Indx
del totalDF["Date"]

source = ColumnDataSource(data=dict())

Years = totalDF.index.to_series().apply(lambda x: x.year)

def update():
    current = totalDF[(Years >= slider.value[0]) & (Years <= slider.value[1])]
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

slider = RangeSlider(title="Year Range", start=2012, end=2017, value=(2012, 2017), step=1, format="0")
slider.on_change('value', lambda attr, old, new: update())

button = Button(label="Download", button_type="success")
button.callback = CustomJS(args=dict(source=source), 
                           code=urlopen(jsPath).read())
columns = [
    TableColumn(field="Date", title="Date", 
                formatter=DateFormatter(format="%Y-%m-%d %H:%M:%S")),
    TableColumn(field="BGT", title="Burke-Gilman"),
    TableColumn(field="Broad", title="Broad"),
    TableColumn(field="Elliot", title="Elliot"),
    TableColumn(field="Fremont", title="Fremont"),
    TableColumn(field="MTS", title="MTS"),
    TableColumn(field="NW58", title="NW58"),
    TableColumn(field="Second", title="Second"),
    TableColumn(field="Thirty", title="Thirty"),
    TableColumn(field="TwoSix", title="Two Six")
    ]


data_table = DataTable(source=source, columns=columns, width=850, height = 530)

controls = widgetbox(slider, button)
table = widgetbox(data_table)

curdoc().add_root(row(controls, table))
curdoc().title = "Export CSV"

update()