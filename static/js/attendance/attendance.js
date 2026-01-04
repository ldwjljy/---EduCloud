let attRole = { isAdmin: false, isTeacher: false };

// 默认筛选配置
const ATT_DEFAULT_FILTERS = {
    collegeName: '人工智能学院',
    departmentName: '移动互联网应用技术',
    className: '2023年移动互联网应用技术G5-1班',
    courseName: 'ArkTs'
};

function statusColor(s) {
    switch (s) {
        case 'present': return '#3fb950';
        case 'late': return '#d4a72c';
        case 'absent': return '#cf222e';
        case 'leave': return '#0969da';
        default: return '#3fb950';
    }
}

async function loadColleges() {
    try {
        const r = await api('/api/org/colleges');
        const c = document.getElementById('att-college');
        if (c) c.innerHTML = '<option value="">选择学院</option>' + r.map(x => `<option value="${x.id}">${x.name}</option>`).join('');
    } catch (e) {}
}

async function loadDepts() {
    let r = [];
    try {
        r = await api('/api/org/departments');
    } catch (e) {
        r = [];
    }
    const col = document.getElementById('att-college');
    const d = document.getElementById('att-dept');
    if (d) {
        const list = col && col.value ? r.filter(x => String(x.college) === String(col.value)) : r;
        d.innerHTML = '<option value="">选择专业</option>' + list.map(x => `<option value="${x.id}">${x.name}</option>`).join('');
    }
}

async function loadClasses() {
    let r = [];
    const dept = document.getElementById('att-dept');
    try {
        // 后端 ClassViewSet 过滤字段是 major，这里传 department 会导致筛选失效
        // 使用专业ID（即部门ID）作为 major 参数，保证按专业筛选班级生效
        const url = dept && dept.value ? ('/api/org/classes?major=' + dept.value) : '/api/org/classes';
        r = await api(url);
    } catch (e) {
        try {
            r = await api('/api/org/classes');
        } catch (err) {
            r = [];
        }
    }
    const c = document.getElementById('att-class');
    if (c) c.innerHTML = '<option value="">选择班级</option>' + r.map(x => `<option value="${x.id}">${x.name}</option>`).join('');
}

// 优化：按需加载学生，只在选择班级时加载
async function loadStudents() {
    const klass = document.getElementById('att-class');
    const klassId = klass && klass.value ? klass.value : '';
    
    // 如果没有选择班级，清空学生列表
    if (!klassId) {
        const s = document.getElementById('att-student');
        if (s) s.innerHTML = '<option value="">全部学生</option>';
        return [];
    }
    
    let r = [];
    try {
        const url = '/api/accounts/students?class=' + klassId;
        r = await api(url);
    } catch (e) {
        try {
            r = await api('/api/accounts/students');
        } catch (err) {
            r = [];
        }
    }
    const s = document.getElementById('att-student');
    if (s) {
        s.innerHTML = '<option value="">全部学生</option>' + r.map(x => {
            const name = (x.user_profile && x.user_profile.user && x.user_profile.user.first_name) || 
                        (x.user_profile && x.user_profile.user && x.user_profile.user.username) || 
                        x.student_id;
            return `<option value="${x.id}">${name}</option>`;
        }).join('');
    }
    return r;
}

async function loadSchedules() {
    let r = [];
    try {
        const result = await api('/api/courses/schedules/');
        r = Array.isArray(result) ? result : (result.results || []);
        const s = document.getElementById('att-schedule');
        if (s) {
            const courseMap = new Map();
            r.forEach(x => {
                const courseId = x.course || x.course_id;
                const courseName = x.course_name || '-';
                if (!courseMap.has(courseId) || courseMap.get(courseId).id > x.id) {
                    courseMap.set(courseId, { id: x.id, courseId: courseId, courseName: courseName, scheduleIds: [] });
                }
                if (courseMap.has(courseId)) {
                    courseMap.get(courseId).scheduleIds.push(x.id);
                }
            });
            s.innerHTML = '<option value="">选择课程</option>' + Array.from(courseMap.values()).map(item => {
                const scheduleIdsStr = item.scheduleIds.join(',');
                return `<option value="${item.id}" data-schedules="${scheduleIdsStr}" data-course-id="${item.courseId}">${item.courseName}</option>`;
            }).join('');
        }
    } catch (e) {
        console.error('加载课程安排失败:', e);
        r = [];
    }
    return r;
}

// 根据名称为下拉框设置默认选中项（仅在当前尚未选择时生效）
function selectOptionByText(selectEl, targetText, force = false) {
    if (!selectEl || !targetText) return false;
    // 如果 force 为 false 且已有值，则不覆盖
    if (!force && selectEl.value) return false;
    const opts = Array.from(selectEl.options || []);
    const found = opts.find(o => (o.text || '').trim() === targetText.trim());
    if (found) {
        selectEl.value = found.value;
        return true;
    }
    return false;
}

async function fetchAttendance(params) {
    const p = new URLSearchParams();
    if (params.date) p.append('date', params.date);
    if (params.schedule) p.append('schedule', params.schedule);
    if (params.college) p.append('college', params.college);
    if (params.department) p.append('department', params.department);
    if (params.klass) p.append('class', params.klass);
    if (params.student) p.append('student', params.student);
     if (params.status) p.append('status', params.status);
    if (params.q) p.append('q', params.q);
    try {
        return await api('/api/attendance/records?' + p.toString());
    } catch (e) {
        return [];
    }
}

function mkRow(att, canEdit) {
    const sid = att.student_id || '-';
    const name = att.student_name || '-';
    const courseName = att.course_name || '-';
    const college = att.college_name || '-';
    const major = att.major_name || '-';
    const className = att.class_name || '-';
    const status = att.status || 'present';
    const statusDisplay = att.status_display || (status === 'present' ? '正常' : status === 'late' ? '迟到' : status === 'absent' ? '缺勤' : '请假');
    const color = statusColor(status);
    const remark = att.remark || '';
    const statusCell = canEdit ? 
        `<select data-att-id="${att.id}" class="form-select form-select-sm" onchange="onStatusChange(this)" style="min-width:100px;">
            <option value="present" ${status === 'present' ? 'selected' : ''}>正常</option>
            <option value="late" ${status === 'late' ? 'selected' : ''}>迟到</option>
            <option value="absent" ${status === 'absent' ? 'selected' : ''}>缺勤</option>
            <option value="leave" ${status === 'leave' ? 'selected' : ''}>请假</option>
        </select>` :
        `<span style="display:inline-block;padding:4px 8px;border-radius:4px;background:${color};color:#fff;font-size:0.875rem;">${statusDisplay}</span>`;
    const remarkCell = canEdit ? 
        `<input type="text" data-att-id="${att.id}" class="form-control form-control-sm" value="${remark}" placeholder="填写备注" onblur="onRemarkChange(this)" style="min-width:150px;">` :
        `<span>${remark || '-'}</span>`;
    return `<tr>
        <td>${sid}</td>
        <td>${name}</td>
        <td>${courseName}</td>
        <td>${college}</td>
        <td>${major}</td>
        <td>${className}</td>
        <td>${statusCell}</td>
        <td>${remarkCell}</td>
    </tr>`;
}

async function renderAttendance() {
    // 如果正在初始化，不执行查询，只显示提示
    if (isInitializing) {
        const tbody = document.getElementById('att-rows');
        const total = document.getElementById('att-total');
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted py-3">请选择筛选条件后点击"查询"按钮</td></tr>';
        }
        if (total) total.textContent = '';
        return;
    }
    
    const date = document.getElementById('att-date').value || new Date().toISOString().slice(0, 10);
    const scheduleSelect = document.getElementById('att-schedule');
    const schedule = scheduleSelect ? scheduleSelect.value || '' : '';
    let scheduleIds = [];
    if (schedule && scheduleSelect) {
        const selectedOption = scheduleSelect.options[scheduleSelect.selectedIndex];
        if (selectedOption && selectedOption.dataset.schedules) {
            scheduleIds = selectedOption.dataset.schedules.split(',').filter(id => id);
        } else {
            scheduleIds = [schedule];
        }
    }
    const college = document.getElementById('att-college').value || '';
    const department = document.getElementById('att-dept').value || '';
    const klass = document.getElementById('att-class').value || '';
    const student = document.getElementById('att-student').value || '';
    const status = document.getElementById('att-status') ? document.getElementById('att-status').value || '' : '';
    const q = (document.getElementById('att-q') && document.getElementById('att-q').value || '').trim();
    const params = {
        date,
        schedule: scheduleIds.length > 0 ? scheduleIds.join(',') : schedule,
        college,
        department,
        klass,
        student,
        status,
        q
    };
    const attRecs = await fetchAttendance(params);
    let records = Array.isArray(attRecs) ? attRecs : (attRecs.results || []);
    if (scheduleIds.length > 1) {
        const statusPriority = { 'absent': 3, 'late': 2, 'leave': 1, 'present': 0 };
        const seen = new Map();
        records.forEach(att => {
            const key = att.student_id + '_' + (att.course_id || att.course);
            if (!seen.has(key)) {
                seen.set(key, att);
            } else {
                const existing = seen.get(key);
                const currentPriority = statusPriority[att.status] || 0;
                const existingPriority = statusPriority[existing.status] || 0;
                if (currentPriority > existingPriority) {
                    seen.set(key, att);
                }
            }
        });
        records = Array.from(seen.values());
    }
    const canEdit = attRole.isAdmin || attRole.isTeacher;
    const rows = records.map(att => mkRow(att, canEdit));
    const tbody = document.getElementById('att-rows');
    const total = document.getElementById('att-total');
    if (tbody) {
        if (rows.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted py-3">暂无考勤记录</td></tr>';
        } else {
            tbody.innerHTML = rows.join('');
        }
    }
    if (total) total.textContent = '共 ' + records.length + ' 条记录';
}

// 初始化默认筛选：学院、专业、班级、课程
async function initAttendanceDefaultFilters() {
    const collegeSelect = document.getElementById('att-college');
    const deptSelect = document.getElementById('att-dept');
    const classSelect = document.getElementById('att-class');
    const scheduleSelect = document.getElementById('att-schedule');

    // 默认学院：直接设置，不触发事件
    if (collegeSelect && ATT_DEFAULT_FILTERS.collegeName) {
        const set = selectOptionByText(collegeSelect, ATT_DEFAULT_FILTERS.collegeName, true);
        if (set) {
            // 如果设置了学院，加载对应的专业和班级（但不触发查询）
            await loadDepts();
            
            // 默认专业：依赖学院
            if (deptSelect && ATT_DEFAULT_FILTERS.departmentName) {
                const deptSet = selectOptionByText(deptSelect, ATT_DEFAULT_FILTERS.departmentName, true);
                if (deptSet) {
                    // 如果设置了专业，加载对应的班级
                    await loadClasses();
                    
                    // 默认班级：依赖专业
                    if (classSelect && ATT_DEFAULT_FILTERS.className) {
                        selectOptionByText(classSelect, ATT_DEFAULT_FILTERS.className, true);
                    }
                }
            }
        }
    }

    // 默认课程：延迟加载，不阻塞初始化
    // 课程列表会在需要时加载，这里只设置值（如果列表已加载）
    if (scheduleSelect && ATT_DEFAULT_FILTERS.courseName) {
        // 如果课程列表还没加载，延迟设置
        if (scheduleSelect.options.length <= 1) {
            // 延迟加载课程并设置默认值
            setTimeout(async () => {
                if (attRole.isAdmin || attRole.isTeacher) {
                    await loadSchedules();
                    const opts = Array.from(scheduleSelect.options || []);
                    const found = opts.find(o => (o.text || '').trim() === ATT_DEFAULT_FILTERS.courseName.trim());
                    if (found) {
                        scheduleSelect.value = found.value;
                    }
                }
            }, 1000);
        } else {
            // 如果已加载，直接设置
            const opts = Array.from(scheduleSelect.options || []);
            const found = opts.find(o => (o.text || '').trim() === ATT_DEFAULT_FILTERS.courseName.trim());
            if (found) {
                scheduleSelect.value = found.value;
            }
        }
    }
}

// 创建广播通道用于跨标签页通信
let attendanceBroadcastChannel = null;
try {
    attendanceBroadcastChannel = new BroadcastChannel('attendance_updates');
} catch (e) {
    console.warn('BroadcastChannel not supported, using localStorage fallback');
}

// 发送考勤更新通知
function notifyAttendanceUpdate(attendanceId, studentId) {
    const notification = {
        type: 'attendance_updated',
        attendanceId: attendanceId,
        studentId: studentId,
        timestamp: Date.now()
    };
    
    console.log('发送考勤更新通知:', notification);
    
    if (attendanceBroadcastChannel) {
        // 使用 BroadcastChannel 发送通知（支持跨标签页和同源窗口）
        attendanceBroadcastChannel.postMessage(notification);
        console.log('已通过 BroadcastChannel 发送通知');
    }
    
    // 同时使用 localStorage 作为降级方案（用于不支持 BroadcastChannel 的浏览器）
    try {
        const timestamp = Date.now().toString();
        localStorage.setItem('attendance_update_check', timestamp);
        // 触发自定义事件（用于同标签页监听）
        window.dispatchEvent(new CustomEvent('attendanceUpdated', { detail: notification }));
        console.log('已通过 localStorage 和 CustomEvent 发送通知, timestamp:', timestamp);
    } catch (e) {
        console.warn('Failed to send attendance update notification:', e);
    }
}

async function onStatusChange(sel) {
    const attId = Number(sel.getAttribute('data-att-id'));
    const status = sel.value;
    try {
        const response = await api('/api/attendance/records/' + attId + '/', 'PATCH', { status });
        // 从响应中获取学生ID
        const studentId = response?.student || null;
        // 发送更新通知
        notifyAttendanceUpdate(attId, studentId);
        renderAttendance();
    } catch (e) {
        alert('更新失败: ' + (e.message || '未知错误'));
    }
}

async function onRemarkChange(input) {
    const attId = Number(input.getAttribute('data-att-id'));
    const remark = input.value || '';
    try {
        const response = await api('/api/attendance/records/' + attId + '/', 'PATCH', { remark });
        // 从响应中获取学生ID
        const studentId = response?.student || null;
        // 发送更新通知
        notifyAttendanceUpdate(attId, studentId);
    } catch (e) {
        alert('更新备注失败: ' + (e.message || '未知错误'));
    }
}

async function gate() {
    try {
        const me = await api('/api/accounts/me');
        const role = me.role;
        attRole.isAdmin = ['super_admin', 'principal', 'vice_principal'].includes(role);
        attRole.isTeacher = ['teacher', 'head_teacher'].includes(role);
    } catch (e) {
        attRole.isAdmin = false;
        attRole.isTeacher = false;
    }
}

// 监听考勤更新通知（用于学生端在考勤管理页面时也能实时更新）
function setupAttendanceUpdateListener() {
    // 创建广播通道用于接收考勤更新通知
    let attendanceUpdateChannel = null;
    try {
        attendanceUpdateChannel = new BroadcastChannel('attendance_updates');
    } catch (e) {
        console.warn('BroadcastChannel not supported');
    }
    
    // 使用 BroadcastChannel 监听（跨标签页）
    if (attendanceUpdateChannel) {
        attendanceUpdateChannel.addEventListener('message', (event) => {
            if (event.data && (event.data.type === 'attendance_updated' || event.data.type === 'attendance_batch_updated')) {
                console.log('考勤管理页面：收到考勤更新通知，立即刷新');
                // 立即刷新考勤列表
                renderAttendance();
            }
        });
    }
    
    // 监听 localStorage 变化（跨标签页，storage 事件）
    window.addEventListener('storage', (event) => {
        if (event.key === 'attendance_update_check' && event.newValue) {
            console.log('考勤管理页面：收到考勤更新通知（Storage事件），立即刷新');
            // 立即刷新考勤列表
            renderAttendance();
        }
    });
    
    // 监听自定义事件（同标签页）
    window.addEventListener('attendanceUpdated', (event) => {
        if (event.detail && (event.detail.type === 'attendance_updated' || event.detail.type === 'attendance_batch_updated')) {
            console.log('考勤管理页面：收到考勤更新通知（CustomEvent），立即刷新');
            // 立即刷新考勤列表
            renderAttendance();
        }
    });
    
    // 轮询检查 localStorage（降级方案）
    let lastUpdateTime = 0;
    try {
        const stored = localStorage.getItem('attendance_update_check');
        if (stored) {
            lastUpdateTime = parseInt(stored, 10) || 0;
        }
    } catch (e) {
        // 忽略错误
    }
    
    setInterval(() => {
        try {
            const updateStr = localStorage.getItem('attendance_update_check');
            if (updateStr) {
                const updateTime = parseInt(updateStr, 10);
                if (updateTime > lastUpdateTime) {
                    lastUpdateTime = updateTime;
                    console.log('考勤管理页面：收到考勤更新通知（轮询），立即刷新');
                    renderAttendance();
                }
            }
        } catch (e) {
            // 忽略错误
        }
    }, 1000);
}

// 优化：只在需要时加载学生，而不是页面加载时
// 标记是否正在初始化，避免初始化时触发查询
let isInitializing = true;

window.addEventListener('DOMContentLoaded', () => {
    const d = document.getElementById('att-date');
    if (d) d.value = new Date().toISOString().slice(0, 10);
    
    // 立即显示提示信息，不等待数据加载
    const tbody = document.getElementById('att-rows');
    if (tbody) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted py-3">请选择筛选条件后点击"查询"按钮</td></tr>';
    }
    
    // 设置考勤更新监听器
    setupAttendanceUpdateListener();
    
    gate().then(async () => {
        // 只加载学院，不自动查询考勤数据
        await loadColleges();
        
        // 如果是管理员或教师，延迟加载课程列表（只在需要时加载）
        if (attRole.isAdmin || attRole.isTeacher) {
            // 延迟加载课程，不阻塞页面
            setTimeout(() => {
                loadSchedules().catch(e => console.warn('加载课程列表失败:', e));
            }, 500);
        }
        
        // 设置默认筛选值，但不触发查询
        try {
            await initAttendanceDefaultFilters();
        } catch (e) {
            console.warn('初始化默认考勤筛选失败:', e);
        }
        
        // 初始化完成，允许查询
        isInitializing = false;
    });
    
    const rowsEl = document.getElementById('att-rows');
    if (rowsEl) {
        new MutationObserver(() => {
            if (typeof initUISelects === 'function') initUISelects();
        }).observe(rowsEl, { childList: true });
    }
    
    // 课程下拉框：只加载课程，不自动查询
    document.getElementById('att-schedule')?.addEventListener('change', () => {
        if (!isInitializing && (attRole.isAdmin || attRole.isTeacher)) {
            // 如果课程列表还没加载，先加载
            const scheduleSelect = document.getElementById('att-schedule');
            if (scheduleSelect && scheduleSelect.options.length <= 1) {
                loadSchedules();
            }
        }
    });
    
    // 学院下拉框：只加载专业和班级，不自动查询
    document.getElementById('att-college')?.addEventListener('change', () => {
        loadDepts();
        loadClasses();
        // 清空学生列表
        const s = document.getElementById('att-student');
        if (s) s.innerHTML = '<option value="">全部学生</option>';
    });
    
    // 专业下拉框：只加载班级，不自动查询
    document.getElementById('att-dept')?.addEventListener('change', () => {
        loadClasses();
        // 清空学生列表
        const s = document.getElementById('att-student');
        if (s) s.innerHTML = '<option value="">全部学生</option>';
    });
    
    // 班级下拉框：只加载学生，不自动查询
    document.getElementById('att-class')?.addEventListener('change', () => {
        loadStudents();
    });
    
    // 其他筛选条件：不自动查询，等用户点击查询按钮
    // 移除所有自动查询的事件监听器
});

// 优化：markAllPresent函数，避免加载所有学生
async function markAllPresent() {
    const date = document.getElementById('att-date').value || new Date().toISOString().slice(0, 10);
    if (!(attRole.isAdmin || attRole.isTeacher)) {
        alert('无权限');
        return;
    }
    const college = document.getElementById('att-college').value || '';
    const department = document.getElementById('att-dept').value || '';
    const klass = document.getElementById('att-class').value || '';
    const student = document.getElementById('att-student').value || '';
    const q = (document.getElementById('att-q') && document.getElementById('att-q').value || '').trim();
    
    // 优化：只加载需要的学生，而不是所有学生
    let students = [];
    if (klass) {
        // 如果选择了班级，只加载该班级的学生
        students = await loadStudents();
    } else if (student) {
        // 如果选择了具体学生，只加载该学生
        try {
            const result = await api('/api/accounts/students?student=' + student);
            students = Array.isArray(result) ? result : (result.results || []);
        } catch (e) {
            students = [];
        }
    } else {
        // 如果没有选择，使用当前查询条件获取学生
        // 通过考勤记录反向查找学生
        const params = { date, college, department, klass, student, q };
        const attRecs = await fetchAttendance(params);
        const records = Array.isArray(attRecs) ? attRecs : (attRecs.results || []);
        const studentIds = [...new Set(records.map(r => r.student))];
        if (studentIds.length > 0) {
            try {
                const result = await api('/api/accounts/students?' + studentIds.map(id => 'id=' + id).join('&'));
                students = Array.isArray(result) ? result : (result.results || []);
            } catch (e) {
                students = [];
            }
        }
    }
    
    // 应用过滤条件
    if (klass) students = students.filter(x => String(x.school_class) === String(klass));
    if (student) students = students.filter(x => String(x.id) === String(student));
    if (q) {
        students = students.filter(x => {
            const name = (x.user_profile && x.user_profile.user && (x.user_profile.user.first_name || x.user_profile.user.username)) || '';
            return (x.student_id || '').includes(q) || name.includes(q);
        });
    }
    
    // 批量更新
    const updatedStudentIds = [];
    for (const s of students) {
        try {
            const existingResp = await api('/api/attendance/records?student=' + s.id + '&date=' + date);
            const existing = Array.isArray(existingResp) ? existingResp : (existingResp.results || []);
            if (existing && existing.length) {
                await api('/api/attendance/records/' + existing[0].id + '/', 'PATCH', { status: 'present' });
            } else {
                await api('/api/attendance/records/', 'POST', { student: s.id, date, status: 'present', remark: '' });
            }
            updatedStudentIds.push(s.id);
        } catch (e) {
            console.error('更新学生考勤失败:', e);
        }
    }
    
    // 批量更新完成后，发送通知（通知所有学生刷新）
    if (updatedStudentIds.length > 0) {
        const notification = {
            type: 'attendance_batch_updated',
            studentIds: updatedStudentIds,
            timestamp: Date.now()
        };
        
        if (attendanceBroadcastChannel) {
            attendanceBroadcastChannel.postMessage(notification);
        }
        
        try {
            localStorage.setItem('attendance_update_check', Date.now().toString());
            window.dispatchEvent(new CustomEvent('attendanceUpdated', { detail: notification }));
        } catch (e) {
            console.warn('Failed to send attendance batch update notification:', e);
        }
    }
    
    renderAttendance();
}
