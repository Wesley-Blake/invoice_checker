from pathlib import Path
from datetime import datetime
import win32com.client
import pandas as pd



def main(dest_dir: Path):
    if not dest_dir.exists():
        print(dest_dir)
        raise SystemExit(1)
    TODAY = datetime.now().date().isoformat()
    # Access outlook email.
    outlook = win32com.client.Dispatch("Outlook.Application")
    namespace = outlook.GetNamespace("MAPI")
    # Get to invoice mailbox.
    inbox = namespace.GetDefaultFolder(6)
    subfolder = inbox.Folders['Invoices']

    index = 0
    messages = subfolder.Items
    while index < len(messages):
        message = messages[index]
        if "Emburse Enterprise Invoice" in message.Subject:
            message.Delete()
            messages = subfolder.Items
            continue
        attachment_count = message.Attachments.Count
        if attachment_count == 0:
            print("Weird email, leaving it here.")
            continue
        if attachment_count == 1:
            attachment = message.Attachments.Item(1)
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
            messages = subfolder.Items
        index += 1


if __name__ == '__main__':
    import configparser
    cfg = configparser.ConfigParser()
    if cfg.read('.env'):
        dest_path = Path(cfg['invoice_checker']['invoices_path'])
        main(dest_path)
    else:
        raise FileNotFoundError("Destination path not found in config file.")
