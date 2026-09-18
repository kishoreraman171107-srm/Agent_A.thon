const toast = document.getElementById('toast');
function showToast(message){toast.textContent=message;toast.classList.add('show');setTimeout(()=>toast.classList.remove('show'),2600)}
function setQuestion(question){document.getElementById('questionInput').value=question;document.getElementById('questionInput').focus()}
document.getElementById('uploadBtn').addEventListener('click',()=>document.getElementById('fileInput').click());
document.getElementById('fileInput').addEventListener('change',event=>{const file=event.target.files[0];if(file)showToast(`${file.name} selected — validation pipeline ready`)});
document.getElementById('askBtn').addEventListener('click',()=>{
 const input=document.getElementById('questionInput').value.trim();
 if(!input){showToast('Enter a question first');return}
 const answer=document.getElementById('answerBox');
 let response='';
 if(/how many|count|enrolled|subjects/i.test(input)) response='<strong>Answer · Subject count</strong><br>241 subjects are enrolled in ATLAS-001, representing 80.3% of the planned target of 300.<br><br><small>Evidence: DM domain · Enrollment snapshot · Confidence: High</small>';
 else if(/site|finding/i.test(input)) response='<strong>Answer · Site findings</strong><br>12 active sites are currently connected. The review queue prioritizes sites with repeated visit-window deviations and unresolved laboratory findings.<br><br><small>Evidence: SV + LB domains · Confidence: Medium</small>';
 else if(/protocol|amendment|change/i.test(input)) response='<strong>Answer · Protocol history</strong><br>Amendment 03 was approved on 18 Aug 2026. The recorded change updates eligibility criteria and is linked to the protocol event timeline.<br><br><small>Evidence: Protocol event log · Confidence: High</small>';
 else response='<strong>Review prepared</strong><br>The question has been received. In the connected backend, ATLAS will normalize relevant domains, align dates, evaluate rules, and return record-level evidence instead of an unsupported guess.<br><br><small>Mode: Deterministic evidence workflow</small>';
 answer.innerHTML=response;answer.classList.remove('hidden');showToast('Evidence response generated');
});
document.getElementById('questionInput').addEventListener('keydown',event=>{if(event.key==='Enter')document.getElementById('askBtn').click()});
document.getElementById('exportBtn').addEventListener('click',()=>{const report='ATLAS-001 Clinical Trial Summary\n\nSubjects: 241/300\nActive sites: 12/14\nOpen safety signals: 4\nEvidence coverage: 96.7%\n';const blob=new Blob([report],{type:'text/plain'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='atlas-trial-summary.txt';a.click();URL.revokeObjectURL(url);showToast('Summary report exported')});
