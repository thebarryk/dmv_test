#!/usr/bin/env python
# coding: utf-8

# In[1]:


get_ipython().run_line_magic('matplotlib', 'notebook')
# Continue to examine affect of ip address risk on passing rate.
# First, focus on period before Oct 27 when it was [72-80%]
# Second, show other periods
# Third, find the outliers for each week
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import re
import sys
from scipy.stats.mstats import winsorize
import piso                       # Provide methods for intervals

import dmv_test_input as dti      # Local library to read and prep data 


# In[2]:


# Intitalize data and parameters

def read_data():
    # Read and cleanse data from akts log and risk database
    df, risk = dti.dmv_risk_input(case=2, save=False)
    
    # Time in minutes. 
    # elapsed time from start to end of test. Sometimes they are out of order.
    df["elapsed"] = abs(df['TestEndDateTime'] - df['TestStartDateTime']).dt.total_seconds()/60.   
    df["passed"]  = (df.Result=="P")
    
    # Drop negative duration since they must be in error
    # Drop long durations because the chance of error is high
    df = df[ (df.duration>0) & (df.duration<120) & (df.elapsed<120)].reset_index()
       
    return df, risk

df, risk = read_data()

# Drop rows in akts where ip has undefined risk<0. They are probably 10. or 192.. nets
df.drop(df[df.score < 0].index, inplace=True)

CHANGEPT = 14.5                   # The passing rate changes at the changept
RATE = 0.67                       # Passing rate reaches steady value
SBIN, EBIN, INC = (5, 100, 5)     # Define bins for risk score
EPSILON = sys.float_info.epsilon  # Smallest float


# In[3]:


# Generate bins from (SBIN, EBIN, INC) for find passing rate vs risk

# For lookup (see below) to work all intervals have be closed='right' (,]. To include 0 in the 1st
# bin, a value <0 has to be used. -np.inf is one choice. It may be difficult to plot. Another
# choice is import sys; epsilon=sys.float_info.epsilon. Rounding should let plots work.

# bins = pd.IntervalIndex.from_breaks([-np.inf] + list(np.arange(sbin, ebin+inc, inc)))

# Alternative:
bins = pd.IntervalIndex.from_breaks([-EPSILON] + list(np.arange(INC, EBIN+INC, INC)))
print(f'The risk score is binned using {SBIN, EBIN, INC=}\n\n{bins=}')

# Construct dataframe for the risk score rates. It can be used to perform the lookup.
rf = pd.DataFrame({'threshold':bins.left, 'bin': list(range(0,20))}, index=bins)


# In[4]:


# Identify the bin for each event. bin # is calulated from inc. Lower bound is 0.
# epsilon is used so lower edge is not included in interval.
# Factor 100 used after tests to make sure same results were obtained.
fbin = lambda x: int((x-100*EPSILON)/INC)
df['bin'] = df.score.apply(fbin)

# Tried piso intervals. It took too long
# df['bin'] = df.score.apply(lambda x: piso.lookup(rf, x).bin[x])


# In[5]:


def find_rate(df, rf):
    # Count # pass (sum of pass) and # (as len)
    # for each (bin, passed.value)

    dr = df.groupby('bin').passed.agg([sum, len]).rename(columns={'sum':'p', 'len':'t'})

    # Calculate the passing rate in each bin
    dr['f'] = dr.t - dr.p
    frate = lambda x:  np.nan if x.t <= 0 else x.p/x.t
    dr['rate'] = dr.apply(frate, axis=1)

    # Join the bin intervals by bin
    dr = dr.merge(rf, left_on='bin', right_on='bin', how='inner')

    # Cum
    dr['cumpass'] = dr.p.cumsum()
    dr['cumfail'] = dr.f.cumsum()
    dr['cumcount'] = dr.t.cumsum()
    
    return dr

# Focus on a particular range - Place to fiddle 

# Drop data after 10/26. This marks the rate apex at 80%. From then
# on it dropped to 62%.
#     df = df[ df.TestStartDateTime <= '10/26/2021' ].reset_index()

# Focus on week following change on 10/26/2021
lo = '11/24/2021'
hi = '11/30/2021'
lotest = df.TestStartDateTime >= lo
hitest =  df.TestStartDateTime <= hi
df1 = df[ (lotest) & (hitest)  ].reset_index()

dr = find_rate(df1, rf)


# In[6]:


# Plot the cumulative tests as score increases

def plot_cum_vs_risk_score(dr):
    fig, ax = plt.subplots(figsize=(8, 4))
    plt.stackplot(dr.threshold, dr.cumpass, dr.cumfail, step='pre', labels=['Pass', 'Fail'], alpha=.4, edgecolor='black')
    ax.set_title(f'Stacked Cumulative Tests vs Risk Score Before 10/27/2021')
    ax.set_xlabel(f'Internet Risk Score for IP')
    ax.set_ylabel(f'Cumulative # of Tests')
    ax.grid(visible=True)
    ax.legend()
    plt.show()

plot_cum_vs_risk_score(dr)    


# In[7]:



def plot_rate_vs_risk_score(dr, lo, hi):   
    # winsorize
    pct = .1
    dw = winsorize(dr.rate, limits=([pct, pct]))
    
    fig, ax = plt.subplots(figsize=(8, 4))

    plt.plot(dr.threshold, dr.rate, drawstyle='steps', alpha=1, label='Rate', color='teal')
    # Jostle the winsorized line a little to right and below so it shows
    plt.plot(dr.threshold+.5, dw-.005, drawstyle='steps', ls='--', 
             label=f'Winsorized at {1-pct:.0%}', alpha=1, color='tab:red')
    ax.set_title(f'Passing Rate vs Risk Score [{lo}, {hi}]')
    ax.set_xlabel(f'Internet Risk Score for IP')
    ax.set_ylabel(f'Passing Rate')
    ax.legend()
    ax.grid(visible=True)
    plt.show()
    
