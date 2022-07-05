#!/usr/bin/env python
# coding: utf-8

# In[2]:


'''  Module of functions to grow a db of risks for ip addresses
    - Debug: print debug messages (doesn't belong here)
    - get_risk(ip_string): Fetch risk score from scamalytics api
    - get_arin(ip_string): Fetch arin netblocks and owner
    - parse_arin: utility to parse the result of arin api call
    - class Risk: Find risk from ip_string. Make db to memoize.
      * Makes api's call to find one it and add to db
      
      **** Undergoing additional changes 
      New parent cidr's are added as lists of cidrs that exclude their children.
      The number of cidr's in the database increased by 2698, from 2291 to 4989.
      
      Some of the parents and children may have the same risk score and shouldn't 
      be added. Leaving them out makes searches more efficient for two reasons. 
      First there are fewer to search. Second the network intervals will be larger
      on average and be matched more quickly.
'''


import sys
import pandas as pd
import numpy as np
import ipaddress
import dbm
import pickle
# import dill as pickle
from sortedcontainers import SortedDict
import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import pprint
from unidecode import unidecode
import pdb


class Debug():
    """ Print debug messages if active """
    def __init__(self, set=1):
        self._set = set
    def prt(self, str):
        if self._set:
            sys.stderr.write(str)
    def set(self):
        self._set = 1
    def unset(self):
        self._set = 0
debug = Debug()       

def get_risk(ip_string):
    # Return risk factors from scamalytics into a dict
    #     {"ip": ? , 
    #      "score": ?, 
    #      "risk": ?, 
    #      "risk_comment: ?"}

    # Fetch the complete record from scamalytics restful api
    # ip_string ... make request by ip address as a string

    html_text = ""
    url = "https://scamalytics.com/ip/" + ip_string
    html_text = requests.get(url).text

    soup = BeautifulSoup(html_text, 'lxml')
    
    # Tag=pre
    result = json.loads(soup.pre.string)

    # The comment is in the body of an unlabelled div. Used the css class to find.
    # Cleanup special characters
    temp = soup.find_all("div", class_="panel_body")[0]
    result["risk_comment"] = unidecode( temp.get_text() ).replace("  "," ").replace("  "," ")
    
    return result

def parse_arin(html_text, ip_string):
    # Return dict of info from arin and scamalytics for each 
    # cidr address associated with this ip.
    # Return None when no information can be found
    # Values that are not found are set to np.NaN
    
    fillna = lambda x: np.nan if x is None else f"{x}" if isinstance(x, str) else f"{x.string}"
    
    def get_streetaddress(cust):
        # More than one address line may be recorded
        tag = cust.streetaddress
        if tag is None:
            return np.nan
        address = []
        for line in tag:
            address.append(f"{line.string}")
        return address
    def get_postalcode(cust):
        return fillna(cust.postalcode)
    def get_city(cust):
        return fillna(cust.city)
    def get_handle(cust):
        return fillna(cust.handle)
    def get_state(cust):
        # The iso3166 tags are the international country codes
        # Ref: https://www.iso.org/glossary-for-iso-3166.html
        # BeautifulSoup does not parse tags contain "-" so
        # use find_all to locate the tags with a string search.
        tag = cust.find_all("iso3166-2")
        # When the iso3166-2 is not present, tag = []
        if tag is None or len(tag) == 0:
            return np.nan
        for t in tag:
            result = fillna(t)
        return result
    def get_country(cust):
        tag = cust.find_all("iso3166-1")
        if tag is None:
            return np.nan
        for t in tag:
            r = fillna(t.find('name'))
        return r
    def get_countrycode(cust):
        tag = cust.find_all("iso3166-1")
        for t in tag:
            r = fillna(t.code2)
        return r 
    def get_organization(cust, info):
        # There are 2 tag=name in the tag=cust, one for country and one for organization. 
        # The country is part of iso3166-1 so it can be isolated. Look for organization
        # by looking at both tags and selecting the one that is not equal to country.
        for t in cust.find_all("name"):
            if t.string != info["country"]:
                r = fillna(t)
        return r
    def get_timestamp():
        return datetime.now().strftime("%m:%d:%Y %H:%M:%S")
    def get_cidr(netw):
        # Return a list of cidr's associated with this ip_string
        cidrs = []
        tag = netw.netblocks
        if tag is None:
            return None
        for netblock in tag:
            # Parse the cidr for each netblock
            cidr_prefix = fillna(netblock.startaddress)
            cidr_length = fillna(netblock.cidrlength)
            if (cidr_prefix is None) or (cidr_length is None):
                continue
            cidrs.append(cidr_prefix + "/" + cidr_length)
        return cidrs if len(cidrs)>0 else None

    # ARIN reports a list of CIDR net_addresses. 
    # The database will be indexed by ipaddress.net_address.
    # A record will be written for each cidr and duplicate the ARIN info
    # Obtain the organization name from tag=net instead of the tag=org which
    # has more than one tag=name making it harder to isolate.
    try:
        # Parse html into a hierarchy using BeautifulSoup 
        soup = BeautifulSoup(html_text, 'lxml')
        # Check to see if tag=customer is available, otherwise use tag.org       
        cust = soup.customer if soup.org is None else soup.org

        # Parse into dict info to return results, item by item
        info  = {}
        risks = {}


        netw = soup.net
        cidrs = get_cidr(netw)
        if cidrs is None:
            return None

        # Get the dict risks
        risk = get_risk(ip_string)

        # Append risks to the arin info. It's the same for each cidr.
        info.update(risk)

        info["address"] = get_streetaddress(cust)
        info["postalcode"] = get_postalcode(cust)
        info["state"] = get_state(cust)
        info["country"] = get_country(cust)
        info["countrycode"] = get_countrycode(cust)
        info["organization"] = get_organization(cust, info)
        info["city"] = get_city(cust)
        info["handle"] = get_handle(cust)
        info["timestamp"] = get_timestamp()

        # Return all the cidrs for this ip
        for cidr in cidrs:
            risks[cidr] = info
        return risks
    
    except:
        debug.prt(f"Error in parse_arin({ip_string=}\n")
        return None

