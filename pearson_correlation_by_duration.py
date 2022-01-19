#!/usr/bin/env python
# coding: utf-8

# In[1]:


get_ipython().run_line_magic('matplotlib', 'notebook')
import mplcursors
import dmv_test_input
import matplotlib.pyplot as plt
from scipy.stats import pearsonr
import numpy as np

# Pearson_by_limit: Pearson correlations for range of test durations.
# Graphs show that % passing scores is higher when test duration is shorter.
# The pearson correlation is calculated for ranges of test duration decreased
# from full range to just 5 min.
class Pearson_by_limit():
    def duration(self, lo=5., hi=100., inc=5.):
        self.limits = np.arange(lo, hi+0.01*(hi-lo)/inc, inc)
    def __init__(self, df, hi=100., inc=5.):
        self.df = df
        self.duration(lo=self.df.duration.min(), hi=hi, inc=inc)
    def pearson(self, field):
        self.correlation = {}
        for limit in self.limits:
            self.short = self.df[self.df.duration <= limit]
            try:
                self.correlation[limit] = pearsonr(self.short["TotalScore"], self.short[field])[0]
            except:
                self.correlation[limit] = 0
        return self.correlation
    def __repr__(self):
        w = ""
        for lim, v in self.correlation.items():
            w += f"Highest duration: {lim:>6}   pearson_correlation: {v:>8f}\n"
        return w

def plot_pearson(df):
    fig, ax = plt.subplots(figsize=(10, 5))
    plt.plot(df.limits, df.correlation.values(), "o")
    mplcursors.cursor(hover=True)
    ax.set_title("Pearson Coefficient vs Upper Limit of Duration (min)")
    ax.set_xlabel("Maximum Duration (min)")
    ax.set_ylabel("Pearson Coefficient")
    plt.show()

def main():
    df, risk = dmv_test_input.dmv_risk_input()
    pearson = Pearson_by_limit(df, hi=30., inc=0.5)
    correlation = pearson.pearson("duration")
    plot_pearson(pearson)

main()


# In[ ]:




