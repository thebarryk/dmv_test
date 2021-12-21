# List overlapping cidr in the whois database.
# Risk.add must make sure to look before adding and report errors.
# There are 4 cases:
# ---------------------------------------- Case 1: Spans on low side
#  |      |-------old------|                       An error. Check ARIN.
#  |           |                                   Do not add cidr.
#  |----new----|
#
# ---------------------------------------- Case 2: Overlaps old completely
#  |      |-------old------|  |                    Add new cidr; delete old one.
#  |                          |                    Caution: May be more than 1 old.
#  |----new-------------------|
#
# ---------------------------------------- Case 3: Overlapped by old completely
#         |-------old------|                       Do not add cidr.
#              |        |                          Error because cidr_search would
#              |--new---|                          find old cidr first.
#
# ---------------------------------------- Case 4: Spans on high side
#         |-------old------|  |                    An error. Check ARIN.
#              |              |                    Do not add cidr.
#              |----new-------|
#

import mywhois
import pandas as pd
from ipaddress import *
import random

class Sample_overlap():
    def __init__(self, sample_fraction=1.0):
        self.overlaps = []
        self.sample_fraction = sample_fraction
    def sample(self, cidr1, cidr2):
        if random.random() < self.sample_fraction:
            self.overlaps.append([cidr1, cidr2])

def main():
    # Read the current mywhois database
    whois = mywhois.Risk("mywhois", readonly=False)
    risk = whois.risk

    # Countrol the looping during development
    count = 0
    mx = 1000000000

    # Remember the risk directory is ordered.
    risk_keys = risk.keys()
    len_keys = len(risk_keys)
    
    # Control output
    def prt(str, show=False, end="\n"):
        if show:
            print(str, end=end)
        
#     import pdb; pdb.set_trace()

    # Sample the two overlaps to see if the arin and risk info is different

    sample_overlaps = Sample_overlap()
    sample = sample_overlaps.sample

            
    # Treat every cidr as a potential candidate.
    # There's no need to test the last one.
    for i in range(len_keys-1):
        new = risk_keys[i]

        # Examine each other cidr. 
        # Do upper triangle since the others have been done
        for j in range(i+1,len_keys):
            old = risk_keys[j]

            # Place a brake to use during development
            count += 1
            if count > mx:
                break

            # Separate into the various cases
            if new[0] < old[0]:
                if new[-1] < old[0]:
                    # Case 0: this new is completely lower than old
                    case = 0 
                    continue
                elif new[-1] <= old[-1]:
                    # Case 1: this new spans part of old on low side
                    case = 1
                    prt(f"New: ({new[0]}, {new[-1]}) Old: ({old[0]}, {old[-1]}) {case=}")
                    continue
                else:
                    # Case 2: this new completely contains old
                    case = 2
                    # (printing this way means they can be sorted)
                    # print(f"({new[0]}, {new[-1]}) Old: ({old[0]}, {old[-1]}) {case=}")
                    prt(f"{risk_keys[j]=}: ({old[0]}, {old[-1]})", end=" ")
                    prt(f"{risk_keys[i]=}: ({new[0]}, {new[-1]}) {case=}")
                    # print(f"{risk_keys[j]=}: ( {old[0]}, {old[-1]}) {risk_keys[i]=}: ({new[0]}, {new[-1]} {case=})")
                    sample(risk_keys[i], risk_keys[j])
                    continue

            if new[-1] <= old[-1]:
                # Case 3: this new is subset of old in reverse
                case = 3
                # Case 2 is repeated in reverse order in the lower triangle as Case 3.
                # That's why we are scanning only the upper triangle.
                # print(f"New: ({new[0]}, {new[-1]}) Old: ({old[0]}, {old[-1]} {case=})")
                prt(f"{risk_keys[i]=}: ({new[0]}, {new[-1]})", end=" ")
                prt(f"{risk_keys[j]=}: ({old[0]}, {old[-1]}) {case=}")
                sample(risk_keys[i], risk_keys[j])
                continue

            if new[0] > old[-1]:
                # Case 5: this new is completely higher than old
                case = 5
                continue

            # Case 4: this new spans part of old on high side
            case = 4
            prt(f"New: ({new[0]}, {new[-1]}) Old: ({old[0]}, {old[-1]} {case=})")

    # Look for diferences in arin and risk for sample
    def chk(cidrs, r, f):
        g1 = f"{cidrs[0]} and {cidrs[1]}"
        g2 = lambda f: f"{f}s {r[0][f]} <-->  {r[1][f]}"
        if r[0][f] != r[1][f]:
            print(g1, "have different", g2(f))
    def chk2(cidrs, r, f="risk"):
        g1 = f"{cidrs[0]} and {cidrs[1]}"
        g2 = lambda f: f"{f}s {r[0][f]} <-->  {r[1][f]}"
        if r[0][f] != r[1][f]:
            print(g1, "have different", g2("risk"))
            print("    ", g2("score"))
            print("    ", g2("organization"))
    
                  
    for cidrs in sample_overlaps.overlaps:
        r = [ risk[ip_network(cidrs[0])], risk[ip_network(cidrs[1])] ]
#         chk(cidrs, r, "score")
        chk2(cidrs, r)
#         chk(cidrs, r, "organization")

main()
print("Done!")
