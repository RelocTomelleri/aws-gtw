import os
import struct
import json
from cryptography import x509
from cryptography.hazmat.primitives import serialization


# === Costanti ===
IOT_ENDPOINT_URL_LEN      = 256
ROOT_CA_LEN               = 4096
ROOT_CA_NAME_LEN          = 128
ROOT_CA_URL_UPDATE_LEN    = 256
CLIENT_ID_LEN             = 64
USERNAME_LEN              = 128
PASSWORD_LEN              = 128
CERT_LEN                  = 4096
PRIVATE_KEY_LEN           = 4096
PASSWORD_ROTATING_LEN     = 64


# === Funzioni di parsing ===
def _read_string(data, offset, length):
    return data[offset:offset+length].split(b'\x00', 1)[0].decode(), offset + length


def _read_der_certificate(data, offset, length):
    der_bytes = data[offset:offset+length]
    cert = x509.load_der_x509_certificate(der_bytes)
    pem = cert.public_bytes(serialization.Encoding.PEM).decode()
    return pem, offset + ROOT_CA_LEN  # usa costante fissa per avanzare nel file


def _read_der_private_key(data, offset, length):
    der_bytes = data[offset:offset+length]
    key = serialization.load_der_private_key(der_bytes, password=None)
    pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    ).decode()
    return pem, offset + PRIVATE_KEY_LEN


def _read_length_prefixed_value(data, offset):
    length = struct.unpack_from("<H", data, offset)[0]
    offset += 2
    return length, offset


def parse_bin_file(filepath):
    with open(filepath, "rb") as f:
        data = f.read()

    offset = 0

    # Version
    version, offset = struct.unpack_from("<I", data, offset)[0], offset + 4
    print(f"VERSION: {version}")

    # IoT Endpoint
    iot_endpoint_url, offset = _read_string(data, offset, IOT_ENDPOINT_URL_LEN)
    # IoT Port
    iot_endpoint_port, offset = struct.unpack_from("<H", data, offset)[0], offset + 2

    # Root CA
    root_ca_len, offset = _read_length_prefixed_value(data, offset)
    root_ca_pem, offset = _read_der_certificate(data, offset, root_ca_len)

    # Info
    root_ca_name, offset = _read_string(data, offset, ROOT_CA_NAME_LEN)
    root_ca_update_url, offset = _read_string(data, offset, ROOT_CA_URL_UPDATE_LEN)
    client_id, offset = _read_string(data, offset, CLIENT_ID_LEN)

    # Skip Username and Psw
    offset += USERNAME_LEN + PASSWORD_LEN  # skip

    # Cert
    cert_len, offset = _read_length_prefixed_value(data, offset)
    certificate, offset = _read_der_certificate(data, offset, cert_len)

    # Private key
    key_len, offset = _read_length_prefixed_value(data, offset)
    private_key, offset = _read_der_private_key(data, offset, key_len)

    # Password rotating
    password_rotating, offset = _read_string(data, offset, PASSWORD_ROTATING_LEN)

    return {
        "version": version,
        "iot_endpoint_url": iot_endpoint_url,
        "iot_endpoint_port": iot_endpoint_port,
        "root_ca_pem": root_ca_pem,
        "root_ca_name": root_ca_name,
        "root_ca_update_url": root_ca_update_url,
        "client_id": client_id,
        "certificate": certificate,
        "private_key": private_key,
        "password_rotating": password_rotating
    }


# Save Json and save root_CA, cert.pem, private.key
def save_as_json(data, output_dir, gateway_id):
    os.makedirs(output_dir, exist_ok=True)

    # Open and write file
    def _write_file(path, content, label):
        if content:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"✅ {label} salvato in: {path}")
        else:
            print(f"⚠️ Nessun {label.lower()} trovato")

    # JSON
    json_path = os.path.join(output_dir, f"{gateway_id}_credentials.json")
    print(f"\n✏️ Scrivo JSON in: {json_path}")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print("✅ File JSON creato!")

    # PEM Files
    _write_file(os.path.join(output_dir, f"{gateway_id}_cert.pem"), data.get("certificate"), "Certificato")
    _write_file(os.path.join(output_dir, f"{gateway_id}_private.key"), data.get("private_key"), "Chiave privata")
    _write_file(os.path.join(output_dir, "root_CA.pem"), data.get("root_ca_pem"), "Root CA")
