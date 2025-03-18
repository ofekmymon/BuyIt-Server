import random
import time
from mongomanager import users_collection


def generate_key():
    return str(int(time.time() * 1000)) + "_" + str(random.randint(100000000, 999999999))
