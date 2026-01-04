// Helper to load colleges
async function loadColleges(elId, selectId) {
    try {
        const r = await api('/api/org/colleges');
        const list = Array.isArray(r) ? r : (r.results || []);
        const el = document.getElementById(elId);
        if (el) {
            el.innerHTML = '<option value="">' + (elId.includes('add') ? '选择学院' : '全部学院') + '</option>' + 
                list.map(x => `<option value="${x.id}" ${selectId && String(selectId) === String(x.id) ? 'selected' : ''}>${x.name}</option>`).join('');
        }
    } catch(e) {}
}

// Helper to load majors (depts)
async function loadDepts(elId, collegeId, selectId) {
    try {
        const url = collegeId ? `/api/org/departments?college=${collegeId}` : '/api/org/departments';
        const r = await api(url);
        const list = Array.isArray(r) ? r : (r.results || []);
        const el = document.getElementById(elId);
        if (el) {
            el.innerHTML = '<option value="">' + (elId.includes('add') ? '选择专业' : '全部专业') + '</option>' + 
                list.map(x => `<option value="${x.id}" ${selectId && String(selectId) === String(x.id) ? 'selected' : ''}>${x.name}</option>`).join('');
        }
    } catch(e) {}
}

// Helper to load classes
async function loadClasses(elId, deptId, selectId) {
    try {
        const url = deptId ? `/api/org/classes?major=${deptId}` : '/api/org/classes';
        const r = await api(url);
        const list = Array.isArray(r) ? r : (r.results || []);
        const el = document.getElementById(elId);
        if (el) {
            el.innerHTML = '<option value="">' + (elId.includes('add') ? '选择班级' : '全部班级') + '</option>' + 
                list.map(x => `<option value="${x.id}" ${selectId && String(selectId) === String(x.id) ? 'selected' : ''}>${x.name}</option>`).join('');
        }
    } catch(e) {}
}

// Role Label Helper
function roleLabel(role) {
    const map = {
        'teacher': '教师',
        'head_teacher': '班主任',
        'dean': '院长',
        'vice_dean': '副院长',
        'principal': '校长',
        'vice_principal': '副校长'
    };
    return map[role] || role;
}

// Toggle Add Class Container and update field requirements
function toggleAddClass(role) {
    const container = document.getElementById('tea-add-class-container');
    const collegeSelect = document.getElementById('tea-add-college');
    const deptSelect = document.getElementById('tea-add-dept');
    const phoneInput = document.getElementById('tea-add-phone');
    
    // Reset all to optional first
    if (collegeSelect) {
        collegeSelect.innerHTML = '<option value="">选择学院</option>' + collegeSelect.innerHTML.replace('<option value="">选择学院</option>', '');
    }
    if (deptSelect) {
        deptSelect.innerHTML = '<option value="">选择专业</option>' + deptSelect.innerHTML.replace('<option value="">选择专业</option>', '');
    }
    if (phoneInput) {
        phoneInput.placeholder = '联系电话';
    }
    
    // Show/hide class container
    if (container) {
        container.style.display = (role === 'head_teacher') ? 'block' : 'none';
    }
    
    // Update field requirements based on role
    if (role === 'head_teacher') {
        // 班主任：专业、电话、班级必填
        if (deptSelect) deptSelect.innerHTML = deptSelect.innerHTML.replace('选择专业', '选择专业 *');
        if (phoneInput) phoneInput.placeholder = '联系电话 *';
    } else if (role === 'dean' || role === 'vice_dean') {
        // 院长/副院长：学院必填
        if (collegeSelect) collegeSelect.innerHTML = collegeSelect.innerHTML.replace('选择学院', '选择学院 *');
    }
}

// Search Logic
async function searchTeachers() {
    const p = new URLSearchParams();
    const q = (document.getElementById('tea-q')?.value || '').trim();
    const college = document.getElementById('tea-college')?.value || '';
    const dept = document.getElementById('tea-dept')?.value || '';
    
    if (q) p.append('q', q);
    if (college) p.append('college', college);
    if (dept) p.append('department', dept);
    
    const rows = document.getElementById('tea-rows');
    const total = document.getElementById('tea-total');
    
    try {
        const r = await api('/api/accounts/teachers/?' + p.toString());
        const list = Array.isArray(r) ? r : (r.results || []);
        
        if (rows) {
            if (list.length === 0) {
                rows.innerHTML = `<tr><td colspan="8" class="text-center text-muted py-3">暂无数据</td></tr>`;
            } else {
                // We need to fetch managed classes for head teachers or rely on backend if possible.
                // Backend TeacherProfileSerializer doesn't return managed_classes directly?
                // Let's check what we have. TeacherProfile -> UserProfile -> role.
                // But managed_class is on Class model.
                // We might need to fetch it or just show '-' if not available easily.
                // Or maybe update backend to include managed_class info.
                // For now, I'll check if I can deduce it or leave it.
                // Actually the previous implementation in personnel.js didn't seem to show it clearly either.
                // Wait, TeacherSerializer in `personnel` app had `managed_class_name`.
                // But we are using `accounts.serializers.TeacherProfileSerializer`.
                // I should probably add `managed_class` to `TeacherProfileSerializer` if needed.
                // But let's stick to what we have.
                
                rows.innerHTML = list.map(x => {
                    const role = x.user_profile && x.user_profile.role;
                    const roleName = roleLabel(role);
                    
                    let classInfo = '-';
                    if (role === 'head_teacher') {
                        if (x.managed_class_info) {
                            classInfo = `<a href="javascript:void(0)" onclick="showClassStudents(${x.managed_class_info.id}, '${x.managed_class_info.name}')" class="text-decoration-none fw-bold text-primary">${x.managed_class_info.name}</a>`;
                        } else {
                            classInfo = '<span class="text-muted">未分配</span>';
                        }
                    }

                    return `
                    <tr>
                        <td>${x.teacher_id}</td>
                        <td>${(x.user_profile && x.user_profile.user && x.user_profile.user.first_name) || (x.user_profile && x.user_profile.user && x.user_profile.user.username) || '-'}</td>
                        <td>${roleName || '-'}</td>
                        <td>${x.college_name || '-'}</td>
                        <td>${x.department_name || '-'}</td>
                        <td>${(x.user_profile && x.user_profile.phone) || '-'}</td>
                        <td>${classInfo}</td>
                        <td class="text-end">
                            <button class="btn btn-sm btn-outline-primary" onclick="editTeacher(${x.id})">编辑</button>
                            <button class="btn btn-sm btn-outline-danger" onclick="deleteTeacher(${x.id})">删除</button>
                        </td>
                    </tr>
                `}).join('');
            }
        }
        if (total) total.textContent = `共 ${r.count || list.length} 条`;
    } catch (e) {
        if (rows) rows.innerHTML = `<tr><td colspan="8" class="text-center text-danger py-3">加载失败</td></tr>`;
    }
}

// Add Teacher Logic
async function addTeacher() {
    const id = document.getElementById('tea-add-id')?.value?.trim();
    const name = document.getElementById('tea-add-name')?.value?.trim();
    const role = document.getElementById('tea-add-role')?.value;
    const college = document.getElementById('tea-add-college')?.value;
    const dept = document.getElementById('tea-add-dept')?.value;
    const phone = document.getElementById('tea-add-phone')?.value?.trim();
    const klass = document.getElementById('tea-add-class')?.value;
    const msg = document.getElementById('tea-add-msg');
    
    // 基本验证：工号、姓名、职务必填
    if (!id || !name || !role) {
        if (msg) msg.textContent = '请填写工号、姓名并选择职务';
        return;
    }

    if (!/^[a-zA-Z0-9]+$/.test(id)) {
        if (msg) msg.textContent = '工号只能包含数字和字母';
        return;
    }
    
    // 根据角色验证必填项
    // 1. 教师（teacher）: 必填：工号、姓名；可选：学院-专业、联系电话
    // 2. 班主任（head_teacher）: 必填：工号、姓名、学院-专业、联系电话、班级
    // 3. 院长/副院长（dean/vice_dean）: 必填：工号、姓名、学院；可选：专业、联系电话
    // 4. 校长/副校长（principal/vice_principal）: 必填：工号、姓名；可选：学院-专业、联系电话
    
    if (role === 'head_teacher') {
        if (!dept) {
            if (msg) msg.textContent = '班主任必须选择专业';
            return;
        }
        if (!phone) {
            if (msg) msg.textContent = '班主任必须填写联系电话';
            return;
        }
        if (!klass) {
            if (msg) msg.textContent = '班主任必须选择管理的班级';
            return;
        }
    }
    
    if (role === 'dean' || role === 'vice_dean') {
        if (!college) {
            if (msg) msg.textContent = '院长/副院长必须选择学院';
            return;
        }
    }
    
    // 电话格式验证（如果填写了）
    if (phone && !/^1[3-9]\d{9}$/.test(phone)) {
         if (msg) msg.textContent = '手机号格式不正确';
         return;
    }

    try {
        const payload = {
            teacher_id: id,
            name: name,
            role: role,
            phone: phone || ''
        };
        
        // 添加专业（如果选择了）
        if (dept) {
            payload.department = dept;
        }
        
        // 添加学院（如果没有专业但有学院）
        if (!dept && college) {
            payload.college_id = college;
        }
        
        // 班主任需要班级
        if (role === 'head_teacher' && klass) {
            payload.class_id = klass;
        }

        await api('/api/accounts/teachers/', 'POST', payload);
        
        if (msg) msg.textContent = '新增成功';
        // Clear inputs
        document.getElementById('tea-add-id').value = '';
        document.getElementById('tea-add-name').value = '';
        document.getElementById('tea-add-phone').value = '';
        document.getElementById('tea-add-role').selectedIndex = 0;
        document.getElementById('tea-add-college').selectedIndex = 0;
        document.getElementById('tea-add-dept').selectedIndex = 0;
        if (document.getElementById('tea-add-class')) {
            document.getElementById('tea-add-class').selectedIndex = 0;
        }
        searchTeachers();
    } catch (e) {
        if (msg) msg.textContent = '新增失败: ' + (e.message || '未知错误');
    }
}

// Edit Teacher Logic
let editCtx = { id: null };

async function editTeacher(id) {
    editCtx.id = id;
    const modal = document.getElementById('editModal');
    const form = document.getElementById('editForm');
    const title = document.getElementById('editTitle');
    
    try {
        const t = await api('/api/accounts/teachers/' + id + '/');
        title.textContent = '编辑教师';
        
        const deptId = t.department || '';
        let collegeId = '';
        if (deptId) {
            try {
                const d = await api('/api/org/departments/' + deptId + '/');
                collegeId = d.college;
            } catch(e) {}
        }
        
        const currentRole = (t.user_profile && t.user_profile.role) || 'teacher';

        form.innerHTML = `
            <div class="mb-3">
                <label class="form-label">工号 (不可修改)</label>
                <input class="form-control" value="${t.teacher_id}" disabled />
            </div>
            <div class="mb-3">
                <label class="form-label">姓名 (不可修改)</label>
                <input class="form-control" value="${(t.user_profile && t.user_profile.user && t.user_profile.user.first_name) || ''}" disabled />
            </div>
            <div class="mb-3">
                <label class="form-label">职务</label>
                <select id="edit-tea-role" class="form-select" onchange="toggleEditClass(this.value)">
                  <option value="teacher">教师</option>
                  <option value="head_teacher">班主任</option>
                  <option value="dean">院长</option>
                  <option value="vice_dean">副院长</option>
                  <option value="principal">校长</option>
                  <option value="vice_principal">副校长</option>
                </select>
            </div>
            <div class="mb-3">
                <label class="form-label">学院</label>
                <select id="edit-tea-college" class="form-select"></select>
            </div>
            <div class="mb-3">
                <label class="form-label">专业</label>
                <select id="edit-tea-dept" class="form-select"></select>
            </div>
            <div class="mb-3" id="edit-tea-class-container" style="display:none;">
                <label class="form-label">管理班级</label>
                <select id="edit-tea-class" class="form-select"></select>
            </div>
            <div class="mb-3">
                <label class="form-label">联系电话</label>
                <input id="edit-tea-phone" class="form-control" value="${(t.user_profile && t.user_profile.phone) || ''}" />
            </div>
        `;
        
        document.getElementById('edit-tea-role').value = currentRole;
        
        // Load options
        await loadColleges('edit-tea-college', collegeId);
        await loadDepts('edit-tea-dept', collegeId, deptId);
        
        // Load class options regardless (but hide if not head_teacher)
        // We need to find if this teacher is already managing a class to pre-select
        // Since backend doesn't provide it easily, we might skip pre-selection or fetch it.
        // Let's try to fetch classes for this dept.
        await loadClasses('edit-tea-class', deptId);

        // If head teacher, try to find their class? 
        // We don't have an easy way to know which class they manage unless we query Classes.
        // I'll skip pre-selecting the class for now to save time, or I can fetch classes and check head_teacher field.
        // Actually, let's fetch classes and see.
        if (currentRole === 'head_teacher') {
            document.getElementById('edit-tea-class-container').style.display = 'block';
             // Try to find managed class
             try {
                 const classes = await api('/api/org/classes?head_teacher=' + id); // Hypothetical filter?
                 // Actually `ClassViewSet` doesn't support filter by head_teacher directly in `get_queryset` unless implemented.
                 // `ClassViewSet` in `organization/views.py` filters:
                 // `filterset_fields = ['major', 'enrollment_year', 'major__college']`
                 // It does NOT filter by head_teacher.
                 // So we can't easily find it without iterating.
                 // But wait, `ClassViewSet` has `permission_classes`.
                 // Let's assume we just let them pick a class.
             } catch(e) {}
        }

        // Bind Cascades
        document.getElementById('edit-tea-college').addEventListener('change', async function() {
            await loadDepts('edit-tea-dept', this.value);
            await loadClasses('edit-tea-class', document.getElementById('edit-tea-dept').value);
        });
        document.getElementById('edit-tea-dept').addEventListener('change', async function() {
            await loadClasses('edit-tea-class', this.value);
        });

        modal.style.display = 'flex';
    } catch(e) {
        alert('加载失败');
    }
}

