#!/usr/bin/env python3
"""
send_telegram.py — deliver a finished report PDF to Telegram as the last action of
Step 3 (Memorize), after verify_report.py has passed and the PDF is confirmed on disk.

Credentials (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID) are never stored in this plugin
directory — they live in ~/.report-generator/telegram.env, loaded at runtime. If that
file is missing, this script fails loudly rather than silently skipping delivery, so a
missing config is never mistaken for "the report wasn't ready."

Usage:
  python3 send_telegram.py <path/to/Company_Name_report.pdf> [--caption "text"]

Exit codes: 0 on confirmed delivery (Telegram API returned ok:true), 1 on any failure
(missing file, missing/invalid credentials, network/API error) — printed to stderr.
"""
import argparse
import mimetypes
import os
import sys
import urllib.request
import uuid

ENV_PATH = os.path.expanduser("~/.report-generator/telegram.env")


def load_env(path):
    values = {}
    if not os.path.exists(path):
        return values
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            values[key.strip()] = val.strip()
    return values


def build_multipart(fields, file_field, file_path):
    boundary = uuid.uuid4().hex
    parts = []
    for name, value in fields.items():
        parts.append(f"--{boundary}\r\n".encode())
        parts.append(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
        parts.append(f"{value}\r\n".encode())

    filename = os.path.basename(file_path)
    ctype = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    parts.append(f"--{boundary}\r\n".encode())
    parts.append(
        f'Content-Disposition: form-data; name="{file_field}"; filename="{filename}"\r\n'.encode()
    )
    parts.append(f"Content-Type: {ctype}\r\n\r\n".encode())
    with open(file_path, "rb") as f:
        parts.append(f.read())
    parts.append(b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode())

    body = b"".join(parts)
    headers = {"Content-Type": f"multipart/form-data; boundary={boundary}"}
    return body, headers


def send_document(pdf_path, caption=None):
    if not os.path.isfile(pdf_path):
        raise SystemExit(f"send_telegram: file not found: {pdf_path}")

    env = {**load_env(ENV_PATH), **os.environ}
    token = env.get("TELEGRAM_BOT_TOKEN")
    chat_id = env.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        raise SystemExit(
            f"send_telegram: TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID not set — "
            f"expected in {ENV_PATH} or the environment"
        )

    fields = {"chat_id": chat_id}
    if caption:
        fields["caption"] = caption[:1024]  # Telegram caption limit

    body, headers = build_multipart(fields, "document", pdf_path)
    url = f"https://api.telegram.org/bot{token}/sendDocument"
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = resp.read().decode()
    except urllib.error.HTTPError as e:
        raise SystemExit(f"send_telegram: HTTP {e.code} — {e.read().decode()}")
    except urllib.error.URLError as e:
        raise SystemExit(f"send_telegram: network error — {e.reason}")

    if '"ok":true' not in result:
        raise SystemExit(f"send_telegram: Telegram API did not confirm delivery — {result}")

    print(f"send_telegram: delivered {os.path.basename(pdf_path)} to chat {chat_id}")
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf_path")
    parser.add_argument("--caption", default=None)
    args = parser.parse_args()
    sys.exit(send_document(args.pdf_path, args.caption))


if __name__ == "__main__":
    main()
