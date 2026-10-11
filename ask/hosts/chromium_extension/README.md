# ASK Chromium host adapter (prototype)

This extension reads the active page's live DOM and computed CSS rather than parsing an HTML source file.

## Supported operations

- `clr`: return `getComputedStyle(element).backgroundColor`.
- `all`: return `element.outerHTML`.
- `type`: return the element tag name in lowercase.
- `text`: return text content, or `NONE` if empty.
- `id`: return the element ID.
- `complete`: return the current document's HTML serialization.

## Try it

1. Open `chrome://extensions` or `opera://extensions`.
2. Enable **Developer mode**.
3. Click **Load unpacked** and select this directory.
4. Open a normal HTTP/HTTPS page.
5. Click the ASK extension icon, enter an element ID, choose `return.type`, and click **Run inspection**.

The extension requests only `activeTab` and `scripting`; it does not need permanent access to every website. Browser-internal and protected pages cannot be inspected.

## ASK source syntax

```ask
check.connect(@chromium)
html=[page].html
el={submit-button}
return.type=clr
return
```

The Python interpreter and extension are not yet connected automatically. A local authenticated bridge or Chromium native-messaging host is still needed so ASK scripts can dispatch these operations directly.

## Safety and limitations

- It does not execute arbitrary ASK programs or inject arbitrary HTML into the current website.
- It does not grant location, camera, microphone, or sensor permissions.
- API calls, dialogs, file delivery, and permission declarations still need host-specific implementations for full integration.
- `complete` returns the live DOM serialization, not the original network response bytes or source of every external resource.
