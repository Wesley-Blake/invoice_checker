"""Pull invoice attachments from an Outlook mailbox into a local directory.

Scans the "Invoices" subfolder of the default Outlook inbox, saves attachments
from each message to dest_dir (prefixed with today's date), and deletes the
message afterward. Automated "Emburse Enterprise Invoice" notification emails
are deleted without processing.
"""

from datetime import datetime
from pathlib import Path

import win32com.client


def main(dest_dir: Path):
    """Save invoice attachments from the Outlook "Invoices" folder into dest_dir.

    Iterates every message in the mailbox's "Invoices" subfolder, saving each
    attachment (skipping inline images and Word temp files) as
    "{today's date} - {filename}" in dest_dir, then deletes the message. Messages
    with the subject "Emburse Enterprise Invoice" are deleted outright without
    saving attachments.

    Args:
        dest_dir: Directory to save attachments into. Must already exist.

    Raises:
        SystemExit: If dest_dir does not exist.
    """
    if not dest_dir.exists():
        print(dest_dir)
        raise SystemExit(1)
    TODAY = datetime.now().date().isoformat()
    # Access outlook email.
    outlook = win32com.client.Dispatch("Outlook.Application")
    namespace = outlook.GetNamespace("MAPI")
    # Get to invoice mailbox.
    inbox = namespace.GetDefaultFolder(6)
    subfolder = inbox.Folders["Invoices"]

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
            index += 1
            continue
        if attachment_count == 1:
            attachment = message.Attachments.Item(1)
            if attachment.FileName.startswith("~WRD") or attachment.FileName.startswith(
                "image"
            ):
                print("Weird email, leaving it here.")
                index += 1
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
        message.Delete()
        messages = subfolder.Items
        index += 1


if __name__ == "__main__":
    import configparser

    cfg = configparser.ConfigParser()
    if cfg.read(".env"):
        dest_path = Path(cfg["invoice_checker"]["invoices_path"])
        main(dest_path)
    else:
        raise FileNotFoundError("Destination path not found in config file.")
