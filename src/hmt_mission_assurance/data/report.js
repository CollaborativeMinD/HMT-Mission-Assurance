"use strict";
(() => {
  const data = JSON.parse(document.getElementById("report-data").textContent);
  const c = data.contract, e = data.evaluation;
  const byId = id => document.getElementById(id);
  const el = (tag, text) => { const n = document.createElement(tag); if (text !== undefined) n.textContent = text; return n; };
  const pretty = v => typeof v === "object" ? JSON.stringify(v, null, 2) : String(v ?? "");
  byId("subject").textContent = `${c.tool_id} / ${c.baseline_version} · ${c.environment_id} · ${c.as_of}`;
  byId("disposition").textContent = `${e.primary_disposition} · ${e.reason_code}`;
  byId("scope").textContent = c.scope;
  byId("footer").textContent = `Contract SHA-256: ${e.contract_sha256} · Evaluator ${e.evaluator_version} · Offline report; no external requests.`;
  const values = [[e.coverage.declared_scenarios,"Declared scenarios"],[e.coverage.exercised_scenarios,"Exercised"],[e.coverage.satisfied_scenarios,"Satisfied"],[e.findings.length,"Findings"]];
  for (const [value,label] of values) { const n = el("div"); n.className="metric"; n.append(el("strong",value),el("span",label)); byId("metrics").append(n); }
  function table(id, headers, rows) {
    const t = el("table"), h = el("tr"), head = el("thead"), body = el("tbody");
    headers.forEach(label => h.append(el("th",label))); head.append(h); t.append(head);
    rows.forEach(row => { const tr=el("tr"); row.forEach(v => tr.append(el("td",pretty(v)))); body.append(tr); });
    t.append(body); byId(id).append(t); if (!rows.length) byId(id).append(el("p","No entries in this declared scope."));
  }
  const tabs = ["graph","findings","paths","couplings","requirements","evidence","record"];
  for (const [index,id] of tabs.entries()) {
    const b = el("button",id[0].toUpperCase()+id.slice(1)); b.id=`tab-${id}`; b.role="tab";
    b.setAttribute("aria-controls",id); b.setAttribute("aria-selected",String(index===0)); byId(id).setAttribute("aria-labelledby",b.id);
    b.addEventListener("click",() => { tabs.forEach(t => { byId(t).hidden=t!==id; byId(`tab-${t}`).setAttribute("aria-selected",String(t===id)); }); });
    b.addEventListener("keydown",event => { if (["ArrowLeft","ArrowRight"].includes(event.key)) { const next=(index+(event.key==="ArrowRight"?1:-1)+tabs.length)%tabs.length; const button=byId(`tab-${tabs[next]}`); button.click(); button.focus(); event.preventDefault(); } });
    byId("tabs").append(b);
  }
  table("findings",["Finding / reason","Disposition","Expected","Observed","Evidence","Hypothesis","Release condition"],e.findings.map(f=>[`${f.id}\n${f.reason_code}`,f.disposition,f.expected,f.observed,f.evidence_refs,f.hypothesis,f.release_condition]));
  const paths=[];
  for (const claim of c.claims) for (const s of claim.scenarios) {
    const checks=e.evidence_checks.filter(w=>w.scenario_id===s.id), fs=e.findings.filter(f=>f.scenario_id===s.id);
    paths.push([claim.id,s.id,s.mode,s.expected,checks.map(w=>`${w.evidence_id}: ${w.actual ?? w.reason_code}`),fs.map(f=>f.id),e.requirements.filter(r=>fs.some(f=>f.id===r.finding_id)).map(r=>r.id)]);
  }
  table("paths",["Claim","Scenario","Mode","Expected","Submitted observations","Findings","Requirements"],paths);
  table("couplings",["Coupling","Source claim","Target claim","Witness scenario","Meaning","Witness state"],c.couplings.map(k=>[k.id,k.source_claim,k.target_claim,k.scenario_id,k.description,e.evidence_checks.filter(w=>w.scenario_id===k.scenario_id)]));
  table("requirements",["Requirement","Finding","Kind","Baseline evidence","Threshold","Regression witnesses","Proposed change","If not demonstrated"],e.requirements.map(r=>[r.id,r.finding_id,r.kind,r.baseline_evidence_refs,r.acceptance_threshold,r.regression_witness,r.proposed_change,r.if_not_demonstrated]));
  table("evidence",["Evidence","Source (inert)","Captured UTC","Hash","Check","Raw submitted record"],c.evidence.map(w=>[w.id,w.source_ref,w.captured_at,w.sha256,e.evidence_checks.find(x=>x.evidence_id===w.id),w.content]));
  byId("record").append(el("h2","Evidence basis and limits"),el("p",e.evidence_basis),el("pre",pretty(e.limitations)),el("h2","Complete structured record"),el("pre",pretty(data)));
  const svg=byId("network"), ns="http://www.w3.org/2000/svg";
  const kinds=["claim","coupling","scenario","evidence","finding","requirement","disposition"].filter(kind=>e.graph.nodes.some(n=>n.kind===kind));
  const colors=["#315b77","#574780","#255f59","#455b35","#7c4838","#665b30","#374572"];
  const counters={}, positions=new Map();
  for (const n of e.graph.nodes) { const col=kinds.indexOf(n.kind), row=counters[n.kind]??0; counters[n.kind]=row+1; positions.set(n.id,{x:col*255+25,y:row*76+40}); }
  const width=kinds.length*255+30, height=Math.max(240,...Object.values(counters).map(n=>n*76+90));
  svg.setAttribute("viewBox",`0 0 ${width} ${height}`);
  const svgEl=(tag,attrs,text)=>{const n=document.createElementNS(ns,tag); for(const [k,v] of Object.entries(attrs)) n.setAttribute(k,String(v)); if(text!==undefined)n.textContent=text; return n;};
  const defs=svgEl("defs",{}),marker=svgEl("marker",{id:"arrow",viewBox:"0 0 10 10",refX:9,refY:5,markerWidth:6,markerHeight:6,orient:"auto-start-reverse"});
  marker.append(svgEl("path",{d:"M0 0 L10 5 L0 10 Z",fill:"#8fa9bc"}));defs.append(marker);svg.append(defs);
  function select(n) {
    byId("node-detail").textContent=`${n.id}\n${n.label}`; byId("node-edges").replaceChildren();
    const connected=e.graph.edges.filter(x=>x.source===n.id||x.target===n.id);
    for(const edge of connected) byId("node-edges").append(el("p",`${edge.source} → ${edge.target} [${edge.relation}]`));
    for(const edge of svg.querySelectorAll(".edge")) { const active=edge.dataset.source===n.id||edge.dataset.target===n.id; edge.style.opacity=active?"1":"0.1"; edge.style.stroke=active?"#62dfbb":"#607d9b"; }
  }
  const edgeNodes=[];
  for (const edge of e.graph.edges) {
    const a=positions.get(edge.source),b=positions.get(edge.target);
    const path=svgEl("path",{d:`M${a.x+202},${a.y+22} C${a.x+235},${a.y+22} ${b.x-35},${b.y+22} ${b.x},${b.y+22}`,class:"edge","marker-end":"url(#arrow)"});
    path.dataset.source=edge.source;path.dataset.target=edge.target;path.append(svgEl("title",{},`${edge.source} → ${edge.target}: ${edge.relation}`));svg.append(path);edgeNodes.push({edge,path});
  }
  const nodeGroups=[];
  for (const n of e.graph.nodes) {
    const p=positions.get(n.id),g=svgEl("g",{class:"node",tabindex:0,role:"button","aria-label":`${n.id}: ${n.label}`});
    g.append(svgEl("rect",{x:p.x,y:p.y,width:202,height:46,rx:7,fill:colors[kinds.indexOf(n.kind)],stroke:"#7a95ab"}));
    const shortId=n.id.split(":")[1];
    g.append(svgEl("text",{x:p.x+9,y:p.y+18},n.kind.toUpperCase()),svgEl("text",{x:p.x+9,y:p.y+35},shortId.length>26?shortId.slice(0,25)+"…":shortId),svgEl("title",{},`${n.id}\n${n.label}`));
    g.addEventListener("click",()=>select(n));g.addEventListener("keydown",event=>{if(event.key==="Enter"||event.key===" "){select(n);event.preventDefault();}});svg.append(g);nodeGroups.push({n,g});
  }
  function filter() {
    const query=byId("search").value.toLowerCase(),visible=new Set();
    for(const {n,g} of nodeGroups){const show=`${n.id} ${n.kind} ${n.label}`.toLowerCase().includes(query);g.style.display=show?"":"none";if(show)visible.add(n.id);}
    for(const {edge,path} of edgeNodes)path.style.display=visible.has(edge.source)&&visible.has(edge.target)?"":"none";
    byId("graph-count").textContent=`${visible.size}/${e.graph.nodes.length} nodes · ${e.graph.edges.length} total edges`;
  }
  function zoom(){const scale=Number(byId("zoom").value)/100;svg.setAttribute("width",width*scale);svg.setAttribute("height",height*scale);}
  byId("search").addEventListener("input",filter);byId("zoom").addEventListener("input",zoom);
  byId("reset").addEventListener("click",()=>{byId("search").value="";byId("zoom").value="80";for(const {path} of edgeNodes){path.style.opacity=".5";path.style.stroke="#607d9b";}filter();zoom();});
  byId("zoom").value=String(Math.max(40,Math.min(90,Math.floor(byId("network").parentElement.clientWidth/width*100))));
  filter();zoom();
})();
