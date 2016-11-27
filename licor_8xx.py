# -*- coding: utf-8 -*-

'''
    IO data from/to a Licor 820 and 840a

    Written by David H. Hagan, May 2016
    Modifications by Laurent Fournier, October 2016

    LI820:  Temp->C    Pres->?    CO2->?
    LI840:  Temp->C    Pres->?    CO2->?     H2O->?     DewPt->C
'''

import os, sys, subprocess
import time, datetime
import serial

from bs4         import BeautifulSoup as bs
from lxml        import etree

# External libraries
import file_manager as fm

#-------------------------------------------------------------
#------------------ Open configurations ----------------------
#-------------------------------------------------------------

  ############
  # Settings #
  ############

CONFIG     = False
CONTINUOUS = True
DEBUG      = True
LOG        = True
LOOPS      = 5                                                                          # Nr of data extractions
DEVICE     = 820                                                                        # List of devices's models

FREQ       = 60
PORT       = '/dev/ttyUSB0'
BAUD       = 9600
PARITY     = 'N'
STOPBIT    = 1
BYTE_SZ    = 8
TIMEOUT    = 5.0
LOG_DIR    = 'logs/'
HEADER     = []


#-------------------------------------------------------------
#----- Better know what you are doing from this point --------
#-------------------------------------------------------------

  ##################
  # Initialisation #
  ##################

class Licor8xx:
    def __init__(self, **kwargs):
        self.port       = kwargs.pop('port',    PORT)
        self.baud       = kwargs.pop('baud',    BAUD)
        self.timeout    = kwargs.pop('timeout', TIMEOUT)
        self.config     = kwargs.pop('config',  CONFIG)
        self.continuous = kwargs.pop('continuous', CONTINUOUS)
        self.debug      = kwargs.pop('debug',   DEBUG)
        self.log        = kwargs.pop('log',     LOG)
        self.loops      = kwargs.pop('loops',   LOOPS)
        self.device     = kwargs.pop('device',  DEVICE)
        self._header    = kwargs.pop('header',  HEADER)

        fp = fm.fManager('config/.cfg', 'r')
        fp.open()
        fp.cfg_loader()

        if self.config:                                                                 # Write to the device
            if   self.device == 820:  self._header = [ line.strip() for line in fp.get_cfg('li820write') ]
            elif self.device == 840:  self._header = [ line.strip() for line in fp.get_cfg('li840write') ]
            else: print ("Wrong device's Model")

        else:                                                                           # Read from the device
            if   self.device == 820:  self._header = [ line.strip() for line in fp.get_cfg('li820read') ]
            elif self.device == 840:  self._header = [ line.strip() for line in fp.get_cfg('li840read') ]
            else: print ("Wrong device's Model")

        fp.close()

    def connect(self):
        try:
            self.con = serial.Serial(self.port, self.baud, timeout=self.timeout)        # Connect to serial device
            self.con.flushInput()
            self.con.flushOutput()

        except Exception as e:
            self.con = None
            return e

        return True

    def read(self):
        if self.device == 820:                                                          # Define data structure
            raw = bs(self.con.readline(), 'lxml')
            raw = raw.li820.data
            res = [ datetime.datetime.now().strftime('%Y-%m-%d'), datetime.datetime.now().strftime('%H:%M:%S'),
                    raw.celltemp.string, raw.cellpres.string, raw.co2.string, ]

        elif self.device == 840:
            raw = bs(self.con.readline(), 'lxml')
            raw = raw.li840.data
            res = [ datetime.datetime.now().strftime('%Y-%m-%d'), datetime.datetime.now().strftime('%H:%M:%S'),
                    raw.celltemp.string, raw.cellpres.string, raw.co2.string, raw.h2o.string, raw.h2odewpoint, ]

        if self.debug:
            print ("\nNew Data Point")
            for each in zip(self._header, res):
                print (each[0], each[1])

        return res

    def config_W(self):                                                                 # Write a complete instruction row
        if self.device == 820:
            conf = etree.Element(self._header[0])                                       # <li820>
            cfgs = etree.SubElement(conf, self._header[9])                              #   <cfg>
            outr = etree.SubElement(cfgs, self._header[11])                             #       <outrate>  --> 1
            outr.text = "1"
            conn = etree.SubElement(conf, self._header[1])                              #   <rs232>
            co2a = etree.SubElement(conn, self._header[5])                              #       <co2abs>   --> False
            co2a.text = "false"
            ivol = etree.SubElement(conn, self._header[6])                              #       <ivolt>    --> False
            ivol.text = "false"
            raws = etree.SubElement(conn, self._header[7])                              #       <raw>      --> False
            raws.text = "false"

        self.con.write(etree.tostring(conf, pretty_print = False))                      # Send command
        print ("Input: " + etree.tostring(conf, pretty_print = False))                  # Licor answer (ACK true or false)
        data_response = self.con.readline()
        print ("Output: " + data_response)

    def config_R(self):                                                                 # Ask actual config
        info = etree.Element(self._header[0])                                           #
        info.text = "?"                                                                 # <liXXX>?</liXXX>

        self.con.write(etree.tostring(info, pretty_print = False))
        print ("Input: " + etree.tostring(info, pretty_print = False))
        data_response = self.con.readline()
        print ("Output: " + data_response)

    def __repr__(self):
        return "Licor Model Li-{}".format(device_nr)
