import requests
import time
import re
import configparser

from prometheus_client.core import REGISTRY, GaugeMetricFamily, CounterMetricFamily
from prometheus_client import start_http_server

class Siemens9330Collector(object):
    def __init__(self, addr):
        self.addr = addr

    def collect(self):
        realtime = requests.get(f'http://{self.addr}/realtime01.html')

        volts = [float(i) for i in re.findall(r'(\d+\.\d+) V', realtime.text)]
        currents = [float(i) for i in re.findall(r'(\d+\.\d+) A', realtime.text)]
        kws = [float(i) for i in re.findall(r'(\d+\.\d+) kW', realtime.text)]
        kvas = [float(i) for i in re.findall(r'(\d+\.\d+) kVA', realtime.text)]
        kvars = [float(i) for i in re.findall(r'(\d+\.\d+) kVAR', realtime.text)]
        percents = [float(i) for i in re.findall(r'(-?\d+\.\d+) %', realtime.text)]
        hz = [float(i) for i in re.findall(r'(\d+\.\d+) Hz', realtime.text)]

        voltage = GaugeMetricFamily('siemens_9330_voltage', 'Volt (V)', labels=['name'])
        voltage.add_metric(['L-L'], volts[0])
        voltage.add_metric(['A-B'], volts[1])
        voltage.add_metric(['B-C'], volts[2])
        voltage.add_metric(['C-A'], volts[3])

        current = GaugeMetricFamily('siemens_9330_current', 'Current (A)', labels=['name'])
        current.add_metric(['avg'], currents[0])
        current.add_metric(['A'], currents[1])
        current.add_metric(['B'], currents[2])
        current.add_metric(['C'], currents[3])

        kw = GaugeMetricFamily('siemens_9330_kw', 'Real Power (kW)', labels=['name'])
        kw.add_metric(['total'], kws[0])

        kva = GaugeMetricFamily('siemens_9330_kva', 'Apparant Power (kVA)', labels=['name'])
        kva.add_metric(['total'], kvas[0])

        kvar = GaugeMetricFamily('siemens_9330_kvar', 'Reactive Power (kVAR)', labels=['name'])
        kvar.add_metric(['total'], kvars[0])

        unbalance = GaugeMetricFamily('siemens_9330_unbalance', 'Unbalance (%)', labels=['name'])
        unbalance.add_metric(['V'], percents[2])
        unbalance.add_metric(['I'], percents[0])

        frequency = GaugeMetricFamily('siemens_9330_frequency', 'Frequency (Hz)', labels=['name'])
        frequency.add_metric(['total'], hz[0])

        pf_sign = GaugeMetricFamily('siemens_9330_pf_sign', 'Power Factor Sign', labels=['name'])
        pf_sign.add_metric(['total'], percents[1])

        yield voltage
        yield current
        yield kw
        yield kva
        yield kvar
        yield unbalance
        yield frequency
        yield pf_sign

        # get the power quality page
        power_quality = requests.get(f'http://{self.addr}/pq01.html')
        values = [float(i) for i in re.findall(r'>(\d+.\d+)<', power_quality.text)]

        voltage_thd = GaugeMetricFamily('siemens_9330_voltage_thd', 'Voltage THD (%)', labels=['name'])
        voltage_thd.add_metric(['A_total'], values[0])
        voltage_thd.add_metric(['A_odd'], values[1])
        voltage_thd.add_metric(['A_even'], values[2])
        voltage_thd.add_metric(['B_total'], values[3])
        voltage_thd.add_metric(['B_odd'], values[4])
        voltage_thd.add_metric(['B_even'], values[5])
        voltage_thd.add_metric(['C_total'], values[6])
        voltage_thd.add_metric(['C_odd'], values[7])
        voltage_thd.add_metric(['C_even'], values[8])

        current_thd = GaugeMetricFamily('siemens_9330_current_thd', 'Current THD (%)', labels=['name'])
        k_factor = GaugeMetricFamily('siemens_9330_k_factor', 'K Factor', labels=['name'])
        current_thd.add_metric(['A_total'], values[9])
        current_thd.add_metric(['A_odd'], values[10])
        current_thd.add_metric(['A_even'], values[11])
        k_factor.add_metric(['A'], values[12])
        current_thd.add_metric(['B_total'], values[13])
        current_thd.add_metric(['B_odd'], values[14])
        current_thd.add_metric(['B_even'], values[15])
        k_factor.add_metric(['B'], values[16])
        current_thd.add_metric(['C_total'], values[17])
        current_thd.add_metric(['C_odd'], values[18])
        current_thd.add_metric(['C_even'], values[19])
        k_factor.add_metric(['C'], values[20])

        yield voltage_thd
        yield current_thd
        yield k_factor

        # get the revenue page
        revenue = requests.get(f'http://{self.addr}/revenue01.html')
        values = [float(i) for i in re.findall(r'>(\d+.\d+)<', revenue.text)]
        energy = CounterMetricFamily('siemens_9330_energy', 'Energy (kWh)', labels=['name'])
        energy.add_metric(['total'], values[0])
        yield energy

if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('config.ini')
    addr = config['siemens']['address']

    REGISTRY.register(Siemens9330Collector(addr=addr))
    start_http_server(int(config['exporter']['port']))
    while True:
        time.sleep(1)