from pymodbus.client import ModbusSerialClient
from pymodbus.exceptions import ModbusException

from crc import Calculator, Crc16

import time

class ModbusSerial:
	def __init__(self, port, baudrate=9600, parity='N', stopbits=1, bytesize=8, timeout=2):
		self.port_name = str(port)
		self.baudrate = int(baudrate)
		self.parity = str(parity)
		self.stopbits = int(stopbits)
		self.bytesize = int(bytesize)
		self.timeout = int(timeout)
		self.client = None

	def connect(self):
		try:
			print(f"🛠️ ModbusSerial Config: \n\tport: {self.port_name}\n\tbaundrate: {self.baudrate}\n\tparity: {self.parity}\n\tstopbits: {self.stopbits}\n\tbytesize: {self.bytesize}\n\ttimeout: {self.timeout}")
			self.client = ModbusSerialClient(
				port=self.port_name,
				baudrate=self.baudrate,
				parity=self.parity,
				stopbits=self.stopbits,
				bytesize=self.bytesize,
				timeout=self.timeout
			)

			if self.client.connect():
				print(f"✅ Porta seriale aperta su {self.port_name}")
			else:
				print(f"❌ Impossibile aprire la porta seriale su {self.port_name}")
				self.client = None
		except Exception as e:
			print(f"❌ Errore apertura porta seriale: {e}")
			self.client = None

	def is_open(self):
		return self.client is not None and self.client.connected

	def close(self):
		if self.is_open():
			self.client.close()
			print(f"🔌 Porta seriale {self.port_name} chiusa")

	def send(self, data: bytes):
		if not self.is_open():
			raise Exception("❌ Porta seriale non aperta")
		try:
			# Calcolo CRC16 (Modbus)
			calculator = Calculator(Crc16.MODBUS, optimized=True)
			crc = calculator.checksum(data)
			crc_bytes = crc.to_bytes(2, byteorder='little')  # Modbus usa little endian

			# Aggiungi il CRC al messaggio
			full_data = data + crc_bytes

			self.client.socket.write(full_data)
			print(f"📤 Inviato su seriale: {full_data.hex()} (CRC: {crc_bytes.hex()})")
		except Exception as e:
			print(f"❌ Errore durante l'invio: {e}")

	def receive(self, size=256):
		if not self.is_open():
			raise Exception("❌ Porta seriale non aperta")
		try:
			time.sleep(0.1)  # attesa breve per evitare letture premature
			response = self.client.socket.read(size)

			print(f"📥 [n° bytes {len(response)}] Ricevuto da seriale: \n{response.hex()}")
			return response
		except Exception as e:
			print(f"❌ Errore durante la ricezione: {e}")
			return b''