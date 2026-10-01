const $ = id => document.getElementById(id);
let state, trace, caseIndex = 0, step = 0, history = [], busy = false, runRevision = "";
let submittedQuestions = [], questionCursor = 0, questionDraft = "";
const el = (tag, text, cls) => { const n = document.createElement(tag); if (text !== undefined) n.textContent = text; if (cls) n.className = cls; return n; };
function status(id, text, error = false) { $(id).textContent = text; $(id).classList.toggle("error", error); }
async function api(path, body, method = "POST", retry = true) {
  const response = await fetch(`/demo/api/${path}`, {method, headers: {"Content-Type":"application/json", "X-Demo-Token": state?.token || ""}, ...(body === undefined ? {} : {body: JSON.stringify(body)})});
  const data = await response.json();
  if (response.status === 403 && retry && typeof data.detail === "string" && data.detail.includes("expired")) { state = await api("status", undefined, "GET", false); return api(path, body, method, false); }
  if (!response.ok) throw new Error(typeof data.detail === "string" ? data.detail : "Check the code, input values, and question length.");
  return data;
}
function input() {
  const raw = $("values").value.trim();
  const parts = raw ? raw.split(",").map(v=>v.trim()) : [];
  if (parts.some(v=>!/^[-+]?\d+$/.test(v)) || !/^[-+]?\d+$/.test($("target").value.trim())) throw new Error("Use comma-separated integers and an integer target.");
  const values = parts.map(Number), target = Number($("target").value);
  if (values.length > 24 || [...values,target].some(v=>Math.abs(v)>999)) throw new Error("Use up to 24 integers between -999 and 999.");
  return {code:$("code").value, values, target};
}
function revision() { return JSON.stringify(input()); }
function markChanged() { if (!trace) return; $("score").textContent = "Run again"; status("runStatus", "Code or input changed. Run again to refresh the output and trace."); $("activeLine").textContent="Trace is out of date. Run code again."; $("array").replaceChildren(); $("variables").replaceChildren(); $("prev").disabled=true; $("next").disabled=true; }
function renderTrace() {
  const current = trace.cases[caseIndex], frames = current.frames;
  $("array").replaceChildren(); $("variables").replaceChildren();
  if (!frames.length) { $("stepLabel").textContent="No trace"; $("activeLine").textContent=current.error || "No recorded step."; $("traceMessage").textContent="Check the AVP code and run it again."; $("prev").disabled=true; $("next").disabled=true; return; }
  step = Math.max(0,Math.min(step,frames.length-1)); const frame=frames[step];
  $("stepLabel").textContent=`${step+1} / ${frames.length}`;
  for (const values of Object.values(frame.arrays)) values.forEach((value,i)=>{const cell=el("div",undefined,"cell"+(frame.variables.i===i?" current":""));cell.append(el("b",String(value)),el("span",`[${i}]`));$("array").append(cell);});
  for (const [key,value] of Object.entries(frame.variables)) $("variables").append(el("span",`${key} = ${value}`));
  $("activeLine").textContent=`Line ${frame.current_line} · after execution\n${frame.code.split("\n")[frame.current_line-1].trim()}`;
  $("traceMessage").textContent=`${current.name} · target ${current.target} · ${frame.recent_events.at(-1)?.description || ""}`;
  $("prev").disabled=step===0; $("next").disabled=step===frames.length-1;
}
function renderResults() {
  const table=el("table",undefined,"results-table"), head=el("thead"), row=el("tr");
  for(const name of ["Case","Expected","Actual","Result"]) row.append(el("th",name)); head.append(row);table.append(head); const body=el("tbody");
  trace.cases.forEach((r,i)=>{const row=el("tr",undefined,i===caseIndex?"selected":"");const td=el("td"),button=el("button",r.name);button.addEventListener("click",()=>{if(runRevision!==revision()) return;caseIndex=i;step=r.frames.length-1;renderResults();renderTrace();});td.append(button);row.append(td,el("td",String(r.expected)),el("td",r.error?"Error":String(r.actual)),el("td",r.passed?"Pass":"Fail",r.passed?"success":"error"));body.append(row);});table.append(body);$("results").replaceChildren(table);
  const current=trace.cases[caseIndex];if(current.error)$("results").append(el("p",current.error,"result-error"));
  $("score").textContent=`${trace.passed} / ${trace.total} tests passed`;
}
async function runCode() {
  $("run").disabled=true;
  try { const request=input(); const result=await api("run",request); trace=result;runRevision=JSON.stringify(request);caseIndex=trace.cases[0].passed ? Math.max(0,trace.cases.findIndex(r=>!r.passed)) : 0;step=trace.cases[caseIndex].frames.length-1;renderResults();renderTrace();status("runStatus",`${trace.engine}: your edited code ran on the shown inputs.`);return true; }
  catch(error){status("runStatus",error.message,true);return false;}
  finally{$("run").disabled=false;}
}
function boundedHistory() { const turns=history.slice(-8); while(turns.reduce((n,t)=>n+t.content.length,0)>10000) turns.splice(0,2); return turns; }
function addMessage(role,text,response) {
  if(!history.length) $("conversation").replaceChildren();
  const item=el("article",undefined,`message ${role}`);item.append(el("div",role==="user"?"You":"AVP Tutor","message-label"),el("div",text,"message-text"));
  if(response){item.append(el("p",`${response.model} · ${(response.latency_ms/1000).toFixed(1)}s · ${response.skill.replace(".md","")}`,"meta"));const details=el("details"),summary=el("summary","References and attached context");details.append(summary,el("p",`Execution: ${response.execution.engine}\nAttached case: ${response.execution.selected_case}\nCode: ${response.execution.code_sha256.slice(0,12)}\nFixed harness: ${response.harness_version}`));const plan=response.teaching_plan;details.append(el("p",`Question: ${plan.question}\nHelp requested: ${plan.intent}\nQuestion focus: ${plan.question_focus}\nSelection basis: ${plan.selection_basis}\nExplanation method: ${plan.explanation_method}`));for(const c of plan.candidate_confusions)details.append(el("p",`Possible confusion: ${c.title}\nEffect on the solution: ${c.impact}`));details.append(el("p",`Runner observations:\n${plan.observations.join("\n")}`),el("p",plan.evidence.limits),el("p",plan.limits));for(const source of response.sources)details.append(el("p",`[${source.id}] ${source.text}`));for(const method of response.methods)details.append(el("p",`[${method.id}] ${method.title}\n${method.basis}\n${method.status}`));details.append(el("p",`Method retrieval: local TF-IDF vectors\nLearning notes recalled: ${response.memory_used.length}`));for(const note of response.memory_used)details.append(el("p",note.text));item.append(details);for(const warning of response.warnings)item.append(el("p",warning,"small error"));}
  $("conversation").append(item);$("conversation").scrollTop=$("conversation").scrollHeight;
}
async function ask(event) {
  event.preventDefault(); if(busy)return;
  const question=$("question").value.trim();if(!question){status("askStatus","Write a question first.",true);return;}
  submittedQuestions.push(question);submittedQuestions=submittedQuestions.slice(-10);questionCursor=submittedQuestions.length;questionDraft="";$("question").value="";
  busy=true;$("ask").disabled=true;$("ask").textContent="Asking tutor…";status("askStatus","Preparing the code, trace, and references…");
  try {
    if(!trace || revision()!==runRevision) if(!await runCode())throw new Error("Fix the input before asking the tutor.");
    const request={...input(),question,mode:$("mode").value,history:boundedHistory(),case_index:caseIndex,step:trace.cases[caseIndex].frames.length?step:null,include_problem:$("includeProblem").checked,use_memory:$("useMemory").checked};
    const response=await api("ask",request);
    addMessage("user",question);history.push({role:"user",content:question});addMessage("assistant",response.answer,response);history.push({role:"assistant",content:response.answer.slice(0,4000)});history=history.slice(-8);status("askStatus","Answer received. Edit the solution or ask a follow-up.");
  }catch(error){if(!$("question").value)$("question").value=question;status("askStatus",error.message,true);}
  finally{busy=false;$("ask").disabled=false;$("ask").textContent="Ask tutor";}
}
async function loadNotes() {const notes=await api("notes",undefined,"GET");$("noteList").replaceChildren();for(const note of notes){const row=el("div",undefined,"note-item"),button=el("button","Delete","quiet");row.append(el("span",note.text),button);button.addEventListener("click",async()=>{try{await api(`notes/${note.id}`,undefined,"DELETE");await loadNotes();status("noteStatus","Note deleted.");}catch(error){status("noteStatus",error.message,true);}});$("noteList").append(row);}}
async function reset() { if(busy)return;$("code").value=state.problem.buggy_code;$("values").value=state.problem.values.join(", ");$("target").value=state.problem.target;$("includeProblem").checked=true;$("useMemory").checked=false;history=[];$("conversation").replaceChildren(el("p","Ask for a hint about the failing case.","welcome"));$("question").value="";$("mode").value="hint";status("askStatus","");await runCode(); }
$("run").addEventListener("click",runCode);$("askForm").addEventListener("submit",ask);$("reset").addEventListener("click",reset);
$("question").addEventListener("keydown",event=>{
  if(event.isComposing)return;
  if(event.key==="Enter"&&!event.shiftKey){event.preventDefault();if(!busy)$("askForm").requestSubmit();}
  else if(event.key==="ArrowUp"&&submittedQuestions.length){event.preventDefault();if(questionCursor===submittedQuestions.length)questionDraft=event.target.value;questionCursor=Math.max(0,questionCursor-1);event.target.value=submittedQuestions[questionCursor];}
  else if(event.key==="ArrowDown"&&questionCursor<submittedQuestions.length){event.preventDefault();questionCursor++;event.target.value=questionCursor===submittedQuestions.length?questionDraft:submittedQuestions[questionCursor];}
});
$("question").addEventListener("input",()=>{questionCursor=submittedQuestions.length;});
$("prev").addEventListener("click",()=>{step--;renderTrace();});$("next").addEventListener("click",()=>{step++;renderTrace();});
for(const id of ["code","values","target"])$(id).addEventListener("input",markChanged);
for(const [id,key] of [["loadBuggy","buggy_code"],["loadCorrect","correct_code"]])$(id).addEventListener("click",()=>{$("code").value=state.problem[key];markChanged();});
document.querySelectorAll("[data-question]").forEach(button=>button.addEventListener("click",()=>{$("question").value=button.dataset.question;$("question").focus();}));
$("code").addEventListener("keydown",event=>{if(event.key==="Tab"){event.preventDefault();const start=event.target.selectionStart,end=event.target.selectionEnd;event.target.setRangeText("    ",start,end,"end");markChanged();}});
$("saveNote").addEventListener("click",async()=>{try{await api("notes",{text:$("noteText").value});$("noteText").value="";await loadNotes();status("noteStatus","Note saved locally. Enable recall to use it.");}catch(error){status("noteStatus",error.message,true);}});
async function init(){try{state=await api("status",undefined,"GET");$("connection").textContent=state.configured?`${state.provider} configured · ${state.model}`:"Tutor needs a local key file";$("providerLabel").textContent=state.provider;$("providerPrivacy").textContent=`Your question, code, and selected context go to ${state.provider} when you ask. Conversations stay in this page.`;$("harnessDetails").textContent=`Fixed harness: ${state.harness_version}. Configuration status does not prove a live answer.`;$("description").textContent=state.problem.description;$("code").value=state.problem.buggy_code;await runCode();await loadNotes();}catch(error){status("connection",error.message,true);}}
init();
