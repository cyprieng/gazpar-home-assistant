import datetime
from urllib.parse import parse_qs, urlparse

import requests
from functools import wraps
import time


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


class Gazpar:
    def __init__(self, username, password, pce):
        """Init gazpar class

        Args:
            username: username
            password: password
            pce: Pce identifier
        """
        self.username = username
        self.password = password
        self.pce = pce

    @retry(Exception, tries=4, delay=60, backoff=3)
    def get_consumption(self):
        session = requests.Session()

        # Default headers
        session.headers.update(
            {
                "User-Agent": "Mozilla/5.0"
                              " (Linux; Android 6.0; Nexus 5 Build/MRA58N)"
                              " AppleWebKit/537.36 (KHTML, like Gecko)"
                              " Chrome/61.0.3163.100 Mobile Safari/537.36",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept": "application/json, */*",
                "Connection": "keep-alive",
                "domain": "grdf.fr",
            }
        )

        # Get redirect url
        res = session.get('https://monespace.grdf.fr/client/particulier/accueil')
        parsed_url = urlparse(res.url)
        goto_url = parse_qs(parsed_url.query)['goto'][0]

        # Login
        session.post('https://login.monespace.grdf.fr/sofit-account-api/api/v1/auth', data={
            'email': self.username,
            'password': self.password,
            'capp': 'meg',
            'goto': goto_url,
            'byPassStatus': 'Active'
        })

        # First request never returns data
        start_date = datetime.datetime.now().date().replace(month=1, day=1).strftime('%Y-%m-%d')
        url = 'https://monespace.grdf.fr/api/e-conso/pce/consommation/informatives?dateDebut={0}&dateFin={1}&pceList%5B%5D={2}'.format(
            start_date,
            datetime.datetime.now().strftime('%Y-%m-%d'),
            self.pce)
        print(url)
        session.get(url)

        # Get data
        response = session.get(url).json()
        index_m3 = response[self.pce]['releves'][-1]['indexFin']
        index_kwh = 0
        for data in response[self.pce]['releves']:
            if data['energieConsomme'] and data['journeeGaziere'] >= start_date:
                index_kwh += data['energieConsomme']

        return index_m3, index_kwh
