# ASK language

ASK is a statement-oriented scripting language intended to bridge web, desktop, and mobile hosts. This directory contains the initial syntax reference, a Python reference interpreter, tests, and a prototype Chromium extension.

## Syntax compatibility

The first implementation preserves the spellings and shapes supplied in the initial specification, including `check.permisions`, `check.connect`, `check.api`, `connection.send`, and `screen.send`. It does not silently rename them.

## Current implementation

- Python standard-library interpreter: `reference/ask.py` (launcher: `ask.py`).
- HTML source lookup by `id`, with `return.type=clr|all|type|text|id|complete`.
- Initial parser for API calls, content sending, dialog choices, and permission declarations.
- Chromium extension prototype at `hosts/chromium_extension/` that can inspect the active tab's live DOM and computed background color through a popup.
- Smoke tests in `tests/`, with a GitHub Actions workflow.

The Python interpreter and browser extension are not yet connected automatically. Native messaging or a local authenticated bridge is needed for an ASK script to control the extension directly. Desktop/mobile host adapters and real permission enforcement are also not yet implemented.

## Run the interpreter

Requires Python 3.10+ and only the Python standard library. From this directory:

```powershell
python ask.py example.ask
```

HTML paths are resolved relative to the working directory. The Python interpreter parses HTML source and only supports a limited CSS fallback; use the Chromium extension to inspect a live page and obtain the computed background color.

## Try the Chromium extension

1. Open `chrome://extensions` or `opera://extensions`.
2. Enable **Developer mode**.
3. Click **Load unpacked** and select `hosts/chromium_extension/`.
4. Open an ordinary HTTP/HTTPS page and click the ASK extension icon.
5. Enter an element ID, select a return type, and run inspection.

## Security model

- API calls can send information to external endpoints. Run only scripts you trust.
- Do not put live API keys in source files; use environment variables or a secure host secret store.
- `yes` in `check.permisions` cannot bypass browser or operating-system consent.
- This prototype does not inject arbitrary HTML into a live page or grant device permissions.
