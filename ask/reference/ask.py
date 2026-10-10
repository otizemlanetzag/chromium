#!/usr/bin/env python3
"""Portable, standard-library reference interpreter for the initial ASK language.

This is a first milestone, not a replacement for Chromium's DOM/style engine.
It preserves the spelling of ASK commands as specified by the language author.
"""
from __future__ import annotations

import html.parser
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class AskError(Exception):
    """A user-facing ASK program error."""


@dataclass
class Element:
    tag: str
    attrs: dict[str, str | None]
    raw: str
    text: str = ""


class _HTMLReader(html.parser.HTMLParser):
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input",
            "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self, source: str):
        super().__init__(convert_charrefs=True)
        self.source = source
        self.elements: list[Element] = []
        self.stack: list[tuple[Element, int]] = []
        self.feed(source)
        self.close()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        start = self.getpos()
        line = self.source.splitlines(keepends=True)
        offset = sum(len(x) for x in line[:start[0] - 1]) + start[1]
        attrmap = dict(attrs)
        element = Element(tag, attrmap, "")
        self.elements.append(element)
        self.stack.append((element, offset))
        if tag.lower() in self.VOID:
            element.raw = self.get_starttag_text() or ""
            self.stack.pop()

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if self.stack and self.stack[-1][0].tag == tag:
            self.stack.pop()

    def handle_endtag(self, tag: str) -> None:
        for i in range(len(self.stack) - 1, -1, -1):
            element, start = self.stack[i]
            if element.tag.lower() == tag.lower():
                lines = self.source.splitlines(keepends=True)
                endpos = self.getpos()
                end = sum(len(x) for x in lines[:endpos[0] - 1]) + endpos[1]
                close = re.search(r"</\s*" + re.escape(tag) + r"\s*>", self.source[end:], re.I)
                if close:
                    end += close.end()
                element.raw = self.source[start:end]
                del self.stack[i:]
                break

    def handle_data(self, data: str) -> None:
        # Inner text belongs to the selected element and each ancestor.
        for element, _start in self.stack:
            element.text += data


def _unquote(value: str) -> str:
    value = value.strip()
    # ASK accepts both "value" and ("value") in its examples.
    if len(value) >= 2 and value[0] == "(" and value[-1] == ")":
        value = value[1:-1].strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\\"":
        return value[1:-1]
    return value


def _extract_braced(line: str, prefix: str) -> str | None:
    match = re.match(r"^\s*" + re.escape(prefix) + r"\s*=\s*\{\s*(.*?)\s*\}\s*$", line)
    return match.group(1) if match else None


def _simple_css_color(source: str, element: Element) -> str:
    # A limited fallback. Real computed style belongs to the browser host adapter.
    style = element.attrs.get("style") or ""
    declarations = {}
    for part in style.split(";"):
        if ":" in part:
            key, value = part.split(":", 1)
            declarations[key.strip().lower()] = value.strip()
    for key in ("background-color", "background"):
        if declarations.get(key):
            return declarations[key]

    rules = re.findall(r"([^{}]+)\{([^{}]*)\}", source)
    element_id = element.attrs.get("id")
    classes = set((element.attrs.get("class") or "").split())
    for selector_group, body in rules:
        selectors = [s.strip() for s in selector_group.split(",")]
        matches = False
        for selector in selectors:
            selector = re.sub(r":(?:hover|focus|active|visited|before|after)", "", selector)
            if element_id and re.fullmatch(r"#" + re.escape(element_id), selector):
                matches = True
            elif any(re.fullmatch(r"\." + re.escape(c), selector) for c in classes):
                matches = True
            elif re.fullmatch(re.escape(element.tag), selector, re.I):
                matches = True
        if matches:
            decl = {}
            for part in body.split(";"):
                if ":" in part:
                    k, v = part.split(":", 1)
                    decl[k.strip().lower()] = v.strip()
            for key in ("background-color", "background"):
                if decl.get(key):
                    return decl[key]
    return "NONE"


