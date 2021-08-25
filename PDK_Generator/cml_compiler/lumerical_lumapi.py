  
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 23 22:57:51 2020
@author: lukasc
"""

###### Find and Import Lumerical API #####
import os, sys, platform
cwd = os.getcwd()

if platform.system() == 'Darwin':
    path_app = '/Applications'
elif platform.system() == 'Linux':
    path_app = '/opt'
elif platform.system() == 'Windows': 
    path_app = r'C:\Program Files'
else:
    print('Not a supported OS')
    exit()

# Application folder paths containing Lumerical
p = [s for s in os.listdir(path_app) if "Lumerical" in s]

# Check sub-folders for lumapi.py
import fnmatch
for dir_path in p:
    search_str = 'lumapi.py'
    matches = []
    for root, dirnames, filenames in os.walk(os.path.join(path_app,dir_path), followlinks=True):
        for filename in fnmatch.filter(filenames, search_str):
            matches.append(root)
    if matches:
        lumapi_path = matches[-1]
if not lumapi_path in sys.path:
    sys.path.insert(0, lumapi_path)
print('Lumerical lumapi.py path: %s' % lumapi_path)
import lumapi

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.dirname(__file__))
print('Simulation project path: %s' % dir_path)