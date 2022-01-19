# Gather modules
import pandas as pd
import mywhois

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

    
def dmv_risk_input():
    # Reads dmv_test test data, preps and adds ip risk.
    # Returns tuple:
    #   df .... dataframe combo of dmv_test data and ip risk
    #   risk .. dict of the risk associated using an ip address
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
    
    # Input data
    sample_filename = "/home/bkrawchuk/notebooks/dmv_test/OPT11022021-11042021.csv"

    # Read the sample data downloaded from the DMV testing web site
    df1 = pd.read_csv(sample_filename)
    df = prep_dmv_sample(df1, save=True)
    
    # Add the risk associated while using the client's ip address
    risk = mywhois.Risk("mywhois", readonly=True)

    vscore = df.loc[:,"ip"].apply(fetch_score).copy()
    vrisk  = df.loc[:,"ip"].apply(fetch_risk).copy()
    df.loc[:,"risk"]  = vrisk
    df.loc[:,"score"] = vscore
    return df, risk
