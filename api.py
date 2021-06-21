import requests, variables, datetime, json

class MichelleIce:
    def __init__(self):
        self._device = None
        self._sess = requests.Session()
        self._sess.headers.update({
            'Accept': 'application/json',
        })

    def _req(self, f):
        r = None
        try:
            r = f(self)
            if r.status_code == 401 or r.status_code == 403:
                self.refreshKey()
                r = f(self)
        except:
            pass

        return r

    def refreshKey(self):
        r = self._sess.post(variables.BASE_URL + 'devices/auth', params={
            'serial_number': variables.AUTH_SERIAL_NUMBER,
            'pin': variables.AUTH_PIN,
        }, timeout=3)

        self._device = r.json()
        self._sess.headers.update({'X-Device-Authentication-Token': self._device['device_authentication_token']})
    
    def fetchConfiguration(self):
        def create_request(c):
            return c._sess.get(variables.BASE_URL + 'devices/' + str(self._device['id']), timeout=3)
        
        r = self._req(create_request)
        return r.json() if r else None

    def insert(self, sensor_id, value):
        def create_request(c):
            return c._sess.post(variables.BASE_URL + 'sensors/' + str(sensor_id) + '/values', params={
                'value': value,
                'recorded_at': datetime.datetime.utcnow().isoformat()
            }, timeout=3)
            
        self._req(create_request)
    
    def fires(self, event_id):
        def create_request(c):
            return c._sess.post(variables.BASE_URL + 'events/' + str(event_id) + '/fire', params={
                'fired_at': datetime.datetime.utcnow().isoformat()
            }, timeout=3)
        
        self._req(create_request)
