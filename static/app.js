'use strict';
const el = id => document.getElementById(id);
const maxBytes = Number(document.body.dataset.maxMb) * 1024 * 1024;
let selected = [], busy = false;
function size(bytes) { return bytes < 1024 ? `${bytes} B` : bytes < 1048576 ? `${(bytes / 1024).toFixed(1)} KB` : `${(bytes / 1048576).toFixed(1)} MB`; }
async function refresh() {
  el('refresh').disabled = true;
  el('list-status').textContent = '正在讀取檔案…';
  try {
    const response = await fetch('/api/files', {cache: 'no-store'});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error);
    el('file-list').replaceChildren();
    for (const file of data.files) {
      const tr = document.createElement('tr');
      const name = document.createElement('td'); name.textContent = file.name;
      const info = document.createElement('td'); info.textContent = size(file.size);
      const date = document.createElement('span'); date.className = 'date';
      date.textContent = new Intl.DateTimeFormat('zh-TW', {year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: false}).format(new Date(file.modified * 1000));
      info.append(date);
      const action = document.createElement('td'); const link = document.createElement('a');
      link.href = `/download/${encodeURIComponent(file.name)}`; link.className = 'download-link'; link.textContent = '下載 ↓';
      link.setAttribute('aria-label', `下載 ${file.name}`); action.append(link); tr.append(name, info, action); el('file-list').append(tr);
    }
    el('list-status').textContent = data.files.length ? '' : '老師尚未提供檔案，請稍後重新整理。';
  } catch (error) { el('list-status').textContent = error.message === 'Failed to fetch' ? '無法連線，請確認老師已啟動服務。' : (error.message || '無法讀取檔案。'); }
  finally { el('refresh').disabled = false; }
}
function showResult(message, error = false) {
  el('upload-result').textContent = message; el('upload-result').classList.toggle('error', error);
}
function renderSelection() {
  el('selected-files').replaceChildren();
  for (const file of selected) { const li = document.createElement('li'); li.textContent = `${file.name} · ${size(file.size)}`; el('selected-files').append(li); }
  el('selection-count').textContent = selected.length ? `已選擇 ${selected.length} 個檔案 · ${size(selected.reduce((n, f) => n + f.size, 0))}` : '尚未選擇檔案';
}
function addFiles(files) {
  if (busy) return;
  selected.push(...Array.from(files)); renderSelection(); showResult('');
}
el('choose').addEventListener('click', () => el('files').click());
el('files').addEventListener('change', event => { addFiles(event.target.files); event.target.value = ''; });
el('clear').addEventListener('click', () => { if (!busy) { selected = []; renderSelection(); } });
for (const name of ['dragenter', 'dragover']) el('drop-zone').addEventListener(name, event => { event.preventDefault(); if (!busy) el('drop-zone').classList.add('dragging'); });
for (const name of ['dragleave', 'drop']) el('drop-zone').addEventListener(name, event => { event.preventDefault(); el('drop-zone').classList.remove('dragging'); });
el('drop-zone').addEventListener('drop', event => addFiles(event.dataTransfer.files));
window.addEventListener('dragover', event => event.preventDefault());
window.addEventListener('drop', event => event.preventDefault());
el('student-id').addEventListener('invalid', () => el('student-id').setCustomValidity('請輸入正確的學號。'));
el('student-id').addEventListener('input', () => el('student-id').setCustomValidity(''));
el('upload-form').addEventListener('submit', event => {
  event.preventDefault(); if (busy) return;
  const student = el('student-id').value;
  if (!/^[0-9]{4,12}$/.test(student)) return showResult('請輸入正確的學號。', true);
  if (!selected.length) return showResult('請先選擇檔案。', true);
  if (selected.length > 100) return showResult('單次最多上傳 100 個檔案。', true);
  if (selected.reduce((n, f) => n + f.size, 0) > maxBytes) return showResult('檔案過大，無法上傳。', true);
  const form = new FormData(); form.append('student_id', student); selected.forEach(file => form.append('files', file, file.name));
  busy = true; ['submit', 'choose', 'clear', 'student-id'].forEach(id => el(id).disabled = true);
  el('progress').hidden = false; el('progress').value = 0; showResult('正在上傳，請勿關閉網頁…');
  const xhr = new XMLHttpRequest(); xhr.open('POST', '/api/upload'); xhr.timeout = 20 * 60 * 1000;
  xhr.upload.onprogress = e => { if (e.lengthComputable) { el('progress').value = e.loaded / e.total * 100; if (e.loaded === e.total) showResult('傳送完成，正在等待老師電腦儲存…'); } };
  xhr.onload = () => {
    let data;
    try { data = JSON.parse(xhr.responseText); } catch (_) { showResult(xhr.status === 413 ? '檔案過大，無法上傳。' : '伺服器回應異常，請通知老師確認檔案是否已收到。', true); return; }
    if (data.error) return showResult(data.error, true);
    showResult(`上傳完成，共 ${data.saved.length} 個檔案。`, data.failed.length > 0);
    const list = document.createElement('ul');
    data.saved.forEach(name => { const li = document.createElement('li'); li.textContent = `成功：${name}`; list.append(li); });
    data.failed.forEach(file => { const li = document.createElement('li'); li.textContent = `失敗：${file.name} — ${file.reason}`; list.append(li); });
    el('upload-result').append(list);
    if (!data.failed.length) { selected = []; renderSelection(); }
  };
  xhr.onerror = xhr.ontimeout = () => showResult('連線中斷或逾時。請先向老師確認是否已收到檔案，再重新上傳。', true);
  xhr.onloadend = () => { busy = false; ['submit', 'choose', 'clear', 'student-id'].forEach(id => el(id).disabled = false); el('progress').hidden = true; };
  xhr.send(form);
});
el('refresh').addEventListener('click', refresh);
refresh();
