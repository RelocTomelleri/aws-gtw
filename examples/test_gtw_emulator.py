import sys
import os
import time

# Serve a rendere importabile il pacchetto dal path 'src/'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from client_cloud.gtw_instance import GatewayEmulator
import config_local  # o come hai chiamato il file di config


# === Variables ===
delay = 10


# === Functions ===

def set_gateway_state(gateway, state_updates):
    for key, value in state_updates.items():
        if hasattr(gateway, key):
            setattr(gateway, key, value)
        else:
            print(f"⚠️ Attenzione: gateway non ha l'attributo '{key}'")


# === Main ===

# Controlla se tra gli argomenti c'è --skip-provisioning
skip_provisioning = '--skip-provisioning' in sys.argv

gateway = GatewayEmulator(config_local)

if not skip_provisioning:
    gateway.provisioning()
gateway.connect()
gateway.start_listening()

gateway.publish_shadow_state()

# Esempio: download and save config_bin from API to config_local.path_config["config_path"]
#           configId = "configuration_id" + "_" + "version" + "_" + "revision(8 numbers)"
config_path = gateway.get_config_bin("GM1_GV1_00000001")
if config_path:
    print(f"✅ Configurazione salvata in: {config_path}")

time.sleep(delay)

# Esempio: modifico lo stato del gateway in INIT prima della pubblicazione sulla shadow
print(f"\n\n⚠️ APP-STATE -> INIT ({delay}s)\n")
state_to_set = {
    "connection_status": True,
    "app_state": "init",
    "versions": {
            "fw_app": "1.0.3",
            "fw_wifi": "1.0.3",
            "hw": "1.0"
        },
    "location": {"latitude": 45.123, "longitude": 7.456, "status": 1},
}
set_gateway_state(gateway, state_to_set)
gateway.publish_shadow_state()

time.sleep(delay)

# Esempio: modifico lo stato del gateway in RUN prima della pubblicazione sulla shadow
print(f"\n\n⚠️ APP-STATE -> RUN ({delay}s)\n")
state_to_set = {
    "connection_status": True,
    "app_state": "run",
    "versions": {
            "fw_app": "1.0.3",
            "fw_wifi": "1.0.3",
            "hw": "1.0"
        },
    "location": {"latitude": 45.123, "longitude": 7.456, "status": 1},
    "devices": {
        "PIPPO": {
          "model": "GM1",
          "version": "GV1",
          "address": "1",
          "anomaly": 0,
          "status": "online",
          "infoFw": "App2.01 Boot3.00",
          "infoHw": "Board0.02 Assembly0.01",
          "infoMore": "Exp 0:RS-485 Exp 1:-----"
        },
        "PAPERINO": {
          "model": "GM5",
          "version": "GV4",
          "address": "2",
          "anomaly": 0,
          "status": "online",
          "infoFw": "1.06",
          "infoHw": "A:B1.00A1.00 B:B1.00A1.00 C:B1.00A1.00",
          "infoMore": ""
        }
      },
}
set_gateway_state(gateway, state_to_set)
gateway.publish_shadow_state(identity=True, devices=True)

time.sleep(delay)

# Esempio: mando delle telemetrie
print(f"\n\n⚠️ SEND TELEMETRIES ({delay}s)\n")
telemetry_metrics = [
    {
        "name":"04_201",
        "type":3,
        "value":1
    },
    {
        "name":"04_73",
        "type":3,
        "value":32767
    },
    {
        "name":"04_74",
        "type":3,
        "value":-32768
    },
    {
        "name":"04_76",
        "type":3,
        "value":-32768
    },
    {
        "name":"04_75",
        "type":3,
        "value":-32768
    },
    {
        "name":"04_77",
        "type":3,
        "value":-32768
    },
    {
        "name":"04_215",
        "type":3,
        "value":3
    },
    {
        "name":"04_78",
        "type":3,
        "value":100
    },
    {
        "name":"04_79",
        "type":3,
        "value":0
    },
    {
        "name":"04_80",
        "type":3,
        "value":0
    },
    {
        "name":"04_81",
        "type":3,
        "value":32767
    },
    {
        "name":"04_82",
        "type":3,
        "value":32767
    },
    {
        "name":"04_83",
        "type":3,
        "value":32767
    },
    {
        "name":"04_200",
        "type":3,
        "value":4
    },
    {
        "name":"04_72",
        "type":3,
        "value":32767
    }
],
gateway.send_telemetries(metrics=telemetry_metrics, device_id="PIPPO", method="mqtt")

time.sleep(delay)

# Esempio: simple publish_shadow (Stato del gateway in OTA)
print(f"\n\n⚠️ APP-STATE -> OTA ({delay}s)\n")
report = {
    "gatewayId": gateway.gateway_id,
    "stage": gateway.env,
    "versions": gateway.versions,
    "identityUpdate": True,
    "devicesUpdate": False,
    "connectionStatus": True,
    "appState": "OTA"   
}
print(f"REPORT: {report}")
gateway.publish_shadow_simple(reported=report)

time.sleep(delay)

# Esempio: modifico lo stato del gateway in OFFLINE prima della pubblicazione sulla shadow
print(f"\n\n⚠️ APP-STATE -> OFFLINE ({delay}s)\n")
state_to_set = {
    "connection_status": "offline",
    "app_state": "N/A"
}
set_gateway_state(gateway, state_to_set)
gateway.publish_shadow_state()

gateway.disconnect()