"""Pull invoice attachments from an Outlook mailbox into a local directory.

Scans the "Invoices" subfolder of the default Outlook inbox, saves attachments
from each message to dest_dir (prefixed with today's date), and deletes the
message afterward. Automated "Emburse Enterprise Invoice" notification emails
are deleted without processing.
"""

import datetime
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
    TODAY = datetime.datetime.now(tz=datetime.UTC).date().isoformat()
    # Access outlook email.
    outlook = win32com.client.Dispatch("Outlook.Application")
    namespace = outlook.GetNamespace("MAPI")
    # Get to invoice mailbox.
    inbox = namespace.GetDefaultFolder(6)
    subfolder = inbox.Folders["Invoices"]

    no_attachement_count = 0
    messages = subfolder.Items
    while no_attachement_count < len(messages):
        current_message = len(messages) - no_attachement_count
        message = messages[current_message]
        if "Emburse Enterprise Invoice" in message.Subject:
            message.Delete()
            messages = subfolder.Items
            continue
        attachment_count = message.Attachments.Count
        if attachment_count == 0:
            print("No attachments in email, leaving it here.")
            no_attachement_count += 1
            continue
        if attachment_count == 1:
            attachment = message.Attachments.Item(1)
            if not attachment.FileName.lower().endswith(".pdf"):
                print(
                    f"Attachments exists, but not PDF{attachment.FileName}, leaving it here."
                )
                no_attachement_count += 1
                continue

        save_failed = False
        for i in range(1, attachment_count + 1):
            attachment = message.Attachments.Item(i)
            if not attachment.FileName.lower().endswith(".pdf"):
                no_attachement_count += 1
                continue
            # Strip any directory components so a crafted attachment
            # filename can't write outside dest_dir.
            safe_name = Path(attachment.FileName).name.lower()
            if not safe_name:
                continue
            file_path = dest_dir / (f"{TODAY} - {safe_name}")
            if file_path.exists():
                print(f"Invoice exits!: {attachment.FileName}")
                continue
            try:
                attachment.SaveAsFile(file_path)
            except Exception as e:
                print(f"Failed to save attachment {attachment.FileName}: {e}")
                save_failed = True
        if save_failed:
            # Leave the message in place so a failed save doesn't lose
            # the only copy of the attachment.
            continue
        message.Delete()
        messages = subfolder.Items


if __name__ == "__main__":
    import configparser

    cfg = configparser.ConfigParser()
    if cfg.read(".env"):
        dest_path = Path(cfg["invoice_checker"]["invoices_path"])
        main(dest_path)
    else:
        raise FileNotFoundError("Destination path not found in config file.")
