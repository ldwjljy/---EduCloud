async function changePwd(){try{const r=await api('/api/accounts/password/change','POST',{old_password:document.getElementById('oldpwd').value,new_password:document.getElementById('newpwd').value});document.getElementById('pwdmsg').textContent=r.detail||'成功'}catch(e){document.getElementById('pwdmsg').textContent=e.message}}
async function changePhone(){
    const phoneInput = document.getElementById('newphone');
    const msgEl = document.getElementById('phonemsg');
    const phone = phoneInput.value.trim();
    
    // 验证手机号格式：11位数字，以1开头
    const phoneRegex = /^1[3-9]\d{9}$/;
    
    if (!phone) {
        msgEl.textContent = '请输入手机号';
        msgEl.className = 'mt-2 text-danger';
        return;
    }
    
    if (!phoneRegex.test(phone)) {
        msgEl.textContent = '手机号格式不正确，请输入11位有效手机号';
        msgEl.className = 'mt-2 text-danger';
        return;
    }
    
    try {
        const r = await api('/api/accounts/phone/change', 'POST', { phone: phone });
        msgEl.textContent = r.detail || '手机号修改成功';
        msgEl.className = 'mt-2 text-success';
        phoneInput.value = '';
        // 刷新个人信息显示
        loadProfileInfo();
    } catch (e) {
        msgEl.textContent = e.message || '修改失败';
        msgEl.className = 'mt-2 text-danger';
    }
}
async function loadProfileInfo() {
    const el = document.getElementById('profileInfo');
    if (!el) return;
    
    try {
        // 先获取当前用户信息
        const me = await api('/api/accounts/me');
        const role = me?.role || 'anonymous';
        
        // 根据角色显示不同的信息
        if (role === 'student') {
            // 学生：获取自己的学生档案
            try {
                const sps = await api('/api/accounts/students/?size=1');
                const list = Array.isArray(sps) ? sps : (sps && sps.results ? sps.results : []);
                
                if (list && list.length > 0) {
                    const sp = list[0];
                    let html = `
                        <div class="row mb-2"><div class="col-4 text-secondary">学号</div><div class="col-8 fw-bold">${sp.student_id || '-'}</div></div>
                        <div class="row mb-2"><div class="col-4 text-secondary">姓名</div><div class="col-8 fw-bold">${sp.name || '-'}</div></div>
                        <div class="row mb-2"><div class="col-4 text-secondary">学院</div><div class="col-8">${sp.college_name || '-'}</div></div>
                        <div class="row mb-2"><div class="col-4 text-secondary">专业</div><div class="col-8">${sp.major_name || '-'}</div></div>
                        <div class="row mb-2"><div class="col-4 text-secondary">班级</div><div class="col-8">${sp.class_name || '-'}</div></div>
                        <div class="row mb-2"><div class="col-4 text-secondary">学籍状态</div><div class="col-8"><span class="badge bg-${sp.status === '在读' ? 'success' : (sp.status === '毕业' ? 'secondary' : 'warning')}">${sp.status || '-'}</span></div></div>
                    `;
                    el.innerHTML = html;
                    return;
                }
            } catch (e) {
                console.error('获取学生信息失败:', e);
            }
        } else if (role === 'teacher' || role === 'head_teacher') {
            // 教师：获取自己的教师档案
            try {
                const tps = await api('/api/accounts/teachers/?size=1');
                const list = Array.isArray(tps) ? tps : (tps && tps.results ? tps.results : []);
                
                if (list && list.length > 0) {
                    const tp = list[0];
                    const user = tp.user_profile?.user || {};
                    
                    // 使用序列化器返回的 position_type_display，如果没有则使用 position_type 映射
                    let positionDisplay = tp.position_type_display;
                    if (!positionDisplay && tp.position_type) {
                        const positionTypeMap = {
                            'super_admin': '超级管理员',
                            'principal': '校长',
                            'vice_principal': '副校长',
                            'dean': '院长',
                            'vice_dean': '副院长',
                            'head_teacher': '班主任',
                            'teacher': '教师'
                        };
                        positionDisplay = positionTypeMap[tp.position_type] || tp.position_type;
                    }
                    if (!positionDisplay) {
                        positionDisplay = tp.title || '-';
                    }
                    
                    let html = `
                        <div class="row mb-2"><div class="col-4 text-secondary">工号</div><div class="col-8 fw-bold">${tp.teacher_id || '-'}</div></div>
                        <div class="row mb-2"><div class="col-4 text-secondary">姓名</div><div class="col-8 fw-bold">${user.first_name || user.username || '-'}</div></div>
                        <div class="row mb-2"><div class="col-4 text-secondary">职务</div><div class="col-8">${positionDisplay}</div></div>
                        <div class="row mb-2"><div class="col-4 text-secondary">部门</div><div class="col-8">${tp.department_name || '-'}</div></div>
                        <div class="row mb-2"><div class="col-4 text-secondary">学院</div><div class="col-8">${tp.college_name || '-'}</div></div>
                        <div class="row mb-2"><div class="col-4 text-secondary">联系电话</div><div class="col-8">${tp.user_profile?.phone || '-'}</div></div>
                    `;
                    el.innerHTML = html;
                    return;
                }
            } catch (e) {
                console.error('获取教师信息失败:', e);
            }
        }
        
        // 管理员或其他角色：显示基本信息
        const roleDisplay = {
            'super_admin': '超级管理员',
            'principal': '校长',
            'vice_principal': '副校长',
            'dean': '院长',
            'vice_dean': '副院长',
            'teacher': '教师',
            'head_teacher': '班主任',
            'student': '学生'
        };
        
        let html = `
            <div class="row mb-2"><div class="col-4 text-secondary">用户名</div><div class="col-8 fw-bold">${me?.username || '-'}</div></div>
            <div class="row mb-2"><div class="col-4 text-secondary">角色</div><div class="col-8"><span class="badge bg-primary">${roleDisplay[role] || role}</span></div></div>
        `;
        
        // 如果有用户档案信息，显示更多
        try {
            const profile = await api(`/api/accounts/profiles/${me?.profile_id || ''}/`);
            if (profile) {
                if (profile.phone) {
                    html += `<div class="row mb-2"><div class="col-4 text-secondary">联系电话</div><div class="col-8">${profile.phone}</div></div>`;
                }
                if (profile.address) {
                    html += `<div class="row mb-2"><div class="col-4 text-secondary">地址</div><div class="col-8">${profile.address}</div></div>`;
                }
            }
        } catch (e) {
            // 忽略错误，继续显示基本信息
        }
        
        el.innerHTML = html;
    } catch (e) {
        el.textContent = '加载失败: ' + (e.message || '未知错误');
        console.error(e);
    }
}
async function loadStudyInfo(){
    const el = document.getElementById('studyInfo');
    if (!el) return;
    
    try {
        const me = await api('/api/accounts/me');
        const role = me?.role || 'anonymous';
        
        // 只有学生才显示学习信息
        if (role !== 'student') {
            el.innerHTML = '<span class="text-muted">此信息仅对学生可见</span>';
            return;
        }
        
        const sps = await api('/api/accounts/students/?size=1');
        const list = Array.isArray(sps) ? sps : (sps && sps.results ? sps.results : []);
        
        if (!list || list.length === 0) {
            el.textContent = '未找到学生资料';
            return;
        }
        
        const sp = list[0];
        const classId = sp.school_class;
        let gradeYear = '';
        try {
            const c = await api('/api/org/classes/' + classId + '/');
            gradeYear = c.enrollment_year || c.grade_year || '';
        } catch (e) {
            console.error('获取班级信息失败:', e);
        }
        
        // 获取本学期课程表（默认第1周）
        // 注意：学生角色访问API时会自动过滤到该学生所在班级的课程表
        let courseCount = 0;
        let coursesList = [];
        try {
            // 获取课程表（学生角色会自动过滤到自己的班级）
            const schedules = await api('/api/courses/schedules/?week_number=1');
            const scheduleList = Array.isArray(schedules) ? schedules : (schedules && schedules.results ? schedules.results : []);
            
            // 去重课程（同一课程可能有多节课）
            const uniqueCourses = new Map();
            scheduleList.forEach(s => {
                if (s.course && !uniqueCourses.has(s.course)) {
                    uniqueCourses.set(s.course, {
                        name: s.course_name || '未知课程'
                    });
                }
            });
            
            courseCount = uniqueCourses.size;
            coursesList = Array.from(uniqueCourses.values());
        } catch (e) {
            console.error('获取课程表失败:', e);
        }
        
        // 获取平均成绩
        let avgScore = '-';
        try {
            const grades = await api('/api/grades/grades/');
            const gradeList = Array.isArray(grades) ? grades : (grades && grades.results ? grades.results : []);
            
            if (gradeList && gradeList.length > 0) {
                const validScores = gradeList.filter(g => g.score != null && g.score !== undefined).map(g => parseFloat(g.score));
                if (validScores.length > 0) {
                    const sum = validScores.reduce((a, b) => a + b, 0);
                    avgScore = (sum / validScores.length).toFixed(1);
                }
            }
        } catch (e) {
            console.error('获取成绩信息失败:', e);
        }
        
        // 构建显示内容
        let html = '';
        if (gradeYear) {
            html += `<div class="mb-2"><span class="text-secondary small">年级：</span><span class="fw-bold">${gradeYear}</span></div>`;
        }
        html += `<div class="mb-2"><span class="text-secondary small">课程数：</span><span class="fw-bold">${courseCount} 门</span></div>`;
        if (avgScore !== '-') {
            html += `<div class="mb-2"><span class="text-secondary small">平均分：</span><span class="fw-bold text-primary">${avgScore}</span></div>`;
        }
        
        // 显示完整课程列表
        if (coursesList.length > 0) {
            html += `<div class="mt-3 pt-2 border-top"><div class="text-secondary small mb-1">本学期课程：</div>`;
            coursesList.forEach(c => {
                html += `<div class="small text-muted mb-1">• ${c.name}</div>`;
            });
            html += `</div>`;
        }
        
        el.innerHTML = html || '<div class="text-secondary small">暂无学习信息</div>';
    } catch (e) {
        el.textContent = '加载失败';
        console.error(e);
    }
}

