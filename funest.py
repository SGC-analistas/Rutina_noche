###
# Autor: Emmanuel Castillo | ecastillo@sgc.gov.co
# Se creo la clase SGC_performance para : 
#       -obtener un inventory con base a unas restricciones
#       -obtener porcentajes a partir de un inventory
#       -obtener un json para la rutina de la noche
#
# Se hiceron mejoras a la rutina funest_json2.py realizada por Ángel Agudelo adagudelo@sgc.gov.co
# Las mejoras consisten en : -optimización, -se implemento en modo OOP para generalizar en futuras rutinas
###

from obspy.core.stream import _headonly_warning_msg
from obspy.clients.fdsn import Client
from obspy import UTCDateTime
import concurrent.futures
import numpy as np
import json
import warnings
import time


RSNC_off = {'network':'*',\
            'station': 'LL*,HI*,VMM*,PG*,ACH*,' +\
                        'BRR,AGCC,CAQC,COBO,EZNC,FOM,MTTC,OCNC,QUET,RGSC,' +\
                        'SBTC,SML1C,SMORC,SNPBC,TVCAC,PGA1B',\
            'location':'*',\
            'channel':'*'}

RNAC_off = {'network':'CM',
            'station':'DRL*,TOL,CMOC6,CPER3,CREAC,CTRUJ,CUIBA,',\
            'location':'*',\
            'channel':'*'}

INTER_off = {'network':'*',\
            'station': 'CONO,POTN,SOMN,LIMN,HUEN,RCON,NANN,' +\
                        'MATN,CARN,CLMA,NIMA,APQN', \
            'location':'*',\
            'channel':'*'}

INTER_EC_on = {'network':'EC',\
            'station':'PPLP,PTGL,MCRA,FLF1,COHC,PAC1,CUSE,PIAT,TULM,BONI',\
            'location':'*',\
            'channel':'*Z'}

OFF_stations = { 'RSNC':RSNC_off, 'RNAC':RNAC_off, 'INTER':INTER_off} #ALWAYS THE KEY NAME MUST HAVE THE NAME WHERE IT BELONGS. ex: DRL,RSNC,RNAC...
ON_stations = {'INTER_EC':INTER_EC_on} #ALWAYS THE KEY NAME MUST HAVE THE NAME WHERE IT BELONGS. 


