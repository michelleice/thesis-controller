#!/usr/bin/python3

import api, json, logging, pigpio, signal, threading, time, variables
from lib import DHT22

EXIT_EVENT = threading.Event()
GPIO_AM2302 = 16
GPIO_LDR = 26
GPIO_SOCKETS = [4, 17, 27, 22, 23, 24, 25, 5]

logging.basicConfig(format='[%(asctime)s] %(levelname)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.INFO)

conn = api.MichelleIce()
conn.refreshKey()
config = conn.fetchConfiguration()

logging.info('Main Controller Logic, Press Ctrl-C to exit.')

if not variables.DEBUG:
    logger = logging.getLogger()
    logger.disabled = True

variables.START_TIME = round(time.time(), 0)

pi = pigpio.pi()

sensor_am2302 = None
if GPIO_AM2302 > 0:
    sensor_am2302 = DHT22.sensor(pi, GPIO_AM2302)

for socket in GPIO_SOCKETS:
    pi.set_mode(socket, pigpio.OUTPUT)
    time.sleep(1)
    pi.write(socket, 0)
    time.sleep(1)
    pi.write(socket, 1)

def sensorForGPIO(gpio):
    global config
    for sensor in config['sensors']:
        if sensor['gpio'] == gpio:
            return sensor
    
    return None

next_reading = time.time()
def readSensorDaemon():
    global conn, next_reading, EXIT_EVENT

    INTERVAL = 5
    while not EXIT_EVENT.is_set():
        logging.info("====================================")

        if sensor_am2302 is not None:
            sensor_am2302.trigger()
            time.sleep(0.2)
            humidity = sensor_am2302.humidity()
            temperature = sensor_am2302.temperature()

            logging.info('Humidity: {0:.2f}%'.format(humidity))
            logging.info('Temperature: {0:.2f}C'.format(temperature))

            if sensorForGPIO(GPIO_AM2302):
                conn.insert(sensorForGPIO(GPIO_AM2302)['id'], json.dumps([humidity, temperature]))

        
        if GPIO_LDR > 0:
            logging.info('Dark: {0}'.format(pi.read(GPIO_LDR)))

            if sensorForGPIO(GPIO_LDR):
                conn.insert(sensorForGPIO(GPIO_LDR)['id'], pi.read(GPIO_LDR))
        
        next_reading += INTERVAL

        if next_reading - time.time() > 0:
            time.sleep(next_reading - time.time())

def syncConfiguration():
    #if should_update
    #variables.EXIT_FLAG = True
    pass

def loopSyncConfiguration():
    global EXIT_EVENT
    while not EXIT_EVENT.is_set():
        syncConfiguration()
        time.sleep(60)

syncConfiguration()

#TODO: check for updates

logging.info('[sensord]: starting...')
sensord_t = threading.Thread(target=readSensorDaemon)
sensord_t.start()

logging.info('[confd]: starting...')
confd_t = threading.Thread(target=loopSyncConfiguration)
confd_t.start()

def exit(a, b):
    global EXIT_EVENT
    EXIT_EVENT.set()

    sensor_am2302.cancel()
    pi.stop()

    sensord_t.join()
    confd_t.join()

signal.signal(signal.SIGINT, exit)

while not EXIT_EVENT.is_set():
    pass


