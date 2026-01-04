let orgCollegeMap = {};
let orgDeptMap = {};
let editingClassId = null;
async function loadCollegeOptions() { try { const r = await api('/api/org/colleges'); const list = Array.isArray(r) ? r : ((r && r.results) ? r.results : []); orgCollegeMap = {}; list.forEach(x => orgCollegeMap[x.id] = x.name); const s = document.getElementById('deptCollegeAdd'); if (s) s.innerHTML = '<option value="">选择学院</option>' + list.map(x => `<option value="${x.id}">${x.name}</option>`).join(''); const c = document.getElementById('classCollegeAdd'); if (c) c.innerHTML = '<option value="">选择学院</option>' + list.map(x => `<option value="${x.id}">${x.name}</option>`).join(''); const ec = document.getElementById('classEditCollege'); if (ec) ec.innerHTML = '<option value="">选择学院</option>' + list.map(x => `<option value="${x.id}">${x.name}</option>`).join(''); const fc = document.getElementById('classFilterCollege'); if (fc) fc.innerHTML = '<option value="">筛选学院</option>' + list.map(x => `<option value="${x.id}">${x.name}</option>`).join(''); const dfc = document.getElementById('deptFilterCollege'); if (dfc) dfc.innerHTML = '<option value="">筛选学院</option>' + list.map(x => `<option value="${x.id}">${x.name}</option>`).join('') } catch (e) { } }
async function loadDeptOptions() { try { const r = await api('/api/org/departments'); const all = Array.isArray(r) ? r : ((r && r.results) ? r.results : []); orgDeptMap = {}; all.forEach(x => { orgDeptMap[x.id] = { name: x.name, college: x.college } }); const s = document.getElementById('classDeptAdd'); const col = (document.getElementById('classCollegeAdd') && document.getElementById('classCollegeAdd').value) || ''; const list = col ? all.filter(x => String(x.college) === String(col)) : all; if (s) s.innerHTML = '<option value="">选择专业</option>' + list.map(x => `<option value="${x.id}">${x.name}</option>`).join(''); const fd = document.getElementById('classFilterDept'); const fcol = (document.getElementById('classFilterCollege') && document.getElementById('classFilterCollege').value) || ''; if (fd) { const flist = fcol ? all.filter(x => String(x.college) === String(fcol)) : all; fd.innerHTML = '<option value="">筛选专业</option>' + flist.map(x => `<option value="${x.id}">${x.name}</option>`).join('') } const ed = document.getElementById('classEditDept'); const ecol = (document.getElementById('classEditCollege') && document.getElementById('classEditCollege').value) || ''; if (ed) { const elist = ecol ? all.filter(x => String(x.college) === String(ecol)) : all; ed.innerHTML = '<option value="">选择专业</option>' + elist.map(x => `<option value="${x.id}">${x.name}</option>`).join('') } } catch (e) { } }
async function loadCollegeList() { 
    let r = []; 
    try { 
        r = await api('/api/org/colleges') 
    } catch (e) { 
        r = [] 
    } 
    const q = (document.getElementById('collegeQ') && document.getElementById('collegeQ').value || '').trim().toLowerCase(); 
    const rows = document.getElementById('collegeRows'); 
    const total = document.getElementById('collegeTotal'); 
    const all = Array.isArray(r) ? r : ((r && r.results) ? r.results : []); 
    // 过滤掉已删除的记录
    const list = all.filter(x => !x.is_deleted); 
    if (rows) {
        if (list.length === 0) {
            rows.innerHTML = '<tr><td colspan="3" class="text-center text-muted py-3">暂无数据</td></tr>';
        } else {
            rows.innerHTML = list.map(x => `
                <tr>
                    <td>${x.code || x.id}</td>
                    <td>${x.name || ''}</td>
                    <td class="text-end">
                        <button class="btn btn-sm btn-outline-primary" onclick="editCollege(${x.id},'${(x.name || '').replace(/'/g, "&#39;")}')">编辑</button> 
                        <button class="btn btn-sm btn-outline-danger" onclick="delCollege(${x.id})">删除</button>
                    </td>
                </tr>
            `).join(''); 
        }
    }
    if (total) total.textContent = '共' + list.length + '条' 
}
function exportColleges() { const q = (document.getElementById('collegeQ') && document.getElementById('collegeQ').value || '').trim(); const p = new URLSearchParams(); if (q) p.append('q', q); const url = '/api/org/colleges/export' + (p.toString() ? ('?' + p.toString()) : ''); window.open(url, '_blank') }
async function loadDeptList() { 
    let r = []; 
    const q = (document.getElementById('deptQ') && document.getElementById('deptQ').value || '').trim(); 
    const college = (document.getElementById('deptFilterCollege') && document.getElementById('deptFilterCollege').value) || ''; 
    const params = new URLSearchParams(); 
    if (q) params.append('search', q); 
    if (college) params.append('college', college); 
    try { 
        r = await api('/api/org/departments?' + params.toString()) 
    } catch (e) { 
        r = [] 
    } 
    const rows = document.getElementById('deptRows'); 
    const total = document.getElementById('deptTotal'); 
    const all = Array.isArray(r) ? r : ((r && r.results) ? r.results : []); 
    // 过滤掉已删除的记录
    const list = all.filter(x => !x.is_deleted);
    
    if (rows) {
        if (list.length === 0) {
            rows.innerHTML = '<tr><td colspan="4" class="text-center text-muted py-3">暂无数据</td></tr>';
        } else {
            rows.innerHTML = list.map(x => { 
                const cname = orgCollegeMap[x.college] || x.college; 
                return `
                    <tr>
                        <td>${x.code || x.id}</td>
                        <td>${x.name || ''}</td>
                        <td>${cname}</td>
                        <td>${x.duration_label || ''}</td>
                        <td class="text-end">
                            <button class="btn btn-sm btn-outline-primary" onclick="editDepartment(${x.id},'${(x.name || '').replace(/'/g, "&#39;")}',${x.college})">编辑</button> 
                            <button class="btn btn-sm btn-outline-danger" onclick="delDepartment(${x.id})">删除</button>
                        </td>
                    </tr>
                `; 
            }).join(''); 
        }
    }
    if (total) total.textContent = '共' + list.length + '条' 
}

function exportDepartments() { 
    const q = (document.getElementById('deptQ') && document.getElementById('deptQ').value || '').trim(); 
    const college = (document.getElementById('deptFilterCollege') && document.getElementById('deptFilterCollege').value) || ''; 
    const p = new URLSearchParams(); 
    if (q) p.append('q', q); 
    if (college) p.append('college', college); 
    const url = '/api/org/departments/export' + (p.toString() ? ('?' + p.toString()) : ''); 
    window.open(url, '_blank') 
}

async function addDepartment() { 
    const name = (document.getElementById('deptNameAdd') && document.getElementById('deptNameAdd').value || '').trim(); 
    const college = Number(document.getElementById('deptCollegeAdd').value || ''); 
    const code = (document.getElementById('deptCodeAdd') && document.getElementById('deptCodeAdd').value || '').trim(); 
    const duration_type = (document.getElementById('deptDurationAdd') && document.getElementById('deptDurationAdd').value || '3_year'); 
    const msg = document.getElementById('deptMsg'); 
    
    if (!name || !college) { 
        if (msg) msg.textContent = '请填写专业名称和所属学院'; 
        return 
    } 
    
    // 如果填写了代码，验证格式（必须是2位数字）
    if (code && (code.length !== 2 || !/^\d{2}$/.test(code))) {
        if (msg) msg.textContent = '专业代码必须为2位数字，如：01'; 
        return;
    }
    
    try { 
        const data = { name, college, duration_type };
        // 只有当code不为空时才添加到请求数据中
        if (code) {
            data.code = code;
        }
        await api('/api/org/departments/', 'POST', data); 
        if (msg) {
            msg.textContent = '新增成功';
            msg.className = 'text-success';
        }
        document.getElementById('deptNameAdd').value = ''; 
        document.getElementById('deptCodeAdd').value = ''; 
        document.getElementById('deptCollegeAdd').value = ''; 
        loadDeptList(); 
        loadDeptOptions(); 
    } catch (e) { 
        if (msg) {
             let errorMsg = '新增失败';
             if (e.code) errorMsg += ': ' + e.code;
             else if (e.message) errorMsg += ': ' + e.message;
             else if (e.error) errorMsg += ': ' + (typeof e.error === 'string' ? e.error : JSON.stringify(e.error));
             else if (e.detail) errorMsg += ': ' + e.detail;
             msg.textContent = errorMsg;
             msg.className = 'text-danger';
        }
    } 
}

async function submitCollegeImport() { 
    const csv = (document.getElementById('collegeCsv') && document.getElementById('collegeCsv').value) || ''; 
    const msg = document.getElementById('collegeImportMsg'); 
    if (!csv.trim()) { 
        if (msg) msg.textContent = '请粘贴CSV'; 
        return 
    } 
    try { 
        const r = await api('/api/org/import', 'POST', { type: 'colleges', csv }); 
        if (msg) msg.textContent = '导入成功：新增' + r.created + '，跳过' + r.skipped; 
        loadCollegeList(); 
        loadCollegeOptions() 
    } catch (e) { 
        if (msg) msg.textContent = e.message || '导入失败' 
    } 
}

async function submitDeptImport() { 
    const csv = (document.getElementById('deptCsv') && document.getElementById('deptCsv').value) || ''; 
    const msg = document.getElementById('deptImportMsg'); 
    if (!csv.trim()) { 
        if (msg) msg.textContent = '请粘贴CSV'; 
        return 
    } 
    try { 
        const r = await api('/api/org/import', 'POST', { type: 'departments', csv }); 
        if (msg) msg.textContent = '导入成功：新增' + r.created + '，跳过' + r.skipped + '；' + (r.errors && r.errors.length ? ('错误' + r.errors.length) : ''); 
        loadDeptList(); 
        loadDeptOptions() 
    } catch (e) { 
        if (msg) msg.textContent = e.message || '导入失败' 
    } 
}

async function editDepartment(id, old, oldCollege) { 
    const name = prompt('专业名称', old || ''); 
    if (name === null) return; 
    const c = prompt('学院ID', String(oldCollege || '')); 
    if (c === null) return; 
    const college = Number(c || ''); 
    try { 
        await api('/api/org/departments/' + id + '/', 'PATCH', { name, college }); 
        loadDeptList(); 
        loadDeptOptions() 
    } catch (e) { } 
}

async function delDepartment(id) { 
    if (!confirm('确认删除该专业？删除后无法恢复！\n\n如果该专业下存在班级，将无法删除。')) return; 
    try { 
        await api('/api/org/departments/' + id + '/', 'DELETE'); 
        loadDeptList(); 
        loadDeptOptions(); 
        alert('删除成功');
    } catch (e) { 
        let errorMsg = '删除失败: ';
        // 尝试解析错误信息
        try {
            if (e.error) {
                if (typeof e.error === 'string') {
                    errorMsg += e.error;
                } else if (e.error.error) {
                    errorMsg += e.error.error;
                } else if (typeof e.error === 'object') {
                    errorMsg += JSON.stringify(e.error);
                } else {
                    errorMsg += String(e.error);
                }
            } else if (e.message) {
                errorMsg += e.message;
            } else if (e.detail) {
                errorMsg += e.detail;
            } else {
                errorMsg += '未知错误，请检查该专业下是否还有班级';
            }
        } catch (parseError) {
            errorMsg += '无法解析错误信息，请检查该专业下是否还有班级';
        }
        alert(errorMsg + '\n\n提示：请先删除该专业下的所有班级，然后再删除专业。');
    } 
}

