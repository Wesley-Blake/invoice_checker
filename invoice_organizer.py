from pathlib import Path
from shutil import move
import pandas as pd

def get_data() -> tuple[tuple[str],tuple[str]]:
    DOWNLOADS = Path.home() / "Downloads"
    WHITE_LIST = ["Invoice Number", "Status"]
    for i in DOWNLOADS.iterdir():
        if not i.name.startswith("My Invoice") and not i.name.endswith(".csv"):
            continue
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
            SystemExit(1)
        # Get paid invoices
        paid_df = df[df[WHITE_LIST[1]] == "Paid"]
        paid_tuple = tuple(paid_df[WHITE_LIST[0]])
        # Everything else is with manager.
        manager_df = df[df[WHITE_LIST[1]] != "Paid"]
        manager_tuple = tuple(manager_df[WHITE_LIST[0]])
        break
    else:
        print("No invoice doc found (.csv).")
        SystemExit(1)
    return paid_tuple, manager_tuple

def my_move(src: Path, dest: Path) -> None:
    destination = dest / src.name
    if destination.exists():
        src.unlink()
    else:
        move(src, destination)

def main():
    invoice_paid, invoice_manager = get_data()

    # Collect invoice dirs.
    with open("invoice_checker\\secrets.txt","r") as file:
        dir_invoice = Path(file.readline()[:-1])
        dir_manager = Path(file.readline()[:-1])
        dir_completed = Path(file.readline()[:-1])

    if not (
        dir_invoice.is_dir() and
        dir_manager.is_dir() and
        dir_completed.is_dir()
    ):
        print("Path errors in invoices.")
        SystemExit(1)

    for file in dir_invoice.iterdir():
        if file.is_file():
            for p in invoice_paid:
                if p in file.name:
                    print(f"Completed in dir_invoice: {file}")
                    my_move(file, dir_completed)
            for m in invoice_manager:
                if m in file.name:
                    print(f"Pending in dir_manager: {file}")
                    my_move(file, dir_manager)
    for file in dir_manager.iterdir():
        if file.is_file():
            for p in invoice_paid:
                if p in file.name:
                    print(f"Completed in dir_manager: {file}")
                    my_move(file, dir_completed)


if __name__ == '__main__':
    main()
