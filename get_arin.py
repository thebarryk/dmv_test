def get_arin(ip_string):
    '''Return dict for the net_address that contains this ip_string
        {"cidr": ?,
         {"organization": ? ,
          "handle": ? ,
          "asn": ?,
          "city": ? ,
          "address" : ? ,
          "postalcode": ? ,
          "countrycode": ? ,
          "state": ? ,
          "country": ? ,
         }
    '''
    
    fillna = lambda x: "" if not x else x.string if not isinstance(x, str) else x
    
    # Fetch the complete record from arin restful api
    # Ref: https://www.arin.net/resources/registry/whois/rws/api/#networks-and-asns
    # ip ... make request by ip address as a string
    # pft .. get full record
    
    url       = "http://whois.arin.net/rest/ip/" + ip_string + "/pft"
    html_text = ""
    try:
        html_text = requests.get(url).text
    except:
        return None

    # Parse html into a hierarchy using BeautifulSoup 
#     soup = BeautifulSoup(html_text, 'lxml')
    soup = BeautifulSoup(html_text, 'xml')
    
    # Parse into dict to return results, item by item
    result = {}
    
    # ARIN reports a list of CIDR net_addresses. 
    # The database will be indexed by ipaddress.net_address.
    # A record will be written for each cidr and duplicate the ARIN info
    # Obtain the organization name from tag=net instead of the tag=org which
    # has more than one tag=name making it harder to isolate.
    try:
        info = {}
        info["organization"] = fillna(soup.net.orgref["name"])
        info["handle"]       = fillna(soup.net.orgref["handle"])
        info["asn"]          = fillna(soup.net.originas)

        # Obtain rest of the info from tag=org
        info["city"]         = fillna(soup.org.city)

        # More than one address line may be recorded
        address = []
        for line in soup.org.streetaddress:
            address.append(line.string)
        info["address"]      = address

        info["postalcode"]   = fillna(soup.org.postalcode)

        # The iso3166 tags are the internation country codes
        # Ref: https://www.iso.org/glossary-for-iso-3166.html
        # The tags contain "-", illegal characters in a python var name. 
        # Use find_all to locates the tags with a string search.
        for t in soup.org.find_all("iso3166-2"):
            info["state"]    = fillna(t)
        for t in soup.org.find_all("iso3166-1"):
            info["country"]  = fillna(t.find('name'))
            info["countrycode"] = fillna(t.code2)

        # Add the risk obtained from scamalytics
        info.update(get_risk(ip_string))

        # The netblocks scope contains a list of netblock sections
        for netblock in soup.net.netblocks:
            cidr = netblock.startaddress.string + "/" + netblock.cidrlength.string      
            result[cidr] = info
    except:
        print(f"get arin error:")
        return None

    return result