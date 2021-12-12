import sys
import pandas as pd
import numpy as np
import ipaddress
import dbm
import pickle
from sortedcontainers import SortedDict
import requests
from bs4 import BeautifulSoup
import json
import os
import traceback
from datetime import datetime
import pprint


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
    # Remove special UTF-8 character \U200b, a zero width space.
    result["risk_comment"] = soup.find_all("div", class_="panel_body")[0].get_text().replace("\u200b","")
#     result["risk_comment"] = ""
    
    return result

def parse_arin(html_text, ip_string):
    # Values that are not found are set to np.NaN
    
    fillna = lambda x: np.nan if x is None else x if isinstance(x, str) else x.string
    
    def get_streetaddress(cust):
        # More than one address line may be recorded
        tag = cust.streetaddress
        if tag is None:
            return np.nan
        address = []
        for line in tag:
            address.append(line.string)
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
        if tag is None:
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
        return datetime.now()
    def get_cidr(netw, info):
        tag = netw.netblocks
        if tag is None:
            return None
        r = {}
        for netblock in tag:
            cidr_prefix = fillna(netblock.startaddress)
            cidr_length = fillna(netblock.cidrlength)
            if (cidr_prefix is None) or (cidr_length is None):
                continue
            cidr = cidr_prefix + "/" + cidr_length
            info["cidr"] = cidr 
            r[cidr] = info
        return r if len(r)>0 else None

    # Parse html into a hierarchy using BeautifulSoup 
    soup = BeautifulSoup(html_text, 'lxml')

    # ARIN reports a list of CIDR net_addresses. 
    # The database will be indexed by ipaddress.net_address.
    # A record will be written for each cidr and duplicate the ARIN info
    # Obtain the organization name from tag=net instead of the tag=org which
    # has more than one tag=name making it harder to isolate.
    try:
        info = {}

        # Check to see if tag=customer is available, otherwise use tag.org
        
        cust = soup.customer if soup.org is None else soup.org
        netw = soup.net

        info["address"] = get_streetaddress(cust)
        info["postalcode"] = get_postalcode(cust)
        info["state"] = get_state(cust)
        info["country"] = get_country(cust)
        info["countrycode"] = get_countrycode(cust)
        info["organization"] = get_organization(cust, info)
        info["city"] = get_city(cust)
        info["handle"] = get_handle(cust)
        info["timestamp"] = get_timestamp()

#         import pdb; pdb.set_trace()

        # Add the risk obtained from scamalytics
        info.update(get_risk(ip_string))
    
        # Parse into dict to return results, item by item
        result = get_cidr(netw, info)

        return result
    
    except:
        debug.prt(f"Error in parse_arin({ip_string=}")
        return None


def get_arin(ip_string):
    '''Return dict for the net_address that contains this ip_string
        {"cidr": ?,
         {"organization": ? ,
          "handle": ? ,
          "city": ? ,
          "address" : ? ,
          "postalcode": ? ,
          "countrycode": ? ,
          "state": ? ,
          "country": ? ,
          "timestamp": ?,
          cidr,
         }
    '''

    # Fetch the complete record from arin restful api
    # Ref: https://www.arin.net/resources/registry/whois/rws/api/#networks-and-asns
    # ip_string ... make request by ip address as a string
    # pft ......... get full record
    
    url = "http://whois.arin.net/rest/ip/" + ip_string + "/pft"
    html_text = ""
    try:
        html_text = requests.get(url).text
    except:
        return None
    return parse_arin(html_text, ip_string)


class Risk():
    
    def __init__(self, filename, readonly=True):

        # Open database. Create as needed.
        
        self.readonly = readonly
        self.open_option = f'{"r" if self.readonly else "w"}'
        self.db_filename = filename
        self.hp = pickle.HIGHEST_PROTOCOL
         
        try:
            self.db = dbm.open(self.db_filename, self.open_option)
        except:
            if self.readonly:
                print(f"{self.db_filename} does not exist but will not be created when class is {readonly=}")
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

        
    def find(self, ip_string):
        """ 
        risk[cidr] = {organization, handle, city, address, postalcode, countrycode, state, ...}
        not readony  ... create one if needed and add it to the database.
        Return:
        - None ........ when Risk.ip is None
                        when Risk.ip and not Risk.findarin then Risk.findarin was found 
                        at ARIN site but could be added to db
        - ARIN dict ... Risk.ip and Risk.searchresult (==Risk.ip)
                        or Risk.ip and Risk.findarin and Risk.addarin (==Risk.findarin)
        """

#         import pdb; pdb.set_trace()
        
        try: 
            self.ip = ipaddress.ip_address(ip_string)
        except:
            self.ip = None
            debug.prt(f"Risk.find: Could not find IPv4Address for {ip_string=}")
            return None
        
        # Find the address to insert
        self.searchresult = None
        self.findarin = None
        self.addarin = None
        
        # Try to find in the existing database
        
        self.searchresult = self.cidr_search(self.ip)

        # Not found:
        if self.searchresult:
            return self.searchresult
        
        # Return None when readonly
        elif self.readonly:
            return None
            
        # Fetch arin and risk info and try to add into the database. Return None if it cannnot
        else:
            self.findarin = get_arin(ip_string)
            if self.findarin is None:
                debug.prt(f"Risk.Find: No arin results for {ip_string=}\n")
                return None
            self.addarin = self.add(self.findarin)
            if self.addarin is None:
                debug.prt(f"Risk.find: ARIN results could not be added for {ip_string=}\n")
                return None
            return self.addarin
    

    def add(self, new_risks):
        '''
        Add the result of get_arin, a dict with cidr as key 
        to both the Risk.risk dict and the database.
        Return:
        False ... No risks to add.
                 A risk value could not be pickle'd
        True ... Risks added successfully
        '''
#         import pdb; pdb.set_trace()
               
        # Store in dictionary first.
        # There may be more than one cidr retrieved by get_arin
        # Each CIDR has to be type ip_network

        for new_cidr, new_risk in new_risks.items():
            netblock = ipaddress.ip_network(new_cidr)
            self.risk[netblock] = new_risk
        
            # Store in database next
            
            # Collect the pickle's of the netblock and risk
            additions = []

            # key and value have to be pickle'd before storing
            try:
                pickled_netblock = pickle.dumps(netblock, protocol=self.hp)
                # This is a hack that allows pickle to work 
                new_risk_temp = f"{new_risk}"
                pickled_risk = pickle.dumps(new_risk_temp, protocol=self.hp)
                additions.append([pickled_netblock, pickled_risk])
            except BaseException as ex:
                debug.prt(f"Pickle error {ex}: {new_cidr=}\n{new_risk=}\n")
                return False

            # Write into database making sure to close it
            with dbm.open(self.db_filename, self.open_option) as self.db:
                for addition in additions:
                    self.db[addition[0]] = addition[1]

        return True
    

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