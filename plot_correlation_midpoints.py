#!/usr/bin/env python
# coding: utf-8

# In[83]:


get_ipython().run_line_magic('matplotlib', 'notebook')
# Graph pearson coefficient for passing fraction vs turning points.
# Reason: The passing fraction below a turning point increases as the
# time to take the test deceases: reward increases with less effort (?).
# But, after the turning point reward is independent of effort.
# The turning point are a set of durations centered around 18 minutess.

import passing_fraction as pfs
from scipy.stats import pearsonr
import mplcursors
import matplotlib.pyplot as plt
import pandas as pd
import dmv_test_input

def calc_correlation(pf, lo=10, hi=30, inc=2):
    def split_tuple(df, src, new):
        # Split the tuple into 2 new columns.
        # See https://www.codegrepper.com/code-examples/python/pandas+split+column+with+tuple
        df[new] = pd.DataFrame(df[src].tolist(), index=df.index)
        
    cf = pd.DataFrame(np.arange(lo, hi, inc), columns=["midpt"])

    less = lambda x: pf[pf.duration <  x]
    more = lambda x: pf[pf.duration >= x]

    before = lambda x: pearsonr(less(x).duration, less(x).fraction)
    after  = lambda x: pearsonr(more(x).duration, more(x).fraction)

    cf["before"] = cf.midpt.apply(before)
    cf["after"]  = cf.midpt.apply(after)
    
    # pearsonr supplies a tuple (pearson coefficient, p-value) so it needs to be split.
    split_tuple(cf, src="before", new=["before_pearson", "before_pvalue"])
    split_tuple(cf, src="after",  new=["after_pearson",   "after_pvalue"])
    return cf

def plot_correlation_midpoints(df):
    fig, ax = plt.subplots()

    plt.plot(df.midpt, df.before_pearson, "-o")
    plt.plot(df.midpt, df.after_pearson,  "-v")
    
    mplcursors.cursor(hover=True)
    fig.set_size_inches(10, 6)
    fig.subplots_adjust(bottom=.25)
    ax.set_title("Pearson Correlation vs. Turning Point (min)")
    ax.set_xlabel("Turning Point (min)\n(i.e. = Duration)")
    ax.set_ylabel("Pearson Correlation")
    ax.legend(["Before turning point", "After turning point"])
    
    ax.annotate("Score Increases with Less Effort (Strong Correlation)",
                xy = (18, -.959), xycoords='data',
                xytext=(-25, 50), textcoords='offset points',
                arrowprops=dict(width=1, facecolor='black', shrink=0.05),
                horizontalalignment='center', verticalalignment='bottom'
               )
    ax.annotate("Score Independent of Effort (Weak Correlation)",
                xy = (18, .031), xycoords='data',
                xytext=(+25, -50), textcoords='offset points',
                arrowprops=dict(width=1, facecolor='orange', edgecolor="orange", shrink=0.05),
                horizontalalignment='center', verticalalignment='bottom'
               )
    plt.grid(visible=True)
    plt.show()

    
def main():
    df, risk = dmv_test_input.dmv_risk_input()

    limits = pfs.duration_intervals(lo=2.8, hi=40, inc=.5)
    pf = pfs.passing_fraction(df, limits)  

    cf = calc_correlation(pf, lo=10, hi=30, inc=2)
    cf.head()
    plot_correlation_midpoints(cf)
    return df, risk, cf
if __name__ == '__main__':
    df, risk, cf = main()


# In[ ]:




