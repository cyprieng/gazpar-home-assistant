import requests
import re
from lxml import etree
import io
import time
from functools import wraps

LOGIN_BASE_URI = 'https://monespace.grdf.fr/web/guest/monespace'
API_ENDPOINT_LOGIN = '?p_p_id=EspacePerso_WAR_EPportlet&p_p_lifecycle=2&p_p_state=normal&p_p_mode=view&p_p_cacheability=cacheLevelPage&p_p_col_id=column-2&p_p_col_count=1&_EspacePerso_WAR_EPportlet__jsfBridgeAjax=true&_EspacePerso_WAR_EPportlet__facesViewIdResource=%2Fviews%2FespacePerso%2FseconnecterEspaceViewMode.xhtml'


def retry(ExceptionToCheck, tries=4, delay=3, backoff=2, logger=None):
    """Retry calling the decorated function using an exponential backoff.

    http://www.saltycrane.com/blog/2009/11/trying-out-retry-decorator-python/
    original from: http://wiki.python.org/moin/PythonDecoratorLibrary#Retry

    :param ExceptionToCheck: the exception to check. may be a tuple of
        exceptions to check
    :type ExceptionToCheck: Exception or tuple
    :param tries: number of times to try (not retry) before giving up
    :type tries: int
    :param delay: initial delay between retries in seconds
    :type delay: int
    :param backoff: backoff multiplier e.g. value of 2 will double the delay
        each retry
    :type backoff: int
    :param logger: logger to use. If None, print
    :type logger: logging.Logger instance
    """

    def deco_retry(f):

        @wraps(f)
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 1:
                try:
                    return f(*args, **kwargs)
                except ExceptionToCheck as e:
                    msg = "%s, Retrying in %d seconds..." % (str(e), mdelay)
                    if logger:
                        logger.warning(msg)
                    else:
                        print(msg)
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            return f(*args, **kwargs)

        return f_retry  # true decorator

    return deco_retry


class GazparLoginException(Exception):
    """Gazpar login error"""
    pass


class GazparServiceException(Exception):
    """Gazpar error"""
    pass


class Gazpar:
    @retry(Exception, tries=4, delay=60, backoff=3)
    def __init__(self, username, password):
        """Init gazpar session

        Args:
            username: username
            password: password
        """
        # Init session
        self.session = requests.Session()
        payload = {
            'javax.faces.partial.ajax': 'true',
            'javax.faces.source': '_EspacePerso_WAR_EPportlet_:seConnecterForm:meConnecter',
            'javax.faces.partial.execute': '_EspacePerso_WAR_EPportlet_:seConnecterForm',
            'javax.faces.partial.render': 'EspacePerso_WAR_EPportlet_:global _EspacePerso_WAR_EPportlet_:groupTitre',
            'javax.faces.behavior.event': 'click',
            'javax.faces.partial.event': 'click',
            '_EspacePerso_WAR_EPportlet_:seConnecterForm': '_EspacePerso_WAR_EPportlet_:seConnecterForm',
            'javax.faces.encodedURL': 'https://monespace.grdf.fr/web/guest/monespace?p_p_id=EspacePerso_WAR_EPportlet&amp;p_p_lifecycle=2&amp;p_p_state=normal&amp;p_p_mode=view&amp;p_p_cacheability=cacheLevelPage&amp;p_p_col_id=column-2&amp;p_p_col_count=1&amp;_EspacePerso_WAR_EPportlet__jsfBridgeAjax=true&amp;_EspacePerso_WAR_EPportlet__facesViewIdResource=%2Fviews%2FespacePerso%2FseconnecterEspaceViewMode.xhtml',
            '_EspacePerso_WAR_EPportlet_:seConnecterForm:email': username,
            '_EspacePerso_WAR_EPportlet_:seConnecterForm:passwordSecretSeConnecter': password
        }
        self.session.headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Mobile Safari/537.36',
            'Accept-Language': 'fr,fr-FR;q=0.8,en;q=0.6',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept': 'application/xml, application/json, text/javascript, */*; q=0.01',
            'Faces-Request': 'partial/ajax',
            'Sec-Fetch-Mode': 'no-cors',
            'Sec-Fetch-Site': 'same-origin',
            'Origin': 'https://monespace.grdf.fr',
            'Referer': 'https://monespace.grdf.fr/monespace/connexion'
        }
        self.session.cookies['KPISavedRef'] = 'https://monespace.grdf.fr/monespace/connexion'
        self.session.get(LOGIN_BASE_URI + API_ENDPOINT_LOGIN, verify=False,
                         timeout=None, data=payload, allow_redirects=False)
        req = self.session.post(LOGIN_BASE_URI + API_ENDPOINT_LOGIN, data=payload, allow_redirects=False)
        xml = etree.fromstring(req.text)
        self.javavxs = xml.xpath("//update[@id = 'javax.faces.ViewState']")[0].text

        # 2nd request
        payload = {
            'javax.faces.partial.ajax': 'true',
            'javax.faces.source': '_EspacePerso_WAR_EPportlet_:seConnecterForm:meConnecter',
            'javax.faces.partial.execute': '_EspacePerso_WAR_EPportlet_:seConnecterForm',
            'javax.faces.partial.render': 'EspacePerso_WAR_EPportlet_:global _EspacePerso_WAR_EPportlet_:groupTitre',
            'javax.faces.behavior.event': 'click',
            'javax.faces.partial.event': 'click',
            'javax.faces.ViewState': self.javavxs,
            '_EspacePerso_WAR_EPportlet_:seConnecterForm': '_EspacePerso_WAR_EPportlet_:seConnecterForm',
            'javax.faces.encodedURL': 'https://monespace.grdf.fr/web/guest/monespace?p_p_id=EspacePerso_WAR_EPportlet&amp;p_p_lifecycle=2&amp;p_p_state=normal&amp;p_p_mode=view&amp;p_p_cacheability=cacheLevelPage&amp;p_p_col_id=column-2&amp;p_p_col_count=1&amp;_EspacePerso_WAR_EPportlet__jsfBridgeAjax=true&amp;_EspacePerso_WAR_EPportlet__facesViewIdResource=%2Fviews%2FespacePerso%2FseconnecterEspaceViewMode.xhtml',
            '_EspacePerso_WAR_EPportlet_:seConnecterForm:email': username,
            '_EspacePerso_WAR_EPportlet_:seConnecterForm:passwordSecretSeConnecter': password
        }
        self.session.post(LOGIN_BASE_URI + API_ENDPOINT_LOGIN, data=payload, allow_redirects=False)

        # Login error
        if 'GRDF_EP' not in self.session.cookies:
            raise GazparLoginException('Login unsuccessful. Check your credentials.')

    def get_data_per_hour(self, start_date, end_date):
        """Retrieve hourly energy consumption data."""
        return self._get_data('Heure', start_date, end_date)

    def get_data_per_day(self, start_date, end_date):
        """Retrieve daily energy consumption data."""
        return self._get_data('Jour', start_date, end_date)

    def get_data_per_week(self, start_date, end_date):
        """Retrieve weekly energy consumption data."""
        return self._get_data('Semaine', start_date, end_date)

    def get_data_per_month(self, start_date, end_date):
        """Retrieve monthly energy consumption data."""
        return self._get_data('Mois', start_date, end_date)

    def get_data_per_year(self):
        """Retrieve yearly energy consumption data."""
        return self._get_data('Mois')

    @retry(Exception, tries=4, delay=60, backoff=3)
    def _get_data(self, resource_id, start_date=None, end_date=None):
        """Get gazpar data

        Args:
            resource_id: Consumption interval to retrieve
            start_date: first consumption to retrieve
            end_date: last consumption to retrieve

        Returns:
            Dict
        """
        self.session.headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Mobile Safari/537.36',
            'Accept-Language': 'fr,fr-FR;q=0.8,en;q=0.6',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept': 'application/xml, application/json, text/javascript, */*; q=0.01',
            'Faces-Request': 'partial/ajax',
            'Host': 'monespace.grdf.fr',
            'Origin': 'https://monespace.grdf.fr',
            'Referer': 'https://monespace.grdf.fr/monespace/particulier/consommation/consommation',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'X-Requested-With': 'XMLHttpRequest'
        }
        resp = self.session.get('https://monespace.grdf.fr/monespace/particulier/consommation/consommations',
                                allow_redirects=False,
                                verify=False, timeout=None)

        parser = etree.HTMLParser()
        tree = etree.parse(io.StringIO(resp.text), parser)
        value = tree.xpath(
            "//div[@id='_eConsoconsoDetaille_WAR_eConsoportlet_']/form[@id='_eConsoconsoDetaille_WAR_eConsoportlet_:idFormConsoDetaille']/input[@id='javax.faces.ViewState']/@value")
        self.javavxs = value

        # Step 1
        payload = {
            'javax.faces.partial.ajax': 'true',
            'javax.faces.source': '_eConsoconsoDetaille_WAR_eConsoportlet_:idFormConsoDetaille:j_idt139',
            'javax.faces.partial.execute': '_eConsoconsoDetaille_WAR_eConsoportlet_:idFormConsoDetaille:j_idt139',
            'javax.faces.partial.render': '_eConsoconsoDetaille_WAR_eConsoportlet_:idFormConsoDetaille',
            'javax.faces.behavior.event': 'click',
            'javax.faces.partial.event': 'click',
            '_eConsoconsoDetaille_WAR_eConsoportlet_:idFormConsoDetaille': '_eConsoconsoDetaille_WAR_eConsoportlet_:idFormConsoDetaille',
            'javax.faces.encodedURL': 'https://monespace.grdf.fr/web/guest/monespace/particulier/consommation/consommations?p_p_id=eConsoconsoDetaille_WAR_eConsoportlet&p_p_lifecycle=2&p_p_state=normal&p_p_mode=view&p_p_cacheability=cacheLevelPage&p_p_col_id=column-3&p_p_col_count=5&p_p_col_pos=3&_eConsoconsoDetaille_WAR_eConsoportlet__jsfBridgeAjax=true&_eConsoconsoDetaille_WAR_eConsoportlet__facesViewIdResource=%2Fviews%2Fconso%2Fdetaille%2FconsoDetailleViewMode.xhtml',
            'javax.faces.ViewState': self.javavxs
        }
        params = {
            'p_p_id': 'eConsoconsoDetaille_WAR_eConsoportlet',
            'p_p_lifecycle': '2',
            'p_p_state': 'normal',
            'p_p_mode': 'view',
            'p_p_cacheability': 'cacheLevelPage',
            'p_p_col_id': 'column-3',
            'p_p_col_count': '5',
            'p_p_col_pos': '3',
            '_eConsoconsoDetaille_WAR_eConsoportlet__jsfBridgeAjax': 'true',
            '_eConsoconsoDetaille_WAR_eConsoportlet__facesViewIdResource': '/views/conso/detaille/consoDetailleViewMode.xhtml'
        }

        self.session.cookies[
            'KPISavedRef'] = 'https://monespace.grdf.fr/monespace/particulier/consommation/consommations'
        self.session.post('https://monespace.grdf.fr/monespace/particulier/consommation/consommations',
                          allow_redirects=False, data=payload, params=params)

        # We send the session token so that the server knows who we are
        payload = {
            'javax.faces.partial.ajax': 'true',
            'javax.faces.source': '_eConsoconsoDetaille_WAR_eConsoportlet_:idFormConsoDetaille:panelTypeGranularite1:2',
            'javax.faces.partial.execute': '_eConsoconsoDetaille_WAR_eConsoportlet_:idFormConsoDetaille:panelTypeGranularite1',
            'javax.faces.partial.render': '_eConsoconsoDetaille_WAR_eConsoportlet_:idFormConsoDetaille:refreshHighchart _eConsoconsoDetaille_WAR_eConsoportlet_:idFormConsoDetaille:updateDatesBean _eConsoconsoDetaille_WAR_eConsoportlet_:idFormConsoDetaille:boutonTelechargerDonnees _eConsoconsoDetaille_WAR_eConsoportlet_:idFormConsoDetaille:panelTypeGranularite _eConsoconsoDetaille_WAR_eConsoportlet_:idFormConsoDetaille:idBlocSeuilParametrage',
            'javax.faces.behavior.event': 'valueChange',
            'javax.faces.partial.event': 'change',
            'eConsoconsoDetaille_WAR_eConsoportlet_:idFormConsoDetaille': '_eConsoconsoDetaille_WAR_eConsoportlet_:idFormConsoDetaille',
            'javax.faces.encodedURL': 'https://monespace.grdf.fr/web/guest/monespace/particulier/consommation/consommations?p_p_id=eConsoconsoDetaille_WAR_eConsoportlet&p_p_lifecycle=2&p_p_state=normal&p_p_mode=view&p_p_cacheability=cacheLevelPage&p_p_col_id=column-3&p_p_col_count=5&p_p_col_pos=3&_eConsoconsoDetaille_WAR_eConsoportlet__jsfBridgeAjax=true&_eConsoconsoDetaille_WAR_eConsoportlet__facesViewIdResource=%2Fviews%2Fconso%2Fdetaille%2FconsoDetailleViewMode.xhtml',
            '_eConsoconsoDetaille_WAR_eConsoportlet_:idFormConsoDetaille:idDateDebutConsoDetaille': start_date,
            '_eConsoconsoDetaille_WAR_eConsoportlet_:idFormConsoDetaille:idDateFinConsoDetaille': end_date,
            '_eConsoconsoDetaille_WAR_eConsoportlet_:idFormConsoDetaille:panelTypeGranularite1': resource_id.lower(),
            '_eConsoconsoDetaille_WAR_eConsoportlet_:idFormConsoDetaille:panelTypeGranularite3': 'mois',
            '_eConsoconsoDetaille_WAR_eConsoportlet_:idFormConsoDetaille:selecteurVolumeType2': 'kwh',
            '_eConsoconsoDetaille_WAR_eConsoportlet_:idFormConsoDetaille:selecteurVolumeType4': 'kwh',
            'javax.faces.ViewState': self.javavxs
        }
        params = {
            'p_p_id': 'eConsoconsoDetaille_WAR_eConsoportlet',
            'p_p_lifecycle': '2',
            'p_p_state': 'normal',
            'p_p_mode': 'view',
            'p_p_cacheability': 'cacheLevelPage',
            'p_p_col_id': 'column-3',
            'p_p_col_count': '5',
            'p_p_col_pos': '3',
            '_eConsoconsoDetaille_WAR_eConsoportlet__jsfBridgeAjax': 'true',
            '_eConsoconsoDetaille_WAR_eConsoportlet__facesViewIdResource': '/views/conso/detaille/consoDetailleViewMode.xhtml'
        }

        self.session.cookies[
            'KPISavedRef'] = 'https://monespace.grdf.fr/monespace/particulier/consommation/consommations'

        req = self.session.post('https://monespace.grdf.fr/monespace/particulier/consommation/consommations',
                                allow_redirects=False, data=payload, params=params)

        # Parse to get the data
        md = re.search("donneesCourante = \"(.*?)\"", req.text)
        d = md.group(1)
        mt = re.search("tooltipDatesInfo = \"(.*?)\"", req.text)
        t = mt.group(1)

        # Make json
        ts = t.split(",")
        ds = d.split(",")
        size = len(ts)
        data = []
        i = 0
        while i < size:
            if ds[i] != "null":
                data.append({'kwh': ds[i], 'time': ts[i].replace('Le ', '')})

            i += 1

        return data
