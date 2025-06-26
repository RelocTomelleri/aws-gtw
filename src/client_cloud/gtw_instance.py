import hashlib
import base64
import os
import time
import random
import string
import time
import json

from login.aws_login import cognito_login
from config import aws_config
from api import aws_api
from utils import decode_and_save_credentials

from utils.modbus_utils import ModbusSerial

from utils.gtw_provisioning import provision_gateway
from utils.mqtt_utils import (
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
        self.config = config_local
        self.gateway_id = config_local.gateway_config['gateway_id']
        self.provvisioning_code = config_local.gateway_config['provvisioning_code']
        self.certs_path = f"{os.path.abspath(config_local.path_config['certs_path'])}/gateways/{self.gateway_id}"

        self.serial = ModbusSerial(
            port        = config_local.modbus['v_port'],
            baudrate    = config_local.modbus['baudrate'],
            parity      = config_local.modbus['parity'],
            stopbits    = config_local.modbus['stopbits'],
            bytesize    = config_local.modbus['bytesize'],
            timeout     = config_local.modbus['timeout']
        )
        self.serial.connect()

        self.credentials_path = f"{self.certs_path}/{self.gateway_id}_credentials.json"
        self.client = None
        self.endpoint = None
        self.port = aws_config.aws['port']
        self.env = aws_config.aws['env']
        self.client_id = self.gateway_id

        self.connection_status = False
        self.app_state = "N/A"
        self.versions = {
            "fw_app": "1.0.3",
            "fw_wifi": "1.0.3",
            "hw": "1.0"
        }
        self.location = {
            "latitude": 0,
            "longitude": 0,
            "status": 0
        }

        self.topics = build_topics(self.gateway_id, self.env)

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
        self.app_state = "run"
        wait_for_connection(self.client, self.endpoint, self.port, self.topics["pub"]["lwt_topic"], self, start_loop)

    def publish(self, topic, payload, qos=1):
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

    def publish_shadow_state(self):
        """
        Pubblica lo stato corrente (shadow) del gateway sul topic MQTT
        """

        if not self.client:
            raise RuntimeError("❌ Client MQTT non connesso.")
        
        shadow_payload = {
            "gatewayId": self.gateway_id,
            "connectionStatus": self.connection_status,
            "connectionType": getattr(self.config.gateway_config, "connection_type", "ethernet"),
            "serialConnectionType": getattr(self.config.gateway_config, "serial_conn_type", "RS485"),
            "stage": self.env,
            "appState": self.app_state,
            "logState": getattr(self.config.gateway_config, "log_state", "disabled"),
            "versions": self.versions,
            "model": getattr(self.config.gateway_config, "model", "full"),
            "location": self.location,
            "identityUpdate": True,
            "devicesUpdate": False
        }

        topic = self.topics["pub"]["shadow_topic"]
        self.publish(topic, json.dumps(shadow_payload))
        print(f"🛰️ Shadow state pubblicato su MQTT: {shadow_payload}")