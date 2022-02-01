#!/usr/bin/env python
# coding: utf-8

# In[9]:


# Show variation of success vs time spent taking the driver's test.
# Add compare duration and elapsed time
# The success rate is averaged over bins of time taken to do the test.
# The bins are calculated by dividing the longest duration by some integer.
# See dmv_test/passing_rate.py

import xdmv_test_input as dti
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import seaborn as sns
import mplcursors

def passing_rate(df, field, limits):
    # passing_rate: DataFrame with columns duration and rate of passed tests 
    # input:
    #    df ...... dmv dataframe with columns duration and Result
    #    limits .. list of (upper, lower) bounds of duration intervals as produced 
    #              by function duration_intervals
    # DataFrame:
    #    duration ... average of the upper and lower bounds of each interval
    #    rate ....... fraction of tests passed over total tests taken during the duration period
    
    def rate(lo, hi, df, field):
        # Calc passing rate inside this interval [lo, hi) of the field
        df["inside"] = (df[field] >= lo) & (df[field] < hi)
        n = df.inside.sum()
        if n == 0:
            return 0   # Should be np.nan so they can be ignored later
        np = ( (df.inside) & (df.passed) ).sum()
        return np/n   
    
    pf = pd.DataFrame( { "lo": [x[0] for x in limits], "hi" : [x[1] for x in limits] } )
    pf["duration"] = 0.5 * (pf.lo + pf.hi)
    pf["rate"] = pf.apply(lambda x: rate(x.lo, x.hi, df, field), axis=1)
    pf["field"] = field
    
    return pf

def duration_intervals(lo=5., hi=100., inc=5.):
    r = np.arange(lo, hi+0.01*(hi-lo)/inc, inc)
    return [ (r[i], r[i+1]) for i in range(len(r)-1) ] 

def plot_passing_rate(pf, field):
    fig, ax = plt.subplots(figsize=(10, 5))
    plt.plot(pf.duration, pf.rate, "o", label=field)
    
    mplcursors.cursor(hover=True)
    ax.set_title(f"Passing Rate vs {field} (min)")
    ax.set_xlabel(f"{field} (min)")
    ax.set_ylabel(f"Passing Rate")
    ax.legend()
    plt.grid(visible=True)
    plt.show() 

def main():

    df = dti.read_dmv_log(case=1)
    df["elapsed"] = abs(df['TestEndDateTime'] - df['TestStartDateTime']).dt.total_seconds()/60.
    df["passed"]  = (df.Result=="P")

    limits = duration_intervals(lo=5, hi=40., inc=1)
    pf = passing_rate(df, "duration", limits)
    
    plot_passing_rate(pf, "duration")
    
    return df, pf

if __name__ == '__main__':
    df, pf = main()


# In[ ]:




