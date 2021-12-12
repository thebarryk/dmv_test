import mywhois
import pprint
import pandas as pd

pp = pprint.PrettyPrinter()

# Routine to read a clean set ip addresses from the sample data
# and incorporate them into the risk database

db_filename = "mywhois"
sample_filename = "clean_test_data.csv"

# Open the database and load the current data
risk = mywhois.Risk(db_filename, readonly=False)

# Read the clean set of sample data set
clean_ip = pd.read_csv(sample_filename)
                       
# range over the unique ip addresses
new = 0
old = 0

ip_todo = clean_ip.ip.drop_duplicates()[:5]

for n, ip in enumerate(ip_todo):
    before = len(risk.risk)
    risk.find(ip)
    after  = len(risk.risk)
    if before == after:
        old += 1
    else:
        new += after - before
        
print(f"{n=} {new=} {old=} {len(risk.risk)=}")