async function loadAttendanceInfo(){
    console.log('[考勤信息] loadAttendanceInfo 函数被调用');
    const el = document.getElementById('attInfo');
    if (!el) {
        console.warn('[考勤信息] 考勤信息元素未找到，ID: attInfo');
        return;
    }
    console.log('[考勤信息] 找到考勤信息元素');
    
    // 先显示加载中
    el.innerHTML = '<div class="text-muted small">加载中...</div>';
    
    try {
        const me = await api('/api/accounts/me');
        const role = me?.role || 'anonymous';
        console.log('[考勤信息] 当前用户角色:', role);
        
        // 只有学生才显示考勤信息
        if (role !== 'student') {
            el.innerHTML = '<span class="text-muted">此信息仅对学生可见</span>';
            return;
        }
        
        // 获取最近7天的考勤记录（而不仅仅是今天）
        const now = new Date();
        const today = now.toISOString().slice(0, 10);
        console.log('[考勤信息] 查询最近7天的考勤记录，今天日期:', today);
        
        // 获取最近7天的考勤记录（不限制日期，让学生能看到所有相关考勤）
        const r = await api('/api/attendance/records/');
        console.log('[考勤信息] API返回数据:', r);
        const list = Array.isArray(r) ? r : (r && r.results ? r.results : []);
        console.log('[考勤信息] 考勤记录列表（全部）:', list);
        
        // 如果没有记录，也显示鼓励信息
        if (!list || list.length === 0) {
            console.log('[考勤信息] 没有考勤记录，显示鼓励信息');
            el.innerHTML = '<div class="text-center py-2"><div class="text-success fw-bold mb-1">今天的你非常棒！</div><div class="text-muted small">继续加油</div></div>';
            return;
        }
        
        // 按日期排序，最新的在前
        const sortedList = list.sort((a, b) => {
            const dateA = new Date(a.date || 0);
            const dateB = new Date(b.date || 0);
            return dateB - dateA;
        });
        
        // 筛选出不正常的考勤（迟到、缺勤、请假），优先显示最近的
        const abnormalRecords = sortedList.filter(x => x.status && x.status !== 'present');
        console.log('[考勤信息] 异常考勤记录:', abnormalRecords);
        
        // 状态显示映射
        const statusMap = {
            'late': '迟到',
            'absent': '缺勤',
            'leave': '请假',
            'present': '正常'
        };
        
        // 状态颜色映射
        const statusColorMap = {
            'late': 'warning',
            'absent': 'danger',
            'leave': 'info',
            'present': 'success'
        };
        
        if (abnormalRecords.length === 0) {
            // 如果都正常，显示鼓励信息，但也可以显示最近的正常记录
            const todayRecords = sortedList.filter(x => x.date === today);
            if (todayRecords.length > 0) {
                console.log('[考勤信息] 今天有考勤记录且都正常，显示鼓励信息');
                el.innerHTML = '<div class="text-center py-2"><div class="text-success fw-bold mb-1">今天的你非常棒！</div><div class="text-muted small">继续加油</div></div>';
            } else {
                console.log('[考勤信息] 今天没有考勤记录，显示鼓励信息');
                el.innerHTML = '<div class="text-center py-2"><div class="text-success fw-bold mb-1">今天的你非常棒！</div><div class="text-muted small">继续加油</div></div>';
            }
            return;
        }
        
        // 显示不正常的考勤记录：日期-课程-考勤状态（最多显示5条最近的）
        console.log('[考勤信息] 显示异常考勤记录，共', abnormalRecords.length, '条');
        const displayRecords = abnormalRecords.slice(0, 5);
        el.innerHTML = displayRecords.map(x => {
            const date = x.date || today;
            const courseName = x.course_name || '未知课程';
            const statusDisplay = statusMap[x.status] || x.status_display || '未知';
            const statusColor = statusColorMap[x.status] || 'secondary';
            return `<div class="small mb-2"><span class="text-secondary">${date}</span> - <span class="fw-bold">${courseName}</span> - <span class="badge bg-${statusColor}">${statusDisplay}</span></div>`;
        }).join('') + (abnormalRecords.length > 5 ? `<div class="text-muted small mt-2">还有 ${abnormalRecords.length - 5} 条记录...</div>` : '');
    } catch (e) {
        console.error('[考勤信息] 加载考勤信息失败:', e);
        el.innerHTML = '<div class="text-danger small">加载失败: ' + (e.message || '未知错误') + '</div>';
    }
}

