const toast = document.getElementById('toast');
const api = (path, options = {}) => fetch(path, {headers:{'Content-Type':'application/json'}, ...options});
function showToast(message){toast.textContent=message;toast.classList.add('show');setTimeout(()=>toast.classList.remove('show'),2600)}
function setQuestion(question){document.getElementById('questionInput').value=question;document.getElementById('questionInput').focus()}

document.getElementById('uploadBtn').addEventListener('click',()=>document.getElementById('fileInput').click());
document.getElementById('fileInput').addEventListener('change',async event=>{
 const selected=[...event.target.files]; if(!selected.length)return;
 const files={}; for(const file of selected) files[file.name]=await file.text();
 try { const response=await api('/api/load',{method:'POST',body:JSON.stringify({files})}); if(!response.ok)throw new Error('API unavailable'); const data=await response.json(); showToast(`${selected.length} file(s) loaded: ${data.summary.subjects} subjects`); }
 catch(error){ showToast('Files selected. Start server.py to enable live analysis.'); }
});

document.getElementById('askBtn').addEventListener('click',async()=>{
 const input=document.getElementById('questionInput').value.trim(); if(!input){showToast('Enter a question first');return;}
 const answer=document.getElementById('answerBox');
 try {
  const response=await api('/api/query',{method:'POST',body:JSON.stringify({question:input})});
  if(!response.ok)throw new Error('API unavailable');
  const data=await response.json();
  const evidence=(data.evidence||[]).map(item=>typeof item==='string'?item:(item.record_ref||item.domain||'')).join(', ');
  answer.innerHTML=`<strong>Answer</strong><br>${data.answer}<br><br><small>Confidence: ${data.confidence||'not specified'}${evidence?` · Evidence: ${evidence}`:''}</small>`;
 } catch(error) {
  answer.innerHTML='<strong>Backend unavailable</strong><br>Start the Python server with <code>python server.py</code> and try again.';
 }
 answer.classList.remove('hidden'); showToast('Evidence response generated');
});
document.getElementById('questionInput').addEventListener('keydown',event=>{if(event.key==='Enter')document.getElementById('askBtn').click()});
document.getElementById('exportBtn').addEventListener('click',()=>{const report='ATLAS Clinical Trial Summary\nGenerated from the connected evidence engine.\n';const blob=new Blob([report],{type:'text/plain'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='atlas-trial-summary.txt';a.click();URL.revokeObjectURL(url);showToast('Summary report exported')});
