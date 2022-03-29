#!/usr/bin/env python
# coding: utf-8

# In[1]:


# Repair the format of the timestamp and over write the risk database

import pandas as pd
import xmywhois as mywhois
import ipaddress
import pickle
import dbm


# In[2]:


class Halt():
    # True after mx iterations. Useful to break after a few iterations
    def __init__(self, mx, maxmx=1000):
        self.i = 0
        self.mx = mx
        self.maxmx = maxmx
    def halt(self):
        for i in range(self.maxmx):
            if i >= self.mx:
                self.last = i
                break
            yield False
        self.last = i
        yield True

def main():
    myrisk = mywhois.Risk("mywhois", readonly=False)
    risk = myrisk.risk

    halt1 = Halt(6)
    isdone = halt1.halt()
    
    for cidr, old_risk in risk.items():
#             if next(isdone): break
        risk[cidr]['timestamp'] = old_risk['timestamp'].replace(':', '/', 2)

    if not myrisk.to_riskdb():
        print(f'Failed to output changed risk dict to dbm database.')

    return risk


# In[3]:


risk = main()


# In[ ]:




