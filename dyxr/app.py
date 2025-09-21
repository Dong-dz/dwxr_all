app_id = "ttd087a63a4f8b334f01"
secret = "008882010c493efb548eaf724d94aae4991b0401"
host_ports = "localhost:8080"
is_sand_box = "0"

app_id_name = "appId"
secret_name = "secret"
host_ports_name = "hostPorts"
is_sand_box_name = "isSandBox"


def get_app_id():
    return app_id


def get_secret():
    return secret


def get_host_ports():
    return host_ports


def get_is_sand_box():
    return is_sand_box


def set_conf(name, conf):
    if name == app_id_name:
        global app_id
        app_id = conf
        return
    elif name == secret_name:
        global  secret
        secret = conf
        return
    elif name == host_ports_name:
        global host_ports
        host_ports = conf
    elif name == is_sand_box_name:
        global is_sand_box
        is_sand_box = conf
    else:
        return
