import secrets
import string
from typing import Dict


def generate_random_alphanumeric_string(length=6):
    characters = string.ascii_letters + string.digits
    random_string = "".join(secrets.choice(characters) for _ in range(length))
    return random_string


def set_dict_attr(dict_val: Dict, obj):
    for key, value in dict_val.items():
        setattr(obj, key, value)
    return obj
