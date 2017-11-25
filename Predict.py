# -*- coding: utf-8 -*-

import pandas as pd
import matplotlib as plt
import numpy as np
from matplotlib import pyplot

from sklearn import datasets, linear_model
from sklearn.metrics import mean_squared_error, r2_score

# Build a linear model with following variables:
# continuous: precipitation, daylight, week index (week 1 = 0, etc)
# dummy: weekend, fog

# Open dataset with imputed variables
predPath = r"C:\Users\asher\Documents\GitHub\data602-finalproject\predictorsDF.csv"
predictorsDF = pd.read_csv(predPath)

regr = linear_model.LinearRegression()
Sunlight = predictorsDF.Sunlight.values.reshape(-1, 1)
Fremont = predictorsDF.Fremont.values.reshape(-1, 1)
regr.fit(Sunlight, Fremont)

predictions = regr.predict(Sunlight)

# The coefficients
print('Coefficients: \n', regr.coef_)

# The mean squared error
print("Root mean squared error: %.2f"
      % mean_squared_error(Fremont, predictions)**.5)

# Explained variance score: 1 is perfect prediction
print('Variance score: %.2f' % r2_score(Fremont, predictions))

# Plot outputs
pyplot.scatter(Sunlight, Fremont,  color='black')
pyplot.plot(Sunlight, predictions, color='blue', linewidth=3)

plt.xticks(())
plt.yticks(())

plt.show()