async function loadClassList() { 
    let r = []; 
    const q = (document.getElementById('classQ') && document.getElementById('classQ').value || '').trim(); 
    const fcol = (document.getElementById('classFilterCollege') && document.getElementById('classFilterCollege').value) || ''; 
    const fdep = (document.getElementById('classFilterDept') && document.getElementById('classFilterDept').value) || ''; 
    const params = new URLSearchParams(); 
    if (q) params.append('search', q); 
    if (fdep) params.append('major', fdep); 
    else if (fcol) params.append('major__college', fcol); 
    try { 
        r = await api('/api/org/classes?' + params.toString()) 
    } catch (e) { 
        r = [] 
    } 
    const rows = document.getElementById('classRows'); 
    const total = document.getElementById('classTotal'); 
    const all = Array.isArray(r) ? r : ((r && r.results) ? r.results : []); 
    // 过滤掉已删除的记录
    const list = all.filter(x => !x.is_deleted);
    if (rows) {
        if (list.length === 0) {
            rows.innerHTML = '<tr><td colspan="5" class="text-center text-muted py-3">暂无数据</td></tr>';
        } else {
            rows.innerHTML = list.map(x => { 
                const d = orgDeptMap[x.department]; 
                const dname = d ? d.name : x.department; 
                // 显示完整的班级ID（class_id），如果没有则显示数据库ID
                const classId = x.class_id || x.id;
                return `
                    <tr>
                        <td>${classId}</td>
                        <td>${x.name || ''}</td>
                        <td>${x.grade_year || ''}</td>
                        <td>${dname}</td>
                        <td class="text-end">
                            <button class="btn btn-sm btn-outline-primary" onclick="openEditClass(${x.id},'${(x.name || '').replace(/'/g, "&#39;")}',${x.grade_year},${x.department})">编辑</button> 
                            <button class="btn btn-sm btn-outline-danger" onclick="delClass(${x.id})">删除</button>
                        </td>
                    </tr>
                `; 
            }).join('');
        }
    }
    if (total) total.textContent = '共' + list.length + '条'
}

async function loadDeptOptionsForClass(collegeId) {
    const s = document.getElementById('classDeptAdd');
    if (!s) return;
    
    s.innerHTML = '<option value="">选择专业</option>';
    
    if (!collegeId) return;
    
    try {
        // 只加载该学院的专业
        const r = await api('/api/org/departments?college=' + collegeId);
        const list = Array.isArray(r) ? r : ((r && r.results) ? r.results : []);
        
        // 更新全局映射
        list.forEach(x => { orgDeptMap[x.id] = { name: x.name, college: x.college } });
        
        s.innerHTML = '<option value="">选择专业</option>' + list.map(x => `<option value="${x.id}">${x.name}</option>`).join('');
    } catch (e) {
        console.error(e);
    }
}

async function addCollege() { 
    const name = (document.getElementById('collegeNameAdd') && document.getElementById('collegeNameAdd').value || '').trim(); 
    const code = (document.getElementById('collegeCodeAdd') && document.getElementById('collegeCodeAdd').value || '').trim(); 
    const msg = document.getElementById('collegeMsg'); 
    
    if (!name) { 
        if (msg) {
            msg.textContent = '请填写学院名称';
            msg.className = 'text-danger';
        }
        return 
    } 
    
    // 如果填写了代码，验证格式（必须是2位数字）
    if (code && (code.length !== 2 || !/^\d{2}$/.test(code))) {
        if (msg) {
            msg.textContent = '学院ID必须为2位数字，如：01';
            msg.className = 'text-danger';
        }
        return;
    }
    
    try { 
        const data = { name };
        if (code) {
            data.code = code;
        }
        await api('/api/org/colleges/', 'POST', data); 
        if (msg) {
            msg.textContent = '新增成功';
            msg.className = 'text-success';
        }
        document.getElementById('collegeNameAdd').value = ''; 
        document.getElementById('collegeCodeAdd').value = ''; 
        loadCollegeList(); 
        loadCollegeOptions(); 
    } catch (e) { 
        if (msg) {
            let errorMsg = '新增失败: ';
            if (e.error) {
                if (typeof e.error === 'string') {
                    errorMsg += e.error;
                } else if (e.error.code) {
                    errorMsg += e.error.code[0] || '学院ID错误';
                } else {
                    errorMsg += JSON.stringify(e.error);
                }
            } else if (e.message) {
                errorMsg += e.message;
            } else {
                errorMsg += '未知错误';
            }
            msg.textContent = errorMsg;
            msg.className = 'text-danger';
        }
    } 
}

async function editCollege(id, old) { 
    const name = prompt('学院名称', old || ''); 
    if (!name) return; 
    try { 
        await api('/api/org/colleges/' + id + '/', 'PATCH', { name }); 
        loadCollegeList(); 
        loadCollegeOptions() 
    } catch (e) { } 
}

async function delCollege(id) { 
    if (!confirm('确认删除该学院？删除后无法恢复！\n\n如果该学院下存在专业，将无法删除。')) return; 
    try { 
        await api('/api/org/colleges/' + id + '/', 'DELETE'); 
        loadCollegeList(); 
        loadCollegeOptions(); 
        alert('删除成功');
    } catch (e) { 
        let errorMsg = '删除失败: ';
        // 尝试解析错误信息
        try {
            if (e.error) {
                if (typeof e.error === 'string') {
                    errorMsg += e.error;
                } else if (e.error.error) {
                    errorMsg += e.error.error;
                } else if (typeof e.error === 'object') {
                    errorMsg += JSON.stringify(e.error);
                } else {
                    errorMsg += String(e.error);
                }
            } else if (e.message) {
                errorMsg += e.message;
            } else if (e.detail) {
                errorMsg += e.detail;
            } else {
                errorMsg += '未知错误，请检查该学院下是否还有专业';
            }
        } catch (parseError) {
            errorMsg += '无法解析错误信息，请检查该学院下是否还有专业';
        }
        alert(errorMsg + '\n\n提示：请先删除该学院下的所有专业，然后再删除学院。');
    } 
}

