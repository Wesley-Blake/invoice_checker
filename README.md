# Invoice Checker

Small pair of scripts for handling invoices on Windows: one collects invoice
attachments out of Outlook, the other sorts them into the right folder based
on their paid/pending status.

## Scripts

### `invoice_collector.py`

Connects to the local Outlook client and scans the `Invoices` subfolder of
the default inbox. For each message:

- If the subject is `Emburse Enterprise Invoice`, the message is deleted
  without further processing.
- Otherwise, every attachment (except inline images and Word temp files like
  `~WRD...`) is saved to the configured invoices directory as
  `{today's date} - {filename}`, and the message is then deleted.

Run it directly:

```
python invoice_collector.py
```

### `invoice_organizer.py`

Looks in your `Downloads` folder for a CSV named `My Invoice*.csv` (exported
from the invoice system), and uses its `Invoice Number` / `Status` columns to
figure out which invoices are `Paid` and which are still pending. It then
moves matching files between the configured directories:

- Files in the invoices directory that are `Paid` move to the completed
  directory; pending ones move to the manager directory.
- Files in the manager directory that are `Paid` move to the completed
  directory.
- If a file with the same name already exists at the destination, the source
  file is deleted instead of moved.

The script exits with an error if no matching CSV is found or if the CSV
contains duplicate invoice numbers.

Run it directly:

```
python invoice_organizer.py
```

## Configuration

Both scripts read directory paths from a `.env` file (INI format) in the
project root, which is git-ignored since it contains local file-system paths:

```ini
[invoice_checker]
invoices_path = C:\path\to\invoices
manager_path = C:\path\to\manager
completed_path = C:\path\to\completed
```

- `invoices_path` — where `invoice_collector.py` saves attachments, and where
  `invoice_organizer.py` looks for files to sort.
- `manager_path` — where pending invoices are moved for manager review.
- `completed_path` — where paid invoices end up.

## Requirements

- Windows, with Outlook installed and configured (for `invoice_collector.py`,
  via `pywin32`).
- Python dependencies: `pandas`, `pywin32`.

## Notes

- `invoice_collector.py` must be run on a machine with a logged-in Outlook
  session; it uses COM automation and will not work headless.
- Neither script currently has automated tests; verify behavior against a
  small sample of files before relying on it for bulk moves.
