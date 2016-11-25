# -*- coding: utf-8 -*-

'''
    IO data from/to multiple sensors
    
    Written by Laurent Fournier, October 2016
'''

import os, sys, subprocess
import time, datetime
import serial
import argparse

from bs4         import BeautifulSoup as bs
from lxml        import etree
from collections import Counter

# External libraries
import file_manager as fm
from tools     import *
from licor_6xx import Licor6xx
from licor_7xx import Licor7xx
from licor_8xx import Licor8xx

#-------------------------------------------------------------
#------------------ Open configurations ----------------------
#-------------------------------------------------------------

  ############
  # Terminal #
  ############

parser = argparse.ArgumentParser(description = '')
parser.add_argument('-c', '--continuous', type=bool, help='No outputs limitation', default=True,  choices=[True, False])
parser.add_argument('-C', '--config',     type=bool, help='Configuration mode',    default=False, choices=[True, False])
parser.add_argument('-d', '--debug',      type=bool, help='Debugging mode',        default=True,  choices=[True, False])
parser.add_argument('-l', '--loops',      type=int,  help='Number of outputs',     default=5)
parser.add_argument('-L', '--logging',    type=bool, help='Storing in .CSV files', default=True,  choices=[True, False])
parser.add_argument('-m', '--model',      type=int,  help='Select device model',   default=6262,  choices=[820, 840, 6262, 7000])
args = parser.parse_args()
  
  ############
  # Settings #
  ############
  
CONFIG     = args.config
CONTINUOUS = args.continuous
DEBUG      = args.debug
DEVICE     = args.model
LOG        = args.logging
LOOPS      = args.loops                                                                 # Nr of data extractions

FREQ       = 5
PORT       = '/dev/ttyUSB0'
BAUD       = 9600
PARITY     = 'N'
STOPBIT    = 1
BYTE_SZ    = 8
TIMEOUT    = 5.0
LOG_DIR    = 'logs/'


#-------------------------------------------------------------
#----- Better know what you are doing from this point --------
#-------------------------------------------------------------    
args_list = { 'port' : PORT,    'baud': BAUD,             'timeout': TIMEOUT,
              'config': CONFIG, 'continuous': CONTINUOUS, 'debug': DEBUG,
              'device': DEVICE, 'log': LOG,               'loops': LOOPS }

try:                                                                                    # Connect to device
    if   DEVICE == 820 or DEVICE == 840: probe = Licor8xx(**args_list)        
    elif DEVICE == 6262:                 probe = Licor6xx(**args_list)
    elif DEVICE == 7000:                 probe = Licor7xx(**args_list)

    probe.connect()
    
except Exception as e:
    if DEBUG: print ("ERROR: {}".format(e))    
    sys.exit("Could not connect to the device")

  ###################
  # Writing routine #
  ###################
  
if CONFIG:                                                                              # Configure the device if required
    try:
        #probe.config_R()
        probe.config_W()
        
    except Exception as e:
        if DEBUG: print ("ERROR: {}".format(e))        
        sys.exit("Could not connect to the device")

  ###################
  # Reading routine #
  ###################
  
filename = 'licor{0}/licor{0}-data-{1}.csv'.format(DEVICE, datetime.datetime.now())

if LOG_DIR:                                                                             # If LOG_DIR is set, add it to filename
    filename = os.path.join(LOG_DIR, filename)

if LOG:                                                                                 # If logging is enabled
    try:                                                                                # Verify if directory already exists
        with open(filename, 'r'): pass
    
    except Exception:                                                                   # If not, create them
        os.system('mkdir {}licor{}/'.format(LOG_DIR, DEVICE))
        pass
        
    with open(filename, 'w') as fp:
        fp.write(';'.join(probe._header))                                               # Write headers
        fp.write('\n')

        while LOOPS:
            if (datetime.datetime.now().strftime("%S") == "59" and isDone == 0):
                isDone = 1                
                try:                
                    data = probe.read()                                                     # Read from device
                    fp.write(';'.join(data))                                                # Write data
                    fp.write('\n')
                    
                except Exception as e:
                    if DEBUG: print ("ERROR: {}".format(e))

            else:
                isDone = 0
                if not CONTINUOUS: LOOPS += 1                    

            if not CONTINUOUS: LOOPS -= 1
                
        fp.close()
            
else:                                                                                   # If logging is Disabled
    while LOOPS:
        if (datetime.datetime.now().strftime("%S") == "59" and isDone == 0):
            isDone = 1
            data = probe.read()

        else:
            isDone = 0
            if not CONTINUOUS: LOOPS += 1

        if not CONTINUOUS: LOOPS -= 1
            