#!/usr/bin/env python

# MIT License
#
# Copyright (c) 2017 Kyle Birkeland
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import time
import logging
import sys
try:
    from urllib.parse import quote as urlquote
except ImportError:
    from urllib import quote as urlquote
#import urllib
import xml.etree.ElementTree as ET
import requests

class ArubaAPI(object):
    _SESSION_COOKIE = 'SESSION'
    def __init__(self, device, username, password, port=4343):
        self.device = device
        self.port = port
        self.username = username
        self.password = password
        self._log = logging.getLogger('arubaapi')
        self._cookies = {}

    def _uri(self):
        uri = 'https://{}'.format(self.device)
        if self.port:
            uri = '{}:{}'.format(uri, self.port)
        return uri

    def _headers(self):
        return {'Origin': self._uri()}

    def _login(self):
        form_data = {
            'opcode': 'login',
            'url': '/',
            'needxml': 0,
            'uid': self.username,
            'passwd': self.password
        }
        resp = requests.post('{}/screens/wms/wms.login'.format(self._uri()),
                             data=form_data) #, headers=self._headers())
        self._log.debug('Login: status %s; cookies %s', resp.status_code, resp.cookies)
        authtoken = resp.cookies[self._SESSION_COOKIE]
        self._cookies[self._SESSION_COOKIE] = authtoken
        self._log.info('logged in')

    def _logout(self):
        resp = requests.get('{}/logout.html'.format(self._uri()), cookies=self._cookies)
        if resp.status_code != 200:
            self._log.error('Status code %s while logging out', resp.status_code)
        del self._cookies[self._SESSION_COOKIE]
        self._log.info('logged out')

    @staticmethod
    def _ms_time():
        return int(time.time() * 1000)

    def _cli_param(self, command):
        return '{}@@{}&UIDARUBA={}'.format(urlquote(command), self._ms_time(),
                                           self._cookies[self._SESSION_COOKIE]).encode()

    def cli(self, command):
        """Performs CLI command on ArubaOS device

        :param command: Command to run
        :type command: str
        :returns: (tabular data, non-tabular data) tuple
        """
        self._log.debug('running %s', command)
        resp = requests.get('{}/screens/cmnutil/execCommandReturnResult.xml'.format(
            self._uri()), cookies=self._cookies, params=self._cli_param(command))
        if resp.status_code != 200:
            raise ValueError('Bad status code {}'.format(resp.status_code))
        try:
            self._log.debug('Got text %r', resp.text)
            if resp.text:
                xdata = ET.fromstring(resp.text)
                self._log.debug('Successfully parsed %d bytes', len(resp.text))
            else:
                self._log.info('No data received for %r', command)
                return None
        except ET.ParseError as exc:
            if sys.version_info > (3, 0, 0):
                raise ValueError('Failed to parse {}'.format(resp.text)) from exc
            else:
                raise
        return self.parse_xml(xdata)
        #return ET.fromstring(resp.text)

    @staticmethod
    def parse_xml(xmldata):
        """Parses ArubaOS HTTP XML

        :returns: (tabular data, non-tabular data) tuple
        """
        rows = []
        data = []
        #print([x for x in xmldata.find('t').find('r')])
        for elem in xmldata.findall('t'):
            if elem.attrib.get('tn'):
                newrow = ['' for i in range(int(elem.attrib.get('nc', 0)))]
                if newrow: 
                    newrow[0] = elem.attrib.get('tn')
                    rows.append(newrow)
            rows += ([[x.text for x in y] for y in elem.findall('r')])
        for elem in xmldata.findall('data'):
            if elem.attrib.get('name'):
                data.append((elem.attrib.get('name'), elem.text))
            else:
                data.append(elem.text)
            #rows.append([[(x.tag, x.attrib, x.text) for x in y] for y in elem.findall('r')])
        #headers = rows[0]
        #data = rows[1:]
        #return {'headers': headers, 'rows': data}
        return {'table': rows, 'data': data}
