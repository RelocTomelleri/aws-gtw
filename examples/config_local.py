gateway_config = dict(
    gateway_id          = "123456789",
    provvisioning_code  = "987654321",
    connection_type     = "wifi",   # eth | wifi | cell
    serial_conn_type    = "RS485",
    log_state           = "enabled",
    model               = "full",
)

path_config = dict(
    certs_path  = "./certs",  # dove salvare i certificati
    config_path = "./gtw_configs"
)

modbus = dict(
    v_port      = "/dev/tty.usbserial-FT2OGIHE",
    baudrate    = 9600,
    parity      = 'E',
    stopbits    = 1,
    bytesize    = 8,
    timeout     = 4,
)