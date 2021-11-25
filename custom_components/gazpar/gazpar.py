import datetime

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

        # Login
        login_response = session.post('https://login.monespace.grdf.fr/sofit-account-api/api/v1/auth', data={
            'email': self.username,
            'password': self.password,
            'capp': 'meg',
            'goto': 'https://sofa-connexion.grdf.fr:443/openam/oauth2/externeGrdf/authorize?response_type=code&scope=openid%20profile%20email%20infotravaux%20%2Fv1%2Faccreditation%20%2Fv1%2Faccreditations%20%2Fdigiconso%2Fv1%20%2Fdigiconso%2Fv1%2Fconsommations%20new_meg&client_id=prod_espaceclient&state=0&redirect_uri=https%3A%2F%2Fmonespace.grdf.fr%2F_codexch&nonce=skywsNPCVa-AeKo1Rps0HjMVRNbUqA46j7XYA4tImeI&by_pass_okta=1&capp=meg'
        })

        # First request never returns data
        url = 'https://monespace.grdf.fr/api/e-conso/pce/consommation/informatives?dateDebut={0}&dateFin={1}&pceList%5B%5D={2}'.format(
            (datetime.datetime.now() - datetime.timedelta(days=7)).strftime('%Y-%m-%d'),
            datetime.datetime.now().strftime('%Y-%m-%d'),
            self.pce)
        print(url)
        session.get(url)

        # Get data
        response = session.get(url)
        return response.json()[self.pce]['releves'][-1]['indexFin']
