let evSel = new Set();
let evRoleCanDelete = false;
let evMineOnly = false;
let evPublisherRole = '';
function roleLabel(r) { switch (r) { case 'super_admin': return '超级管理员'; case 'principal': return '校长'; case 'vice_principal': return '副校长'; case 'dean': return '院长'; case 'vice_dean': return '副院长'; case 'teacher': return '教师'; case 'head_teacher': return '班主任'; default: return r || '' } }
async function loadEvents() { const p = new URLSearchParams(); p.append('ts', Date.now()); const qEl = document.getElementById('evQ'); const q = (qEl && qEl.value || '').trim(); if (q) p.append('q', q); if (evMineOnly) p.append('mine', '1'); if (evPublisherRole) p.append('publisher_role', evPublisherRole); const r = await api('/api/calendar/events/?' + p.toString()); const list = Array.isArray(r) ? r : (r && r.results ? r.results : []); document.getElementById('eventList').innerHTML = list.map(x => `<div class="d-flex align-items-center justify-content-between py-2 border-bottom"><div class="form-check"><input class="form-check-input" type="checkbox" value="${x.id}" ${evSel.has(x.id) ? 'checked' : ''} onchange="evToggle(${x.id}, this.checked)"><label class="form-check-label">#${x.id} ${x.title} · ${x.visibility}${x.college_name ? ('(' + x.college_name + ')') : ''} · 发布者：${x.created_by_name || ''}（${roleLabel(x.created_by_role)}）</label></div><div class="d-flex gap-2"><button class="btn btn-outline-secondary btn-sm" onclick="viewEvent(${x.id})">查看</button>${evRoleCanDelete ? (`<button class="btn btn-outline-danger btn-sm" onclick="deleteEvent(${x.id})">删除</button>`) : ''}</div></div>`).join('') }
function eventTypeLabel(t) { switch (t) { case 'campus': return '全校活动'; case 'teaching': return '教学安排'; case 'meeting': return '会议'; case 'custom': return '自定义'; default: return t || '' } }
function visibilityLabel(v) { switch (v) { case 'all': return '全校范围'; case 'college': return '学院范围'; default: return v || '' } }
async function viewEvent(id) { try { const x = await api('/api/calendar/events/' + id + '/'); const mEl = document.getElementById('eventModal'); if (!mEl) return; document.getElementById('eventModalTitle').textContent = x.title || ''; document.getElementById('eventModalBody').textContent = x.description || ''; const s = new Date((x.start_time || '').replace(' ', 'T')); const e = new Date((x.end_time || '').replace(' ', 'T')); const st = isNaN(s.getTime()) ? '' : s.toLocaleString('zh-CN'); const et = isNaN(e.getTime()) ? '' : e.toLocaleString('zh-CN'); const meta = `${eventTypeLabel(x.event_type)} · ${visibilityLabel(x.visibility)}${x.college_name ? ('（' + x.college_name + '）') : ''} · ${st && et ? (st + ' ~ ' + et) : ''} · 发布者：${x.created_by_name || ''}（${roleLabel(x.created_by_role)}）`; document.getElementById('eventModalMeta').textContent = meta; const modal = new bootstrap.Modal(mEl); modal.show() } catch (e) { alert('加载失败') } }
function evToggle(id, checked) { if (checked) evSel.add(id); else evSel.delete(id) }
function evSelectAll(checked) { const boxes = document.querySelectorAll('#eventList input[type=checkbox]'); boxes.forEach(cb => { cb.checked = checked; evToggle(Number(cb.value), checked) }) }
async function deleteEvent(id) { if (!evRoleCanDelete) return; try { await api('/api/calendar/events/' + id + '/', 'DELETE'); loadEvents() } catch (e) { alert('删除失败') } }
async function deleteSelectedEvents() { if (!evRoleCanDelete || evSel.size === 0) return; const ids = Array.from(evSel); for (const id of ids) { try { await api('/api/calendar/events/' + id + '/', 'DELETE') } catch (e) { } } evSel.clear(); const all = document.getElementById('evSelAll'); if (all) all.checked = false; loadEvents() }
function onEvMineToggle(checked) { evMineOnly = !!checked; loadEvents() }
function onEvPublisherRoleChange(sel) { evPublisherRole = sel && sel.value || ''; loadEvents() }
async function addEvent() { const title = document.getElementById('evTitle').value; const description = document.getElementById('evDesc').value; const event_type = document.getElementById('evType').value; const visibility = document.getElementById('evVis').value; const start_time = document.getElementById('evStart').value.replace(' ', 'T'); const end_time = document.getElementById('evEnd').value.replace(' ', 'T'); const remind_minutes_before = Number(document.getElementById('evRemind').value || 0); const payload = { title, description, event_type, visibility, start_time, end_time, remind_minutes_before }; if (visibility === 'college') { payload.college = document.getElementById('evCollege').value || null } try { await api('/api/calendar/events/', 'POST', payload); document.getElementById('evmsg').textContent = '成功'; loadEvents() } catch (e) { document.getElementById('evmsg').textContent = e.message } }
async function gate() { 
    try { 
        const me = await api('/api/accounts/me'); 
        const role = me.role; 
        // 只有管理员和院长可以创建/删除日程安排（不包括教师/班主任/学生）
        const allowed = ['super_admin', 'principal', 'vice_principal', 'dean', 'vice_dean'].includes(role); 
        evRoleCanDelete = allowed; 
        const add = document.getElementById('eventAdd'); 
        if (add) add.style.display = allowed ? '' : 'none'; 
        const actions = document.getElementById('eventListActions'); 
        if (actions) actions.style.display = allowed ? '' : 'none' 
    } catch (e) { 
        const add = document.getElementById('eventAdd'); 
        if (add) add.style.display = 'none'; 
        const actions = document.getElementById('eventListActions'); 
        if (actions) actions.style.display = 'none' 
    } 
}
function bindVisibility() { const v = document.getElementById('evVis'); const c = document.getElementById('evCollege'); if (!v || !c) return; const ensureColleges = async () => { if (c.dataset.loaded === '1') return; const r = await api('/api/org/colleges'); c.innerHTML = '<option value="">选择学院</option>' + r.map(x => `<option value="${x.id}">${x.name}</option>`).join(''); c.dataset.loaded = '1' }; v.addEventListener('change', async () => { if (v.value === 'college') { c.style.display = ''; await ensureColleges() } else { c.style.display = 'none' } }); if (v.value === 'college') { c.style.display = ''; ensureColleges() } else { c.style.display = 'none' } }
function initDatePickers() { const s = document.getElementById('evStart'); const e = document.getElementById('evEnd'); if (!s || !e) return; const pad = n => String(n).padStart(2, '0'); const fmt = d => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`; const now = new Date(); const end = new Date(now.getTime() + 60 * 60 * 1000); s.value = fmt(now); e.value = fmt(end) }
window.addEventListener('DOMContentLoaded', () => {
    loadEvents();
    gate();
    bindVisibility();
    initDatePickers();
    const q = document.getElementById('evQ'); if (q) q.addEventListener('input', loadEvents);
    // Auto-refresh every 20s
    setInterval(loadEvents, 20000);
})