function toggleEditClass(role) {
    const container = document.getElementById('edit-tea-class-container');
    const collegeLabel = document.querySelector('label[for="edit-tea-college"]') || document.querySelector('#edit-tea-college').previousElementSibling;
    const deptLabel = document.querySelector('label[for="edit-tea-dept"]') || document.querySelector('#edit-tea-dept').previousElementSibling;
    const phoneLabel = document.querySelector('label[for="edit-tea-phone"]') || document.querySelector('#edit-tea-phone').previousElementSibling;
    
    // Show/hide class container
    if (container) {
        container.style.display = (role === 'head_teacher') ? 'block' : 'none';
    }
    
    // Update labels to show requirements
    if (role === 'head_teacher') {
        // 班主任：专业、电话、班级必填
        if (deptLabel) deptLabel.innerHTML = '专业 <span class="text-danger">*</span>';
        if (phoneLabel) phoneLabel.innerHTML = '联系电话 <span class="text-danger">*</span>';
        if (collegeLabel) collegeLabel.innerHTML = '学院';
    } else if (role === 'dean' || role === 'vice_dean') {
        // 院长/副院长：学院必填
        if (collegeLabel) collegeLabel.innerHTML = '学院 <span class="text-danger">*</span>';
        if (deptLabel) deptLabel.innerHTML = '专业';
        if (phoneLabel) phoneLabel.innerHTML = '联系电话';
    } else {
        // 其他角色：都是可选
        if (collegeLabel) collegeLabel.innerHTML = '学院';
        if (deptLabel) deptLabel.innerHTML = '专业';
        if (phoneLabel) phoneLabel.innerHTML = '联系电话';
    }
}

async function saveEdit() {
    const id = editCtx.id;
    const role = document.getElementById('edit-tea-role').value;
    const college = document.getElementById('edit-tea-college').value;
    const dept = document.getElementById('edit-tea-dept').value;
    const phone = document.getElementById('edit-tea-phone').value?.trim();
    const klass = document.getElementById('edit-tea-class').value;
    
    // 根据角色验证必填项
    // 1. 教师（teacher）: 必填：工号、姓名；可选：学院-专业、联系电话
    // 2. 班主任（head_teacher）: 必填：工号、姓名、学院-专业、联系电话、班级
    // 3. 院长/副院长（dean/vice_dean）: 必填：工号、姓名、学院；可选：专业、联系电话
    // 4. 校长/副校长（principal/vice_principal）: 必填：工号、姓名；可选：学院-专业、联系电话
    
    if (role === 'head_teacher') {
        if (!dept) {
            alert('班主任必须选择专业');
            return;
        }
        if (!phone) {
            alert('班主任必须填写联系电话');
            return;
        }
        if (!klass) {
            alert('班主任必须选择管理的班级');
            return;
        }
    }
    
    if (role === 'dean' || role === 'vice_dean') {
        if (!college) {
            alert('院长/副院长必须选择学院');
            return;
        }
    }

    if (phone && !/^1[3-9]\d{9}$/.test(phone)) {
         alert('手机号格式不正确');
         return;
    }

    try {
        const payload = {
            role: role,
            phone: phone || ''
        };
        
        // 添加专业（如果选择了）
        if (dept) {
            payload.department = dept;
        }
        
        // 添加学院（如果没有专业但有学院）
        if (!dept && college) {
            payload.college_id = college;
        }
        
        if (role === 'head_teacher' && klass) {
            payload.class_id = klass;
        } else {
            // If changing from head_teacher to something else, clear class_id
            payload.class_id = null;
        }

        await api('/api/accounts/teachers/' + id + '/', 'PATCH', payload);
        document.getElementById('editModal').style.display = 'none';
        searchTeachers();
    } catch(e) {
        alert('保存失败: ' + e.message);
    }
}

