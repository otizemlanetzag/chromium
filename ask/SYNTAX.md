# ASK syntax reference (initial draft)

This reference records the initial syntax exactly. It is intentionally statement-oriented; ASK does not require user-defined functions.

## Engine and device

```ask
check.connect(@chromium)
check.type={device}
```

`check.connect(@chromium)` selects the Chromium host adapter. Another browser or runtime can implement the same host contract. `check.type={device}` stores runtime/device capabilities in `DEVICE`.

## HTML element inspection

```ask
html=[page.html].html
el={submit-button}
return.type=text
return
```

Element lookup is by HTML `id`. Supported initial return types:

- `clr`: the element's color/body-color value. The Python reference implementation uses a limited CSS fallback; a browser adapter should use the host's computed style.
- `all`: full source markup for the selected element.
- `type`: element kind/tag.
- `text`: text content, or `NONE` when there is no text.
- `id`: element ID, or `NONE` when absent.
- `complete`: the complete HTML source file.

## External APIs

The two forms are equivalent ways to express an API request.

Block form:

```ask
check.connect(@API):
  endpointurl=("https://example.invalid/search")
  key=("")
  query=(path)+("text")
```

Inline form:

```ask
check.api(endpointurl="https://example.invalid/search",key="", query=path + "text")
```

The endpoint's protocol determines the exact request method, query/body encoding, authentication scheme, and response format. The first reference interpreter uses GET and a Bearer token as a documented baseline; this will need a configurable API adapter for general APIs. Do not put live secrets in source files.

## Sending content to the host

```ask
check.connect(@chromium)
connection.send(path/to/file or ""
  text""
```

The host adapter should deliver a file and/or text to the connected browser/runtime. The Python reference fallback prints the content; it does not claim to control a real Chromium tab.

## Styled dialog

```ask
screen.send (
  svg
  "text"
  svg
  ["ok" | "no"]
  )
    return (answer)
```

The dialog host adapter receives the graphic payload, text, and choices. The reference interpreter provides a terminal fallback and returns the chosen value through `return (answer)`. SVG support here is for dialog graphics only; it does not imply SVG is required for HTML rendering.

## Permissions

```ask
check.permisions:
  location = ask
  camera = ask
  acelometer= yes
  microphone = no
```

Allowed policy values are `ask`, `yes`, and `no`. They express ASK's requested policy; they cannot override browser or operating-system consent, sandbox restrictions, or platform security policy.
