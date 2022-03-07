#!/usr/bin/env python
# coding: utf-8

# In[56]:


get_ipython().run_line_magic('matplotlib', 'notebook')
# Show variation of success vs time spent taking the driver's test
# as it changes from week to week, or some other period.
# The passing rate is averaged over bins of time when the test was taken.

import dmv_test_input as dti
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import mplcursors


# In[57]:


# Read test logs from alts database
df = dti.read_dmv_log(case=2)
df["passed"]  = (df.Result=="P")


# In[61]:


def plot_passing_rate(pf):
    linestyle = cycle(["-", "--"])
    color = cycle(["red", "green"])
    fig, ax = plt.subplots(figsize=(8, 4))
    plt.plot(pf.week, 
             pf['rate'],  "o",
             color=next(color),
             linestyle=next(linestyle), 
             label="Passing rate")
    
    ax.set_title(f"Passing Rate by Week")
    ax.set_xlabel(f"Week")
    ax.set_ylabel(f"Passing Rate")
    ax.legend()
    plt.grid(visible=True)
    plt.show() 

def main():
    
    mn, mx = df.TestStartDateTime.agg([min, max])
    weeks = pd.date_range(start=mn, end=mx, freq='W')
    pf = df.resample('W', on='TestStartDateTime').passed.agg([sum,len]).reset_index()
    pf.columns=['week', 'p', 'n']
    pf['rate'] = pf.apply(lambda x: x.p/x.n if x.n != 0 else 0, axis=1)
    
    plot_passing_rate(pf)
    
    return df, pf

if __name__ == '__main__':
    
    df, pf = main()
    pf


# In[55]:


pf.head()


# In[ ]:




