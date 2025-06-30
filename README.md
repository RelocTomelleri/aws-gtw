[version]: 0.0.2

# 🌐 Gateway Emulator for AWS IoT

Emulatore di gateway intelligente per simulare un dispositivo embedded connesso ad AWS IoT tramite MQTT, completo di: 
- provisioning
- gestione shadow
- telemetrie
- supporto per Modbus (seriale)


*Questo progetto è pensato per sviluppatori e team QA che desiderano testare il comportamento cloud-to-edge di un gateway senza hardware fisico*

---

## 🚀 Installazione
1. Clona il repository:
```bash
git clone https://github.com/RelocTomelleri/aws-gtw.git
cd aws-gtw
```
2. Ambiente virtuale:
> È fortemente consigliato utilizzare un ambiente virtuale per isolare le dipendenze:
```bash
python3 -m venv venv
source venv/bin/activate  # Su Windows: venv\Scripts\activate
```

3. Installa dipendenze:
```bash
pip install -r requirements.txt
```

4. Prepara la configurazione:
> Copia e modifica *examples/config_local.py* per definire i parametri del gateway da emulare all'interno della tua directory:
```python
gateway_config = dict(
    gateway_id          = "123456789",
    provvisioning_code  = "987654321",
    connection_type     = "wifi",       # eth | wifi | cell
    serial_conn_type    = "RS485",
    log_state           = "enabled",    # enable | disable
    model               = "full",
)

path_config = dict(
    certs_path  = "./certs",            # salvataggio certificati
    config_path = "./gtw_configs"       # salvataggio gtw config. bin
)

modbus = dict(
    v_port      = "/dev/tty.usbserial-FT2OGIHE",
    baudrate    = 9600,
    parity      = 'E',
    stopbits    = 1,
    bytesize    = 8,
    timeout     = 4,
)
```

5. Test rapido:
```bash
python3 examples/test_gtw_emulator.py
```

6. Importazione nel tuo progetto Python
> Puoi importare l’oggetto principale nel tuo codice con:
```python
from client_cloud.gtw_instance import GatewayEmulator
import config_local

gateway = GatewayEmulator(config_local)
gateway.provisioning()      # Solo la prima volta
gateway.connect()
```

---

# 🧠 Come funziona
Il modulo principale da utilizzare è **GatewayEmulator** definito in *gtw_instance.py*. L'oggetto gestisce:
- Provisioning e certificati
- Connessione a MQTT AWS IoT
- Pubblicazione di shadow state
- Invio di telemetrie
- Interazione (opzionale) con dispositivi Modbus

*è possibile trovare un esempio di utilizzo completo all'interno di examples/test_gtw_emulator.py*

---

# ⚙️ Metodi Principali (GatewayEmulator)
| Metodo                                 | Descrizione                                             |
| -------------------------------------- | ------------------------------------------------------- |
| `provisioning()`                       | Esegue il provisioning su AWS IoT e scarica certificati |
| `connect()`             | Connette il client MQTT con i certificati salvati       |
| `disconnect()`                         | Chiude la connessione MQTT                              |
| `publish(topic, payload)`              | Pubblica un messaggio generico su MQTT                  |
| `send_telemetries(metrics, device_id)` | Invia metriche di telemetria                            |
| `publish_shadow_state()`               | Pubblica lo stato shadow completo del gateway           |
| `publish_shadow_simple(reported)`      | Pubblica uno stato shadow arbitrario                    |
| `get_config_bin(config_id)`            | Scarica una configurazione binaria dal cloud AWS        |

---

# 📡 MQTT Topics
Il sistema genera automaticamente i seguenti topic in base all’ambiente (**env**) e all’**id** del gateway:
- LWT (Last Will and Testament)
- Device Telemetry (dt)
- Shadow State
*Tutti i topic sono accessibili tramite gateway.topics.*

---
# 🧩 Supporto Modbus (opzionale)
(beta) Il modulo modbus_utils.py può essere abilitato decommentando la sezione nel costruttore della classe. È possibile simulare letture/scritture da dispositivi collegati tramite RS485.

---

## 📁 Struttura del Progetto
- project-root
    - examples/
        - config_local.py   # *File di configurazione personalizzata per l'emulatore*
        - test_gtw_emulator.py  # *Esempio di utilizzo completo dell'emulatore*
    - src/client_cloud/
        - gtw_instance.py   # *📍 Entry-point principale (GatewayEmulator)*
        - api/
            - aws_api.py    # *Implementazioni chiamate AWS API*
        - config/
            - aws_config.py # *Definizione topics, user, aws specs*
        - login/
            - aws_login.py
        - utils/    # *Funzioni di utilità per il funzionamento*

---

# 📬 Contatti
- 📧 Email: michael.tomelleri@reloc.it
- 🧑‍💻 Dev: Michael Tomelleri

---

# ℹ Utilità
> Creazione file dipendenze
```bash
pip freeze > requirements.txt
```