@dataclass
class AskRuntime:
    engine: str | None = None
    source_path: Path | None = None
    source_html: str = ""
    element: Element | None = None
    return_type: str = "text"
    device: dict[str, Any] = field(default_factory=dict)
    permissions: dict[str, str] = field(default_factory=dict)
    last_answer: str = ""

    def connect(self, target: str) -> None:
        self.engine = target

    def load_html(self, path: str) -> None:
        candidate = Path(path).expanduser()
        if not candidate.is_file():
            raise AskError(f"HTML source file not found: {candidate}")
        self.source_path = candidate
        self.source_html = candidate.read_text(encoding="utf-8")
        self.element = None

    def select_element(self, element_id: str) -> None:
        if not self.source_html:
            raise AskError("Set html=[path].html before selecting an element.")
        reader = _HTMLReader(self.source_html)
        for element in reader.elements:
            if element.attrs.get("id") == element_id:
                self.element = element
                return
        raise AskError(f"No element with id={element_id!r} was found.")

    def get_return_value(self) -> str:
        kind = self.return_type.lower()
        if kind == "complete":
            return self.source_html
        if kind == "device":
            return json.dumps(self.device, ensure_ascii=False, indent=2)
        if self.element is None:
            raise AskError("Select an element with el={element-id} before returning this value.")
        if kind == "all":
            return self.element.raw or "NONE"
        if kind == "type":
            return self.element.tag.lower()
        if kind == "text":
            text = " ".join(self.element.text.split())
            return text if text else "NONE"
        if kind == "id":
            value = self.element.attrs.get("id")
            return value if value else "NONE"
        if kind == "clr":
            return _simple_css_color(self.source_html, self.element)
        raise AskError(f"Unknown return.type: {self.return_type}")

    def send(self, path: str | None, text: str | None) -> None:
        if path:
            file_path = Path(path).expanduser()
            if not file_path.is_file():
                raise AskError(f"File to send was not found: {file_path}")
            content = file_path.read_text(encoding="utf-8")
        else:
            content = text or ""
        # Until a Chromium/desktop/mobile adapter is connected, the portable
        # reference host writes the payload to stdout instead of claiming to
        # have delivered it to a real browser window.
        sys.stdout.write(content)
        if content and not content.endswith("\n"):
            sys.stdout.write("\n")

    def call_api(self, endpoint: str, key: str, query: str) -> str:
        url = endpoint
        if query:
            url = url + ("&" if "?" in url else "?") + query.lstrip("?&")
        headers = {"Accept": "application/json, text/plain, */*"}
        if key:
            headers["Authorization"] = "Bearer " + key
        request = urllib.request.Request(url, headers=headers, method="GET")
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                data = response.read(2_000_000)
                return data.decode("utf-8", errors="replace")
        except (urllib.error.URLError, TimeoutError) as exc:
            raise AskError(f"API request failed: {exc}") from exc

    def show_dialog(self, text: str, choices: list[str]) -> str:
        # Portable fallback for hosts without a graphical adapter.
        print(text)
        for i, choice in enumerate(choices, 1):
            print(f"{i}. {choice}")
        while True:
            answer = input("ASK choice: ").strip()
            if answer in choices:
                self.last_answer = answer
                return answer
            if answer.isdigit() and 1 <= int(answer) <= len(choices):
                self.last_answer = choices[int(answer) - 1]
                return self.last_answer
            print("Choose one of: " + ", ".join(choices))


def _read_multiline(lines: list[str], start: int) -> tuple[list[str], int]:
    out: list[str] = []
    depth = 0
    begun = False
    for i in range(start, len(lines)):
        line = lines[i]
        depth += line.count("(") - line.count(")")
        if "(" in line:
            begun = True
        out.append(line)
        if begun and depth <= 0:
            return out, i + 1
    raise AskError("Unclosed parenthesized command.")


