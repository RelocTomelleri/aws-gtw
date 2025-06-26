import os
import sys
import json
import time
import ssl
import re
import paho.mqtt.client as mqtt
from client_cloud.config import aws_config as config

# === Costanti ====
lwt_payload = {
  "state": {
    "reported": {
      "gatewayId": "123456789",
      "stage": "dev",
      "connectionStatus": "offline",
      "identityUpdate": True
    }
  }
}

# === Metodi ===

def build_topics(gateway_id, env):

    return {
        "sub": {
            "cmd_topic_exe":    config.mqtt["cmd_topic_exe"].replace("+", env, 1).replace("+", gateway_id, 1),
            "ota_topic_exe":    config.mqtt["ota_topic_exe"].replace("+", env, 1).replace("+", gateway_id, 1),
            "pt_topic_exe":     config.mqtt["pt_topic_exe"].replace("+", env, 1).replace("+", gateway_id, 1),
            "pt_topic_bin":     config.mqtt["pt_topic_bin"].replace("+", env, 1),   # pt/esc-v0/{env}/{gateway_id}/{sid}/bin
        },
        "pub": {
            "shadow_topic":     config.mqtt["shadow_topic"].replace("+", gateway_id),
            "lwt_topic":        config.mqtt["lwt_topic"].replace("+", env, 1,).replace("+", gateway_id, 1),
            "cmd_topic_rpl":    config.mqtt["cmd_topic_rpl"].replace("+", env, 1).replace("+", gateway_id, 1),
            "pt_topic_rpl":     config.mqtt["pt_topic_rpl"].replace("+", env, 1),
            "pt_topic_bin":     config.mqtt["pt_topic_bin"].replace("+", env, 1),   # pt/esc-v0/{env}/{tid}/{pt-id}/bin
            "dt_topic":         config.mqtt["dt_topic"].replace("+", env, 1).replace("+", gateway_id, 1),
        }
    }

def check_required_files(certs_path, gateway_id):
    required = [
        f"{certs_path}/{gateway_id}_credentials.json",
        f"{certs_path}/root_CA.pem",
        f"{certs_path}/{gateway_id}_cert.pem",
        f"{certs_path}/{gateway_id}_private.key"
    ]
    for file in required:
        if not os.path.isfile(file):
            print(f"❌ File mancante: {file}")
            sys.exit(1)

def load_credentials(credentials_path, gateway_id):
    try:
        with open(credentials_path, "r") as f:
            data = json.load(f)
            endpoint = data["iot_endpoint_url"].replace("mqtts://", "")
            port = data.get("iot_endpoint_port", 8883)
            client_id = data.get("client_id", gateway_id)
            return endpoint, port, client_id
    except Exception as e:
        print(f"❌ Errore caricando credenziali: {e}")
        sys.exit(1)

def setup_mqtt_client(client_id, certs_path, gateway_id, topics, gtw_instance):
    print(f"\n🛠️ MQTT Setup data:")
    print(f"\nClient id: \t{client_id}\nCerts path: \t{certs_path}\ngateway id: \t{gateway_id}\nTopics: \t{topics}\n")
    print(f"🛠️ MQTT Setup client...")

    ca_path = f"{certs_path}/root_CA.pem"
    cert_path = f"{certs_path}/{gateway_id}_cert.pem"
    key_path = f"{certs_path}/{gateway_id}_private.key"

    client = mqtt.Client(client_id=client_id, userdata=gtw_instance)
    client.on_connect = _on_connect
    client.on_message = _on_message
    client.on_subscribe = _on_subscribe

    client.pending_subscriptions = {}

    try:
        client.tls_set(
            ca_certs=ca_path,
            certfile=cert_path,
            keyfile=key_path,
            tls_version=ssl.PROTOCOL_TLSv1_2
        )
    except ssl.SSLError as e:
        print(f"❌ Errore TLS: {e}")
        sys.exit(1)

    return client

