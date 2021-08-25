#################################################################################
#                Common                                                        #
#################################################################################

'''
Author: Sean Lam
Contact: seanlm@student.ubc.ca
'''

# package dependancies

try:
    import yaml
except:
    import pip
    pip.main(['install', 'yaml'])
    import yaml
    
import xml.etree.ElementTree as ET
import re

