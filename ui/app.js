'use strict';
const $=id=>document.getElementById(id);
const state={data:null,revision:-1,selected:null,previewKey:null,filesKey:'',visible:100,polling:false,settingsKey:'',drag:0};
const descriptions={jpg:'El clásico para tus fotografías.',webp:'Menos peso, listo para la web.',png:'Sin pérdida, con transparencia.',tiff:'Sin pérdida, para conservar detalle. · 8 bits'};
const formatBytes=n=>n<1024?`${n} B`:n<1048576?`${(n/1024).toFixed(1)} KB`:`${(n/1048576).toFixed(1)} MB`;
const icon=name=>`<svg aria-hidden="true"><use href="#i-${name}"/></svg>`;
const escapeHTML=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let toastTimer;
function toast(message){$('toast').textContent=message;$('toast').hidden=false;clearTimeout(toastTimer);toastTimer=setTimeout(()=>{$('toast').hidden=true},6500)}
async function api(method,...args){
  if(!window.pywebview?.api?.[method]){toast('Abre Revela desde su acceso directo para usar esta función.');return null}
  try{const result=await window.pywebview.api[method](...args);if(result?.error)toast(result.error);else if(result?.message)toast(result.message);return result}catch(error){toast('No se pudo completar la acción. Inténtalo de nuevo.');console.error(error);return null}
}
async function poll(){
  if(state.polling||!window.pywebview?.api)return;state.polling=true;
  try{const data=await window.pywebview.api.get_state(state.revision);if(data){state.revision=data.revision;state.data=data;render(data)}}catch(error){console.error(error)}finally{state.polling=false}
}
function formatSettings(){
  const format=document.querySelector('input[name=format]:checked').value;
  $('format-note').textContent=descriptions[format];
  $('lossless-row').hidden=format!=='webp';
  const lossy=format==='jpg'||format==='webp'&&!$('lossless').checked;
  $('quality-section').hidden=!lossy;
  $('quality-value').innerHTML=`${$('quality').value}<span>%</span>`;
  $('custom-size-row').hidden=$('max-size').value!=='custom';
  requestAnimationFrame(updateScrollHint);
}
function updateScrollHint(){
  const controls=document.querySelector('.settings-controls'),button=$('more-settings');
  if(!button)return;
  const scrollable=controls.scrollHeight>controls.clientHeight+2;
  button.hidden=!scrollable;
  const bottom=controls.scrollTop+controls.clientHeight>=controls.scrollHeight-5;
  button.classList.toggle('at-bottom',bottom);
  button.firstChild.textContent=bottom?'Volver arriba ':'Ver más ajustes ';
}
async function saveSettings(){
  let maxSize=$('max-size').value==='custom'?Number($('custom-size').value):Number($('max-size').value);
  if(!Number.isInteger(maxSize)||maxSize<0||maxSize>65535||($('max-size').value==='custom'&&maxSize<1)){toast('Escribe un tamaño entre 1 y 65 535 píxeles.');return false}
  formatSettings();
  const result=await api('update_settings',{format:document.querySelector('input[name=format]:checked').value,quality:Number($('quality').value),max_size:maxSize,lossless:$('lossless').checked,metadata:$('metadata').checked});
  await poll();return Boolean(result&&!result.error);
}
function syncSettings(settings){
  const key=JSON.stringify(settings);if(key===state.settingsKey)return;state.settingsKey=key;
  document.querySelector(`input[name=format][value="${settings.format}"]`).checked=true;
  $('quality').value=settings.quality;$('lossless').checked=settings.lossless;$('metadata').checked=settings.metadata;
  const known=[0,3840,2560,1920,1280].includes(settings.max_size);
  $('max-size').value=known?String(settings.max_size):'custom';if(!known)$('custom-size').value=settings.max_size;
  $('destination-label').textContent=settings.destination?settings.destination.split(/[\\/]/).filter(Boolean).pop():'Carpeta junto al original';
  $('destination').title=settings.destination||'Se crea una carpeta Revela junto a cada imagen original.';
  $('destination-note').textContent=settings.destination?'Todas las imágenes en esta carpeta.':'Se creará una carpeta «Revela».';
  $('reset-destination').hidden=!settings.destination;formatSettings();
}
function render(data){
  $('app-version').textContent='Revela '+data.version;
  const files=data.files,busy=data.busy,locked=busy||data.scanning,done=files.filter(f=>f.state==='done').length,errors=files.filter(f=>f.state==='error').length,pending=files.length-done;
  syncSettings(data.settings);
  $('empty').hidden=Boolean(files.length);$('preview').hidden=!files.length;$('queue').hidden=!files.length;
  $('queue-description').textContent=files.length?`${files.length} ${files.length===1?'imagen':'imágenes'} · ${formatBytes(files.reduce((sum,f)=>sum+f.size,0))}`:'Una foto o toda una carpeta. Tú eliges.';
  $('queue-count').textContent=`${files.length} ${files.length===1?'imagen':'imágenes'}${done?` · ${done} lista${done===1?'':'s'}`:''}`;
  $('status-message').textContent=data.message;
  for(const id of ['add-files','add-folder','empty-add','clear','change-destination','destination','reset-destination'])$(id).disabled=locked;
  $('report').disabled=busy||!files.length;
  document.querySelectorAll('.settings input,.settings select').forEach(element=>element.disabled=busy);
  $('convert').disabled=data.scanning||(!busy&&!files.length)||(busy&&data.cancelling);
  $('convert').classList.toggle('stop',busy);
  $('convert-label').textContent=busy?(data.cancelling?'Deteniendo…':'Detener conversión'):!files.length?'Convertir imágenes':pending?`Convertir ${pending} ${pending===1?'imagen':'imágenes'}`:'Convertir otra vez';
  $('convert').querySelector('use').setAttribute('href',busy?'#i-close':'#i-arrow');
  $('convert-hint').textContent=busy?'Puedes detener la tanda en cualquier momento.':!files.length?'Añade imágenes para comenzar.':pending?'Ctrl + Enter para convertir.':'Crea una nueva copia con estos ajustes.';
  const batch=data.batch,processed=batch.completed+batch.errors;
  const percent=batch.total?Math.round(processed/batch.total*100):0;
  $('progress-fill').style.width=`${percent}%`;
  document.querySelector('.progress-track').setAttribute('aria-valuenow',String(percent));
  $('progress-count').textContent=batch.total?`${processed} / ${batch.total}`:'';
  $('status-label').textContent=data.scanning?'Buscando imágenes…':busy?(data.cancelling?'Deteniendo…':'Convirtiendo…'):batch.cancelled?'Tanda detenida':errors?`${errors} con error · puedes reintentar`:done?'Conversión terminada':'Lista para convertir';
  $('open-output').hidden=!done;
  if(!files.some(f=>f.id===state.selected)){state.selected=files[0]?.id||null;state.previewKey=null}
  const filesKey=JSON.stringify(files.map(f=>[f.id,f.state,f.error,f.output,f.output_size]))+state.selected+locked+state.visible;
  if(filesKey!==state.filesKey){state.filesKey=filesKey;renderFiles(files.slice(0,state.visible),locked)}
  $('show-more').hidden=files.length<=state.visible;
  if(state.selected&&state.previewKey!==state.selected)loadPreview(state.selected);
  if(!state.selected){state.previewKey=null;$('preview-image').hidden=true;$('preview-image').removeAttribute('src')}
  const selected=files.find(f=>f.id===state.selected);
  if(selected?.state==='error')$('preview-note').textContent=selected.error;
  else if(selected?.note)$('preview-note').textContent=selected.note;
}
function renderFiles(files,locked){
  const list=$('file-list'),scroll=list.scrollTop;
  list.innerHTML=files.map(f=>{
    const status=f.state==='done'?'Lista':f.state==='error'?'Error':f.state==='working'?'Convirtiendo':'En espera';
    const meta=f.state==='error'?f.error:f.output?`${formatBytes(f.size)} → ${formatBytes(f.output_size)} · ${f.output.split(/[\\/]/).pop()}`:`${formatBytes(f.size)}${f.raw?' · RAW':''}`;
    return `<div class="file-row${f.id===state.selected?' selected':''}" data-id="${f.id}" data-state="${f.state}" data-raw="${f.raw}" role="listitem"><button class="file-select" data-action="select" data-id="${f.id}" aria-label="Vista previa de ${escapeHTML(f.name)}" aria-pressed="${f.id===state.selected}" title="${escapeHTML(f.path)}"></button><span class="file-kind" aria-hidden="true">${escapeHTML(f.extension.slice(0,4))}</span><div class="file-info"><div class="file-name">${escapeHTML(f.name)}</div><div class="file-meta" title="${escapeHTML(meta)}">${escapeHTML(meta)}</div></div><span class="file-status">${f.state==='done'?icon('check'):f.state==='error'?icon('info'):''}${status}</span><button class="icon-button remove-file" data-action="remove" data-id="${f.id}" aria-label="Quitar ${escapeHTML(f.name)}" ${locked?'disabled':''}>${icon('close')}</button></div>`;
  }).join('');list.scrollTop=scroll;
}
async function loadPreview(id){
  state.previewKey=id;const item=state.data?.files.find(f=>f.id===id);if(!item)return;
  $('preview-image').hidden=true;$('preview-placeholder').hidden=false;$('preview-loading').textContent='Preparando vista previa…';$('preview-name').textContent=item.name;$('preview-dimensions').textContent='';$('preview-note').textContent='';$('preview-badge').textContent=item.raw?'Vista previa RAW':'Original';
  const result=await api('get_preview',id);if(state.previewKey!==id)return;
  if(!result||result.error){$('preview-loading').textContent=result?.error||'Vista previa no disponible.';return}
  $('preview-image').src=result.image;$('preview-image').hidden=false;$('preview-placeholder').hidden=true;$('preview-dimensions').textContent=`${result.width.toLocaleString('es')} × ${result.height.toLocaleString('es')} px`;
  const current=state.data?.files.find(f=>f.id===id);$('preview-note').textContent=current?.error||current?.note||result.note||'';
}
async function convertAction(){
  if($('convert').disabled)return;
  if(state.data?.busy){await api('cancel_batch');await poll();return}
  if(!await saveSettings())return;
  const again=state.data.files.every(f=>f.state==='done');await api('start_batch',again);await poll();
}
$('add-files').onclick=$('empty-add').onclick=()=>api('choose_files');$('add-folder').onclick=()=>api('choose_folder');
$('change-destination').onclick=$('destination').onclick=async()=>{await api('choose_destination');await poll()};
$('reset-destination').onclick=async()=>{await api('update_settings',{destination:''});await poll()};
$('clear').onclick=async()=>{await api('clear');await poll()};$('report').onclick=()=>api('export_report');$('convert').onclick=convertAction;$('open-output').onclick=()=>api('open_output',state.selected||'');
$('show-more').onclick=()=>{state.visible+=100;render(state.data)};
$('more-settings').onclick=()=>{const controls=document.querySelector('.settings-controls');controls.scrollTo({top:$('more-settings').classList.contains('at-bottom')?0:controls.scrollHeight,behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'})};
document.querySelector('.settings-controls').addEventListener('scroll',updateScrollHint);
window.addEventListener('resize',updateScrollHint);
$('file-list').onclick=async event=>{const button=event.target.closest('button[data-action]');if(!button)return;if(button.dataset.action==='remove'){await api('remove_file',button.dataset.id);await poll()}else{state.selected=button.dataset.id;render(state.data)}};
document.querySelectorAll('input[name=format],#lossless,#metadata,#max-size').forEach(el=>el.onchange=saveSettings);
$('quality').oninput=formatSettings;$('quality').onchange=saveSettings;$('custom-size').onchange=saveSettings;
$('help').onclick=()=>$('help-dialog').showModal();$('close-help').onclick=()=>$('help-dialog').close();$('help-dialog').onclick=event=>{if(event.target===$('help-dialog')){const r=event.target.getBoundingClientRect();if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom)event.target.close()}};
document.addEventListener('keydown',event=>{if(event.ctrlKey&&event.key.toLowerCase()==='o'){event.preventDefault();if(!$('add-files').disabled)api('choose_files')}if(event.ctrlKey&&event.key==='Enter'){event.preventDefault();convertAction()}});
document.addEventListener('dragenter',event=>{event.preventDefault();state.drag++;if([...event.dataTransfer.types].includes('Files'))$('drop-overlay').hidden=false});
document.addEventListener('dragover',event=>{event.preventDefault();event.dataTransfer.dropEffect=state.data?.busy?'none':'copy'});
document.addEventListener('dragleave',()=>{state.drag=Math.max(0,state.drag-1);if(!state.drag)$('drop-overlay').hidden=true});
document.addEventListener('drop',event=>{event.preventDefault();state.drag=0;$('drop-overlay').hidden=true});
window.addEventListener('pywebviewready',()=>{window.revelaReady=true;poll();setInterval(poll,450)});
formatSettings();
