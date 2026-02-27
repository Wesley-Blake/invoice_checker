from pathlib import Path
from datetime import datetime
import win32com.client
import pandas as pd


def main(dest_dir: Path):
    if not dest_dir.exists():
        print(dest_dir)
        SystemExit(1)
    TODAY = datetime.now().date().isoformat()
    # Access outlook eamil.
    outlook = win32com.client.Dispatch("Outlook.Application")
    namespace = outlook.GetNamespace("MAPI")
    # Get to invoice mailbox.
    inbox = namespace.GetDefaultFolder(6)
    subfolder = inbox.Folders['Invoices']

    messages = subfolder.Items
    for message in messages:
        attachment_count = message.Attachments.Count
        if attachment_count == 0:
            print("Weird email, leaving it here.")
            continue
        if attachment_count == 1:
            if (
                attachment.FileName.startswith("~WRD") or
                attachment.FileName.startswith("image")
            ):
                print("Weird email, leaving it here.")
                continue

        for i in range(1, attachment_count + 1):
            attachment = message.Attachments.Item(i)
            if attachment.FileName.startswith("~WRD"):
                continue
            if attachment.FileName.startswith("image"):
                continue
            file_path = dest_dir / (f"{TODAY} - {attachment.FileName.lower()}")
            if file_path.exists():
                print(f"Invoice exits!: {attachment.FileName}")
            else:
                attachment.SaveAsFile(file_path)
        else:
            message.Delete()


if __name__ == '__main__':
    with open("invoice_checker\\secrets.txt", "r") as file:
        destination_path = Path(file.readline()[:-1])
        main(destination_path)
