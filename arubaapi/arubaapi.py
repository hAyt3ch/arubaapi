import time
import logging
import xml.etree.ElementTree as ET
import requests
try:
    from urllib.parse import quote as urlquote
except ImportError:
    from urllib import quote as urlquote

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
        self._cookies = dict()
        self.verify = not insecure
        self.session = requests.Session()
        if not self.verify:
            try:
                from requests.packages.urllib3.exceptions import InsecureRequestWarning
                requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
            except ImportError:
                pass
        self._login()

    def __enter__(self):
        return self

    def __exit__(self, type, value, tb):
        self.close()

    def _uri(self):
        uri = 'https://{}'.format(self.device)
        if self.port:
            uri = '{}:{}'.format(uri, self.port)
        return uri

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
                                 data=form_data, verify=self.verify)
        self._log.debug('Login: status %s; cookies %s', resp.status_code, resp.cookies)
        self._log.info('logged in to {}'.format(self.device))

    def _logout(self):
        resp = self.session.get('{}/logout.html'.format(self._uri()), verify=self.verify)
        # For some reason it's always a 404 when logging out
        if resp.status_code != 404:
            self._log.error('Unexpected status code %s while logging out', resp.status_code)
        self.session = requests.Session()
        self._log.info('logged out of {}'.format(self.device))

    @staticmethod
    def _ms_time():
        return int(time.time() * 1000)

    def _cli_param(self, command):
        """Returns URL parameters AOS requires for running commands

        :param command: Command to run
        :type command: str
        :returns: URL-encoded parameter string
        """
        return '{}@@{}&UIDARUBA={}'.format(urlquote(command), self._ms_time(),
                                           self.session.cookies[self._SESSION_COOKIE]).encode()

    def cli(self, command):
        """Performs CLI command on ArubaOS device

        :param command: Command to run
        :type command: str
        :returns: {'tables': {}, 'namedData': {}', 'data': []}
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
        except ET.ParseError:
            raise
        return self.parse_xml(xdata)

    def close(self):
        """Logs out of the controller"""
        self._logout()

    @staticmethod
    def _parse_xml_table(xmldata):
        table = []
        name = xmldata.attrib.get('tn')
        rows = [[x.text for x in y] for y in xmldata.findall('r')]
        th = xmldata.find('th')
        if th:
            header = [x.text for x in th.findall('h')]
        else:
            header = rows[0]
            rows = rows[1:]
        for row in rows:
            table.append(dict(zip(header, row)))
        return {name: table}

    @staticmethod
    def parse_xml(xmldata):
        tables = dict()
        data = []
        namedData = dict()
        for elem in xmldata:
            if elem.tag == 'data':
                if not elem.text:
                    continue
                if elem.attrib.get('name'):
                    name = elem.attrib.get('name')
                    if name in namedData:
                        if type(namedData[name]) is str:
                            namedData[name] = [namedData[name]]
                        namedData[name].append(elem.text)
                    else:
                        namedData[elem.attrib.get('name')] = elem.text
                else:
                    data.append(elem.text)
            elif elem.tag == 're':
                data.append(ArubaAPI._parse_xml(elem))
            elif elem.tag == 't':
                tables.update(ArubaAPI._parse_xml_table(elem))
        return {'tables': tables, 'data': data, 'namedData': namedData}