def run_program(program: str, base_dir: Path | None = None) -> str:
    rt = AskRuntime()
    lines = program.splitlines()
    i = 0
    result = ""
    base_dir = base_dir or Path.cwd()

    while i < len(lines):
        raw = lines[i]
        line = raw.strip()
        i += 1
        if not line or line.startswith("&&") or line.startswith("#"):
            continue

        if line.startswith("check.connect(@API)"):
            # The API block is parsed separately below; this branch remains
            # for exact syntax compatibility if indentation varies.
            block = []
            while i < len(lines) and (not lines[i].strip() or lines[i][:1].isspace()):
                block.append(lines[i].strip())
                i += 1
            values = {}
            for entry in block:
                m = re.match(r"^(endpointurl|key|query)\s*=\s*(.*)$", entry)
                if m:
                    values[m.group(1)] = m.group(2)
            endpoint = _unquote(values.get("endpointurl", ""))
            key = _unquote(values.get("key", ""))
            query = values.get("query", "")
            query = query.replace("path", "").strip()
            query = _unquote(query.lstrip("+ ").strip())
            result = rt.call_api(endpoint, key, query)
            print(result)
            continue

        if line.startswith("check.connect(@"):
            match = re.match(r"check\.connect\(@([A-Za-z0-9_.-]+)\)", line)
            if not match:
                raise AskError(f"Invalid check.connect syntax on line {i}.")
            rt.connect(match.group(1))
            continue

        if line == "check.type={device}":
            rt.device = {
                "runtime": "ASK Python reference interpreter",
                "platform": sys.platform,
                "python": sys.version.split()[0],
                "engine": rt.engine or "NONE",
                "screen_color_support": "unknown (requires host adapter)",
                "hardware_details": "limited by the current host adapter",
            }
            continue

        html_match = re.match(r"^html=\[(.*?)\]\.html$", line)
        if html_match:
            path = _unquote(html_match.group(1))
            candidate = Path(path)
            if not candidate.is_absolute():
                candidate = base_dir / candidate
            rt.load_html(str(candidate))
            continue

        element_id = _extract_braced(line, "el")
        if element_id is not None:
            rt.select_element(element_id)
            continue

        type_match = re.match(r"^return\.type\s*=\s*([A-Za-z_]+)\s*$", line)
        if type_match:
            rt.return_type = type_match.group(1)
            continue

        if line == "return":
            result = rt.get_return_value()
            print(result)
            continue

        if line.startswith("check.permisions:"):
            while i < len(lines) and (not lines[i].strip() or lines[i][:1].isspace()):
                permission_line = lines[i].strip()
                i += 1
                if not permission_line:
                    continue
                m = re.match(r"^([A-Za-z_]+)\s*=\s*(ask|yes|no)\s*$", permission_line)
                if not m:
                    raise AskError(f"Invalid permission declaration: {permission_line}")
                rt.permissions[m.group(1)] = m.group(2)
            continue

        if line.startswith("check.api("):
            joined = line
            while joined.count("(") > joined.count(")") and i < len(lines):
                joined += " " + lines[i].strip()
                i += 1
            params = dict(re.findall(r'(endpointurl|key|query)\s*=\s*(?:"([^"]*)"|([^,)]*))', joined))
            endpoint_match = re.search(r'endpointurl\s*=\s*"([^"]*)"', joined)
            key_match = re.search(r'key\s*=\s*"([^"]*)"', joined)
            query_match = re.search(r'query\s*=\s*(.*?)(?:\)\s*)$', joined)
            endpoint = endpoint_match.group(1) if endpoint_match else ""
            key = key_match.group(1) if key_match else ""
            query = query_match.group(1).strip() if query_match else ""
            query = re.sub(r'^path\s*\+\s*', '', query).strip()
            query = _unquote(query)
            if not endpoint:
                raise AskError("check.api requires endpointurl.")
            result = rt.call_api(endpoint, key, query)
            print(result)
            continue

        if line.startswith("connection.send"):
            block, i = _read_multiline(lines, i - 1)
            joined = "\n".join(block)
            path_match = re.search(r'connection\.send\s*\(\s*([^\\n]+)', joined)
            path = None
            text = None
            if path_match:
                candidate = path_match.group(1).strip()
                if candidate not in ('""', "or", "or \\"\\""):
                    candidate = candidate.split(" or ")[0].strip()
                    if candidate and not candidate.startswith('text'):
                        path = _unquote(candidate)
            text_match = re.search(r'text\s*"([\s\S]*?)"', joined)
            if text_match:
                text = text_match.group(1)
            if path and not Path(path).is_absolute():
                path = str(base_dir / path)
            rt.send(path, text)
            continue

        if line.startswith("screen.send"):
            block, i = _read_multiline(lines, i - 1)
            joined = "\n".join(block)
            text_match = re.search(r'"([\s\S]*?)"', joined)
            text = text_match.group(1) if text_match else ""
            choices_match = re.search(r'\[([^\]]*)\]', joined, re.S)
            choices = re.findall(r'"([^"]*)"', choices_match.group(1)) if choices_match else []
            if not choices:
                raise AskError("screen.send requires at least one choice.")
            rt.last_answer = rt.show_dialog(text, choices)
            continue

        if line.startswith("return (answer)"):
            result = rt.last_answer
            print(result)
            continue

        raise AskError(f"Unrecognized ASK statement on line {i}: {line}")

    return result


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python ask.py <program.ask>", file=sys.stderr)
        return 2
    program_path = Path(sys.argv[1]).expanduser()
    try:
        program = program_path.read_text(encoding="utf-8")
        run_program(program, program_path.resolve().parent)
    except (OSError, AskError) as exc:
        print(f"ASK error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
