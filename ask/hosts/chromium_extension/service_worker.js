"use strict";
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (!message || message.channel !== "ASK_HOST" || !sender.id) return false;
  if (!["device", "inspect"].includes(message.command)) { sendResponse({ok:false,error:"Unsupported ASK host command."}); return false; }
  chrome.tabs.query({active:true,lastFocusedWindow:true}, tabs => {
    const tab=tabs[0]; if (!tab?.id) { sendResponse({ok:false,error:"No active tab is available."}); return; }
    chrome.tabs.sendMessage(tab.id,{channel:"ASK",command:message.command,id:message.id,returnType:message.returnType},response => {
      if (chrome.runtime.lastError) { sendResponse({ok:false,error:chrome.runtime.lastError.message}); return; }
      sendResponse(response || {ok:false,error:"The page did not respond."});
    });
  });
  return true;
});