def _on_connect(client, userdata, flags, rc):
    if rc == 0:
        userdata.connection_status = True
        print("✅ Connessione MQTT riuscita")

        # Subscribe topics
        for topic in userdata.topics["sub"].values():
            reuslt, mid = client.subscribe(topic)
            client.pending_subscriptions[mid] = topic
            print(f"📩 [{mid}] Richiesta sottoscrizione a: {topic}")
    else:
        print(f"❌ Connessione fallita, codice: {rc}")


def _on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload

    if isinstance(payload, bytes):
        # Contenuto binario
        print(f"📨 Mqtt Msg Hex [{topic}]: \n{payload.hex()}")
        print(f"📨 Mqtt Msg Bin [{topic}]: \n{payload}")
    elif isinstance(payload, str):
        # Contenuto stringa
        print(f"📨 Mqtt Msg [{topic}]: \n{payload.decode()}")

    gateway = userdata

    try:
        # Decodifica payload se è in formato JSON (comandi PT)
        if topic.endswith("/app/pt/json"):
            print(f"\n⚙️\t⚙️\t⚙️\t⚙️\t⚙️")
            print(f"⚙️ \tPASS THROUGH MODE! \t⚙️")
            print(f"⚙️\t⚙️\t⚙️\t⚙️\t⚙️\n")
            data = json.loads(payload.decode('utf-8'))
            gateway.handle_pt_cmd(topic, data, client)
            return

        # Se in modalità PT e topic binario
        if gateway.pt_enabled and re.match(r'^pt/ecs-v0/.+/sid.+/bin$', topic):
            try:
                gateway.serial.send(payload)
                response = gateway.serial.receive()
                
                if response:
                    # Pubblica su MQTT (assumendo tu abbia il topic)
                    rsp_topic = gateway.topics["pub"]["pt_topic_bin"]
                    client.publish(rsp_topic, response)
                    print(f"📤 Risposta inviata su topic: {rsp_topic}")
            except Exception as e:
                print(f"❌ Errore comunicazione seriale: {e}")
            return

        # Altri messaggi generici
        print(f"⚠️ Ricevuto messaggio non gestito - Topic: {topic}, Payload: {payload}")

    except Exception as e:
         print(f"⚠️ Errore nella gestione del messaggio su {topic}: {e}")


def _on_subscribe(client, userdata, mid, granted_qos):
    topic = client.pending_subscriptions.get(mid, "<sconosciuto>")
    print(f"✅ [{mid}] Sottoscrizione completata topic: {topic}.")
    client.pending_subscriptions.pop(mid, None)


def wait_for_connection(client, endpoint, port, lwt_topic, gtw_instance, timeout=30, start_loop=True):  # Timeout: "Dopo quanto smettere di tentare la connessione"
    keepalive = int(config.mqtt["keepalive"])

    # Imposto il Last Will prima della connessione
    client.will_set(
        topic=lwt_topic,
        payload=json.dumps(lwt_payload),
        qos=1,
        retain=False
    )
    print(f"\n📝 LWT impostato su topic '{lwt_topic}' con payload:\n {lwt_payload}\n")

    print(f"🔌 Connessione a {endpoint}:{port} (keepalive={keepalive}s)...")
    try:
        client.connect(endpoint, port, keepalive=keepalive)
    except Exception as e:
        print(f"❌ Errore di connessione: {e}")
        sys.exit(1)

    if start_loop:
        client.loop_start()

    start_time = time.time()
    while not gtw_instance.connection_status and time.time() - start_time < timeout:
        time.sleep(0.1)

    if not gtw_instance.connection_status:
        print("❌ Timeout connessione MQTT")
        if start_loop:
            client.loop_stop()
        sys.exit(1)


def publish_message(client, topic, payload, qos):
    result = client.publish(topic, json.dumps(payload), qos=qos)
    if result.rc == mqtt.MQTT_ERR_SUCCESS:
        print(f"📤 Pubblicato su {topic}\nPayload: \n{payload}")
    else:
        print(f"❌ Errore pubblicazione, rc={result.rc}")

def start_loop(client):
    if client:
        client.loop_start()
        print("▶️ Ascolto avviato")

def stop_loop(client):
    if client:
        client.loop_stop()
        print("⏹️ Ascolto interrotto")

def disconnect_client(client):
    if client:
        client.disconnect()
        print("🔌 Disconnesso dal broker")