async function loadGradeInfo(){
    const el = document.getElementById('gradeInfo');
    if (!el) return;
    
    try {
        const me = await api('/api/accounts/me');
        const role = me?.role || 'anonymous';
        
        // 只有学生才显示成绩信息
        if (role !== 'student') {
            el.innerHTML = '<span class="text-muted">此信息仅对学生可见</span>';
            return;
        }
        
        const items = await api('/api/grades/grades/');
        const list = Array.isArray(items) ? items : (items && items.results ? items.results : []);
        
        if (!list || list.length === 0) {
            el.textContent = '暂无成绩';
            return;
        }
        
        // 直接使用API返回的course_name字段，只显示课程名称，不显示课程代号
        const rows = [];
        for (const g of list.slice(0, 10)) {
            const courseName = g.course_name || '未知课程';
            const score = g.score !== null && g.score !== undefined ? g.score : '-';
            rows.push(`<div class="small mb-2"><div class="fw-bold text-primary">${courseName}</div><div class="text-secondary">分数：<strong class="text-dark">${score}</strong></div></div>`);
        }
        el.innerHTML = rows.join('');
    } catch (e) {
        // 如果是403错误（权限不足），静默处理，避免在控制台产生干扰
        if (e.message && e.message.includes('403')) {
            if (el) el.innerHTML = '<span class="text-muted">此信息仅对学生可见</span>';
            return;
        }
        el.textContent = '加载失败';
        console.error(e);
    }
}
// 创建广播通道用于接收考勤更新通知
let attendanceUpdateChannel = null;
try {
    attendanceUpdateChannel = new BroadcastChannel('attendance_updates');
} catch (e) {
    console.warn('BroadcastChannel not supported, using localStorage fallback');
}