async function addClass() { 
    const grade_year = Number(document.getElementById('classYearAdd').value || ''); 
    const class_number = Number(document.getElementById('classNumAdd').value || ''); 
    const department = Number(document.getElementById('classDeptAdd').value || ''); 
    const msg = document.getElementById('classMsg'); 
    
    console.log('Adding class:', { grade_year, class_number, department });
    
    if (!grade_year || !class_number || !department) { 
        if (msg) msg.textContent = '请填写完整信息'; 
        return 
    } 
    
    try { 
        await api('/api/org/classes/', 'POST', { 
            major: department, 
            enrollment_year: grade_year,
            class_number: class_number
        }); 
        if (msg) {
            msg.textContent = '新增成功';
            msg.className = 'text-success';
        }
        document.getElementById('classYearAdd').value = ''; 
        document.getElementById('classNumAdd').value = ''; 
        // Don't clear selections to allow easier continuous entry
        // document.getElementById('classDeptAdd').value = ''; 
        // document.getElementById('classCollegeAdd').value = ''; 
        loadClassList(); 
    } catch (e) { 
        if (msg) {
            let errorMsg = '新增失败: ';
            if (e.error) {
                if (typeof e.error === 'string') {
                    errorMsg += e.error;
                } else if (e.error.non_field_errors) {
                    errorMsg += e.error.non_field_errors[0];
                } else {
                    errorMsg += JSON.stringify(e.error);
                }
            } else if (e.message) {
                errorMsg += e.message;
            } else if (e.detail) {
                errorMsg += e.detail;
            } else {
                errorMsg += '未知错误';
            }
            msg.textContent = errorMsg;
            msg.className = 'text-danger';
        }
    } 
}
async function editClass(id, old, oldYear, oldDept) { const y = prompt('年级', String(oldYear || '')); if (y === null) return; const d = prompt('专业ID', String(oldDept || '')); if (d === null) return; const grade_year = Number(y || ''); const department = Number(d || ''); try { await api('/api/org/classes/' + id + '/', 'PATCH', { major: department, enrollment_year: grade_year }); loadClassList() } catch (e) { } }
async function delClass(id) { 
    if (!confirm('确认删除该班级？删除后无法恢复！\n\n如果该班级存在班主任或学生，将无法删除。')) return; 
    try { 
        await api('/api/org/classes/' + id + '/', 'DELETE'); 
        loadClassList(); 
        alert('删除成功');
    } catch (e) { 
        let errorMsg = '删除失败: ';
        // 尝试解析错误信息
        try {
            if (e.error) {
                if (typeof e.error === 'string') {
                    errorMsg += e.error;
                } else if (e.error.error) {
                    errorMsg += e.error.error;
                } else if (typeof e.error === 'object') {
                    errorMsg += JSON.stringify(e.error);
                } else {
                    errorMsg += String(e.error);
                }
            } else if (e.message) {
                errorMsg += e.message;
            } else if (e.detail) {
                errorMsg += e.detail;
            } else {
                errorMsg += '未知错误，请检查该班级是否还有班主任或学生';
            }
        } catch (parseError) {
            errorMsg += '无法解析错误信息，请检查该班级是否还有班主任或学生';
        }
        alert(errorMsg + '\n\n提示：请先解除该班级的班主任关联，并确保没有学生关联，然后再删除班级。');
    } 
}
function debounce(func, wait) {
    let timeout;
    return function(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}

function bindOrgEvents() { 
    const cq = document.getElementById('collegeQ'); 
    if (cq) {
        cq.addEventListener('input', debounce(loadCollegeList, 300)); 
    } else { console.warn('Element collegeQ not found'); }
    
    const dq = document.getElementById('deptQ'); 
    if (dq) {
        dq.addEventListener('input', debounce(loadDeptList, 300)); 
    } else { console.warn('Element deptQ not found'); }
    
    const dfc = document.getElementById('deptFilterCollege'); 
    if (dfc) {
        dfc.addEventListener('change', loadDeptList); 
    } else { console.warn('Element deptFilterCollege not found'); }
    
    const kq = document.getElementById('classQ'); 
    if (kq) {
        kq.addEventListener('input', debounce(loadClassList, 300)); 
    } else { console.warn('Element classQ not found'); }
    
    const cc = document.getElementById('classCollegeAdd'); 
    if (cc) cc.addEventListener('change', loadDeptOptions); 
    
    const fcc = document.getElementById('classFilterCollege'); 
    if (fcc) {
        fcc.addEventListener('change', async () => { 
            await loadDeptOptions(); 
            loadClassList(); 
        }); 
    } else { console.warn('Element classFilterCollege not found'); }
    
    const fdc = document.getElementById('classFilterDept'); 
    if (fdc) {
        fdc.addEventListener('change', loadClassList); 
    } else { console.warn('Element classFilterDept not found'); }
    
    const ec = document.getElementById('classEditCollege'); 
    if (ec) ec.addEventListener('change', loadDeptOptions);
}

async function openEditClass(id, name, year, dept) { editingClassId = id; const card = document.getElementById('classEditCard'); const title = document.getElementById('classEditTitle'); const nm = document.getElementById('classEditName'); const yr = document.getElementById('classEditYear'); const ec = document.getElementById('classEditCollege'); const ed = document.getElementById('classEditDept'); const msg = document.getElementById('classEditMsg'); if (msg) msg.textContent = ''; if (title) title.textContent = '正在编辑：#' + id; if (nm) nm.value = name || ''; if (yr) yr.value = String(year || ''); const di = orgDeptMap[dept]; const collegeId = di ? di.college : ''; if (ec) ec.value = collegeId || ''; await loadDeptOptions(); if (ed) ed.value = String(dept || ''); if (card) card.style.display = 'block' }

async function saveEditClass() { const id = editingClassId; const yr = document.getElementById('classEditYear'); const ed = document.getElementById('classEditDept'); const msg = document.getElementById('classEditMsg'); const grade_year = Number((yr && yr.value || '')); const department = Number((ed && ed.value || '')); if (!id || !grade_year || !department) { if (msg) msg.textContent = '请填写完整'; return } try { await api('/api/org/classes/' + id + '/', 'PATCH', { major: department, enrollment_year: grade_year }); if (msg) msg.textContent = '修改成功'; cancelEditClass(); loadClassList() } catch (e) { if (msg) msg.textContent = e.message || '修改失败' } }

function cancelEditClass() { editingClassId = null; const card = document.getElementById('classEditCard'); if (card) card.style.display = 'none' }
async function exportClasses() { 
    const q = (document.getElementById('classQ') && document.getElementById('classQ').value || '').trim(); 
    const college = (document.getElementById('classFilterCollege') && document.getElementById('classFilterCollege').value) || ''; 
    const department = (document.getElementById('classFilterDept') && document.getElementById('classFilterDept').value) || ''; 
    const p = new URLSearchParams(); 
    if (q) p.append('q', q); 
    if (department) p.append('department', department); 
    else if (college) p.append('college', college); 
    p.append('size', 10000); // Get all for export

    try {
        const r = await api('/api/org/classes?' + p.toString());
        const list = Array.isArray(r) ? r : (r.results || []);
        
        if (list.length === 0) {
            alert('暂无数据可导出');
            return;
        }

        // Sort by Major Name then Class Number (1, 2, 3...)
        list.sort((a, b) => {
            const majorA = (orgDeptMap[a.department] && orgDeptMap[a.department].name) || '';
            const majorB = (orgDeptMap[b.department] && orgDeptMap[b.department].name) || '';
            if (majorA !== majorB) return majorA.localeCompare(majorB);
            return (a.class_number || 0) - (b.class_number || 0);
        });

        // Format data for Excel
        const data = list.map(x => {
            const d = orgDeptMap[x.department];
            const dname = d ? d.name : x.department;
            return {
                '班级ID': x.class_id || x.id,
                '班级序号': x.class_number || '',
                '年级': x.grade_year || '',
                '专业': dname || '',
                '名称': x.name || ''
            };
        });

        const ws = XLSX.utils.json_to_sheet(data);
        const wb = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(wb, ws, "班级列表");
        XLSX.writeFile(wb, "班级列表.xlsx");
        
    } catch (e) {
        console.error(e);
        alert('导出失败: ' + (e.message || '未知错误'));
    }
}
window.addEventListener('DOMContentLoaded', () => {
    // 确保 bindOrgEvents 在 DOM 加载后被调用
    bindOrgEvents();
    
    loadCollegeOptions();
    loadDeptOptions();
    loadCollegeList();
    loadDeptList();
    loadClassList();
    
    // Auto-refresh every 20s
    setInterval(() => {
        loadCollegeList();
        loadDeptList();
        loadClassList();
    }, 20000);
})

// Make functions global
window.loadCollegeList = loadCollegeList;
window.loadDeptList = loadDeptList;
window.loadClassList = loadClassList;
window.loadCollegeOptions = loadCollegeOptions;
window.loadDeptOptions = loadDeptOptions;
window.addCollege = addCollege;
window.editCollege = editCollege;
window.delCollege = delCollege;
window.exportColleges = exportColleges;
window.addDepartment = addDepartment;
window.editDepartment = editDepartment;
window.delDepartment = delDepartment;
window.exportDepartments = exportDepartments;
window.addClass = addClass;
window.editClass = editClass;
window.delClass = delClass;
window.exportClasses = exportClasses;
window.openEditClass = openEditClass;
window.saveEditClass = saveEditClass;
window.cancelEditClass = cancelEditClass;
window.submitCollegeImport = submitCollegeImport;
window.submitDeptImport = submitDeptImport;
window.loadDeptOptionsForClass = loadDeptOptionsForClass;
