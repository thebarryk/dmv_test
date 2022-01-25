#!/usr/bin/env python
# coding: utf-8

# In[1]:


# %%python - passing_fraction.py passing_rate,py
# usage: git_history.py [-h] file new_name .. Output git history of file.
# Useful to update the comments when a file has been renamed.
# The name of the file will be replaced by new_name.

import sys, os, re, argparse
from datetime import datetime

def colors(choice='NC'):
    colors = {'RED' : '\033[0;31m',
              'NC'  : '\033[0;0m'
             }
    return colors[choice] if choice in colors else colors["NC"]

def git_history():
    cmd = f"git log"
    lines = os.popen(cmd).read()

    # Pattern will find the full message for a commit.
    # The commit must have started the comments with the name of the file.
    paragraphs_pattern = re.compile(r"Date:\s*(?P<date>.*)\s*(?P<program>.*)\s*(?P<description>(?:.+\n)*)")
    
    paragraphs = paragraphs_pattern.findall(lines)

    for day, program, description in paragraphs:
        day = datetime.strptime(day, "%a %b %d %H:%M:%S %Y %z")
        
        # Output history changing the name of the file.
        if re.search(opt.file, program):
            print(f'> {day:%m/%d/%Y %H:%M}\n> {opt.new_name}\n{colors("RED")}{description}{colors()}')

def main():
    return git_history()

# Define the programs cli parameters
p = argparse.ArgumentParser(description='''Get full git history of file''')
p.add_argument("file", help="File to list")
p.add_argument("new_name", help="New name for the file")
opt = p.parse_args()

ps = main()


# In[ ]:





# In[ ]:




