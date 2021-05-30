import os
import yaml


# Look for these files in the local directory
default_file = os.path.join(os.path.dirname(__file__), "defaults.yml")
local_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "machine.yml"))

# Look for this file in the working directory
user_file = '_config.yml'

defaults = {}

if os.path.exists(default_file):
    with open(default_file) as file:
        defaults.update(yaml.load(file, Loader=yaml.FullLoader))

if os.path.exists(local_file):
    with open(local_file) as file:
        defaults.update(yaml.load(file, Loader=yaml.FullLoader))

if os.path.exists(user_file):
    with open(user_file) as file:
        defaults.update(yaml.load(file, Loader=yaml.FullLoader))

if defaults=={}:
    raise ValueError(
        "No configuration file found at either "
        + user_file
        + " or "
        + local_file
        + " or "
        + default_file
        + "."
    )

