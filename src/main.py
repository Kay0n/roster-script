import argparse
import os
import sys

from dotenv import load_dotenv

import config
from kronos_driver import KronosDriver
from roster_parser import find_roster_file
from roster_validation import load_valid_roster


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Enter roster shifts from Excel into Kronos.")
    parser.add_argument("--file", help="roster .xlsx (default: the only .xlsx in the current directory)")
    parser.add_argument("--start-day-offset", type=int, default=config.START_DAY_OFFSET,
                        help="skip this many days at the start of the roster, e.g. to resume a partial run")
    parser.add_argument("--proxy", action="store_true", default=config.USE_PROXY,
                        help=f"use a SOCKS proxy on localhost:{config.PROXY_PORT}")
    parser.add_argument("--dry-run", action="store_true",
                        help="log in and check the roster, but print the entries instead of adding them")
    return parser.parse_args()


def load_credentials() -> tuple[str, str]:
    load_dotenv(override=True)
    user = os.getenv("KRONOS_USERNAME")
    password = os.getenv("KRONOS_PASSWORD")
    if user is None or password is None:
        raise Exception("KRONOS_USERNAME or KRONOS_PASSWORD enviroment vars not set")
    return user, password


def main():
    args = parse_args()
    user, password = load_credentials()

    roster_file = args.file or find_roster_file()

    # Check the sheet before opening Kronos, and get the date range from it
    roster = load_valid_roster(roster_file, config.ICU_LAYOUT, args.start_day_offset)
    if roster is None:
        sys.exit("Fix the errors above and run again.")
    start_date, end_date = roster.start_date, roster.end_date
    print(f"Roster: {roster_file} ({start_date} to {end_date})")

    input("Press ENTER to start kronos...")
    kronos = KronosDriver(args.proxy, config.PROXY_PORT)
    kronos.open_schedule(user, password, start_date, end_date)

    input("Press ENTER to ingest excel...")
    while True:
        roster = load_valid_roster(roster_file, config.ICU_LAYOUT, args.start_day_offset)
        if roster and (roster.start_date, roster.end_date) != (start_date, end_date):
            print(f"ERROR: Roster dates changed to {roster.start_date} to {roster.end_date}, "
                  f"but Kronos is showing {start_date} to {end_date}. Restart to use the new dates.")
            roster = None

        if roster is None:
            input("Fix the errors above, then press ENTER to reingest")
            continue

        roster.print_summary(kronos.get_employee_ids())
        if input("Press ENTER to continue, press SPACE then ENTER to reingest") != " ":
            break

    if args.dry_run:
        print("Dry run, would add:")
        roster.print_entries()
    else:
        input("Press ENTER to upload shifts...")
        report = kronos.add_entries_to_schedule(roster.entries)
        report.print_summary()

    input("Press ENTER to finish...")


if __name__ == "__main__":
    main()
