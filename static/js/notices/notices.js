let noticeSel = new Set();
let noticeRoleCanDelete = false;
let noticeMineOnly = false;
let noticePublisherRole = '';
function roleLabel(r) { switch (r) { case 'super_admin': return '超级管理员'; case 'principal': return '校长'; case 'vice_principal': return '副校长'; case 'dean': return '院长'; case 'vice_dean': return '副院长'; case 'teacher': return '教师'; case 'head_teacher': return '班主任'; default: return r || '' } }
async function loadNotices() { const p = new URLSearchParams(); const qEl = document.getElementById('noticeQ'); const q = (qEl && qEl.value || '').trim(); if (q) p.append('q', q); if (noticeMineOnly) p.append('mine', '1'); if (noticePublisherRole) p.append('publisher_role', noticePublisherRole); const r = await api('/api/notices/notices/?' + p.toString()); const list = Array.isArray(r) ? r : (r && r.results ? r.results : []); document.getElementById('noticeList').innerHTML = list.map(x => `<div class="d-flex align-items-center justify-content-between py-2 border-bottom"><div class="form-check"><input class="form-check-input" type="checkbox" value="${x.id}" ${noticeSel.has(x.id) ? 'checked' : ''} onchange="noticeToggle(${x.id}, this.checked)"><label class="form-check-label">#${x.id} ${x.title} · ${(x.scope === 'all') ? '全校' : '教师范围'} · 发布者：${x.created_by_name || ''}（${roleLabel(x.created_by_role)}）</label></div><div class="d-flex gap-2"><button class="btn btn-outline-secondary btn-sm" onclick="viewNotice(${x.id})">查看</button>${noticeRoleCanDelete ? (`<button class="btn btn-outline-danger btn-sm" onclick="deleteNotice(${x.id})">删除</button>`) : ''}</div></div>`).join('') }
async function viewNotice(id) { try { const x = await api('/api/notices/notices/' + id + '/'); const mEl = document.getElementById('noticeModal'); if (!mEl) return; document.getElementById('noticeModalTitle').textContent = x.title || ''; document.getElementById('noticeModalBody').textContent = x.content || ''; const t = new Date(x.created_at); const time = isNaN(t.getTime()) ? '' : t.toLocaleString('zh-CN'); const meta = `${x.created_by_name || ''}（${roleLabel(x.created_by_role)}） · ${(x.scope === 'all') ? '全校' : '教师范围'}${time ? (' · ' + time) : ''}`; document.getElementById('noticeModalMeta').textContent = meta; const modal = new bootstrap.Modal(mEl); modal.show() } catch (e) { alert('加载失败') } }
function noticeToggle(id, checked) { if (checked) noticeSel.add(id); else noticeSel.delete(id) }
function noticeSelectAll(checked) { const boxes = document.querySelectorAll('#noticeList input[type=checkbox]'); boxes.forEach(cb => { cb.checked = checked; noticeToggle(Number(cb.value), checked) }) }
async function deleteNotice(id) { if (!noticeRoleCanDelete) return; try { await api('/api/notices/notices/' + id + '/', 'DELETE'); loadNotices() } catch (e) { alert('删除失败') } }
async function deleteSelectedNotices() { if (!noticeRoleCanDelete || noticeSel.size === 0) return; const ids = Array.from(noticeSel); for (const id of ids) { try { await api('/api/notices/notices/' + id + '/', 'DELETE') } catch (e) { } } noticeSel.clear(); const all = document.getElementById('noSelAll'); if (all) all.checked = false; loadNotices() }
async function addNotice() { const title = document.getElementById('noticeTitle').value; const content = document.getElementById('noticeContent').value; const scope = document.getElementById('noticeScope').value; try { await api('/api/notices/notices/', 'POST', { title, content, scope }); document.getElementById('noticemsg').textContent = '成功'; loadNotices() } catch (e) { document.getElementById('noticemsg').textContent = e.message } }
async function gate() { 
    try { 
        const me = await api('/api/accounts/me'); 
        const role = me.role; 
        // 只有管理员可以创建/删除通知公告
        const allowed = ['super_admin', 'principal', 'vice_principal', 'dean', 'vice_dean'].includes(role); 
        noticeRoleCanDelete = allowed; 
        const add = document.getElementById('noticeAdd'); 
        if (add) add.style.display = allowed ? '' : 'none'; 
        const actions = document.getElementById('noticeListActions'); 
        if (actions) actions.style.display = allowed ? '' : 'none' 
    } catch (e) { 
        const add = document.getElementById('noticeAdd'); 
        if (add) add.style.display = 'none'; 
        const actions = document.getElementById('noticeListActions'); 
        if (actions) actions.style.display = 'none' 
    } 
}
function onNoticeMineToggle(checked) { noticeMineOnly = !!checked; loadNotices() }
function onNoticePublisherRoleChange(sel) { noticePublisherRole = sel && sel.value || ''; loadNotices() }
window.addEventListener('DOMContentLoaded', () => {
    loadNotices();
    gate();
    const q = document.getElementById('noticeQ'); if (q) q.addEventListener('input', loadNotices);
    // Auto-refresh every 20s
    setInterval(loadNotices, 20000);
})