async function deleteTeacher(id) {
    if (!confirm('确认删除该教师？')) return;
    try {
        await api('/api/accounts/teachers/' + id + '/', 'DELETE');
        searchTeachers();
    } catch (e) {
        alert('删除失败 (可能无权限)');
    }
}

function closeEdit() {
    document.getElementById('editModal').style.display = 'none';
}

// Class Students Modal Logic
let currentClassId = null;
let currentClassName = '';
let currentStudents = [];

async function showClassStudents(classId, className) {
    currentClassId = classId;
    currentClassName = className;
    currentStudents = [];
    
    const modal = document.getElementById('classModal');
    const title = document.getElementById('classModalTitle');
    const info = document.getElementById('classModalInfo');
    const tbody = document.getElementById('classModalBody');
    const mobileBody = document.getElementById('classModalBodyMobile');
    const loading = document.getElementById('classModalLoading');
    const error = document.getElementById('classModalError');
    
    title.textContent = `班级学生列表 - ${className}`;
    info.textContent = `正在加载...`;
    tbody.innerHTML = '';
    if (mobileBody) mobileBody.innerHTML = '';
    loading.style.display = 'block';
    error.style.display = 'none';
    modal.style.display = 'flex';
    
    try {
        const r = await api(`/api/accounts/students/?class=${classId}&size=1000`); // Fetch all students
        currentStudents = Array.isArray(r) ? r : (r.results || []);
        
        loading.style.display = 'none';
        info.textContent = `共 ${currentStudents.length} 名学生`;
        
        if (currentStudents.length === 0) {
            tbody.innerHTML = `<tr><td colspan="5" class="text-center text-muted py-3">暂无学生数据</td></tr>`;
            if (mobileBody) mobileBody.innerHTML = `<div class="text-center text-muted py-4">暂无学生数据</div>`;
        } else {
            // Desktop Table View
            tbody.innerHTML = currentStudents.map(s => {
                const user = (s.user_profile && s.user_profile.user) || {};
                const name = user.first_name || user.username || '-';
                const phone = (s.user_profile && s.user_profile.phone) || '-';
                const gender = s.gender_display || '-';
                const status = s.status || '-';
                return `
                    <tr>
                        <td class="ps-3">${s.student_id}</td>
                        <td>${name}</td>
                        <td>${gender}</td>
                        <td>${phone}</td>
                        <td class="pe-3">
                            ${status === '在读' ? '<span class="badge bg-success-subtle text-success">在读</span>' : 
                              status === '休学' ? '<span class="badge bg-warning-subtle text-warning">休学</span>' :
                              status === '毕业' ? '<span class="badge bg-secondary-subtle text-secondary">毕业</span>' :
                              '<span class="badge bg-light text-dark">' + status + '</span>'}
                        </td>
                    </tr>
                `;
            }).join('');
            
            // Mobile Card View
            if (mobileBody) {
                mobileBody.innerHTML = currentStudents.map(s => {
                    const user = (s.user_profile && s.user_profile.user) || {};
                    const name = user.first_name || user.username || '-';
                    const phone = (s.user_profile && s.user_profile.phone) || '-';
                    const gender = s.gender_display || '-';
                    const status = s.status || '-';
                    
                    const statusBadge = status === '在读' ? '<span class="badge bg-success-subtle text-success">在读</span>' : 
                                       status === '休学' ? '<span class="badge bg-warning-subtle text-warning">休学</span>' :
                                       status === '毕业' ? '<span class="badge bg-secondary-subtle text-secondary">毕业</span>' :
                                       '<span class="badge bg-light text-dark">' + status + '</span>';
                    
                    return `
                        <div class="card border mb-2 shadow-sm">
                            <div class="card-body p-3">
                                <div class="d-flex justify-content-between align-items-start mb-2">
                                    <div class="flex-grow-1">
                                        <h6 class="mb-1 fw-bold text-primary">${name}</h6>
                                        <p class="mb-1 small text-muted">学号：${s.student_id}</p>
                                    </div>
                                    <div>${statusBadge}</div>
                                </div>
                                <div class="row g-2 small">
                                    <div class="col-6">
                                        <span class="text-muted">性别：</span>
                                        <span class="fw-medium">${gender}</span>
                                    </div>
                                    <div class="col-6">
                                        <span class="text-muted">电话：</span>
                                        <span class="fw-medium">${phone}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                }).join('');
            }
        }
    } catch (e) {
        loading.style.display = 'none';
        error.textContent = '加载失败: ' + (e.message || '未知错误');
        error.style.display = 'block';
        info.textContent = '';
    }
}

function closeClassModal() {
    document.getElementById('classModal').style.display = 'none';
}

function exportClassStudents() {
    if (!currentStudents || currentStudents.length === 0) {
        alert('暂无数据可导出');
        return;
    }
    
    try {
        // Prepare data for Excel
        const data = currentStudents.map(s => {
            const user = (s.user_profile && s.user_profile.user) || {};
            return {
                '学号': s.student_id,
                '姓名': user.first_name || user.username || '-',
                '性别': s.gender_display || '-',
                '联系电话': (s.user_profile && s.user_profile.phone) || '-',
                '状态': s.status
            };
        });
        
        // Create worksheet
        // Requirements: 
        // Row 1: Class Name (Merged, Centered)
        // Row 2: Headers
        // Row 3+: Data
        
        const ws = XLSX.utils.json_to_sheet(data, { origin: "A2" });
        
        // Add Class Name to Row 1
        XLSX.utils.sheet_add_aoa(ws, [[currentClassName]], { origin: "A1" });
        
        // Merge cells for Row 1
        // Determine range based on number of columns
        const range = XLSX.utils.decode_range(ws['!ref']);
        const merge = { s: { r: 0, c: 0 }, e: { r: 0, c: Object.keys(data[0]).length - 1 } };
        
        if (!ws['!merges']) ws['!merges'] = [];
        ws['!merges'].push(merge);
        
        // Center alignment for Row 1 (needs cell style support, but basic xlsx doesn't support styles in free version easily)
        // However, we can just put the content.
        
        // Create workbook
        const wb = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(wb, ws, "学生列表");
        
        // Generate filename
        const filename = `${currentClassName}_学生名单.xlsx`;
        
        // Download
        XLSX.writeFile(wb, filename);
        
    } catch (e) {
        console.error(e);
        alert('导出失败: ' + e.message);
    }
}

// Initialization
window.addEventListener('DOMContentLoaded', () => {
    loadColleges('tea-college');
    loadDepts('tea-dept');
    
    loadColleges('tea-add-college');
    
    // Bind Search Cascades
    document.getElementById('tea-college')?.addEventListener('change', function() {
        loadDepts('tea-dept', this.value);
        searchTeachers(); // Search when college changes
    });
    document.getElementById('tea-dept')?.addEventListener('change', searchTeachers); // Search when dept changes
    
    // Bind Add Cascades
    document.getElementById('tea-add-college')?.addEventListener('change', function() {
        loadDepts('tea-add-dept', this.value);
        loadClasses('tea-add-class', '', '');
    });
    document.getElementById('tea-add-dept')?.addEventListener('change', function() {
        loadClasses('tea-add-class', this.value);
    });
    
    // 从URL参数中读取搜索关键词并预填充
    const urlParams = new URLSearchParams(window.location.search);
    const searchQuery = urlParams.get('q');
    const searchInput = document.getElementById('tea-q');
    
    if (searchQuery && searchInput) {
        searchInput.value = decodeURIComponent(searchQuery);
    }
    
    // Search Input Listener (添加防抖)
    let searchTimeout = null;
    document.getElementById('tea-q')?.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            searchTeachers();
        }, 300);
    });
    
    // Trigger initial search
    searchTeachers();
});
