aws = dict(
    region          =   'eu-west-1',
    api_endpoint    =   'https://vbr6mw0eg4.execute-api.eu-west-1.amazonaws.com/dev',
    endpoint        =   'a3b2ln3xydg5pt-ats.iot.eu-west-1.amazonaws.com',
    user_pool_id    =   'eu-west-1_ZJPkoHfSt',
    client_id       =   '546nomko3ljqus3v7ugkqjckkm',
    ca_cert         =   'certs/root-CA.crt',
    special_key     =   'ELCOS_MASTERING_IOT',
    env             =   'dev',
    certs_dir       =   'certs/',
    port            =   8883,
)

user = dict(
    usr     =   'michael.tomelleri@reloc.it',
    psw     =   'Reloc@123'
)

"""
    Note: Quando si aggiunge un topic, andarlo ad inserire all'interno di mqtt_utils -> build_topics()
"""
mqtt = dict(
    keepalive       =   5,                                           # seconds
    shadow_topic    =   '$aws/things/+/shadow/update/accepted',      # $aws/things/{gateway_id}/shadow/update/accepted
    lwt_topic       =   'lwt/ecs-v0/+/+',                            # lwt/ecs-v0/{env}/{gateway_id}
    cmd_topic_exe   =   'cmd/ecs-v0/+/+/EXE/+/json',                 # cmd/ecs-v0/{env}/{gateway_id}/EXE/{resource}/json  |   Es. resource="{device-id}/custom"
    cmd_topic_rpl   =   'cmd/ecs-v0/+/+/RPL/+/json',                 # cmd/ecs-v0/{env}/{gateway_id}/RPL/{resource}/json  |   Es. resource="{device-id}/custom"
    ota_topic_exe   =   'cmd/ecs-v0/+/+/EXE/+/ota/json',             # cmd/ecs-v0/{env}/{gateway_id}/EXE/{target_definition}/ota/json    |   Es. target_definition="WIFI"
    pt_topic_exe    =   'cmd/ecs-v0/+/+/EXE/app/pt/json',            # cmd/ecs-v0/{env}/{gateway_id}/EXE/app/pt/json
    pt_topic_rpl    =   'cmd/ecs-v0/+/+/RPL/+/json',                 # cmd/ecs-v0/{env}/{tid}/RPL/{sid}/json    |   Es. tid = Tool ID   |   sid = Session ID
    pt_topic_bin    =   'pt/ecs-v0/+/+/+/bin',                       # pt/esc-v0/{env}/{cid|req-cid}/{pt-id}/bin
    dt_topic        =   'dt/ecs-v0/+/+/+/data/json'                  # dt/esc-v0/{env}/{gateway_id}/{device_id}/data/json
)
