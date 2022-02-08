"""
APINexus
Class definition
"""
import json
import time
from datetime import datetime

import pandas
import requests
import urllib3
from pandas import json_normalize

'''import NexusRequest
from NexusValue import NexusValue
'''

def WarningsAndJson(func):
    """Decorator including InsecureRequestWarning and then JSON() format"""

    def f(*args, **kwargs):
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        rv = func(*args, **kwargs)
        return rv.json()

    return f


class APINexus:
    def __init__(self, IP_Maquina="localhost", Puerto=56000, token="", version="v1"):
        """Metodo de inicialización de la clase. Aquí se define la IP y el puerto al que hemos de conectar así como el token"""
        print("Creada nueva instancia de tipo NEXUS API")
        self.IP_Maquina = IP_Maquina
        self.Puerto = str(Puerto)
        self.token = token
        self.version = version
        self.url_NX = "http://" + IP_Maquina + ":" + str(Puerto)
        self.header = {
            "nexustoken": self.token,
            "nexusapiversion": self.version,
            "Content-Type": "application/json",
        }

    def statusConnection(self, url_completa):
        """COD respuesta de la API"""
        resp = requests.get(url_completa, headers=self.header)
        return resp.status_code

    @WarningsAndJson
    def __getResponse(self, url):
        """GET method using Request"""
        return requests.get(url, verify=False, headers=self.header)

    @WarningsAndJson
    def __postResponse(self, url, body):
        """POST method using Request"""
        return requests.post(url, verify=False, headers=self.header, data=body)

    def callGetDocuments(self):
        """Lectura de vistas compartidas con el mismo token"""
        url_completa = self.url_NX + "/api/Documents"
        return self.__getResponse(url_completa)

    def callGetTagViews(self, uid):
        """Lectura de variables contenidas en una vista. Como parametros recibe unicamente el uid de la vista que queremos leer ya que el token , la IP y el puerto ya se han definido en la instanciacion de la clase"""
        url = self.url_NX + "/api/Documents/tagviews/" + uid
        print(url)
        return self.__getResponse(url)

    def callGetTagViewsRealTime(self, uid, uids_vbles):
        """Lectura de variables de una vista. Devuelve el valor en tiempo real de las variables establecidas en el array uids, contenidas en la vista uid """
        body = json.dumps(uids_vbles)
        url = self.url_NX + "/api/Documents/tagviews/" + uid + "/realtime"
        return self.__postResponse(url, body)

    def callGetDataviewHistory(self, uid, nexusRequest):
        """Lectura de valores historicos de variables"""
        body = json.dumps(
            nexusRequest, default=lambda o: o.__dict__, sort_keys=True, indent=2
        )
        url = self.url_NX + "/api/Documents/tagviews/" + uid + "/historic"
        return self.__postResponse(url, body)

    def callGetTagsWritable(self):
        """Metodo de consultas de tags escribibles"""
        url = self.url_NX + "/api/Tags/writable"
        return self.__getResponse(url)

    def callGetTags(self):
        """Método de consulta de tags de la instalación"""
        url = self.url_NX + "/api/Tags"
        return self.__getResponse(url)

    def callGetTagsRealTime(self,uids_vbles):
        """Devuelve valor RT de los tags de la instalacion definidos en un array UIDS_VBLES"""
        body=json.dumps(uids_vbles)
        url = self.url_NX + "/api/Tags/realtime"
        return self.__postResponse(url,body)

    def callGetTagsHistory(self,nexusRequest):
        """Devuelve valor historico de los tags especificados en la estructura NexusRequest"""
        body = json.dumps(nexusRequest, default=lambda o: o.__dict__, sort_keys=True, indent=2)
        url = self.url_NX + "/api/Tags/historic"
        
        return self.__postResponse(url,body)



    def callPostTagInsert(self, variable_name):
        """consulta de tags"""
        url_get = self.url_NX + "/api/Tags/writable"
        variables = self.__getResponse(url_get)
        variables_names=list()
        try:                  
            variables_norm = json_normalize(variables)
            variables_names = list(variables_norm.name)
        except:
            print(variables_names)
        
        if not variable_name in variables_names:
            print("Se procede a crear la variable con nombre "
                + variable_name
                + "Se devuelve json con uid y nombre de variable creada"
            )
            payload = '["' + variable_name + '"]'
            print(payload)
            url_post = self.url_NX + "/api/Tags/insert"
            print(url_post)
            response = self.__postResponse(url_post, payload)
            dataReceived = json_normalize(response)
        else:
            print(
                "La variable ya existe, no se creará ninguna variable. Se devuelve el json con el uid de la variable existente"
            )
            dataReceived = variables_norm[variables_norm.name == variable_name]

        return dataReceived

    def callPostValueRT(self, variable_name, variable_value):
        """Escritura de variable en tiempo real."""
        # La función comprueba primero si existe la variable en la que se quiere escribir
        url = self.url_NX + "/api/Tags/writable"
        # print(url_completa)
        variables = self.__getResponse(url)
        variables_norm = json_normalize(variables)
        variables_names = list(variables_norm.name)

        # La función escribe en la variable
        if variable_name in variables_names:
            variable_uid = list(
                variables_norm[variables_norm.name == variable_name].uid
            )[0]
            print(
                "El uid de la variable que se ha solicitado escribir es " + variable_uid
            )
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            url_completa = self.url_NX + "/api/Tags/realtime/insert"
            timestamp = datetime.now()
            #timestamp = time.mktime(timestamp.timetuple())
            #nexusvalue = NexusValue(variable_uid, variable_value, timestamp)
            #
            nexusvalue = NexusValue(variable_uid, variable_value)
            payload = (
                "["
                + json.dumps(
                    nexusvalue, default=lambda o: o.__dict__, sort_keys=True, indent=2
                )
                + "]"
            )
            # payload= "[{\"uid\": \"" + variable_uid + "\",\"value\": " + str(variable_value) + ",\"timeStamp\": " + str(TimeSTAMP) + "}]"

            headers = {
                "nexustoken": self.token,
                "nexusapiversion": self.version,
                "Content-Type": "application/json",
            }
            response = requests.request(
                "POST", url_completa, headers=headers, data=payload
            )

            if response.status_code == 200:
                dataReceived = "Escritura correcta"
            else:
                dataReceived = (
                    "Se ha intentado escribir en la variable "
                    + variable_name
                    + " con uid "
                    + variable_uid
                    + " pero la operación ha fallado"
                )
                print(response.text.encode("utf8"))
        # Si no existe, devuelve un mensaje para que el usuario cree la variable deseada (no lo hace automático para evitar creación de variables por errores tipográficos
        else:
            dataReceived = "La variable en la que se ha solicitado escribir no existe. Por favor creela mediante la función callPostTagInsert"

        return dataReceived

    def callPostValueHist(self, df_value_timestamp):
        """Función de escritura de variable para diferentes historicos."""
        
        # La función comprueba primero si existe la variable en la que se quiere escribir
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        url_completa = self.url_NX + "/api/Tags/writable"
        # print(url_completa)
        response = requests.get(url_completa, verify=False, headers=self.header)
        variables = response.json()
        variables_norm = json_normalize(variables)
        variables_names = list(variables_norm.name)
        variable_name = list(df_value_timestamp.name)[0]
        print(variable_name)

        # La función escribe en la variable
        if variable_name in variables_names:
            variable_uid = list(
                variables_norm[variables_norm.name == variable_name].uid
            )[0]
            df2 = df_value_timestamp.copy()
            df2["uid"] = variable_uid
            # df2.set_index('timestamp',inplace=True, drop=False)
            # df2.timestamp=time.mktime(df2.timestamp.timetuple())
            df2 = df2.drop(columns=["name"])
            print(
                "El uid de la variable que se ha solicitado escribir es " + variable_uid
            )
            payload = pandas.DataFrame.to_json(
                df2, date_format="epoch", orient="records"
            )
            #print(payload)
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            url_completa = self.url_NX + "/api/Tags/historic/insert"
            headers = {
                "nexustoken": self.token,
                "nexusapiversion": self.version,
                "Content-Type": "application/json",
            }
            response = requests.request(
                "POST", url_completa, headers=headers, data=payload
            )

            if response.status_code == 200:
                dataReceived = "Escritura correcta"
            else:
                dataReceived = (
                    "Se ha intentado escribir en la variable "
                    + variable_name
                    + " con uid "
                    + variable_uid
                    + " pero la operación ha fallado"
                )
                print(response.text.encode("utf8"))
        # Si no existe, devuelve un mensaje para que el usuario cree la variable deseada (no lo hace automático para evitar creación de variables por errores tipográficos
        else:
            dataReceived = "La variable en la que se ha solicitado escribir no existe. Por favor creela mediante la función callPostTagInsert"

        return dataReceived, payload
    
    def callPostValueHistmult(self, df_value_timestamp):
        """Función de escritura de variable para diferentes historicos."""
        #la funcion mira cuantas variables diferentes contiene el dataframe y comprueba si todas ellas existen
        vbles=list(df_value_timestamp.name.unique())
        n=len(vbles)
        print('se intenta escribir en ' + str(n) + ' variables')
        # La función comprueba primero si existe la variable en la que se quiere escribir
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        url_completa = self.url_NX + "/api/Tags/writable"
        # print(url_completa)
        response = requests.get(url_completa, verify=False, headers=self.header)
        variables = response.json()
        variables_pd=pandas.DataFrame(variables)
        variables_norm = json_normalize(variables)
        diccio=dict([(i,j) for i,j in zip(variables_pd.name,variables_pd.uid)])
        
        
        variables_names = list(variables_norm.name)
        NOK=0
        for j in vbles:
            if j not in variables_names:
                NOK=1
                print('la variable ' + str(j) + 'no esta creada')
                
        

        if NOK==0:
            df2 = df_value_timestamp
            df2['uid']=df2['name'].map(diccio)

            df2.drop(columns=["name"], inplace=True)
            print(str(df2))
            payload = pandas.DataFrame.to_json(
                df2, date_format="epoch", orient="records"
            )
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            url_completa = self.url_NX + "/api/Tags/historic/insert"
            headers = {
                "nexustoken": self.token,
                "nexusapiversion": self.version,
                "Content-Type": "application/json",
            }
            response = requests.request(
                "POST", url_completa, headers=headers, data=payload
            )

            if response.status_code == 200:
                dataReceived = "Escritura correcta"
            else:
                dataReceived = (
                    "Se ha intentado escribir en la variable "
                    + " pero la operación ha fallado" + str(response.status_code)
                )
                print(response.text.encode("utf8"))
        # Si no existe, devuelve un mensaje para que el usuario cree la variable deseada (no lo hace automático para evitar creación de variables por errores tipográficos
        else:
            dataReceived = "La variable en la que se ha solicitado escribir no existe. Por favor creela mediante la función callPostTagInsert"
            payload=[]

        return dataReceived, payload 
    
    def callPostValueRTmult(self, df_variable_name_value):
        """Escritura de variable en tiempo real."""
        #obtención de variables a escribir
        vbles=list(df_variable_name_value.name.unique())
        n=len(vbles)
        # La función comprueba primero si existe la variable en la que se quiere escribir
        url = self.url_NX + "/api/Tags/writable"
        # print(url_completa)
        variables = self.__getResponse(url)
        #variables = variables.json()
        variables_pd=pandas.DataFrame(variables)
        variables_norm = json_normalize(variables)
        diccio=dict([(i,j) for i,j in zip(variables_pd.name,variables_pd.uid)])
        df2 = df_variable_name_value
        df2['uid']=df2['name'].map(diccio)
        df2.drop(columns=["name"], inplace=True)       
        payload=pandas.DataFrame.to_json( df2, date_format="epoch", orient="records")
 
        variables_names = list(variables_norm.name)
        NOK=0
        for j in vbles:
            if j not in variables_names:
                NOK=1
                print('la variable ' + str(j) + 'no esta creada')             
        

        if NOK==0:
            # La función escribe en la variable
            print('se actualiza el valor RT de ' + str(n) + ' vbles')
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            url_completa = self.url_NX + "/api/Tags/realtime/insert"
            headers = {
                "nexustoken": self.token,
                "nexusapiversion": self.version,
                "Content-Type": "application/json",
            }
            response = requests.request("POST", url_completa, headers=headers, data=payload)
            if response.status_code == 200:
                dataReceived = "Escritura correcta"
            else:
                dataReceived = (
                    "Se ha intentado escribir en la variable "
                    + " pero la operación ha fallado" + str(response.status_code)
                )
                print(response.text.encode("utf8"))
                
        return dataReceived

"""
NexusRequest
Class definition
"""

class NexusRequest:
    uids: str
    startTs: float
    endTs: float
    dataSource: int
    resolution: int

    def __init__(self, uids, startTs, endTs, dataSource, resolution):
        """Genera la estructura a pasar al método de recuperación de variables históricas
        uids: Variables que queremos leer
        startTS: fecha de inicio en formato....
        endTS: fecha de fin en formato...
        dataSource:[ 0-->RAW, 1-->STATS_PER_HOUR, 2-->STATS_PER_DAY, 3-->STATS_PER_MONTH, 4-->TRANSIENT ]
            resolution: de 0 a 10 [ RES_30_SEC, RES_1_MIN, RES_15_MIN, RES_1_HOUR, RES_1_DAY, RES_1_MONTH, RES_1_YEAR, RES_5_MIN, RES_200_MIL, ES_500_MIL, RES_1_SEC ]
        """
        self.uids = uids
        self.startTs = time.mktime(startTs.timetuple())
        self.endTs = time.mktime(endTs.timetuple())
        self.dataSource = dataSource
        self.resolution = resolution


"""
NexusValue
Class definition
"""
class NexusValue:
    uid: str
    value: float

    def __init__(self, Uid, Value):
        self.uid = Uid
        self.value = Value


    def __repr__(self):
        return f"[uid: {self.uid}, value: {self.value}]"