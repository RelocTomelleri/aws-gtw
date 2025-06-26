import os
import base64

from parse_credentials_bin import parse_bin_file, save_as_json

def decode_and_save_credentials(binary_data, gateway_id, certs_path):
    gateway_data_path = f'{certs_path}'
    certs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), gateway_data_path))
    os.makedirs(certs_dir, exist_ok=True)

    bin_path = os.path.join(certs_dir, f"{gateway_id}_credentials.bin")
    with open(bin_path, "wb") as f:
        f.write(binary_data)

    print(f"📦 File binario salvato in: {bin_path}")

    print(f"䷑ Decodifica file binario...")
    parsed_data = parse_bin_file(bin_path)
    save_as_json(parsed_data, output_dir=certs_dir, gateway_id=gateway_id)
    print(f"✅ Decodifica file binario...")

    # Se vuoi restituire anche i dati letti per usarli
    return {
        "gateway_id": gateway_id,
        "path": gateway_data_path,
        "size": len(binary_data)
    }
