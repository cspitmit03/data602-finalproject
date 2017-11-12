from os.path import dirname, join
from datetime import datetime
import pandas as pd
from bokeh.layouts import row, widgetbox
from bokeh.models import ColumnDataSource, CustomJS
from bokeh.models.widgets import RangeSlider, Button, DataTable, TableColumn, NumberFormatter
from bokeh.io import curdoc

totalPath = "https://raw.githubusercontent.com/cspitmit03/data602-finalproject/master/histDF.csv"
totalDF = pd.read_csv(totalPath)
totalDF.index = totalDF.Date
Indx = [] # Index to house dates
for i in range(len(totalDF)): 
    Indx.append(datetime.strptime(totalDF.index[i], '%m/%d/%Y %H:%M'))
totalDF.index = Indx
del totalDF["Date"]

source = ColumnDataSource(data=dict())

def update():
    current = totalDF[(totalDF.index.year >= slider.value[0]) & (totalDF.index.year <= slider.value[1])].dropna()
    source.data = {
        'Fremont'             : current.Fremont,
    }

slider = RangeSlider(title="Date Range", start=2012, end=2017, value=(2012, 2017), step=1, format="0,0")
slider.on_change('value', lambda attr, old, new: update())

button = Button(label="Download", button_type="success")
button.callback = CustomJS(args=dict(source=source),
                           code=open(join(dirname(__file__), "download.js")).read())

columns = [
    TableColumn(field="Date", title="Date & Time"),
    TableColumn(field="BGT", title="BGT"),
    TableColumn(field="Broad", title="Broad"),
    TableColumn(field="Elliot", title="Elliot"),
    TableColumn(field="Fremont", title="Fremont Counter"),
    TableColumn(field="MTS", title="Fremont Counter"),
    TableColumn(field="NW58", title="Fremont Counter"),
    TableColumn(field="Second", title="Fremont Counter"),
    TableColumn(field="Thirty", title="Fremont Counter"),
    TableColumn(field="Two Six", title="Fremont Counter"),
]

data_table = DataTable(source=source, columns=columns, width=800)

controls = widgetbox(slider, button)
table = widgetbox(data_table)

curdoc().add_root(row(controls, table))
curdoc().title = "Export CSV"

update()