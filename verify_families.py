#!/usr/bin/env python
# coding: utf-8

# When ip addresses are added to the mywhois database there is a process that checks each new cidr for children that may already been in the database. When some are found, the parent is subdivided into a list of cidrs that exclude those addresses. This list is then added to the database.
# 
# In order to check that the calculation is accurate, a dict, risk.families, is made. Its key is the cidr of the original parent. The value stored is a list of 2 lists, children, the list of the children of the original parent, and parents, the list of the subdivided parent that exclude the children.
# 
# After the load program was complete the families object was saved to disk as follows:
# 1. Convert dict to families\[cidr\]={ "children": \[...\], "parents": \[...\]}
# 2. Convert to json
# 3. Write to file 
# 
# ```# Construct a dict, cidrs, from the families dict as strings.
# cidrs={}
# for k,v in newip.risk.families.items():
#     cidrs[str(k)] = {'children': [str(x) for x in v[0]], 
#                      'parents':  [str(x) for x in v[1]]}
# 
# # Change the dict into a json list, cidrout, so it is all plain text
# import json
# cidrout = json.dumps(cidrs)
# 
# # And save it on a file 'families.json'
# with open('families.json', 'w') as ff:
#     ff.write(cidrout)
# ```
# 
# The program reads the saves families, with string objects, and verifies that there are no gaps when the subdivided parent is added to the database. That they are all, when combined with their children, contiguous.Two cidrs are contiguous when the last host of the previous cidr is is 3 less than the first host of the next cidr. The difference is 3 because some of the cidr addresses are not used.

# In[2]:


from ipaddress import *
import json

def read_families(fn='families.json'):
    # read the json 
    with open(fn, 'r') as hi:
        j_families = hi.read()
    families = json.loads(j_families)
    return families

def edges(lst):
    # Find list of tuples (first ip, lastip) of a list of cidrs. 
    # All objects are convert to ip_network
    edges = lambda x: (list(ip_network(x).hosts())[0], list(ip_network(x).hosts())[-1])
    r = []
    for l in lst:
        r.append(edges(l))
    return r

def prt_gaps(parent):
    # Output any gap. s is sorted list of children + subdivided parent
    p = parent
    ns = len(s)
    for i in range(0, ns-1):
        diff = s[i+1][0]==s[i][1]+3
        if not diff:
            print(f'{i=:<12} {str(s[i+1][0]):20} {str(s[i][1]):20} {diff}')

def merge_members(parent):
    # Merge the children and subdivided parents of the original parent
    l1 = parent['children']
    l2 = parent['parents']
    return edges(l1 + l2)


# In[4]:



families = read_families()

print('Be patient it takes time')
n = len(families)
c = 0
for cidr, parent in families.items():
    # Look over all the families. 
    # Provide progress reports to user
    c += 1
    ctr = f'{c} of {n}'
    print(f'{ctr:15} {str(cidr)}')
    
    s = merge_members(parent)
    s = sorted(s, key=lambda x: x[0])
    prt_gaps(s)


# In[ ]:




