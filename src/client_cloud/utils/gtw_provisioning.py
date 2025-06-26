import hashlib
import base64

from ..login.aws_login import cognito_login
from ..config import aws_config as config
from ..api import aws_api
from ..utils import decode_and_save_credentials


def provision_gateway(gateway_id, certs_path):
	print("🔐 Login con Cognito...")

	authorization = hashlib.sha256((gateway_id + config.aws['special_key']).encode('UTF-8')).hexdigest()
	print(f"Authorization (passwordRoot): \t{authorization}")

	print("🚀 Chiamata a provision_gateway...")
	response = aws_api.get_credentials(authorization, gateway_id)

	if response is None or "content" not in response:
		raise RuntimeError(f"❌ Risposta non valida o senza contenuto binario: {response}")

	# Decodifica base64 → binario
	base64_str = response["content"]
	binary_data = base64.b64decode(base64_str)

	info = decode_and_save_credentials.decode_and_save_credentials(binary_data, gateway_id, certs_path)
	print("✅ Decodifica completata:\n", info)
	return info