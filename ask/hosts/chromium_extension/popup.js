"use strict";
const sourceBox=document.getElementById("source"), runButton=document.getElementById("run"), status=document.getElementById("status"), resultBox=document.getElementById("result");
async function activeTab(){const [tab]=await chrome.tabs.query({active:true,lastFocusedWindow:true});if(!tab?.id)throw new Error("No active tab is available.");return tab;}
async function inspectActivePage(id,type){
 const tab=await activeTab();
 const r=await chrome.scripting.executeScript({target:{tabId:tab.id},args:[id,type],func:(elementId,t)=>{
  if(t==="device")return {platform:navigator.userAgentData?.platform||navigator.platform||"unknown",userAgent:navigator.userAgent,language:navigator.language,screen:{width:screen.width,height:screen.height,colorDepth:screen.colorDepth,pixelDepth:screen.pixelDepth},touchPoints:navigator.maxTouchPoints||0,engine:"chromium"};
  if(t==="complete")return document.documentElement.outerHTML;
  const e=document.getElementById(elementId);if(!e)throw new Error("No element with id="+JSON.stringify(elementId)+" was found.");
  switch(t){case "clr":return getComputedStyle(e).backgroundColor||"NONE";case "all":return e.outerHTML;case "type":return e.tagName.toLowerCase();case "text":return (e.innerText??e.textContent??"").trim()||"NONE";case "id":return e.id||"NONE";default:throw new Error("Unsupported return.type: "+t);}
 }});
 return r?.[0]?.result;
}
async function inspectSourceDocument(source,id,type){
 const frame=document.createElement("iframe");frame.setAttribute("sandbox","allow-same-origin");frame.style.display="none";
 const safeSource='<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; img-src data:; style-src \'unsafe-inline\' data:; font-src data:">'+source;
 frame.srcdoc=safeSource;document.body.append(frame);
 try{
  await new Promise((resolve,reject)=>{frame.onload=resolve;frame.onerror=()=>reject(new Error("Could not load selected HTML."));});
  const d=frame.contentDocument;if(type==="complete")return d.documentElement.outerHTML;
  const e=d.getElementById(id);if(!e)throw new Error("No element with id="+JSON.stringify(id)+" was found in the selected HTML file.");
  switch(type){case "clr":return frame.contentWindow.getComputedStyle(e).backgroundColor||"NONE";case "all":return e.outerHTML;case "type":return e.tagName.toLowerCase();case "text":return (e.innerText??e.textContent??"").trim()||"NONE";case "id":return e.id||"NONE";default:throw new Error("Unsupported return.type: "+type);}
 }finally{frame.remove();}
}
function showDialog(text,choices){return new Promise(resolve=>{const overlay=document.createElement("div");Object.assign(overlay.style,{position:"fixed",inset:"0",zIndex:"9999",background:"rgba(0,0,0,.55)",display:"grid",placeItems:"center",padding:"14px"});const panel=document.createElement("div");Object.assign(panel.style,{width:"100%",boxSizing:"border-box",padding:"16px",borderRadius:"12px",background:"Canvas",color:"CanvasText"});const msg=document.createElement("div");msg.textContent=text;msg.style.marginBottom="16px";panel.append(msg);const row=document.createElement("div");Object.assign(row.style,{display:"flex",gap:"8px",flexWrap:"wrap"});for(const c of choices){const b=document.createElement("button");b.textContent=c;b.addEventListener("click",()=>{overlay.remove();resolve(c);});row.append(b);}panel.append(row);overlay.append(panel);document.body.append(overlay);});}
function qvalue(s,n){const m=s.match(new RegExp(n+"\\s*=\\s*\\(?[\"']([^\"']*)[\"']\\)?"));return m?m[1]:"";}
async function apiCall(endpoint,key,query){if(!endpoint)throw new Error("API endpointurl is required.");const u=new URL(endpoint);if(query)u.searchParams.set("q",query);const h={Accept:"application/json, text/plain, */*"};if(key)h.Authorization="Bearer "+key;const r=await fetch(u,{method:"GET",headers:h});const t=await r.text();if(!r.ok)throw new Error("API returned HTTP "+r.status+": "+t.slice(0,300));return t;}
async function runAsk(program){
 const lines=program.split(/\r?\n/);let engine="",returnType="text",id="",device=null,answer="",apiResponse="",sent="",permissions={},sourceMode="active",sourceHtml=null;const out=[];
 for(let i=0;i<lines.length;i++){
  const line=lines[i].trim();if(!line||line.startsWith("#")||line.startsWith("&&"))continue;
  if(line.startsWith("check.connect(@API)")){const block=[];while(i+1<lines.length&&(!lines[i+1].trim()||/^\s/.test(lines[i+1])))block.push(lines[++i].trim());const ep=qvalue(block.find(x=>x.startsWith("endpointurl"))||"","endpointurl"),key=qvalue(block.find(x=>x.startsWith("key"))||"","key"),ql=block.find(x=>x.startsWith("query"))||"",qm=ql.match(/\+\s*[\"']([^\"']*)[\"']/);apiResponse=await apiCall(ep,key,qm?qm[1]:"");continue;}
  if(line.startsWith("check.api(")){const ep=qvalue(line,"endpointurl"),key=qvalue(line,"key"),qm=line.match(/query\s*=\s*path\s*\+\s*[\"']([^\"']*)[\"']/);apiResponse=await apiCall(ep,key,qm?qm[1]:"");continue;}
  if(line.startsWith("check.connect(@")){const m=line.match(/^check\.connect\(@([A-Za-z0-9_.-]+)\)/);if(!m)throw new Error("Invalid check.connect at line "+(i+1));engine=m[1];continue;}
  if(line==="check.type={device}"){device=await inspectActivePage("","device");continue;}
  if(line.startsWith("html=[")){const m=line.match(/^html=\[(.*?)\]\.html$/);if(!m)throw new Error("Invalid html source at line "+(i+1));if(m[1]==="active"){sourceMode="active";sourceHtml=null;}else if(m[1]==="file"){const file=document.getElementById("htmlFile").files[0];if(!file)throw new Error("Choose an HTML file for html=[file].html first.");sourceHtml=await file.text();sourceMode="file";}else throw new Error("Use html=[file].html or html=[active].html.");continue;}
  const em=line.match(/^el=\{\s*(.*?)\s*\}$/);if(em){id=em[1];continue;}
  const tm=line.match(/^return\.type\s*=\s*([A-Za-z_]+)$/);if(tm){returnType=tm[1].toLowerCase();continue;}
  if(line.startsWith("check.permisions:")){while(i+1<lines.length&&(!lines[i+1].trim()||/^\s/.test(lines[i+1]))){const p=lines[++i].trim();if(!p)continue;const m=p.match(/^([A-Za-z_]+)\s*=\s*(ask|yes|no)$/);if(!m)throw new Error("Invalid permission declaration: "+p);permissions[m[1]]=m[2];}continue;}
  if(line.startsWith("screen.send")){const block=[line];while(i+1<lines.length&&!block.join("\n").includes(")"))block.push(lines[++i]);const joined=block.join("\n"),text=(joined.match(/"([^"]*)"/)||[])[1]||"",cm=joined.match(/\[([^\]]*)\]/s),choices=cm?Array.from(cm[1].matchAll(/"([^"]*)"/g),m=>m[1]):[];if(!choices.length)throw new Error("screen.send needs at least one choice.");answer=await showDialog(text,choices);continue;}
  if(line.startsWith("connection.send")){const block=[line];while(i+1<lines.length&&(!lines[i+1].trim()||/^\\s/.test(lines[i+1])))block.push(lines[++i]);const m=block.join("\\n").match(/text\\s*"([\\s\\S]*?)"/);if(!m)throw new Error("connection.send currently supports text; local file delivery needs a native host.");sent=m[1];out.push({connection_send:sent});continue;}
  if(line==="return (answer)"){out.push(answer||"NONE");continue;}
  if(line==="return"){if(returnType==="device")out.push(device||"NONE");else if(returnType==="api")out.push(apiResponse||"NONE");else if(returnType==="answer")out.push(answer||"NONE");else if(returnType==="permissions")out.push(permissions);else if(returnType==="sent")out.push(sent||"NONE");else out.push(sourceMode==="file"?await inspectSourceDocument(sourceHtml,id,returnType):await inspectActivePage(id,returnType));continue;}
  throw new Error("Unrecognized ASK statement at line "+(i+1)+": "+line);
 }
 if(!out.length)out.push({engine:engine||"NONE",device:device||"NONE",permissions});return out;
}
runButton.addEventListener("click",async()=>{runButton.disabled=true;status.textContent="Running ASK…";resultBox.textContent="";try{const out=await runAsk(sourceBox.value);status.textContent="Finished";resultBox.textContent=out.map(v=>typeof v==="string"?v:JSON.stringify(v,null,2)).join("\n\n");}catch(e){status.textContent="ASK error";resultBox.textContent=String(e?.message||e);}finally{runButton.disabled=false;}});