// 监听考勤更新通知
function setupAttendanceUpdateListener() {
    console.log('[考勤监听] 设置考勤更新监听器');
    
    // 使用 BroadcastChannel 监听（跨标签页）
    if (attendanceUpdateChannel) {
        attendanceUpdateChannel.addEventListener('message', (event) => {
            console.log('[考勤监听] 收到 BroadcastChannel 消息:', event.data);
            if (event.data && (event.data.type === 'attendance_updated' || event.data.type === 'attendance_batch_updated')) {
                console.log('[考勤监听] 收到考勤更新通知（BroadcastChannel），立即刷新考勤信息');
                // 延迟一小段时间确保数据已更新
                setTimeout(() => {
                    loadAttendanceInfo();
                }, 100);
            }
        });
    } else {
        console.warn('[考勤监听] BroadcastChannel 不可用');
    }
    
    // 监听 localStorage 变化（跨标签页，storage 事件）
    window.addEventListener('storage', (event) => {
        console.log('[考勤监听] 收到 storage 事件:', event.key, event.newValue);
        if (event.key === 'attendance_update_check' && event.newValue) {
            console.log('[考勤监听] 收到考勤更新通知（Storage事件），立即刷新考勤信息');
            // 延迟一小段时间确保数据已更新
            setTimeout(() => {
                loadAttendanceInfo();
            }, 100);
        }
    });
    
    // 监听自定义事件（同标签页）
    window.addEventListener('attendanceUpdated', (event) => {
        console.log('[考勤监听] 收到 CustomEvent:', event.detail);
        if (event.detail && (event.detail.type === 'attendance_updated' || event.detail.type === 'attendance_batch_updated')) {
            console.log('[考勤监听] 收到考勤更新通知（CustomEvent），立即刷新考勤信息');
            // 延迟一小段时间确保数据已更新
            setTimeout(() => {
                loadAttendanceInfo();
            }, 100);
        }
    });
    
    // 轮询检查 localStorage（降级方案，用于不支持 BroadcastChannel 和 storage 事件的场景）
    let lastUpdateTime = 0;
    try {
        const stored = localStorage.getItem('attendance_update_check');
        if (stored) {
            lastUpdateTime = parseInt(stored, 10) || 0;
            console.log('[考勤监听] 初始化轮询，最后更新时间:', lastUpdateTime);
        }
    } catch (e) {
        console.warn('[考勤监听] 初始化轮询失败:', e);
    }
    
    setInterval(() => {
        try {
            const updateStr = localStorage.getItem('attendance_update_check');
            if (updateStr) {
                const updateTime = parseInt(updateStr, 10);
                if (updateTime > lastUpdateTime) {
                    lastUpdateTime = updateTime;
                    console.log('[考勤监听] 收到考勤更新通知（轮询），立即刷新考勤信息, timestamp:', updateTime);
                    // 延迟一小段时间确保数据已更新
                    setTimeout(() => {
                        loadAttendanceInfo();
                    }, 100);
                }
            }
        } catch (e) {
            // 忽略错误
        }
    }, 500); // 改为500ms轮询，更及时
}

window.addEventListener('DOMContentLoaded',()=>{
    loadProfileInfo();
    loadStudyInfo();
    loadAttendanceInfo();
    loadGradeInfo();
    
    // 设置考勤更新监听器
    setupAttendanceUpdateListener();
    
    // Auto-refresh every 20s
    setInterval(() => {
        loadProfileInfo();
        loadStudyInfo();
        loadAttendanceInfo();
        loadGradeInfo();
    }, 20000);
})
async function navGate(){try{const me=await api('/api/accounts/me');if(me&&me.role==='student'){document.querySelectorAll('.side a').forEach(a=>{const href=a.getAttribute('href')||'';if(href!=='/ui/accounts')a.style.display='none'})}}catch(e){}}
window.addEventListener('DOMContentLoaded',navGate)
