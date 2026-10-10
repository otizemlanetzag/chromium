# ASK language

ASK is a small, statement-oriented scripting language intended to bridge web, desktop, and mobile hosts. This directory contains the initial language specification and a portable Python reference interpreter.

## Compatibility promise

The interpreter keeps the spellings and shapes from the initial ASK examples, including `check.permisions`, `check.connect`, `check.api`, `connection.send`, and `screen.send`. These spellings are part of the language surface and are not silently renamed.

## First milestone

The reference interpreter currently focuses on the source/element/return flow:

- `check.connect(@chromium)`
- `check.type={device}` (portable runtime/device information)
- `html=[path].html`
- `el={element-id}`
- `return.type=clr|all|type|text|id|complete`
- `return`

It also defines and parses the API and permissions syntax in the language documentation. Browser-computed styles, browser DOM access, native sensor permissions, native dialogs, and delivering content into a real Chromium tab require host adapters; the Python reference interpreter does not pretend to grant those platform capabilities on its own.

## Run the reference interpreter

Requires Python 3.10+ and only the Python standard library:

```powershell
python ask.py example.ask
```

Paths in `html=[...].html` are resolved relative to the current working directory. Element lookup uses the HTML `id` attribute. The `clr` return first checks the element's inline `background-color`, then inline `color`, and then simple matching CSS rules in the same HTML file. It reports `NONE` if no color declaration is found; a browser host adapter will be needed for full computed CSS.

## Security model

- API calls are external network requests and may send data to the configured endpoint. Run only ASK scripts you trust.
- API keys should be supplied via environment variables or a secure host secret store; do not commit real keys into scripts.
- `yes` in `check.permisions` is a request to the host policy, not a bypass of operating-system/browser consent.
- HTML sent to a browser must be treated as untrusted input and rendered in an appropriately isolated context.