class SGC_Performance(object):
    def __init__(self, ip_fdsn, port_fdsn, starttime,endtime):
        self.ip_fdsn = ip_fdsn
        self.port_fdsn = port_fdsn
        self.starttime = starttime
        self.endtime = endtime

    @property
    def sgc_client(self):
        return Client(self.ip_fdsn+":"+self.port_fdsn)

    @property
    def __RSNC_inv(self):
        inv = self.sgc_client.get_stations(network='CM', 
                                            location="00,20",
                                            channel = "*Z",
                                            starttime=self.starttime,
                                            endtime=self.endtime,
                                            level="channel")
        return inv

    @property
    def __DRL_inv(self):
        inv = self.sgc_client.get_stations(network='CM',
                                            station='DRL*',
                                            channel = "*Z",
                                            starttime=self.starttime,
                                            endtime=self.endtime,
                                            level="channel")
        return inv

    @property
    def __RNAC_inv(self):
        inv = self.sgc_client.get_stations(network='CM',
                                            location="10",
                                            channel = "*Z",
                                            starttime=self.starttime,
                                            endtime=self.endtime,
                                            level="channel")
        return inv

    @property
    def __INTER_inv(self):
        inter_net= "CU,BR,IU,VE,GT,II,IU,NU,OM,OP,PA,PR,RP"
        inv = self.sgc_client.get_stations(network=inter_net,
                                            channel = "*Z",
                                            starttime=self.starttime,
                                            endtime=self.endtime,
                                            level="channel")
        return inv

    @property
    def __SUB_inv(self):
        inv = self.sgc_client.get_stations(network='CM',
                                            station='CVER,TABC',
                                            location ='00,20',
                                            channel = "*Z",
                                            starttime=self.starttime,
                                            endtime=self.endtime,
                                            level="channel")
        return inv

    def __ON_inv(self, network, station, location, channel):
        inv = self.sgc_client.get_stations(network=network,
                            station=station,
                            location= location,
                            channel = channel,
                            starttime=self.starttime,
                            endtime=self.endtime,
                            level="channel")
        return inv

    def _remove(self, inv, net_dict):

        networks = net_dict['network'].split(',')
        stations = net_dict['station'].split(',')
        locations = net_dict['location'].split(',')
        channels = net_dict['channel'].split(',')
        for network in networks :
            for station in stations :
                for location in locations :
                    for channel in channels :
                        inv = inv.remove(network=network,
                                        station=station,
                                        location=location,
                                        channel=channel)
        return inv

    def _inv(self, on_stations=ON_stations,off_stations=OFF_stations):
        """
        parameters
        ----------
        on_stations: dict
            dict that contains information about on stations
        off_stations: dict
            dict that contains information about off stations
        
        returns
        -------
        inv_dict: dict
            dict that contains the next inventories: 'RSNC', 'RNAC','DRL','SUB','INTER' 
        """

        RSNC_inv = self.__RSNC_inv
        RNAC_inv = self.__RNAC_inv
        DRL_inv = self.__DRL_inv
        SUB_inv = self.__SUB_inv
        INTER_inv = self.__INTER_inv

        invs = [('RSNC',RSNC_inv),('RNAC',RNAC_inv),\
                ('DRL',DRL_inv),('SUB',SUB_inv),\
                ('INTER',INTER_inv )]
        
        inv_dict={}
        for admin,inv in invs:
            off_key = [key for key in off_stations.keys() if admin in key]
            for key in off_key:
                inv = self._remove(inv,off_stations[key])
            
            on_key = [key for key in on_stations.keys() if admin in key]
            for key in on_key:
                on_inv = self.__ON_inv(network=on_stations[key]['network'],
                                      station=on_stations[key]['station'],
                                      location=on_stations[key]['location'],
                                      channel=on_stations[key]['channel'] )
                inv= inv.__add__(on_inv)
            inv_dict[admin]= inv.copy()
            
        return inv_dict

    def inv(self, on_stations=ON_stations,off_stations=OFF_stations):
        """
        parameters
        ----------
        on_stations: dict
            dict that contains information about on stations
        off_stations: dict
            dict that contains information about off stations
                
        returns
        -------
        inv_dict: dict
            dict that contains the next inventories: 'RSNC', 'RNAC','DRL','SUB','INTER' 
        """
        return self._inv(on_stations,off_stations)

    def _get_availability_percentage(self, network, station, location, channel,
                                    starttime, endtime):

        #adapted method from sds client
        """
        Get percentage of available data.

        :type network: str
        :param network: Network code of requested data (e.g. "IU").
        :type station: str
        :param station: Station code of requested data (e.g. "ANMO").
        :type location: str
        :param location: Location code of requested data (e.g. "").
        :type channel: str
        :param channel: Channel code of requested data (e.g. "HHZ").
        :type starttime: :class:`~obspy.core.utcdatetime.UTCDateTime`
        :param starttime: Start of requested time window.
        :type endtime: :class:`~obspy.core.utcdatetime.UTCDateTime`
        :param endtime: End of requested time window.
        
        :rtype: 2-tuple (float, int)
        :returns: 2-tuple of percentage of available data (``0.0`` to ``1.0``)
            and number of gaps/overlaps.
        """
        if starttime >= endtime:
            msg = ("'endtime' must be after 'starttime'.")
            raise ValueError(msg)

        
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore", _headonly_warning_msg, UserWarning,
                "obspy.core.stream")

            try:
                st = self.sgc_client.get_waveforms(network, station, location, channel,
                                        starttime, endtime)
                st_existence = True
            except:
                st_existence = False


        if st_existence == True:
            # even if the warning was silently caught and not shown it gets
            # registered in the __warningregistry__ and will not be shown
            # subsequently in a place were it's not caught
            # see https://bugs.python.org/issue4180
            # see e.g. http://blog.ionelmc.ro/2013/06/26/testing-python-warnings/
            try:
                from obspy.core.stream import __warningregistry__ as \
                    stream_warningregistry
            except ImportError:
                # import error means no warning has been issued from
                # obspy.core.stream before, so nothing to do.
                pass
            else:
                for key in list(stream_warningregistry.keys()):
                    if key[0] == _headonly_warning_msg:
                        stream_warningregistry.pop(key)
            st.sort(keys=['starttime', 'endtime'])
            st.traces = [tr for tr in st
                        if not (tr.stats.endtime < starttime or
                                tr.stats.starttime > endtime)]

            if not st:
                return (0, 1)

            total_duration = endtime - starttime
            # sum up gaps in the middle
            gaps = [gap[6] for gap in st.get_gaps()]
            gap_sum = np.sum(gaps)
            gap_count = len(gaps)
            # check if we have a gap at start or end
            earliest = min([tr.stats.starttime for tr in st])
            latest = max([tr.stats.endtime for tr in st])
            if earliest > starttime:
                gap_sum += earliest - starttime
                gap_count += 1
            if latest < endtime:
                gap_sum += endtime - latest
                gap_count += 1

            percentage = 100*( 1 - (gap_sum / total_duration))
            percentage = int(round(percentage))

        else:
            percentage = 0
            gap_count = 0


        return (percentage, gap_count)

    def _percentage_executor(self,parameters):
        network,station,location,channel = parameters.split('.')
        percentage = self._get_availability_percentage(network=network, 
                                        station=station, 
                                        location=location, 
                                        channel=channel,
                                        starttime=self.starttime,
                                        endtime=self.endtime)
        return percentage

    def _get_percentage_dict(self,inv_dict):
        """
        parameters
        ----------
        inv_dict: dict
        
        returns
        -------
        perc_dict : dict
            dictionary of dictionaries where de deep dictionary contains the percentage
        """
        perc_dict={}
        for key in inv_dict.keys():

            contents = inv_dict[key].get_contents()['channels']
            tic = time.time()
            with concurrent.futures.ProcessPoolExecutor() as executor:
                percentages = executor.map(self._percentage_executor,contents )
                contents_dict = dict(zip(contents,percentages))
            perc_dict[key] = contents_dict

            toc = time.time()
            print('\t\t',  "{0:>15}".format(key+': OK'),'\t\t',
                "{0:>15}".format(f'# stations: {len(contents)}'),'\t\t',
                "{0:>15}".format(f'delay: {toc-tic:.2f}s'))

        return perc_dict

    def get_percentage_dict(self,inv_dict):
        """
        parameters
        ----------
        inv_dict: dict
                
        returns
        -------
        perc_dict : dict
            dictionary of dictionaries where de deep dictionary contains the percentage
        """
        return self._get_percentage_dict(inv_dict)

    def _create_json(self, on_stations=ON_stations, off_stations=OFF_stations):
        inv_dict = self._inv(on_stations, off_stations)
        perc_dict = self._get_percentage_dict(inv_dict)
        
        jsonlist= []
        SGC = {}
        for key in inv_dict.keys():
            for network in inv_dict[key]:
                for station in network:
                    for channel in station:
                        content = '.'.join((network.code,station.code,\
                                            channel.location_code,\
                                            channel.code))

                        SGC["administrador"] = key
                        SGC["net"] = network.code
                        SGC["localizacion"] = channel.location_code
                        SGC["estacion"] = station.code
                        SGC["longitud"] = station.longitude
                        SGC["latitud"] = station.latitude
                        SGC["valor"], SGC["#Gaps"] = perc_dict[key][content]

                        jsonlist.append(SGC.copy())
        return jsonlist

    def create_json(self, filepath, on_stations=ON_stations, off_stations=OFF_stations):
        json2 = self._create_json(on_stations,off_stations)
        with open(filepath,"w") as jsonfile:
            json.dump(json2, jsonfile)

if __name__ == "__main__":
    ip_fdsn = "http://10.100.100.232"
    port_fdsn = "8091"
    starttime = UTCDateTime(2020,7,31,0,0,0)
    endtime = UTCDateTime(2020,8,1,0,0,0)
    filename = 'funest.json'

    sgc_perf = SGC_Performance(ip_fdsn, port_fdsn, starttime,endtime)
    sgc_perf.create_json(filename,on_stations=ON_stations,
                        off_stations=OFF_stations)
