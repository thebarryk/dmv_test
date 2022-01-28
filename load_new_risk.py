#!/usr/bin/env python
# coding: utf-8

# In[1]:


# Output ip addresses from splunk search that are not in the risk database

import pandas as pd
import mywhois
import dmv_test_input as dti


# In[10]:


class NewIp():
    def __init__(self, case=2, save=False):
        self.df, self.risk = dti.dmv_risk_input(case=case, save=save)
        self.num_missing = len(self.df.ip[self.df.risk=="Unknown"])
        self.missing_ips = list(set(self.df.ip[self.df.risk=="Unknown"]))
        self.num_unique = len(self.missing_ips)
        self.num_risk = len(self.risk.risk)
        return

def main():
    newip = NewIp()
    
    print(f'Number of ipaddresses not in risk is {newip.num_missing}')
    print(f'Number of unique ip addresses not in risk is {newip.num_unique}')
    print(f'Number of ip addresses currently in risk is {newip.num_risk}')

    msgrate = 2

    count_failed = 0
    count_added  = 0

    print()    # Create a space for the running report
    
    newip.risk.set_readonly(readonly=False)
    for n, ip in enumerate(newip.missing_ips):

        newips = newip.risk.find(ip)

        if newips is None:
            count_failed += 1

        else:
            count_added  += len(newips)
            
            if not count_added%msgrate:
                print(f"{80*' '}", end="\r")
                print(f"Added ip {count_added} {n/newip.num_unique:.0%}", end="\r")

    print(f"\n{count_failed=}")
    print(f"{count_added=}")
    print(f"Risk now has {len(newip.risk.risk)} ips in database")
    print(f"It should be {newip.num_risk + count_added}.")
  
    return newip.df, newip.risk, newip.missing_ips


# In[11]:


ans = input("Have you made a backup of the risk database? (yes/no):  ")
if ans == "yes":
    df, risk, missing_ips = main()
else:
    print("Make sure you do.")


# In[ ]:




