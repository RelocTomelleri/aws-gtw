import hashlib
import base64
import os
import time
import threading
import time
import json

from client_cloud.login.aws_login import cognito_login
from client_cloud.config import aws_config
from client_cloud.api import aws_api
from client_cloud.utils import decode_and_save_credentials

from client_cloud.utils.modbus_utils import ModbusSerial

from client_cloud.utils.gtw_provisioning import provision_gateway
from client_cloud.utils.mqtt_utils import (
    build_topics,
    check_required_files,
    load_credentials,
    setup_mqtt_client,
    wait_for_connection,
    publish_message,
    start_loop,
    stop_loop,
    disconnect_client
)

class GatewayEmulator:
    def __init__(self, config_local):
        # 🔧 CONFIGURAZIONE BASE
        self.config = config_local
        self.connected = threading.Event()
        self.gateway_id = config_local.gateway_config['gateway_id']
        self.provvisioning_code = config_local.gateway_config['provvisioning_code']
        self.certs_path = f"{os.path.abspath(config_local.path_config['certs_path'])}/gateways/{self.gateway_id}"
        self.credentials_path = f"{self.certs_path}/{self.gateway_id}_credentials.json"

        # 📡 COMUNICAZIONE MODBUS (commentata per ora)
        # self.serial = ModbusSerial(
        #     port        = config_local.modbus['v_port'],
        #     baudrate    = config_local.modbus['baudrate'],
        #     parity      = config_local.modbus['parity'],
        #     stopbits    = config_local.modbus['stopbits'],
        #     bytesize    = config_local.modbus['bytesize'],
        #     timeout     = config_local.modbus['timeout']
        # )
        # self.serial.connect()

        # ☁️ CONFIGURAZIONE MQTT E AWS
        self.client = None
        self.endpoint = None
        self.port = aws_config.aws['port']
        self.env = aws_config.aws['env']
        self.client_id = self.gateway_id
        self.topics = build_topics(self.gateway_id, self.env)

    # == STATO GATEWAY ==
        # 📶 Stato della connessione e dell'applicazione
        self.connection_status = False
        self.connection_error_code = None
        self.app_state = "N/A"

        # 📦 Versioni firmware e hardware
        self.versions = {
            "fw_app": "N/A",
            "fw_wifi": "N/A",
            "hw": "N/A"
        }

        # 📍 Posizione GPS / localizzazione
        self.location = {
            "latitude": 0,
            "longitude": 0,
            "status": 0
        }

        # 🧩 Dispositivi collegati
        self.devices = {}

        # 🔄 Dati trasmissioni Pass-Through
        self.pt_enabled = False
        self.pt_id = ""
        self.sid = ""
        self.tid = ""


# === Provvisioning ===

    def provisioning(self):
        provision_gateway(self.gateway_id, self.certs_path)


# === MQTT ===

    def connect(self, start_loop=True):
        check_required_files(self.certs_path, self.gateway_id)
        self.endpoint, self.port, self.client_id = load_credentials(self.credentials_path, self.gateway_id)
        self.client = setup_mqtt_client(self.client_id, self.certs_path, self.gateway_id, self.topics, self)
        self.app_state = "init"
        wait_for_connection(self.client, self.endpoint, self.port, self.topics["pub"]["lwt_topic"], self, start_loop)

    def publish(self, topic, payload, qos=1):
        if not self.connection_status:
            print("⚠️ Impossibile pubblicare: MQTT non connesso.")
            return
        publish_message(self.client, topic, payload, qos)

    def start_listening(self):
        start_loop(self.client)

    def stop_listening(self):
        stop_loop(self.client)

    def disconnect(self):
        self.app_state = "N/A"
        disconnect_client(self.client)


# === Telemetries ===

    def send_telemetries(self, metrics: dict, device_id: str, method: str = "mqtt"):
        """
        Invia telemetrie attraverso il metodo specificato.
        :param data: Dizionario con le telemetrie
        :param method: Metodo di invio ('mqtt', 'file', ecc.)
        """

        ts = int(time.time())
        dt_payload = {
            #"gatewayId": self.gateway_id,
            "ts": ts,
            "metrics": metrics
        }
        
        if method == "mqtt":
            if not self.client:
                raise RuntimeError("❌ Client MQTT non connesso.")
            topic = self.topics["pub"]["dt_topic"].replace("+", device_id, 1)
            self.publish(topic, json.dumps(dt_payload))
            print(f"📡 Telemetria pubblicata su MQTT: {dt_payload}")

        # TODO
        # elif method == "file":

        # elif method == "http":
            
        else:
            raise ValueError(f"❌ Metodo di invio non supportato: {method}")


# === Shadow ===

    def publish_shadow_state(self, identity=True, devices=False):
        """
        Pubblica lo stato corrente (shadow) del gateway sul topic MQTT
        nel formato AWS IoT Shadow con metadata e timestamp per ogni campo.
        """

        if not self.client:
            raise RuntimeError("❌ Client MQTT non connesso.")
        
        # Timestamp corrente (esempio: UNIX time)
        now_ts = int(time.time())

        # Funzione helper ricorsiva per costruire metadata con timestamp
        def build_metadata(obj):
            if isinstance(obj, dict):
                return {k: build_metadata(v) for k, v in obj.items()}
            else:
                return {"timestamp": now_ts}

        reported_state = {
            "gatewayId": self.gateway_id,
            "stage": self.env,
            "versions": self.versions,
            "model": getattr(self.config.gateway_config, "model", "full"),
            "connectionType": getattr(self.config.gateway_config, "connection_type", ""),
            "serialConnectionType": getattr(self.config.gateway_config, "serial_conn_type", "RS485"),
            "connectionStatus": "online" if self.connection_status else "offline",
            "appState": self.app_state,
            "logState": getattr(self.config.gateway_config, "log_state", "disabled"),
            "location": self.location,
            "devices": self.devices,
            "identityUpdate": identity,
            "devicesUpdate": devices
        }

        shadow_payload = {
            "state": {
                "reported": reported_state
            },
            "metadata": {
                "reported": build_metadata(reported_state)
            },
            "version": 1,  # Se hai una versione dinamica, la metti qui
            "timestamp": now_ts
        }

        topic = self.topics["pub"]["shadow_topic"]
        self.publish(topic, shadow_payload)
        #print(f"🛰️ Shadow state pubblicato su MQTT: {json.dumps(shadow_payload, indent=2)}")


    def publish_shadow_simple(self, reported: dict):
        """
        Pubblica uno stato arbitrario come shadow AWS IoT.
        
        Parametri:
        - reported: dict contenente lo stato da pubblicare.
        - version: int opzionale, default 1. Usato per il campo 'version'.
        """

        if not self.client:
            raise RuntimeError("❌ Client MQTT non connesso.")

        now_ts = int(time.time())

        def build_metadata(obj):
            if isinstance(obj, dict):
                return {k: build_metadata(v) for k, v in obj.items()}
            return {"timestamp": now_ts}

        shadow_payload = {
            "state": {
                "reported": reported
            },
            "metadata": {
                "reported": build_metadata(reported)
            },
            "version": 2,
            "timestamp": now_ts
        }

        topic = self.topics["pub"]["shadow_topic"]
        self.publish(topic, shadow_payload)
