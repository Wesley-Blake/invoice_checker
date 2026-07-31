"""Sort local invoice files into paid/pending/completed folders based on a status CSV.

Reads a "My Invoice*.csv" export from the Downloads folder to determine which
invoice numbers are paid versus still with the manager, then moves the matching
files between the directories configured in .env.
"""

import configparser
import filecmp
import re
from pathlib import Path
from shutil import move

import pandas as pd

DOWNLOADS = Path.home() / "Downloads"
WHITE_LIST = ["Invoice Number", "Status"]


def get_data() -> tuple[tuple[str], tuple[str]]:
    """Parse the newest "My Invoice*.csv" in Downloads into paid/pending invoice numbers.

    Returns:
        A tuple of (paid_invoice_numbers, manager_invoice_numbers), each a tuple
        of invoice number strings.

    Raises:
        SystemExit: If no matching CSV is found, or if duplicate invoice numbers
            are detected in the data.
    """
    for i in DOWNLOADS.iterdir():
        if i.name.startswith("My Invoice") and i.name.endswith(".csv"):
            # Create Dataframe.
            df = pd.read_csv(i)
            # Last row isn't needed.
            df = df.drop(df.index[-1])
            # Get rid of columns.
            df = df[WHITE_LIST]
            # Cast invoice numbers to int then to str.
            df[WHITE_LIST[0]] = df[WHITE_LIST[0]].apply(lambda x: str(int(x)))
            # Check duplicates, if their are, crash.
            duplicates = df[df[WHITE_LIST[0]].duplicated(keep=False)]
            if not duplicates.empty:
                print(f"Duplicates!: {duplicates}")
                raise SystemExit(1)
            # Get paid invoices
            paid_df = df[df[WHITE_LIST[1]] == "Paid"]
            paid_tuple = tuple(paid_df[WHITE_LIST[0]])
            # Everything else is with manager.
            manager_df = df[df[WHITE_LIST[1]] != "Paid"]
            manager_tuple = tuple(manager_df[WHITE_LIST[0]])
            break
    else:
        print("No invoice doc found (.csv).")
        raise SystemExit(1)
    return paid_tuple, manager_tuple


def _contains_invoice_number(filename: str, invoice_number: str) -> bool:
    """Return True if invoice_number appears in filename as a standalone number.

    Uses digit-boundary matching so invoice number "12" doesn't match a
    filename containing the unrelated number "1123".
    """
    pattern = rf"(?<!\d){re.escape(invoice_number)}(?!\d)"
    return re.search(pattern, filename) is not None


def my_move(src: Path, dest: Path) -> None:
    """Move src into dest.

    If a file with the same name already exists at dest, src is only
    deleted when it's byte-identical to the existing file (a genuine
    duplicate). Otherwise src is left in place and a warning is printed,
    since two different invoices can share a filename and deleting src
    would silently destroy one of them.
    """
    destination = dest / src.name
    if destination.exists():
        if filecmp.cmp(src, destination, shallow=False):
            src.unlink()
        else:
            print(
                f"Skipping move: a different file already exists at {destination}"
            )
    else:
        move(src, destination)


def main():
    """Move invoice files between the invoice, manager, and completed directories.

    Reads directory paths from .env, then relocates files in the invoice and
    manager directories according to their paid/pending status from get_data().
    """
    invoice_paid, invoice_manager = get_data()

    # Collect invoice dirs.
    cfg = configparser.ConfigParser()
    if cfg.read(".env"):
        dir_invoice = Path(cfg["invoice_checker"]["invoices_path"])
        dir_manager = Path(cfg["invoice_checker"]["manager_path"])
        dir_completed = Path(cfg["invoice_checker"]["completed_path"])
    else:
        raise FileNotFoundError(".env file not found.")

    for file in dir_manager.iterdir():
        if not file.is_file():
            continue
        for p in invoice_paid:
            if _contains_invoice_number(file.name, p):
                print(f"Completed in dir_manager: {file.name}")
                my_move(file, dir_completed)
    for file in dir_invoice.iterdir():
        if not file.is_file():
            continue
        for p in invoice_paid:
            if _contains_invoice_number(file.name, p):
                print(f"Completed in dir_invoice: {file.name}")
                my_move(file, dir_completed)
        for m in invoice_manager:
            if _contains_invoice_number(file.name, m):
                print(f"Pending in dir_manager: {file.name}")
                my_move(file, dir_manager)


if __name__ == "__main__":
    main()
