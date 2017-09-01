#!/usr/bin/env python

import time
import logging
import sys
try:
    from urllib.parse import quote as urlquote
except ImportError:
    from urllib import quote as urlquote
import xml.etree.ElementTree as ET
import requests

class ArubaAPI(object):
    """Performs CLI commands over the ArubaOS HTTPS API"""

    _SESSION_COOKIE = 'SESSION'

    def __init__(self, device, username, password, port=4343, insecure=False):
        """Instantiates an ArubaAPI object

        :param device: Name or IP address of controller
        :type device: str
        :param username: Username to log in with
        :type username: str
        :param password: Password to log in with
        :type password: str
        :param port: Port running HTTPS server
        :type port: int
        :default port: 4343
        :param insecure: Disables verification of the TLS certificate
        :type insecure: bool
        :default insecure: False
        """
        self.device = device
        self.port = port
        self.username = username
        self.password = password
        self._log = logging.getLogger('arubaapi')
        self._cookies = {}
        self.verify = not insecure
        self.session = requests.Session()
        if not self.verify:
            try:
                from requests.packages.urllib3.exceptions import InsecureRequestWarning
                requests.packages.urllib3.disable_warning(InsecureRequestWarning)
            except ImportError:
                pass
        self._login()

    def _uri(self):
        uri = 'https://{}'.format(self.device)
        if self.port:
            uri = '{}:{}'.format(uri, self.port)
        return uri

    def _headers(self):
        return {'Origin': self._uri()}

    def _login(self):
        self._log.debug('logging in')
        form_data = {
            'opcode': 'login',
            'url': '/',
            'needxml': 0,
            'uid': self.username,
            'passwd': self.password
        }
        resp = self.session.post('{}/screens/wms/wms.login'.format(self._uri()),
                             data=form_data, verify=self.verify) #, headers=self._headers())
        self._log.debug('Login: status %s; cookies %s', resp.status_code, resp.cookies)
        authtoken = resp.cookies[self._SESSION_COOKIE]
        #self._cookies[self._SESSION_COOKIE] = authtoken
        self._log.info('logged in')

    def _logout(self):
        resp = self.session.get('{}/logout.html'.format(self._uri()), verify=self.verify)
        # For some reason it's always a 404 when logging out
        if resp.status_code != 404:
            self._log.error('Unexpected status code %s while logging out', resp.status_code)
        #del self.session.cookies[self._SESSION_COOKIE]
        self.session = requests.Session()
        self._log.info('logged out')

    @staticmethod
    def _ms_time():
        return int(time.time() * 1000)

    def _cli_param(self, command):
        return '{}@@{}&UIDARUBA={}'.format(urlquote(command), self._ms_time(),
                                           self.session.cookies[self._SESSION_COOKIE]).encode()

    def cli(self, command):
        """Performs CLI command on ArubaOS device

        :param command: Command to run
        :type command: str
        :returns: (tabular data, non-tabular data) tuple
        """
        self._log.debug('running %s', command)
        resp = self.session.get('{}/screens/cmnutil/execCommandReturnResult.xml'.format(
            self._uri()), params=self._cli_param(command),
            verify=self.verify)
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
            raise
        return self.parse_xml(xdata)

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
