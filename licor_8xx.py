# -*- coding: utf-8 -*-

'''
    IO data from/to a Licor 820 and 840a

    Written by David H. Hagan, May 2016
    Modifications by Laurent Fournier, October 2016
'''

import os, datetime, serial

from bs4  import BeautifulSoup as bs
from lxml import etree

# External libraries
import file_manager as fm

  ##################
  # Initialisation #
  ##################

class Licor8xx:
    def __init__(self, data, device):
        self.port    = device['port']
        self.baud    = device['baud']
        self.timeout = device['timeout']
        self.debug   = device['debug']
        self.device  = device['device']

        self.q_data, self.q_header = data

        fp = fm.fManager('config/.cfg', 'r')
        fp.open()
        fp.cfg_loader()
        
        '''# Write to the device
        if (self.config):
            if   (self.device == 820):  self._header = [ line.strip() for line in fp.get_cfg('li820write') ]
            elif (self.device == 840):  self._header = [ line.strip() for line in fp.get_cfg('li840write') ]
            else: print ("Wrong device's Model")

        # Read from the device
        else:'''
        if   (self.device is '820'):  self._header = [ line.strip() for line in fp.get_cfg('li820read') ]
        elif (self.device is '840'):  self._header = [ line.strip() for line in fp.get_cfg('li840read') ]
        else: print ("Wrong device's Model")
        
        self.q_header.put(self._header)
        fp.close()

    def connect(self):
        try:
            # Connect to serial device
            self.con = serial.Serial(self.port, self.baud, timeout=self.timeout)
            # Wash buffers
            self.con.flushInput()
            self.con.flushOutput()

        except Exception as e:
            self.con = None
            return e

        return True

    def disconnect(self):
        try:
            self.con.flush()
            self.con.close()
            self.con.__del__()

        except Exception as e:
            self.con = None
            return e

        return True

    def read(self):
        self.con.readline()

        # Define data structure
        if self.device is '820':
            raw = bs(self.con.readline(), 'lxml')
            raw = raw.li820.data

            res = [ raw.celltemp.string, raw.cellpres.string, raw.co2.string, ]

        elif self.device is '840':
            raw = bs(self.con.readline(), 'lxml')
            raw = raw.li840.data

            res = [ raw.celltemp.string, raw.cellpres.string, raw.co2.string, raw.h2o.string, raw.h2odewpoint, ]

        self.q_data.put(res)

        if self.debug:
            print ("\nNew Data Point")
            for each in zip(self._header, res):
                print (each[0], each[1])

        return res

    # Write a complete instruction row
    def config_W(self):
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

        # Send command
        self.con.write(etree.tostring(conf, pretty_print = False))
        print ("Input: " + etree.tostring(conf, pretty_print = False))
        # Licor answer (ACK true or false)
        data_response = self.con.readline()
        print ("Output: " + data_response)

    # Ask actual config
    def config_R(self):
        info = etree.Element(self._header[0])
        # <liXXX>?</liXXX>
        info.text = "?"

        self.con.write(etree.tostring(info, pretty_print = False))
        print ("Input: " + etree.tostring(info, pretty_print = False))
        data_response = self.con.readline()
        print ("Output: " + data_response)

    def get_data(self, search):
        if (search is 'pid'): answer = self.pid

        return answer

    def __repr__(self):
        return "Licor Model Li-{}".format(self.device)
