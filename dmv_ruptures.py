#!/usr/bin/env python
# coding: utf-8

# In[1]:


get_ipython().run_line_magic('matplotlib', 'notebook')
# The dmv akts data describes examinees who take driving tests on the dmv web site.
# This study proposes that there is a dependence of the passing rate (score>=40/50) on the
# time it takes the examinee to finish the test (duration). 
# In particular, it looks for a duration where the passing rate changes from independence
# on duration to significant dependence.
# The ruptures package is designed to detect such change points.
# Ref: https://centre-borelli.github.io/ruptures-docs/
#      https://techrando.com/2019/08/14/a-brief-introduction-to-change-point-detection-using-python/

import ruptures as rpt
from ruptures.utils import pairwise

import pandas as pd
import matplotlib.pyplot as plt
import mplcursors
import datetime as dt
import traceback
from itertools import cycle

# private. part of dmv_test
import dmv_test_input as dti    # ToDo: migrate changes to dmv_test_input
from passing_rate import passing_rate, duration_intervals
#---------------------------------------------------------------------------
def find_passing_rate(case=1, field="duration"):
    # Read and prepare the dmv_akts. Case=1 ... sample ... =2 ... akts database

    # Set shortest and longest duration to consider in minutes
    # To reduce effect of wild variation
    min_test_duration = 5
    max_test_duration = 35
    
    df = dti.read_dmv_log(case=case)

    df["elapsed"] = abs(df['TestEndDateTime'] - df['TestStartDateTime']).dt.total_seconds()/60.
    df["passed"]  = (df.Result=="P")

    # Break up the test duration into bins
    bins = duration_intervals(lo=min_test_duration, hi=max_test_duration, inc=.5)
    # Calculate passing_rate during each bin
    pr = passing_rate(df, [field], bins)

    # Return the akts, passing rate and bins so it can be analysed interactively after run
    return df, pr, bins

# RUPTURES PACKAGE

#---------------------------------------------------------------------------
def pelt_changepoint(points):
    # Changepoint detection with the Pelt search method
    model="rbf"
    try:
        algo = rpt.Pelt(model=model).fit(points)
    except Exception as e:
        print(f"Unable to predict for {model=}")
        print("")
        return

    bkps = algo.predict(pen=10)
    return bkps

# pelt_changepoint(points)

#---------------------------------------------------------------------------
def binary_changepoint(points):
    # Changepoint detection with the Binary Segmentation search method
    model = "l2"  
    try:
        algo = rpt.Binseg(model=model).fit(points)
    except Exception as e:
        print(f"Unable to predict for {model=}")
        print("")
        return
    bkps = algo.predict(n_bkps=5)
    return bkps

#---------------------------------------------------------------------------
def window_changepoint(points):
    # Changepoint detection with window-based search method
    model = "l2"  
    try:
        algo = rpt.Window(width=40, model=model).fit(points)
    except Exception as e:
        print(f"Unable to predict for {model=}")
        print("")
        return
    bkps = algo.predict(n_bkps=10)
    return bkps

#---------------------------------------------------------------------------
def dynamic_changepoint(points):
    # Changepoint detection with dynamic programming search method
    model = "l1"  
    try:
        algo = rpt.Dynp(model=model, min_size=3, jump=5).fit(points)
    except Exception as e:
        print(f"Unable to predict for {model=}")
        print(traceback.format_exc())
        print(e)
        return

    my_bkps = algo.predict(n_bkps=4)
    rpt.show.display(points, my_bkps, figsize=(fw, fh))
    plt.subplots_adjust(top=0.95)
    mplcursors.cursor(hover=True)
    plt.title('Change Point Detection: Dynamic Programming Search Method')
    plt.show()

#---------------------------------------------------------------------------
def display(x, y, bkps, median, field="duration", fw=10, fh=5):
    # Colors are for shaded regions
    color = cycle(["#f44174", "#4286f4"])
    alpha = 0.1
    legend_position = "upper right"
    
    fig, ax = plt.subplots(figsize=(fw, fh))
    # Calc changepoints in 
    my_bkps = [x[i-1] for i in bkps]
    # Plot x vs y 
    plt.plot(x, y, "-o",
             color="red",
             label=field+" rate")
    # Shade the areas demarcated by changepoints
    for (start, end), col in zip(pairwise(my_bkps), color):
        plt.axvspan(max(0, start), end, facecolor=col, alpha=alpha)

#     mplcursors.cursor(hover=True)

    plt.xlabel("Duration (m)")
    plt.ylabel("Fraction who passed")
    # Make room for the title and labels
    plt.subplots_adjust(top=0.90)
    plt.subplots_adjust(bottom=0.15)
    plt.subplots_adjust(left=.1)
    
    plt.legend(loc=legend_position)
    
    # Use axes limits to determine offset of text from vertical lines
    (xmin, xmax) = ax.get_xlim()
    (ymin, ymax) = ax.get_ylim()
    dt0 = (-(xmax - xmin)*.02, ymin+(ymax-ymin)*0.5)
    dt1 = (dt0[0], ymin+(ymax-ymin)*0.5)
    
    # Draw annotated line at median
    plt.axvline(x=median, linestyle="dotted")
    plt.text(median+dt0[0], dt0[1], f"{median=:.1f} min", rotation=90)

    # Draw annotated line at 1st changepoint
    changept = my_bkps[0]
    plt.axvline(x=changept, linestyle="dotted")
    plt.text(changept+dt1[0], dt1[1], f"{changept=:.1f} min", rotation=90)

#---------------------------------------------------------------------------

field = "duration"
fieldrate = field + "_rate"

df, pr, bins = find_passing_rate(case=2, field=field)
median = df[field].median()

points = pd.DataFrame(pr[fieldrate], columns=[fieldrate])

# Use the window-based search method and graph
my_bkps = window_changepoint(points)
display(pr.duration, pr[fieldrate], my_bkps, median, field=field)
plt.title('Change Point Detection: Window-Based Search Method')
# plt.show()

# Use the Binary Segmentation search method dnd graph
my_bkps1 = binary_changepoint(points)
display(pr.duration, pr[fieldrate], my_bkps1, median, field=field) 
plt.title("Change Point Detection: Binary Segmentation search")
# plt.show()

# Use the Pelt search method and graph
my_bkps2 = pelt_changepoint(points)
display(pr.duration, pr[fieldrate], my_bkps2, median, field=field) 
plt.title("Change Point Detection: Pelt search method")
plt.show()


# In[ ]:




