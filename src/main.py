import os

from dotenv import load_dotenv

import config
from kronos_driver import KronosDriver
from roster_parser import load_roster


def load_credentials() -> tuple[str, str]:
    load_dotenv(override=True)
    user = os.getenv("KRONOS_USERNAME")
    password = os.getenv("KRONOS_PASSWORD")
    if user is None or password is None:
        raise Exception("KRONOS_USERNAME or KRONOS_PASSWORD enviroment vars not set")
    return user, password


def main():
    user, password = load_credentials()

    input("Press ENTER to start kronos...")
    kronos = KronosDriver(config.USE_PROXY, config.PROXY_PORT)
    kronos.open_schedule(user, password, config.START_DATE, config.END_DATE)

    input("Press ENTER to ingest excel...")
    while True:
        roster = load_roster(config.ICU_LAYOUT, config.START_DAY_OFFSET)
        roster.print_summary(kronos.get_employee_ids())
        if input("Press ENTER to continue, press SPACE then ENTER to reingest") != " ":
            break

    input("Press ENTER to upload shifts...")
    kronos.add_entries_to_schedule(roster.entries)

    input("Press ENTER to finish...")


if __name__ == "__main__":
    main()
