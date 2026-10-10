"use strict";

const inspectButton = document.getElementById("inspect");
const status = document.getElementById("status");
const result = document.getElementById("result");

inspectButton.addEventListener("click", async () => {
  const id = document.getElementById("elementId").value.trim();
  const returnType = document.getElementById("returnType").value;
  if (returnType !== "complete" && !id) {
    status.textContent = "Enter an element ID first.";
    return;
  }

  inspectButton.disabled = true;
  status.textContent = "Inspecting active tab…";
  result.textContent = "";
  try {
    const [tab] = await chrome.tabs.query({active: true, lastFocusedWindow: true});
    if (!tab?.id) throw new Error("No active tab is available.");
    const execution = await chrome.scripting.executeScript({
      target: {tabId: tab.id},
      args: [id, returnType],
      func: (elementId, type) => {
        if (type === "complete") return document.documentElement.outerHTML;
        const element = document.getElementById(elementId);
        if (!element) throw new Error("No element with id=" + JSON.stringify(elementId) + " was found.");
        switch (type) {
          case "clr": return getComputedStyle(element).backgroundColor || "NONE";
          case "all": return element.outerHTML;
          case "type": return element.tagName.toLowerCase();
          case "text": {
            const value = (element.innerText ?? element.textContent ?? "").trim();
            return value || "NONE";
          }
          case "id": return element.id || "NONE";
          default: throw new Error("Unsupported return.type: " + type);
        }
      }
    });
    const value = execution?.[0]?.result;
    status.textContent = "Success";
    result.textContent = typeof value === "string" ? value : JSON.stringify(value, null, 2);
  } catch (error) {
    status.textContent = "Could not inspect this page.";
    result.textContent = String(error?.message || error);
  } finally {
    inspectButton.disabled = false;
  }
});
