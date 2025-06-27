import os
import re

def save_config_bin(path, response):
    """
    Salva il contenuto binario della risposta come file nel percorso specificato.

    :param path: Directory di destinazione.
    :param response: Oggetto di risposta con chiavi 'headers' e 'content'.
    :return: Percorso completo del file salvato, oppure None in caso di errore.
    """
    if not response or "headers" not in response or "content" not in response:
        print("❌ Risposta non valida.")
        return None

    # Estrai il nome del file da Content-Disposition
    content_disp = response["headers"].get("Content-Disposition", "")
    match = re.search(r'filename="?([^";]+)"?', content_disp)
    filename = match.group(1) if match else "default_config.bin"

    # Percorso completo del file
    os.makedirs(path, exist_ok=True)
    save_path = os.path.join(path, filename)

    # Salva il contenuto binario
    try:
        with open(save_path, "wb") as f:
            f.write(response["content"])
        print(f"✅ Config salvata in: {save_path}")
        return save_path
    except Exception as e:
        print(f"❌ Errore durante il salvataggio: {e}")
        return None
