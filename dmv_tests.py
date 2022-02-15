#!/usr/bin/env python
# coding: utf-8

# In[1]:


get_ipython().run_line_magic('matplotlib', 'notebook')
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import xdmv_test_input as dti    # ToDo: migrate changes to dmv_test_input

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


# In[12]:


def draw_passfail_duration(x, changept, rate, fw=8, fh=4):
    
    def gfilter(y, sigma=2):
        from scipy.ndimage.filters import gaussian_filter1d
        return x, gaussian_filter1d(y, sigma=sigma)
    
    def smooth(x, y, order=3, num=100):
        from scipy.interpolate import interp1d
        from scipy.interpolate import BSpline
#     smooth = interp1d(p.duration, p.outlier, kind='cubic')
        
#         yfiltered = gfilter(y) 
        smoother = BSpline(x, y, order)
        u = np.linspace(x.min(), x.max(), num)
        v = smoother(u)
        return u, v

    # Find median of all the data
    median = x.duration.median()

    fig, ax = plt.subplots(figsize=(fw, fh))
    
    # Exclude tests that take a long time or have questionable time
    df = x[(x.duration > 0) & (x.duration <= 40) & (x.elapsed > 0) & (x.elapsed < 60)]
    
    # Draw histograms of the tests that pass and fail
    h1 = ax.hist(df[(df.Result!='P')].duration, bins=100, histtype="step", label="Fail")
    h2 = ax.hist(df[(df.Result=='P')].duration, bins=100, histtype="step", label="Pass")
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

    h3 = ax.step(p.duration, p['expected'], label='expected')
    
    u, v = smooth(p.duration, p.outlier, order=2, num=100)
    h4 = ax.plot(u, v, label='outlier')
#     h4 = ax.step(p.duration, p['outlier'], label='outlier')

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


# In[ ]:


# list(zip(h1[1],h1[0],h2[0]))[:5]
p = pd.DataFrame(h1[1][:-1], columns=['duration'])
p['pass'] = h1[0]
p['fail'] = h2[0]
p['cheat'] = p['fail']*2.

def draw_passfail_duration2(x, changept, fw=8, fh=4):

    fig, ax = plt.subplots(figsize=(fw, fh))
    
    # Exclude tests that take a long time or have questionable time
    df = x[(x.duration > 0) & (x.duration <= 40)]
#     print(df)
    h1 = ax.step(df.duration, df['pass'], label='Pass')
    h2 = ax.step(df.duration, df['fail'], label='Pass')
    h3 = ax.step(df.duration, df['cheat'], label='Pass')
#     h1 = ax.plot(df.duration, df.pass, )
# #     h2 = ax.hist(df[(df.Result!='P')].duration, bins=100, histtype="step", label="Fail")

#     ax.axvline(x=changept, color="red", linewidth=4, ls=":", label=f"{changept=} min")
# #     ax.axvline(x=median, color="green", linewidth=4, ls=":", label=f"{median=:.1f} min")

#     ax.set_title(f'DMV - Duration of Passed and Failed Tests')
#     ax.set_xlabel(f'Duration (min)')
#     ax.set_ylabel(f'Passed')
#     ax.grid(True)
#     ax.legend()
#     plt.show
#     return h1
draw_passfail_duration2(p, 12.1, .67, fw=8, fh=4)


# In[ ]:


list(zip(h1[1],h1[0],h2[0]))[:5]


# In[ ]:


p


# In[ ]:





# In[ ]:


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


df[df.passed] - df[~df.passed]


# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:


def displot_duration(df, bw_adjust=0.6):
    # sns.displot(data=df, x='TotalTimeSpent', stat='count', kind='kde', cumulative=False, kde=True, bw_adjust=.25,\
    g1 = sns.displot(data=df, x='TotalTimeSpent', kind='kde', cumulative=False, bw_adjust=bw_adjust,                     hue='result_std', palette='prism', aspect=1.5, height=6,                      fill=True, linewidth=2,                       facet_kws={'sharex':True, 'sharey':True}
                     )
    g1.fig.set_figwidth=(15)
    g1.fig.set_figheight=(5)
    plt.axvline(x=600, color="red", linewidth=4, ls=":", label="5 min")

displot_duration(df)


# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:


g1 = sns.displot(data=df, x='duration', kind='kde', cumulative=False, bw_adjust=bw_adjust,                     hue='result_std', palette='prism', aspect=1.5, height=6,                      fill=True, linewidth=2,                       facet_kws={'sharex':True, 'sharey':True}
                     )


# In[ ]:





# In[ ]:


# Add column ip with the port number from the reported ip address
df["ip"] = df.IPAddress.apply(lambda x: np.nan if pd.isna(x) else x.split(":")[0])  #2x faster


# In[ ]:


# Add column result_std with NaN converted to None
df["result_std"] = df.Result.apply(lambda x: "None" if pd.isna(x) else x)

# alternative
# df.fillna("None")  


# In[ ]:





# In[ ]:


draw_duration(df)


# In[ ]:


draw_duration(df, cum=True)


# In[ ]:


g1 = sns.displot(data=df, x='TotalTimeSpent', stat='count', kind='hist', cumulative=False, kde=True, col='result_std',                  hue='result_std', palette='prism', aspect=1.5, element='step', height=6,                  fill=True, linewidth=2, common_bins=False, common_norm=False,                  facet_kws={'sharex':True, 'sharey':True}
                 
                 )


# In[ ]:


sns.distplot(df[df.result_std == "P"]["TotalTimeSpent"], kind='hist', cumulative=False, kde=True,                  palette='prism', aspect=1.5, hist=False,
                 element='step', height=6, fill=False, linewidth=2, rug=True )
sns.distplot(df[df.result_std == "F"]["TotalTimeSpent"],  kind='hist', cumulative=False, kde=True,                  palette='prism', aspect=1.5, hist=False,
                 element='step', height=6, fill=False, linewidth=2, rug=True )
sns.distplot(df[df.result_std == "None"]["TotalTimeSpent"], kind='hist', cumulative=False, kde=True,                  palette='prism', aspect=1.5, hist=False,
                 element='step', height=6, fill=False, linewidth=2, rug=True )
plt.show()


# In[ ]:


def distplot_duration(df):
    fig = plt.figure(figsize=(15,8))
    ax = plt.axes()

#     sns.distplot(df[df.result_std == "P"]["TotalTimeSpent"],    hist=False, label="Pass")
    sns.distplot(df[(df.result_std == "P") | (df.result_std == "None")]["TotalTimeSpent"],    hist=False, label="Pass")
    sns.distplot(df[df.result_std == "F"]["TotalTimeSpent"],    hist=False, label="Fail")
#     sns.distplot(df[df.result_std == "None"]["TotalTimeSpent"], hist=True, label="None")
    ax.axvline(x=600, color="red", linewidth=4, ls=":", label="5 min")
    ax.set_xlim(left=0)
    plt.legend()
    plt.title("DMV - Time Spent Taking Test (sec)")
    plt.show()
    
distplot_duration(df)


# In[ ]:




