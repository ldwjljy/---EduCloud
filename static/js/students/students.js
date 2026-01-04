// Helper to load colleges
async function loadColleges(elId, selectId) {
    try {
        const r = await api('/api/org/colleges');
        const list = Array.isArray(r) ? r : ((r && r.results) ? r.results : []);
        const el = document.getElementById(elId);
        if (el) {
            el.innerHTML = '<option value="">' + (elId.includes('add') ? '选择学院' : '全部学院') + '</option>' + 
                list.map(x => `<option value="${x.id}" ${selectId && String(selectId) === String(x.id) ? 'selected' : ''}>${x.name}</option>`).join('');
        }
    } catch(e) {
        console.error('加载学院失败:', e);
    }
}

// Helper to load majors (depts)
async function loadDepts(elId, collegeId, selectId) {
    try {
        const url = collegeId ? `/api/org/departments?college=${collegeId}` : '/api/org/departments';
        const r = await api(url);
        const list = Array.isArray(r) ? r : ((r && r.results) ? r.results : []);
        const el = document.getElementById(elId);
        if (el) {
            el.innerHTML = '<option value="">' + (elId.includes('add') ? '选择专业' : '全部专业') + '</option>' + 
                list.map(x => `<option value="${x.id}" ${selectId && String(selectId) === String(x.id) ? 'selected' : ''}>${x.name}</option>`).join('');
        }
    } catch(e) {
        console.error('加载专业失败:', e);
    }
}

// Helper to load classes
async function loadClasses(elId, deptId, selectId) {
    try {
        // 使用major参数，因为ClassViewSet的filterset_fields是['major', 'enrollment_year', 'major__college']
        const url = deptId ? `/api/org/classes?major=${deptId}` : '/api/org/classes';
        const r = await api(url);
        const list = Array.isArray(r) ? r : ((r && r.results) ? r.results : []);
        const el = document.getElementById(elId);
        if (el) {
            el.innerHTML = '<option value="">' + (elId.includes('add') ? '选择班级' : '全部班级') + '</option>' + 
                list.map(x => `<option value="${x.id}" ${selectId && String(selectId) === String(x.id) ? 'selected' : ''}>${x.name}</option>`).join('');
        }
    } catch(e) {
        console.error('加载班级失败:', e);
    }
}

// Search Logic
async function searchStudents() {
    const p = new URLSearchParams();
    const q = (document.getElementById('stu-q')?.value || '').trim();
    const status = document.getElementById('stu-status')?.value || '';
    const college = document.getElementById('stu-college')?.value || '';
    const dept = document.getElementById('stu-dept')?.value || '';
    const klass = document.getElementById('stu-klass')?.value || '';
    
    if (q) p.append('q', q);
    if (status) p.append('status', status);
    if (college) p.append('college', college);
    if (dept) p.append('department', dept);
    if (klass) p.append('class', klass);
    
    const rows = document.getElementById('stu-rows');
    const total = document.getElementById('stu-total');
    const pagination = document.getElementById('stu-pagination');
    
    try {
        const r = await api('/api/accounts/students/?' + p.toString());
        const list = Array.isArray(r) ? r : (r.results || []); 
        const count = list.length;
        
        if (rows) {
            if (list.length === 0) {
                rows.innerHTML = `<tr><td colspan="8" class="text-center text-muted py-3">暂无数据</td></tr>`;
            } else {
                rows.innerHTML = list.map(x => `
                    <tr>
                        <td class="ps-3"><input type="checkbox" class="form-check-input student-check" value="${x.id}"></td>
                        <td>${x.student_id}</td>
                        <td>${(x.user_profile && x.user_profile.user && x.user_profile.user.first_name) || (x.user_profile && x.user_profile.user && x.user_profile.user.username) || '-'}</td>
                        <td>${x.gender_display || '-'}</td>
                        <td>${x.class_name || x.school_class || '-'}</td>
                        <td>${x.status || '-'}</td>
                        <td>${(x.user_profile && x.user_profile.phone) || '-'}</td>
                        <td class="text-end">
                            <button class="btn btn-sm btn-outline-primary" onclick="editStudent(${x.id})">编辑</button>
                            <button class="btn btn-sm btn-outline-danger" onclick="deleteStudent(${x.id})">删除</button>
                        </td>
                    </tr>
                `).join('');
                // Reset check all box
                const checkAll = document.getElementById('check-all');
                if (checkAll) checkAll.checked = false;
            }
        }
        
        if (total) total.textContent = `共 ${count} 条`;
        
        // 隐藏分页控件（因为现在显示所有数据）
        if (pagination) {
            pagination.innerHTML = '';
        }
        
    } catch (e) {
        if (rows) rows.innerHTML = `<tr><td colspan="7" class="text-center text-danger py-3">加载失败</td></tr>`;
    }
}

// Bulk Edit Logic
function toggleAll(source) {
    const checkboxes = document.querySelectorAll('.student-check');
    checkboxes.forEach(cb => cb.checked = source.checked);
}

function getCheckedStudentIds() {
    return Array.from(document.querySelectorAll('.student-check:checked')).map(cb => cb.value);
}

function openBulkEditModal() {
    const ids = getCheckedStudentIds();
    if (ids.length === 0) {
        alert('请先选择要修改的学生');
        return;
    }
    
    const modal = document.getElementById('bulkEditModal');
    if (modal) {
        modal.style.display = 'flex';
        document.getElementById('bulkEditInfo').textContent = `已选择 ${ids.length} 名学生`;
        loadColleges('bulk-college');
        // Clear dependent selects
        document.getElementById('bulk-dept').innerHTML = '<option value="">请选择专业</option>';
        document.getElementById('bulk-klass').innerHTML = '<option value="">请选择班级</option>';
    }
}

function closeBulkEditModal() {
    const modal = document.getElementById('bulkEditModal');
    if (modal) modal.style.display = 'none';
}

async function loadBulkDepts() {
    const collegeId = document.getElementById('bulk-college').value;
    loadDepts('bulk-dept', collegeId);
    document.getElementById('bulk-klass').innerHTML = '<option value="">请选择班级</option>';
}

async function loadBulkClasses() {
    const deptId = document.getElementById('bulk-dept').value;
    loadClasses('bulk-klass', deptId);
}

async function confirmBulkEdit() {
    const ids = getCheckedStudentIds();
    const classId = document.getElementById('bulk-klass').value;
    const status = document.getElementById('bulk-status').value;
    
    if (!classId && !status) {
        alert('请至少选择一项要修改的内容（班级或状态）');
        return;
    }
    
    try {
        await api('/api/accounts/students/bulk_update/', 'POST', {
            ids: ids,
            class_id: classId,
            status: status
        });
        alert('批量修改成功');
        closeBulkEditModal();
        searchStudents();
    } catch (e) {
        console.error(e);
        alert('批量修改失败: ' + (e.message || '未知错误'));
    }
}

// Export Modal Logic
function openExportModal() {
    const modal = document.getElementById('exportModal');
    if (modal) {
        modal.style.display = 'flex';
        loadExportColleges();
        // Clear previous selections
        document.getElementById('export-dept').innerHTML = '';
        document.getElementById('export-klass').innerHTML = '';
    }
}

function closeExportModal() {
    const modal = document.getElementById('exportModal');
    if (modal) modal.style.display = 'none';
}

function getSelectedValues(selectId) {
    const select = document.getElementById(selectId);
    if (!select) return [];
    return Array.from(select.selectedOptions).map(opt => opt.value).filter(v => v);
}

async function loadExportColleges() {
    try {
        const r = await api('/api/org/colleges');
        const list = Array.isArray(r) ? r : ((r && r.results) ? r.results : []);
        const el = document.getElementById('export-college');
        if (el) {
            el.innerHTML = list.map(x => `<option value="${x.id}">${x.name}</option>`).join('');
        }
    } catch(e) {}
}

async function loadExportDepts() {
    try {
        const collegeIds = getSelectedValues('export-college');
        let url = '/api/org/departments';
        if (collegeIds.length > 0) {
            // Note: Currently backend for departments filter might not support multi-college like ?college__in=...
            // Standard DRF filter usually supports ?college=1&college=2 if properly configured or custom filter.
            // But let's assume our backend might need multiple calls or a custom filter.
            // For now, let's try querying departments for each college or if the backend supports filtering by multiple colleges.
            // Since we didn't modify DepartmentViewSet, let's just fetch all if no specific filter support, or fetch individually.
            // Actually, best approach is to fetch all departments and filter client side if list is small, or just fetch all.
            // But wait, the prompt is about export filter.
            // Let's assume we fetch all departments for now or improve backend to support ?college__in
            // For simplicity, let's just fetch all departments and filter in JS if needed, or better yet:
            // Let's implement dynamic fetching.
            
            // However, to be safe and simple: Fetch all departments and filter by selected colleges in JS.
            // Or better: Use the API but we know the current API might strictly filter by one college.
            // Let's try to fetch all departments (size=1000) and filter.
            url = '/api/org/departments?size=1000';
        }
        
        const r = await api(url);
        let list = Array.isArray(r) ? r : ((r && r.results) ? r.results : []);
        
        if (collegeIds.length > 0) {
            list = list.filter(d => collegeIds.includes(String(d.college) || String(d.college_id)));
        }
        
        const el = document.getElementById('export-dept');
        if (el) {
            el.innerHTML = list.map(x => `<option value="${x.id}">${x.name}</option>`).join('');
        }
        // Also clear classes
        document.getElementById('export-klass').innerHTML = '';
    } catch(e) {}
}

async function loadExportClasses() {
    try {
        const deptIds = getSelectedValues('export-dept');
        let url = '/api/org/classes?size=1000';
        
        const r = await api(url);
        let list = Array.isArray(r) ? r : ((r && r.results) ? r.results : []);
        
        if (deptIds.length > 0) {
            list = list.filter(c => deptIds.includes(String(c.major) || String(c.major_id)));
        }
        
        const el = document.getElementById('export-klass');
        if (el) {
            el.innerHTML = list.map(x => `<option value="${x.id}">${x.name}</option>`).join('');
        }
    } catch(e) {}
}

async function confirmExport() {
    try {
        const collegeIds = getSelectedValues('export-college');
        const deptIds = getSelectedValues('export-dept');
        const classIds = getSelectedValues('export-klass');
        
        const p = new URLSearchParams();
        if (collegeIds.length > 0) p.append('college', collegeIds.join(','));
        if (deptIds.length > 0) p.append('department', deptIds.join(','));
        if (classIds.length > 0) p.append('class', classIds.join(','));
        p.append('size', '10000');

        const r = await api('/api/accounts/students/?' + p.toString());
        const list = Array.isArray(r) ? r : (r.results || []);

        if (list.length === 0) {
            alert('没有数据可导出');
            return;
        }

        const data = list.map(x => ({
            '学号': x.student_id,
            '姓名': (x.user_profile && x.user_profile.user && x.user_profile.user.first_name) || (x.user_profile && x.user_profile.user && x.user_profile.user.username) || '-',
            '班级': x.class_name || x.school_class || '-',
            '状态': x.status || '-',
            '联系方式': (x.user_profile && x.user_profile.phone) || '-'
        }));

        const ws = XLSX.utils.json_to_sheet(data);
        const wb = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(wb, ws, "学生列表");
        XLSX.writeFile(wb, "学生列表.xlsx");
        
        closeExportModal();
    } catch (e) {
        console.error(e);
        alert('导出失败: ' + (e.message || '未知错误'));
    }
}

// Import Logic
async function importStudents(input) {
    const file = input.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = async function(e) {
        try {
            const data = new Uint8Array(e.target.result);
            const workbook = XLSX.read(data, {type: 'array'});
            const firstSheetName = workbook.SheetNames[0];
            const worksheet = workbook.Sheets[firstSheetName];
            const jsonData = XLSX.utils.sheet_to_json(worksheet);

            if (jsonData.length === 0) {
                alert('文件内容为空');
                return;
            }

            // 转换数据格式
            const students = jsonData.map(row => ({
                student_id: row['学号'], // 仅用于验证或更新
                name: row['姓名'],
                class_name: row['班级'], // 需要后端支持按班级名称查找
                status: row['状态'] || '在读',
                phone: row['联系方式']
            }));

            // 批量导入需要后端支持，这里我们使用逐个添加或后端提供的批量接口
            // 假设后端有一个批量导入接口 /api/accounts/import
            // 但目前后端 BulkImportView 只支持 CSV/Excel 文件的直接上传
            // 所以我们使用文件上传方式调用 BulkImportView

            const formData = new FormData();
            formData.append('file', file);
            formData.append('type', 'students');

            await api('/api/accounts/import', 'POST', formData);
            
            alert('导入成功');
            searchStudents();
        } catch (e) {
            console.error(e);
            alert('导入失败: ' + (e.detail || e.message || '未知错误'));
        } finally {
            input.value = ''; // 重置 input
        }
    };
    reader.readAsArrayBuffer(file);
}

// Add Student Logic
async function addStudent() {
    const name = document.getElementById('stu-add-name')?.value?.trim();
    const gender = document.getElementById('stu-add-gender')?.value;
    const klass = document.getElementById('stu-add-klass')?.value;
    const phone = document.getElementById('stu-add-phone')?.value?.trim();
    const msg = document.getElementById('stu-add-msg');
    
    // 验证必填字段
    if (!name) {
        if (msg) {
            msg.textContent = '请填写姓名';
            msg.className = 'text-danger';
        }
        return;
    }
    
    if (!klass) {
        if (msg) {
            msg.textContent = '请选择学院-专业-班级';
            msg.className = 'text-danger';
        }
        return;
    }
    
    // Validate phone if provided
    if (phone && phone !== '无' && !/^1[3-9]\d{9}$/.test(phone)) {
         if (msg) {
             msg.textContent = '手机号格式不正确（应为11位数字，以1开头，或填写"无"）';
             msg.className = 'text-danger';
         }
         return;
    }

    try {
        const data = {
            name_write: name,
            school_class: Number(klass)
        };
        if (gender) {
            data.gender = gender;
        }
        if (phone && phone !== '无') {
            data.phone = phone;
        }
        
        const result = await api('/api/accounts/students/', 'POST', data);
        if (msg) {
            msg.textContent = `新增成功！学号：${result.student_id}`;
            msg.className = 'text-success';
        }

        // Clear inputs
        document.getElementById('stu-add-name').value = '';
        document.getElementById('stu-add-gender').value = '';
        document.getElementById('stu-add-college').value = '';
        document.getElementById('stu-add-dept').value = '';
        document.getElementById('stu-add-klass').value = '';
        document.getElementById('stu-add-phone').value = '';
        // 重新加载专业和班级选项
        loadDepts('stu-add-dept', '');
        loadClasses('stu-add-klass', '');
        
        // Refresh list from database
        searchStudents();
    } catch (e) {
        if (msg) {
            let errorMsg = '新增失败: ';
            if (e.error) {
                if (typeof e.error === 'string') {
                    errorMsg += e.error;
                } else if (e.error.school_class) {
                    errorMsg += e.error.school_class[0] || '班级选择错误';
                } else if (e.error.name) {
                    errorMsg += e.error.name[0] || '姓名错误';
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

// Edit Student Logic
let editCtx = { id: null };

async function editStudent(id) {
    editCtx.id = id;
    const modal = document.getElementById('editModal');
    const form = document.getElementById('editForm');
    const title = document.getElementById('editTitle');
    
    try {
        const s = await api('/api/accounts/students/' + id + '/');
        title.textContent = '编辑学生';
        
        // Determine current selections
        const klassId = s.school_class || '';
        let deptId = '';
        let collegeId = '';
        
        if (klassId) {
            try {
                const k = await api('/api/org/classes/' + klassId + '/');
                deptId = k.department;
                const d = await api('/api/org/departments/' + deptId + '/');
                collegeId = d.college;
            } catch(e) {}
        }

        // 获取当前性别
        const currentGender = (s.user_profile && s.user_profile.gender) || '';

        form.innerHTML = `
            <div class="row g-3">
                <div class="col-12 col-md-6">
                    <label class="form-label small fw-bold text-secondary">学号 <span class="text-muted">(不可修改)</span></label>
                    <input class="form-control form-control-sm" value="${s.student_id}" disabled />
                </div>
                <div class="col-12 col-md-6">
                    <label class="form-label small fw-bold text-secondary">姓名 <span class="text-muted">(不可修改)</span></label>
                    <input class="form-control form-control-sm" value="${(s.user_profile && s.user_profile.user && s.user_profile.user.first_name) || ''}" disabled />
                </div>
                <div class="col-12 col-md-6">
                    <label class="form-label small fw-bold text-secondary">性别</label>
                    <select id="edit-stu-gender" class="form-select form-select-sm">
                        <option value="">未设置</option>
                        <option value="male" ${currentGender === 'male' ? 'selected' : ''}>男</option>
                        <option value="female" ${currentGender === 'female' ? 'selected' : ''}>女</option>
                    </select>
                </div>
                <div class="col-12 col-md-6">
                    <label class="form-label small fw-bold text-secondary">学院</label>
                    <select id="edit-stu-college" class="form-select form-select-sm"></select>
                </div>
                <div class="col-12 col-md-6">
                    <label class="form-label small fw-bold text-secondary">专业</label>
                    <select id="edit-stu-dept" class="form-select form-select-sm"></select>
                </div>
                <div class="col-12 col-md-6">
                    <label class="form-label small fw-bold text-secondary">班级</label>
                    <select id="edit-stu-class" class="form-select form-select-sm"></select>
                </div>
                <div class="col-12 col-md-6">
                    <label class="form-label small fw-bold text-secondary">联系电话</label>
                    <input id="edit-stu-phone" class="form-control form-control-sm" value="${(s.user_profile && s.user_profile.phone) || ''}" placeholder="请输入联系电话" />
                </div>
            </div>
        `;
        
        // Load options with pre-selection
        await loadColleges('edit-stu-college', collegeId);
        await loadDepts('edit-stu-dept', collegeId, deptId);
        await loadClasses('edit-stu-class', deptId, klassId);
        
        // Bind Edit Cascades
        document.getElementById('edit-stu-college').addEventListener('change', async function() {
            await loadDepts('edit-stu-dept', this.value);
            await loadClasses('edit-stu-class', document.getElementById('edit-stu-dept').value);
        });
        document.getElementById('edit-stu-dept').addEventListener('change', async function() {
            await loadClasses('edit-stu-class', this.value);
        });

        modal.style.display = 'flex';
    } catch(e) {
        alert('加载失败');
    }
}

async function saveEdit() {
    const id = editCtx.id;
    const gender = document.getElementById('edit-stu-gender').value;
    const klass = document.getElementById('edit-stu-class').value;
    const phone = document.getElementById('edit-stu-phone').value;
    
    if (!klass) {
        alert('请选择班级');
        return;
    }
    if (phone && phone !== '无' && !/^1[3-9]\d{9}$/.test(phone)) {
         alert('手机号格式不正确（应为11位数字，以1开头，或填写"无"）');
         return;
    }

    try {
        const data = {
            school_class: klass,
            phone: phone
        };
        if (gender) {
            data.gender = gender;
        }
        
        await api('/api/accounts/students/' + id + '/', 'PATCH', data);
        document.getElementById('editModal').style.display = 'none';
        searchStudents();
    } catch(e) {
        alert('保存失败: ' + e.message);
    }
}

async function deleteStudent(id) {
    if (!confirm('确认删除该学生？')) return;
    try {
        await api('/api/accounts/students/' + id + '/', 'DELETE');
        searchStudents();
    } catch (e) {
        alert('删除失败 (可能无权限)');
    }
}

function closeEdit() {
    document.getElementById('editModal').style.display = 'none';
}

// Initialization
window.addEventListener('DOMContentLoaded', () => {
    // Load initial filters
    loadColleges('stu-college');
    loadDepts('stu-dept');
    loadClasses('stu-klass');
    
    // Load Add form options
    loadColleges('stu-add-college');
    
    // Bind Search Cascades
    document.getElementById('stu-college')?.addEventListener('change', function() {
        loadDepts('stu-dept', this.value);
        loadClasses('stu-klass', '', ''); // Reset class
    });
    document.getElementById('stu-dept')?.addEventListener('change', function() {
        loadClasses('stu-klass', this.value);
    });
    
    // Bind Add Cascades
    document.getElementById('stu-add-college')?.addEventListener('change', function() {
        loadDepts('stu-add-dept', this.value);
        loadClasses('stu-add-klass', '', '');
    });
    document.getElementById('stu-add-dept')?.addEventListener('change', function() {
        loadClasses('stu-add-klass', this.value);
    });
    
    // 从URL参数中读取搜索关键词并预填充
    const urlParams = new URLSearchParams(window.location.search);
    const searchQuery = urlParams.get('q');
    const searchInput = document.getElementById('stu-q');
    
    if (searchQuery && searchInput) {
        searchInput.value = decodeURIComponent(searchQuery);
    }
    
    // Search Input Listener (添加防抖)
    let searchTimeout = null;
    document.getElementById('stu-q')?.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            searchStudents();
        }, 300);
    });
    document.getElementById('stu-status')?.addEventListener('change', searchStudents);
    document.getElementById('stu-klass')?.addEventListener('change', searchStudents);

    // 执行初始搜索（如果有URL参数，会使用预填充的值）
    searchStudents(1);
});
