import time

from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError

from config import Config


def wait():

    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)

    retries = 30

    while retries > 0:

        try:

            conn = engine.connect()

            conn.close()

            print("Database Ready")

            return

        except OperationalError:

            retries -= 1

            print("Waiting for MySQL...")

            time.sleep(2)

    raise RuntimeError("Database never became ready.")


if __name__ == "__main__":
    wait()