plot_rate_vs_risk_score(dr, lo, hi)


# In[8]:


def find_outliers(df, rate=RATE):
    # Find number of outliers per week. Return dataframe, dr

    df['n'] = True                                                 # use to count # tests
    grouped_by_week = df.resample('W',on='TestStartDateTime')      # Group data by week

    # Sum grouped fields by week
    dr = grouped_by_week.sum().reset_index()

    # Find the rate each week 
    dr['rate'] = dr['passed'] / dr['n']
    dr['failed'] = dr['n'] - dr['passed']

    dr['wkly_adjusted'] = dr.failed*dr.rate/(1-dr.rate)    # This week's num pass excl. outliers
    dr['adjusted'] = dr.failed*rate/(1-rate)               # Same but based on longterm rate
#     dr['outlier'] = dr.passed - dr.adjusted              # Num people who exceed 88% of others
    frate = lambda x: max(0, x.passed-x.adjusted)
    dr['outlier'] = dr.passed - dr.adjusted                # Num people who exceed 88% of others
    dr.outlier = dr.outlier.apply(lambda x: max(0,x))      # Some are < 0 because of fluctuations
    
    # Cum
    dr['cumadjusted'] = dr.adjusted.cumsum()               # Number without outliers
    dr['cumoutlier'] = dr.outlier.cumsum()                 # Num outliers
    dr['cumpassed'] = dr.passed.cumsum()                   # Num who passed
    dr['cumfailed'] = dr.failed.cumsum()                   # Num who failed
    
    return dr


# In[9]:


col = ['TestStartDateTime', 'passed', 'failed', 'n', 'rate'
      , 'wkly_adjusted', 'adjusted', 'outlier']

dr = find_outliers(df)
dr[col]


# In[10]:


def plot_outliers(dr, lo, hi, fw=6, fh=4):
    fig, ax = plt.subplots(figsize=(fw, fh))
    plt.plot(dr.TestStartDateTime, dr['passed'], label='Passed')
    plt.plot(dr.TestStartDateTime, dr.failed, label='Failed')
    plt.plot(dr.TestStartDateTime, dr.adjusted, label='Adjusted')
    plt.plot(dr.TestStartDateTime, dr.outlier, label='Outliers')
#     import mplcursors
#     mplcursors.cursor(hover=True)
    ax.set_title(f'Counts Showing Outliers for [{lo:%m/%d/%y}, {hi:%m/%d/%y}]')
    ax.set_xlabel(f'Test Date by Week')
    ax.set_ylabel(f'Count Per Week')
    ax.legend()
    ax.grid(visible=True)
    ax.legend()
    plt.show()
    
lo1 = df.TestStartDateTime.min()
hi1 = df.TestStartDateTime.max()

plot_outliers(dr, lo1, hi1, fw=8, fh=5)


# In[11]:


# Plot the cumulative tests as score increases

def plot_outliers_cum(dr, hi, lo):
    fig, ax = plt.subplots(figsize=(8, 4))
    plt.stackplot(dr.TestStartDateTime
                  , dr.cumoutlier, dr.cumadjusted
                  , step='pre', alpha=.4, edgecolor='black'
                  , labels=['Outliers', 'Adjusted'])
    plt.plot(dr.TestStartDateTime, dr.cumpassed, label='Passed')
    ax.set_title(f'Stacked Cumulative Outliers by Week for [{lo:%m/%d/%y}, {hi:%m/%d/%y}]')
    ax.set_xlabel(f'Test Date by Week')
    ax.set_ylabel(f'Cumulative Count per Week')
    ax.grid(visible=True)
    ax.legend(loc='upper left')
    plt.show()

plot_outliers_cum(dr, lo1, hi1)  


# In[12]:


dr[dr.TestStartDateTime>'11/07/2021'].outlier.describe()


# In[13]:


col=['TestStartDateTime', 'TotalScore', 'duration', 
     'score', 'passed', 'n', 'rate', 'failed', 'adjusted',
       'outlier', 'cumadjusted', 'cumoutlier', 'cumpassed', 'cumfailed']
dr[col]


# In[14]:


dr[['n', 'outlier', 'passed', 'failed']].sum()


# In[15]:


def outlier_variation(df, mxscore=20, changept=CHANGEPT):
    # Variation of Outliers by duration, risk and countrycode

    def count_outliers(df, condition):
        df2 = df[ df.passed & condition ].reset_index()
        try:
            dr2 = find_outliers(df2)
            return dr2[['passed', 'outlier']].sum()
        except:
            return -1, -1

    conditions = [df.duration<=changept, df.duration>changept, 
                  df.score >= mxscore, df.score < mxscore, 
                  df.passed == True, df.passed == False, 
                  df.countrycode == "US", df.countrycode != "US",
                  ((df.score >= mxscore) | (df.countrycode!="US"))]

    labels = [f'duration<={changept}', f'duration>{changept}', 
              f'score >= {mxscore}', f'score < {mxscore}', 
              'passed == True', 'passed == False', 
              'in "US"', 'not in US', 'Risk or not US']

    for i, a in enumerate(conditions[0:2]):
        print(f'\n{labels[i]:32}outliers')

        for j, b in enumerate(conditions[2:]):
            print(f'--> {labels[j+2]:25}   ', end='')
            condition = a & b
            passed, outlier = count_outliers(df, condition)
            print(f'{outlier:8.0f}')
    return


for ms in [15]:
    outlier_variation(df, mxscore=ms)

