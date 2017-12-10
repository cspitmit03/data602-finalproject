FROM python:3.5

WORKDIR /usr/src/app/bicycle
ADD . /usr/src/app/bicycle

RUN apt-get update -qq && apt-get upgrade -y && \
   apt-get install -y --no-install-recommends \
       libatlas-base-dev gfortran\
        python-pip
RUN pip install --no-cache-dir pandas && \
    pip install bs4 && \
    pip install numpy && \
    pip install Flask-WTF && \
    pip install matplotlib && \
    pip install requests && \
    pip install pymongo && \
    pip install lxml && \
    pip install emoji && \
    pip install fbprophet && \
    pip install seaborn && \
    pip install bokeh
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 5006
COPY . .
CMD ["bokeh", "serve", "/usr/src/app/bicycle/HistoricalDashboard.py", "/usr/src/app/bicycle/Predict.py"]