def get_arin(ip_string):
    '''Return dict for the net_address that contains this ip_string
        {"cidr": ?, 
            {"organization": ? , "handle": ? ,     "city": ? ,
             "address" : ? ,     "postalcode": ? , "countrycode": ? ,
             "state": ? ,        "country": ? ,    "timestamp": ?, cidr,}
        }
    '''
    # Fetch the complete record from arin restful api
    # Ref: https://www.arin.net/resources/registry/whois/rws/api/#networks-and-asns
    # ip_string ... make request by ip address as a string
    # pft ......... get full record
    
    try:
        url = "http://whois.arin.net/rest/ip/" + ip_string + "/pft"
        html_text = ""
        html_text = requests.get(url).text
    except:
        return None

#     import pdb; pdb.set_trace()

    result = parse_arin(html_text, ip_string)
    return result

class Risk():
    
    def __init__(self, filename, readonly=True):

        # Open database. Create as needed.
        
        self.set_readonly(readonly)
        self.db_filename = filename
        self.hp = pickle.HIGHEST_PROTOCOL
        # Keep dict {parent:[children]}  
        self.families = {}
         
        try:
            self.db = dbm.open(self.db_filename, self.open_option)
        except:
            if self.readonly:
                debug.prt(f"{self.db_filename} does not exist but will not be created when class is {readonly=}\n")
                return None
            else:
                self.db = dbm.open(self.db_filename, "c")
                
        # Read the data into dictionary:
        #   risk[ipaddress.ipv4network] = [organization, country, risk]
        #   
        
        self.risk = SortedDict()
        self.risk_count = 0

        for key in self.db.keys():
            self.risk[pickle.loads(key)] = pickle.loads(self.db[key])

        self.risk_count = len(self.risk)
        self.db.close()
    
    def set_readonly(self, readonly):
        self.readonly = readonly
        self.open_option = f'{"r" if self.readonly else "w"}'

    def find(self, ip_string):
        """ 
        risk[cidr] = {organization, handle, city, ...}
        not readonly... create one if needed and add it to the database.
        Return:
        - None ........ when Risk.ip is None
                        when Risk.ip and not Risk.findarin then Risk.findarin was found 
                        at ARIN site but could be added to db
        - ARIN dict ... Risk.ip and Risk.searchresult (==Risk.ip)
                        or Risk.ip and Risk.findarin and Risk.addarin (==Risk.findarin)
        """
        self.searchresult = None
        self.getarin = None
        self.addarin = None

        # ip_address object is used in database
        try: 
            self.ip = ipaddress.ip_address(ip_string)
        except:
            self.ip = None
            debug.prt(f"Risk.find: Could not find IPv4Address for {ip_string=}\n")
            return None
        
        # Find the cidr in the database
        self.searchresult = self.cidr_search(self.ip)

        # Not found when None:
        if self.searchresult:
            return self.searchresult
        
        # Return None when readonly so database is not changed
        if self.readonly:
            return None
            
        # Fetch arin info. Otherwise return None
        self.getarin = get_arin(ip_string)
        if self.getarin is None:
            debug.prt(f"Risk.Find: No arin results for {ip_string=}\n")
            return None
        
        # Add new value to the dict self.risk. Otherwise return None.
        self.addarin = self.add(self.getarin)
        if self.addarin is None:
            debug.prt(f"Risk.find: ARIN results could not be added for {ip_string=}\n")
            return None
        # 
        return self.addarin
    
    def qfind(self, ip_string):
        # quick find - searches without trying to add to db. 
        # Convenient to use when db is not readonly because new data is not added.
        try: 
            self.ip = ipaddress.ip_address(ip_string)
        except:
            self.ip = None
            debug.prt(f"Risk.find: Could not find IPv4Address for {ip_string=}\n")
            return None
        # Find the cidr in the database
        self.searchresult = self.cidr_search(self.ip)
        return self.searchresult

    def add(self, new_risks):
        '''
        Add the result of get_arin, a dict with cidr as key 
        to both the Risk.risk dict.
        Return:
        False ....... No risks to add.
                      A risk value could not be pickle'd
        new_risks ... Risks that were added successfully
        Note: Use to_riskdb to save any changes
        '''
               
        # Store in dictionary first.
        # There may be more than one cidr retrieved by get_arin
        # Each type(new_cidr) is string, type(new_risk) is dict
        for new_cidr, new_risk in new_risks.items():          
            
            # Subdivide new_cidr into subcidr's that exclude children
            subcidrs = self.exclude_children(ipaddress.ip_network(new_cidr), new_risk)
            
            # Add them, all with the same risk
            for subcidr in subcidrs:
                self.risk[subcidr] = new_risk
            
        return new_risks
                
    def exclude_children(self, parent, parent_risk):
        def new_parents(cs, ps):
            if not cs: return ps
            p = ps.pop()
            try:
                x = p.address_exclude(cs[-1])
                x = list(x)
                return new_parents(cs[0:-1], ps.extend(x))
            except:
                return [p].extend(new_parents(cs, ps))
        
        children = self.find_children(parent, parent_risk)
        parents  = list([parent])       
        np = new_parents(children, parents)
        if len(np) > 1:
            self.families[parent] = (children,np)
        return np

    def find_children(self, parent, parent_risk):
        # Find the children of the ip_network, parent.
        # A child is a subset of a parent.
        children = []
        for potential_child in self.risk:
            # Skip a duplicate
            if potential_child == parent or parent_risk == self.risk[potential_child]['score']:
                continue
            # search_cidr always finds existing parent. To find out
            # whether the ip is part of a child, we would have to 
            # make an expensive lookup in arin. Almost all savings
            # from memoization would be spent.
            if potential_child.subnet_of(parent):
                children.append(potential_child)
        return children
    
    def cidr_search(self, target_ip):
        # risk.cidr_search(target_ip) is is the net_address that contains the target_ip
        # = None when ip's network is not in db
        # type(target_ip) is ipaddress.IPv4Address
        # Updates cidr_search_result property with risk[cidr of target_ip] else None

        s = 0
        e = len(self.risk) - 1
        while s <= e:
            m = (s + e)//2
            cidr = self.risk.peekitem(m)[0]
            if target_ip in cidr:
                self.cidr_search_result = self.risk[cidr]
                return self.cidr_search_result
            if target_ip < cidr[0]:
                e = m - 1
            else:
                s = m + 1
        self.cidr_search_result = None
        return self.cidr_search_result

    def to_riskdb(self):
        # Output dict self.risk to the database
        if self.readonly:
            debug.prt(f'Risk database is readonly. Risk dict will not be outputted.')
            return

        with dbm.open(self.db_filename, self.open_option) as self.db:
            for cidr, risk_info in self.risk.items():
                netblock = ipaddress.ip_network(cidr)
                try:
                    pickled_netblock = pickle.dumps(netblock, protocol=self.hp)
                    pickled_risk     = pickle.dumps(risk_info, protocol=self.hp)

                except BaseException as ex:
                    debug.prt(f"Pickle error {ex}: {cidr=}\n{risk_info=}\n")
                    return False

                self.db[pickled_netblock] = pickled_risk

        return True               
        
