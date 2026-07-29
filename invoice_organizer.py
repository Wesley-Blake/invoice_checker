"""Sort local invoice files into paid/pending/completed folders based on a status CSV.

Reads a "My Invoice*.csv" export from the Downloads folder to determine which
invoice numbers are paid versus still with the manager, then moves the matching
files between the directories configured in .env.
"""

import configparser
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


def my_move(src: Path, dest: Path) -> None:
    """Move src into dest, or delete src if a file with the same name already exists there."""
    destination = dest / src.name
    if destination.exists():
        src.unlink()
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
            if p in file.name:
                print(f"Completed in dir_manager: {file.name}")
                my_move(file, dir_completed)
    for file in dir_invoice.iterdir():
        if not file.is_file():
            continue
        for p in invoice_paid:
            if p in file.name:
                print(f"Completed in dir_invoice: {file.name}")
                my_move(file, dir_completed)
        for m in invoice_manager:
            if m in file.name:
                print(f"Pending in dir_manager: {file.name}")
                my_move(file, dir_manager)


if __name__ == "__main__":
    main()
