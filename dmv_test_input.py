#!/usr/bin/env python
# coding: utf-8

# In[1]:


# Reads dmv data of different formats and cleanses it
import pandas as pd
import mywhois

#-----------------------------------------------------------------------------

def dmv_risk_input(case=1, save=False):
    # Reads dmv_test test data, preps and adds ip risk.
    # Returns tuple:
    #   df .... dataframe combo of dmv_test data and ip risk
    #   risk .. dict of the risk associated using an ip address

    sample_filename = "/home/bkrawchuk/notebooks/dmv_test/OPT11022021-11042021.csv"

    def fetch_score(ip):
        # Fetch the risk score associated with this ip address
        # Return as float so it can be used numerically
        r = risk.find(ip)
        if r:
            return float(r["score"])
        return -1

    def fetch_risk(ip):
        # Fetch the risk discriptor
        r = risk.find(ip)
        if r:
            return r["risk"]
        return "Unknown"

    def fetch_countrycode(ip):
        # Fetch the risk discriptor
        r = risk.find(ip)
        if r:
            return r["countrycode"]
        return "Unknown"

    # Input dmv test log for the selected case

    df = read_dmv_log(case=case, save=save)

    # Add the risk associated while using the client's ip address
    risk = mywhois.Risk("mywhois", readonly=True)

    vscore = df.loc[:,"ip"].apply(fetch_score).copy()
    vrisk  = df.loc[:,"ip"].apply(fetch_risk).copy()
    vcountrycode = df.loc[:,"ip"].apply(fetch_countrycode).copy()
    df.loc[:,"risk"]  = vrisk
    df.loc[:,"score"] = vscore
    df.loc[:,"countrycode"] = vcountrycode
    return df, risk

#-----------------------------------------------------------------------------

def read_dmv_log(case=1, save=False):
    # Reads dmv_test test data, preps and adds ip risk.
    sample_filename = "/home/bkrawchuk/notebooks/dmv_test/OPT11022021-11042021.csv"
    # Periodically update csv on splunk. Use load_new_risk to update the risk database
#     splunk_filename = "/home/bkrawchuk/notebooks/dmv_test/dmv_akts_2021-10-01_to_2022-01-25.csv"
    splunk_filename = "/home/bkrawchuk/notebooks/dmv_test/dmv_akts_2021-10-01_to_2022-02-17.csv"

    if (case==1):
        # Read the sample data downloaded from the DMV testing web site
        filename = sample_filename
        df1 = pd.read_csv(filename,                           parse_dates=["TestRegistrationDate","TestStartDateTime","TestEndDateTime",                                        "CreateDate", "UpdateDate", "UpdateLogin", "LastAnswerDate",                                        "CancellationDate", "PartnerTransmissionDate", "CreateDate.1",                                        "UpdateDate.1", "LastLoginDate", "LastLockoutDate",                                        "TokenCreateDate", "TokenExpirationDate", "LicExpireDate"])
        df = prep_dmv_sample(df1, save=save)

    else:
        # Read the data downloaded from splunk query
        filename = splunk_filename
        df1 = pd.read_csv(filename, parse_dates=["TestRegistrationDate","TestStartDateTime","TestEndDateTime"])
        df = prep_dmv_splunk(df1, save=save)

    return df

#-----------------------------------------------------------------------------

def prep_dmv_sample(raw_dataframe, save=False, filename="clean_test_data.csv"):
    # Data prep from sample downloaded from web site database

    original_length = len(raw_dataframe)
    print(f"Original length of sample data is {original_length}")

    # Drop data with Result.isna(). These events also have TotalScore=0, IPAddress.isna().
    # - Show them using: df[df["Result"].isna()]
    # - rest_index() is needed after the rows are dropped

    df = raw_dataframe.dropna(axis=0, subset=["Result"]).reset_index(drop=True)

    dropped_nan = original_length - len(df)
    print(f"{dropped_nan} tests with Result, IPAddress, TotalScore = NaN dropped")

    # Add column, ip, with the port number from the reported ip address
    df["ip"] = df.IPAddress.apply(lambda x: x.split(":")[0])

    # Add column, duration, for the TotalTimeSpent in minutes
    df["duration"] = df.TotalTimeSpent/60

    # Add column, duration, for the TotalTimeSpent in minutes
    df["duration"] = df.TotalTimeSpent/60

    # Some events have more than 1 ip address
    df["multiple_ip"] = df.ip.apply( lambda x: len(x.split(","))>1)

    # Remove the extra ip address from tests with more than 1 ip address
    df.loc[:,"ip"] = df.ip.apply(lambda x: x.split(",")[0])
    print(f'Extra ip address dropped in {len(df[df["multiple_ip"]])} tests')

    # Make a copy of the cleaned data
    if save:
        df.to_csv("clean_test_data.csv", index=False)
    return df

#-----------------------------------------------------------------------------

def prep_dmv_splunk(raw_dataframe, save=False, filename="clean_test_download.csv"):

    # Rename the columns to match sample before using it.
    df = raw_dataframe.rename(columns={"IPaddress" : "IPAddress", "ExamineeID" : "ExamineeId"})

    df = prep_dmv_sample(df, save=False)

    # Cast the TotalScore from float to int
    df.TotalScore = df.TotalScore.astype(int)

    # Make a copy of the cleaned data
    if save:
        df.to_csv(filename, index=False)
    return df

#-----------------------------------------------------------------------------


# In[ ]:




