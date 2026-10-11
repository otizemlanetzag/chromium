# ASK language

ASK is a small, statement-oriented language intended for web, desktop, and mobile hosts. This branch contains an early reference implementation and a Chromium extension prototype.

## Implemented subset

- The Python standard-library interpreter is in `reference/ask.py`; launch it with `python ask.py example.ask`.
- HTML lookup by element `id` supports `clr`, `all`, `type`, `text`, `id`, and `complete`.
- The extension runner can inspect the active tab's live DOM and computed background color, report basic device/screen information, and inspect a selected local HTML file in an isolated frame.
- Both `check.connect(@API)` and `check.api(...)` have initial GET-request handling. The extension asks for access to the endpoint origin; servers may still reject cross-origin requests.
- `screen.send` displays a dialog with choices and supports a restricted SVG subset. SVG scripts, event handlers, external links, and unknown elements are discarded.
- `connection.send` can prepare a browser download from text or a file selected through the file picker. It does not silently read arbitrary local paths.
- `check.permisions` is parsed and shown for user confirmation. It does not grant permissions by itself.

## Try the extension

1. Open [the extension folder](https://github.com/otizemlanetzag/chromium/tree/ask-language-foundation/ask/hosts/chromium_extension).
2. Download the folder to your computer.
3. Visit `chrome://extensions` or `opera://extensions`, enable Developer mode, and choose **Load unpacked**.
4. Select `hosts/chromium_extension`.
5. Open a normal web page, click the ASK extension icon, enter a program, and click **Run ASK**.

For a ready-to-extract extension ZIP, open the [ASK reference tests workflow](https://github.com/otizemlanetzag/chromium/actions/workflows/ask-tests.yml), choose a successful run, and download the `ask-chromium-extension` artifact at the bottom of that run.

Example for a live page:

```ask
check.connect(@chromium)
html=[active].html
el={submit-button}
return.type=clr
return
```

Replace `submit-button` with an ID actually present on the page. For a local HTML file, choose it in the HTML source picker and use `html=[file].html`.

## Limitations — important

This is not yet a complete cross-platform runtime. The Python interpreter is not automatically connected to the extension; the extension popup runs the browser subset itself. A native-messaging or similarly authenticated host bridge is still needed for scripts launched from Python to control a browser. Desktop and mobile host adapters are not implemented. Permission declarations do not override browser or operating-system consent. Local-file delivery is represented as a download rather than direct injection into a page. Browser-internal pages may refuse inspection.

External API requests can send data to third parties. Only run scripts you trust, and do not embed private API keys in programs that other people can read. Use HTTPS endpoints whenever possible.
