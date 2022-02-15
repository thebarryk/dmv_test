#!/usr/bin/env python
# coding: utf-8

# In[1]:


get_ipython().run_line_magic('matplotlib', 'notebook')
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import dmv_test_input as dti    # ToDo: migrate changes to dmv_test_input

# Used to smooth jagged histgrams
from scipy.interpolate import interp1d
from scipy.interpolate import BSpline
from scipy.ndimage.filters import gaussian_filter

def read_log(case=1, field="duration"):
    # Read and prepare the dmv_akts. Case=1 ... sample ... =2 ... akts database

    df = dti.read_dmv_log(case=case)
    df["elapsed"] = abs(df['TestEndDateTime'] - df['TestStartDateTime']).dt.total_seconds()/60.
    df["passed"]  = (df.Result=="P")
    
    # Drop negative duration since they must be in error
    # Drop long durations because the chance of error is high
    
    df = df[ (df.duration>0) & (df.duration<120) & (df.elapsed<120)].reset_index()
    
    return df

df = read_log(case=2)


# In[2]:


def draw_duration(x, changept, fw=8, fh=4):
    fig, ax = plt.subplots(figsize=(fw, fh))

    h1 = ax.hist(x.duration, bins=100, histtype="step", label="Duration")
    h2 = ax.hist(x.elapsed, bins=100, histtype="step", label="Elapsed")

    duration_median = x.duration.median()
    elapsed_median = x.elapsed.median()
    
    ax.axvline(x=changept, color="red", linewidth=4, ls=":", label=f"{changept} min")
    ax.axvline(x=duration_median, color="green", linewidth=4, ls=":", label=f"{duration_median:.1f} min")
    ax.axvline(x=elapsed_median, color="magenta", linewidth=4, ls=":", label=f"{elapsed_median:.1f} min")

    ax.set_title(f'DMV - Test Time Taken')
    ax.set_xlabel(f'Duration (min)')
    ax.set_ylabel(f'Count')
    ax.grid(True)
    ax.legend()
    plt.show
    return h1, ax


# In[3]:


col = ["ExamineeId", "TotalScore", "duration", "elapsed", "passed"]

h1 = draw_duration(df, 12)


# In[4]:


def draw_passfail_duration(x, changept, rate, fw=8, fh=4):
    
    def gfilter(y, sigma=2):
        # Sooth the jags in histgram with gaussian filter
        return gaussian_filter(y, sigma=sigma)
    
    def smooth(x, y, order=3, num=100):
        # Smooth with a spline interpolation
        yfiltered = gfilter(y)
        smoother = BSpline(x, yfiltered, order)
        u = np.linspace(x.min(), x.max(), num)

        return u, smoother(u)

    # Find median of all the data
    median = x.duration.median()

    fig, ax = plt.subplots(figsize=(fw, fh))
    
    # Exclude tests that take a long time or have questionable time
    # Also minimizes the effect of long tail for short duration tests
    df = x[(x.duration > 0) & (x.duration <= 40) & (x.elapsed > 0) & (x.elapsed < 60)]
    
    # Draw histograms of the tests that pass and fail
    h1 = ax.hist(df[(df.Result!='P')].duration, bins=100, histtype="step", label="Fail")
    h2 = ax.hist(df[(df.Result=='P')].duration, bins=100, histtype="step", label="Pass")
    # Draw x=0 axis
    ax.axhline(y=0, color="gray", linewidth=1)

    # Use the counts calculated by plt.hist to find:
    # expected ... # tests expected to pass based on passing rate for duration > changept
    # outlier  ... # tests that occurred greater than the expected rate of passing
    # 
    p = pd.DataFrame(h2[1][:-1], columns=['duration'])
    p['pass'] = h2[0]
    p['fail'] = h1[0]
    p['expected'] = p['fail']*(rate/(1. - rate))              # passing rate is .67
    p['outlier'] = p['pass'] - p['expected']

    # Sooth the jaggy histograms into a smooth curves
    u, v = smooth(p.duration, p.expected, order=2, num=100)
    h3 = ax.plot(u, v, label='expected')
#     h3 = ax.step(p.duration, p.expected, label='expected')

    u, v = smooth(p.duration, p.outlier, order=2, num=100)
    h4 = ax.plot(u, v, label='outlier')
#     h4 = ax.step(p.duration, p['outlier'], label='outlier')

    # Display the changept and media
    ax.axvline(x=changept, color="red", linewidth=1, ls=":", label=f"{changept=} min")
    ax.axvline(x=median, color="green", linewidth=1, ls=":", label=f"{median=:.1f} min")

    ax.set_title(f'DMV - Duration of Passed and Failed Tests')
    ax.set_xlabel(f'Duration (min)')
    ax.set_ylabel(f'Count')
    ax.grid(False)
    ax.legend()
    plt.show
    return h1, h2

h1, h2 = draw_passfail_duration(df, 12.1, .67, fw=8, fh=7)


# In[8]:


def duration_kde(df, field, vert, fw=8, fh=4):

    sns.set_style("whitegrid")
    g1 = sns.displot(data=df, x=field, hue="passed",
                     kde=True, 
                     palette='prism',
                     height=fh,
                     fill=False,
                     aspect=2)

    median = df[field].median()
    plt.axvline(x=median, color="green", linewidth=4, ls=":", label=f"Median {median:.1f} min")
    plt.axvline(x=vert, color="red", linewidth=4, ls=":", label=f"Changept {vert:.1f} min")

    plt.legend()
    return g1

g1 = duration_kde(df, "duration", 12.1)


# In[ ]:




