import time
import pymysql

from config import Config


MAX_RETRIES = 60
WAIT_SECONDS = 3


def wait_for_mysql():

    print("Waiting for MySQL...")

    retries = 0

    while retries < MAX_RETRIES:

        try:

            connection = pymysql.connect(

                host=Config.DB_HOST,

                user=Config.DB_USER,

                password=Config.DB_PASSWORD,

                database=Config.DB_NAME,

                port=int(Config.DB_PORT)

            )

            connection.close()

            print("MySQL Connected.")

            return True

        except Exception as e:

            retries += 1

            print(

                f"Retry {retries}/{MAX_RETRIES} : {e}"

            )

            time.sleep(WAIT_SECONDS)

    raise Exception(

        "Unable to connect to MySQL."

    )


if __name__ == "__main__":

    wait_for_mysql()