import os
import yaml

def load_config(user_file=["_config.yml"], directory=".", append=[], ignore=[]):
    default_file = os.path.join(os.path.dirname(__file__), "defaults.yml")
    local_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "machine.yml"))

    conf = {}

    if os.path.exists(default_file):
        with open(default_file) as file:
            conf.update(yaml.load(file, Loader=yaml.FullLoader))

    if os.path.exists(local_file):
        with open(local_file) as file:
            conf.update(yaml.load(file, Loader=yaml.FullLoader))

    if type(user_file) is not list:
        user_file = [user_file]
    conf.update(load_user_config(user_file=user_file,
                                 directory=directory))

    if conf=={}:
        raise ValueError(
            "No configuration file found at either "
            + user_file
            + " or "
            + local_file
            + " or "
            + default_file
            + "."
        )

    for key, item in conf.items():
        if item is str:
            conf[key] = os.path.expandvars(item)

    if "logging" in conf:
        if not "level" in conf["logging"]:
            conf["logging"]["level"] = 20

        if not "filename" in conf["logging"]:
            conf["logging"]["filename"] = "log.log"
    else:
        conf["logging"] = {"level": 20, "filename": "log.log"}
    return conf

def load_user_config(user_file=["_config.yml"], directory="."):
    if type(user_file) is not list:
        user_file = [user_file]
    exist = False
    for fn in user_file:
        filename = os.path.join(os.path.expandvars(directory), fn)
        if os.path.exists(filename):
            exist = True
            break

    if exist:
        with open(filename) as file:
            conf = yaml.load(file, Loader=yaml.FullLoader)
    else:
        conf = {}

    return conf

config = load_config(user_file="_config.yml", directory=".")

    
