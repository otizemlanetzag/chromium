(() => {
  "use strict";
  function describeElement(element) {
    if (!(element instanceof Element)) throw new Error("No element was found.");
    const style = getComputedStyle(element);
    const text = (element.innerText ?? element.textContent ?? "").trim();
    return {id: element.id || "NONE", type: element.tagName.toLowerCase(), text: text || "NONE", all: element.outerHTML, clr: style.backgroundColor || "NONE", complete: document.documentElement.outerHTML};
  }
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (!message || message.channel !== "ASK") return false;
    try {
      if (message.command === "device") {
        sendResponse({ok:true,value:{platform:navigator.userAgentData?.platform || navigator.platform || "unknown", userAgent:navigator.userAgent, language:navigator.language, screen:{width:screen.width,height:screen.height,colorDepth:screen.colorDepth,pixelDepth:screen.pixelDepth},touchPoints:navigator.maxTouchPoints || 0,engine:"chromium"}}); return false;
      }
      if (message.command === "inspect") {
        const id=String(message.id ?? ""); if (!id) throw new Error("ASK inspect requires an element id.");
        const element=document.getElementById(id); if (!element) throw new Error("No element with id="+JSON.stringify(id)+" was found.");
        const data=describeElement(element); const allowed=new Set(["clr","all","type","text","id","complete"]); const type=String(message.returnType || "all").toLowerCase();
        if (!allowed.has(type)) throw new Error("Unsupported return.type: "+type); sendResponse({ok:true,value:data[type]}); return false;
      }
      throw new Error("Unsupported ASK host command.");
    } catch(error) { sendResponse({ok:false,error:String(error?.message || error)}); return false; }
  });
})();
