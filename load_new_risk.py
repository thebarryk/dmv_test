#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# Output ip addresses from splunk search that are not in the risk database

import pandas as pd
import xmywhois as mywhois
import xdmv_test_input as dti
import ipaddress

class NewIp():
    def __init__(self, db_filename='mywhois', case=2):

        self.db_filename = db_filename
        
        # Open for writing
        self.df, self.risk = dti.dmv_risk_input(self.db_filename, case=case, readonly=False)
        
        # Count # of ip's in log that are unknown
        self.num_missing = len(self.df.ip[self.df.risk=="Unknown"])
        
        # Make a list of the distinct ip's in the log that are unknown. Count then.
        self.missing_ips = list(set(self.df.ip[self.df.risk=="Unknown"]))
        self.num_unique  = len(self.missing_ips)
        
        # Count the # of ip's in the risk database
        self.num_risk    = len(self.risk.risk)
        
        return 

ans = input("Have you made a backup of the risk database? (yes/no):  ")

if not ans == "yes":
    print("Make sure you do.")

else:
    # Work in xmywhois during development to not disturb existing db
    newip = NewIp(db_filename='xmywhois')
    
    print(f'Number of ipaddresses not in risk is {newip.num_missing}')
    print(f'Number of unique ip addresses not in risk is {newip.num_unique}')
    print(f'Number of ip addresses currently in risk is {newip.num_risk}')
          
    msgrate = 2           # Frequency of the progress report
    count_failed = 0
    count_added  = 0

    out = open('load_new_risk.log', 'w')

    print()    # Skip a line to leave space in the running report

    for n, ip in enumerate(newip.missing_ips):

        out.write(f'{n=} {ip=}\n')

        # Skip private addresses
        if ipaddress.ip_address(ip).is_private:
            out.write(f'{ip=} is private so it was skipped')
            continue
            
        newips = newip.risk.find(ip)

        if newips is None:
            count_failed += 1

        else:
            count_added  += len(newips)
            
            if not count_added%msgrate:
                print(f"{80*' '}", end="\r")
                print(f'{n=} Added ip {count_added} {n/newip.num_unique:.0%}', end='\r')

    # Save the results in database
    newip.risk.to_riskdb()
    out.close()
    
    print(f"\n{count_failed=}")
    print(f"{count_added=}")
    print(f"Risk now has {len(newip.risk.risk)} ips in database")
    print(f"It should be {newip.num_risk + count_added}.")
 
    


# In[ ]:


newip.risk.to_riskdb()



# In[ ]:


ipaddress.ip_address('12.87.57.250').is_private


# In[ ]:


f = newip.risk.families


# In[ ]:


def tablist(l, ncol):
    n = len(l)
    for i in range(0, n, ncol):
        line = ''
        for j in range(i, min(i+ncol,n)):
            line += f'{str(l[j]):20}'
        print(line)

from pprint import pprint
for k, v in f.items():
    print(f'\n{k}')
    print(f'# children: {len(v[0])}')
    tablist(v[0], 5)
    print(f'# new parents: {len(v[1])}')
    tablist(v[1], 5)

    


# In[ ]:


# Construct a dict, cidrs, from the families dict as strings.
cidrs={}
for k,v in newip.risk.families.items():
    cidrs[str(k)] = {'children': [str(x) for x in v[0]], 'parents': [str(x) for x in v[1]]}

# Change the dict into a json list, cidrout, so it is all plain text
import json
cidrout = json.dumps(cidrs)


# And save it on a file 'families.json'
with open('families.json', 'w') as ff:
    ff.write(cidrout)


# In[ ]:


from ipaddress import *
def nedges(lst):
    # Find tuples (first ip, lastip) of a list of cidr. 
    # All objects are ip_network
    nedge = lambda x: (list(ip_network(x).hosts())[0], list(ip_network(x).hosts())[-1])
    r = []
    for l in lst:
        r.append(nedge(l))
    return r


# In[ ]:


r = nedges(cidrs['69.112.0.0/12']['parents'])
print(r)


# In[ ]:


sorted(r, key=lambda p: p[0])


# In[ ]:


r1=nedges(cidrs['69.112.0.0/12']['children'])


# In[ ]:


r1


# In[ ]:


R=r + r1


# In[ ]:


r+r1


# In[ ]:


s=sorted(R, key=lambda p: p[0])
s


# In[ ]:


ip_address('69.126.224.1') == (ip_address('69.126.223.254')+3)


# In[ ]:


def prt_gaps(parent):
    # Output any gap. s is sorted list of children + subdivided parent
    p = parent
    ns = len(s)
    for i in range(0, ns-1):
        diff = s[i+1][0]==s[i][1]+3
        if not diff:
            print(f'{i=:<12} {str(s[i+1][0]):20} {str(s[i][1]):20} {diff}')

i=0; imx=len(cidrs)+1

def fff(parent):
#     import pdb; pdb.set_trace()
    l1 = parent['children']
    l2 = parent['parents']
    return nedges(l1 + l2)

for cidr, parent in cidrs.items():
    print(str(cidr))
#     if (i:=i+1)>imx: break
#     s = nedges(parent['children']) + nedges(parent['parents'])
    s = fff(parent)
    s = sorted(s, key=lambda x: x[0])
    prt_gaps(s)
    


# In[ ]:


s


# In[ ]:


i


# In[ ]:




