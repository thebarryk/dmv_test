#!/usr/bin/env python
# coding: utf-8

# In[10]:


# Show variation of success vs time spent taking the driver's test.
# Add compar duration and elapsed time
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
    pf = []
    for lim in limits:
        np = df[(df[field]>=lim[0]) & (df[field]<lim[1]) & (df.Result=="P")][field].count()
        nf = df[(df[field]>=lim[0]) & (df[field]<lim[1]) & (df.Result!="P")][field].count()
        duration = 0.5*(lim[0] + lim[1])
        try:
            rate = float(np)/( float(np) + float(nf) )
        except:
            rate = 0
        pf.append( (duration, rate) )
    return pd.DataFrame({
        field : [x[0] for x in pf],
        "rate": [x[1] for x in pf]
    })

def duration_intervals(lo=5., hi=100., inc=5.):
    r = np.arange(lo, hi+0.01*(hi-lo)/inc, inc)
    return [ (r[i], r[i+1]) for i in range(len(r)-1) ] 

def plot_passing_rate(df, field):
    fig, ax = plt.subplots(figsize=(10, 5))
    
    plt.plot(df[field], df.rate, "o", label=field)
    
    mplcursors.cursor(hover=True)
    ax.set_title(f"Passing Rate vs {field} (min)")
    ax.set_xlabel(f"{field} (min)")
    ax.set_ylabel(f"Passing Rate")
    ax.legend()
    plt.grid(visible=True)
    plt.show() 

def main():
#     df, risk = dmv_test_input.dmv_risk_input()
    df = dti.read_dmv_log(case=1)
    df["elapsed"] = abs(df['TestEndDateTime'] - df['TestStartDateTime']).dt.total_seconds()/60.

    limits = duration_intervals(lo=5, hi=40., inc=1)
    pf = passing_rate(df, "elapsed", limits)

    plot_passing_rate(pf, "elapsed")
    return df, pf

if __name__ == '__main__':
    df, pf = main()


# In[8]:


for k,v in pf.items():
    print(k,v)


# In[ ]:




