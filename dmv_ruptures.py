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
import traceback
from itertools import cycle
from ruptures.utils import pairwise

from passing_rate import passing_rate, duration_intervals
import pandas as pd
import dmv_test_input
import matplotlib.pyplot as plt
import mplcursors
import datetime as dt
import xdmv_test_input as dti


def main():
    max_test_duration = 60
    # Read and prepare the dmv_akts. Case=1 ... sample ... =2 ... akts database
    df = dti.read_dmv_log(case=1)
    df["elapsed"] = abs(df['TestEndDateTime'] - df['TestStartDateTime']).dt.total_seconds()/60.
    df["passed"]  = (df.Result=="P")

    # Calculate the passing rates before and after a list of duration change points
    limits = duration_intervals(lo=2.8, hi=max_test_duration, inc=.5)
    pr = passing_rate(df, ["duration"], limits)

    # Return the akts and passing rate data so it can be analysed interactively.
    return df, pr, limits

#RUPTURES PACKAGE
#Changepoint detection with the Pelt search method
def pelt_changepoint(points):
    model="rbf"
    try:
        algo = rpt.Pelt(model=model).fit(points)
    except Exception as e:
        print(f"Unable to predict for {model=}")
        print("")

    result = algo.predict(pen=10)

    rpt.display(points, result, figsize=(fw, fh))

    mplcursors.cursor(hover=True)
    plt.title('Change Point Detection: Pelt Search Method')
    plt.xlabel("Duration (m)")
    plt.ylabel("Fraction who passed")
    plt.subplots_adjust(top=0.90)
    plt.subplots_adjust(bottom=0.15)
    plt.subplots_adjust(left=.1)
    plt.show()  

# pelt_changepoint(points)

#Changepoint detection with the Binary Segmentation search method
def binary_changepoint(points):
    model = "l2"  
    algo = rpt.Binseg(model=model).fit(points)
    my_bkps = algo.predict(n_bkps=10)
    # show results
    # rpt.show.display(points, my_bkps, figsize=(fw, fh))
    f_bkps = [ pr.duration.iloc[x-1] for x in my_bkps]
    rpt.show.display(points, f_bkps, figsize=(fw, fh))
    plt.subplots_adjust(top=0.90)
    plt.subplots_adjust(bottom=0.15)
    plt.subplots_adjust(left=.1)
    mplcursors.cursor(hover=True)
    plt.title('Change Point Detection: Binary Segmentation Search Method')
    plt.xlabel("Duration (m)")
    plt.ylabel("Fraction who passed")
    plt.show()

# binary_changepoint(points)


#Changepoint detection with window-based search method
def window_changepoint(points):
    model = "l2"  
    algo = rpt.Window(width=40, model=model).fit(points)
    try:
        bkps = algo.predict(n_bkps=10)
    except Exception as e:
        print(f"Unable to predict for {model=}")
        print("")
        return
    return bkps

#Changepoint detection with dynamic programming search method
def dynamic_changepoint(points):

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

# dynamic_changepoint(points)

def xrdisplay(points, bkps, fw, fh):
    rpt.show.display(points, bkps, figsize=(fw, fh))
    mplcursors.cursor(hover=True)
    plt.title('Change Point Detection: Window-Based Search Method')
    plt.xlabel("Duration (m)")
    plt.ylabel("Fraction who passed")
    plt.subplots_adjust(top=0.90)
    plt.subplots_adjust(bottom=0.15)
    plt.subplots_adjust(left=.1)
    
def rdisplay(x, y, bkps, fw, fh):
    color = cycle(["#4286f4", "#f44174"])
    fig, ax = plt.subplots(figsize=(10, 5))
    my_bkps = [x[i-1] for i in bkps]
    plt.plot(x, y, "-o",
             color="red",
             label="duration_rate")
    for (start, end), col in zip(pairwise(my_bkps), color):
        plt.axvspan(max(0, start - 0.5), end - 0.5, facecolor=col, alpha=0.1)

#     mplcursors.cursor(hover=True)

    plt.title('Change Point Detection: Window-Based Search Method')
    plt.xlabel("Duration (m)")
    plt.ylabel("Fraction who passed")
    plt.subplots_adjust(top=0.90)
    plt.subplots_adjust(bottom=0.15)
    plt.subplots_adjust(left=.1)


# df.duration.median()

if __name__ == '__main__':
    df, pr, limits = main()

points = pd.DataFrame(pr.duration_rate, columns=["duration_rate"])
fw,fh = 6,4
my_bkps = window_changepoint(points)

median = df.duration.median()
rdisplay(pr.duration, pr.duration_rate, my_bkps, fw, fh)
plt.axvline(x=median, linestyle="dotted")
plt.text(median-1.05, .3, f"{median=:.1f} min", rotation=90)
changept = pr.duration[my_bkps[0]-2]
plt.axvline(x=changept, linestyle="dotted")
# plt.axvline(x=pr.duration[my_bkps[0]-2], linestyle="dotted")
plt.text(changept-1.05, .3, f"{changept=:.1f} min", rotation=90)

plt.show()


# In[ ]:




