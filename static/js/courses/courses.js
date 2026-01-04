
let tt = {
    slots: [],
    slotByKey: {},
    slotById: {},
    maxIndex: 0,
    courses: [],
    courseMap: {},
    teachers: [],
    teacherMap: {},
    teacherLabelMap: {},
    departments: [],
    deptMap: {},
    rooms: [],
    roomMap: {},
    indexLabel: {},
    selectedCourses: new Set(),
    config: { morning: 4, afternoon: 4 },
    weekdayNames: { 1: '周一', 2: '周二', 3: '周三', 4: '周四', 5: '周五', 6: '周六', 7: '周日' }
};

// ==================== 统一弹窗系统 ====================

let confirmCallback = null;

// 自定义 Alert 弹窗
function customAlert(message, title = '提示', type = 'info') {
    const modal = document.getElementById('customAlert');
    const titleEl = document.getElementById('alertTitle');
    const messageEl = document.getElementById('alertMessage');
    const iconEl = document.getElementById('alertIcon');

    if (!modal) return;

    titleEl.textContent = title;
    messageEl.textContent = message;

    // 设置图标类型
    iconEl.className = 'custom-modal-icon';
    switch (type) {
        case 'success':
            iconEl.classList.add('success-icon');
            iconEl.innerHTML = '<i class="fa-solid fa-circle-check"></i>';
            break;
        case 'warning':
            iconEl.classList.add('warning-icon');
            iconEl.innerHTML = '<i class="fa-solid fa-triangle-exclamation"></i>';
            break;
        case 'error':
            iconEl.classList.add('error-icon');
            iconEl.innerHTML = '<i class="fa-solid fa-circle-xmark"></i>';
            break;
        default:
            iconEl.innerHTML = '<i class="fa-solid fa-circle-info"></i>';
    }

    modal.style.display = 'flex';
}

function closeCustomAlert() {
    const modal = document.getElementById('customAlert');
    if (modal) modal.style.display = 'none';
}

// 自定义 Confirm 弹窗
function customConfirm(message, title = '确认操作') {
    return new Promise((resolve) => {
        const modal = document.getElementById('customConfirm');
        const titleEl = document.getElementById('confirmTitle');
        const messageEl = document.getElementById('confirmMessage');

        if (!modal) {
            resolve(false);
            return;
        }

        titleEl.textContent = title;
        messageEl.textContent = message;

        confirmCallback = resolve;
        modal.style.display = 'flex';
    });
}

function closeCustomConfirm(result) {
    const modal = document.getElementById('customConfirm');
    if (modal) modal.style.display = 'none';

    if (confirmCallback) {
        confirmCallback(result);
        confirmCallback = null;
    }
}

const cache = {
    teachers: null,
    colleges: null,
    departments: null,
    classes: null,
    rooms: null,
    timeConfigs: null
};

// Debounce utility
function debounce(func, wait) {
    let timeout;
    return function (...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}

async function loadCourses() {
    try {
        const q = (document.getElementById('courseSearch') || {}).value || '';
        const college = (document.getElementById('courseFilterCollege') || {}).value || '';
        const department = (document.getElementById('courseFilterDept') || {}).value || '';

        const params = new URLSearchParams();
        if (q) params.append('q', q);
        if (college) params.append('college', college);
        if (department) params.append('department', department);

        const response = await api('/api/courses/courses/?' + params.toString());
        // 处理可能的分页格式
        const r = Array.isArray(response) ? response : (response.results || []);
        tt.courses = r;
        tt.courseMap = {};
        tt.courseObjs = {};
        r.forEach(x => {
            tt.courseMap[x.id] = x.name;
            tt.courseObjs[x.id] = x;
        });

        const tbody = document.getElementById('courseList');
        if (tbody) {
            tbody.innerHTML = r.map(x => {
                const teacherLabel = tt.teacherLabelMap[x.teacher] || x.teacher_name || '-';
                // 课程名称—老师 格式
                const courseWithTeacher = `${x.name}—${teacherLabel}`;
                // deptMap keys are integers, x.department is integer
                const deptLabel = tt.deptMap[x.department] || (x.department ? 'ID:' + x.department : '跨学院');
                const requiredLabel = x.course_type === 'required' ? '必修' : '选修';
                return `<tr>
                    <td><input type="checkbox" data-course="${x.id}" ${tt.selectedCourses.has(x.id) ? 'checked' : ''}/></td>
                    <td>
                        <div style="display:flex;align-items:center;gap:8px;">
                            <span>${courseWithTeacher}</span>
                            <button class="btn btn-sm btn-link p-0" onclick="editCourse(${x.id})" title="编辑课程">
                                <i class="fa fa-edit"></i>
                            </button>
                        </div>
                    </td>
                    <td>${x.subject_id || '-'}</td>
                    <td>${requiredLabel}</td>
                    <td>${deptLabel}</td>
                </tr>`;
            }).join('');

            tbody.querySelectorAll('input[type=checkbox]').forEach(ch => {
                ch.addEventListener('change', () => {
                    const id = Number(ch.dataset.course);
                    if (ch.checked) tt.selectedCourses.add(id);
                    else tt.selectedCourses.delete(id);
                    updateSelectedCount();
                    updateBatchButtons();
                    renderPalette();
                });
            });
        }
        // 渲染课程列表（用于拖拽）
        renderCourseList(r);
        renderPalette();
    } catch (e) {
        const tbody = document.getElementById('courseList');
        if (tbody) tbody.innerHTML = '';
        const listContainer = document.getElementById('courseListContainer');
        if (listContainer) {
            listContainer.innerHTML = '<div class="text-center text-danger small p-3">加载失败</div>';
        }
    }
}

// 渲染课程列表（新增）
function renderCourseList(courses) {
    const container = document.getElementById('courseListContainer');
    const countBadge = document.getElementById('courseCount');

    if (!container) return;

    if (!courses || courses.length === 0) {
        container.innerHTML = '<div class="text-center text-secondary small p-3">暂无课程</div>';
        if (countBadge) countBadge.textContent = '0';
        updateSelectedCount();
        return;
    }

    if (countBadge) countBadge.textContent = courses.length;

    container.innerHTML = courses.map(course => {
        const teacherName = tt.teacherLabelMap[course.teacher] || course.teacher_name || '未指定';
        const courseType = course.course_type === 'required' ? '必修' : '选修';
        const badgeClass = course.course_type === 'required' ? 'required' : 'elective';
        const hasTeacher = course.teacher ? true : false;
        const warningClass = !hasTeacher ? 'no-teacher' : '';
        const warningIcon = !hasTeacher ? '<i class="fa-solid fa-exclamation-triangle text-warning ms-1" title="未指定教师，无法排课"></i>' : '';
        const isSelected = tt.selectedCourses.has(course.id);
        const selectedClass = isSelected ? 'selected' : '';

        return `
            <div class="course-list-item ${warningClass} ${selectedClass}" 
                 draggable="${hasTeacher}" 
                 data-course-id="${course.id}"
                 data-course-name="${course.name}"
                 data-teacher-name="${teacherName}">
                <input type="checkbox" class="course-checkbox" data-course-id="${course.id}" ${isSelected ? 'checked' : ''} onclick="event.stopPropagation()">
                <div class="course-list-item-info" style="flex: 1;">
                    <div class="course-list-item-name" title="${course.name}—${teacherName}">
                        ${course.name}${warningIcon}
                    </div>
                    <div class="course-list-item-teacher" title="${teacherName}">
                        <i class="fa-solid fa-user me-1"></i>${teacherName}
                    </div>
                </div>
                <span class="course-list-item-badge ${badgeClass}">${courseType}</span>
            </div>
        `;
    }).join('');

    // 为每个课程项添加事件
    container.querySelectorAll('.course-list-item').forEach(item => {
        const courseId = Number(item.dataset.courseId);
        const checkbox = item.querySelector('.course-checkbox');

        // 复选框变化事件
        checkbox.addEventListener('change', (e) => {
            e.stopPropagation();
            const id = Number(checkbox.dataset.courseId);
            if (checkbox.checked) {
                tt.selectedCourses.add(id);
                item.classList.add('selected');
            } else {
                tt.selectedCourses.delete(id);
                item.classList.remove('selected');
            }
            updateSelectedCount();
            updateBatchButtons();
            renderPalette();
        });

        // 点击行选择（支持Ctrl键多选）
        item.addEventListener('click', (e) => {
            // 如果点击的是复选框，不处理（复选框有自己的事件）
            if (e.target === checkbox || e.target.closest('.course-checkbox')) {
                return;
            }

            // 如果点击的是编辑按钮区域，不处理
            if (e.target.closest('.course-list-item-badge')) {
                return;
            }

            e.preventDefault();
            e.stopPropagation();

            // 检查是否按下了Ctrl键（Windows/Linux）或Cmd键（Mac）
            const isMultiSelect = e.ctrlKey || e.metaKey;

            if (isMultiSelect) {
                // Ctrl/Cmd + 点击：切换选择状态
                const isSelected = tt.selectedCourses.has(courseId);
                if (isSelected) {
                    tt.selectedCourses.delete(courseId);
                    checkbox.checked = false;
                    item.classList.remove('selected');
                } else {
                    tt.selectedCourses.add(courseId);
                    checkbox.checked = true;
                    item.classList.add('selected');
                }
            } else {
                // 普通点击：单选（清除其他选择，只选择当前项）
                // 或者如果当前项已选中，则取消选择
                const isSelected = tt.selectedCourses.has(courseId);
                if (isSelected && tt.selectedCourses.size === 1) {
                    // 如果只有当前项被选中，则取消选择
                    tt.selectedCourses.delete(courseId);
                    checkbox.checked = false;
                    item.classList.remove('selected');
                } else {
                    // 清除所有选择，只选择当前项
                    tt.selectedCourses.clear();
                    container.querySelectorAll('.course-list-item').forEach(i => {
                        i.classList.remove('selected');
                        i.querySelector('.course-checkbox').checked = false;
                    });
                    tt.selectedCourses.add(courseId);
                    checkbox.checked = true;
                    item.classList.add('selected');
                }
            }

            updateSelectedCount();
            updateBatchButtons();
            renderPalette();
        });

        // 只给有教师（draggable=true）的课程添加拖拽事件
        if (item.draggable) {
            item.addEventListener('dragstart', handleCourseItemDragStart);
            item.addEventListener('dragend', handleCourseItemDragEnd);
        }

        // 所有课程都可以双击编辑
        item.addEventListener('dblclick', (e) => {
            e.stopPropagation();
            const courseId = item.dataset.courseId;
            openEditCourseFromList(courseId);
        });
    });

    updateSelectedCount();
    updateBatchButtons();
}

// 课程列表项拖拽开始
function handleCourseItemDragStart(e) {
    const courseId = e.target.dataset.courseId;
    e.dataTransfer.setData('text/plain', JSON.stringify({ course: Number(courseId) }));
    e.dataTransfer.effectAllowed = 'copy';
    e.target.classList.add('dragging');

    const ttGrid = document.getElementById('ttGrid');
    if (ttGrid) ttGrid.classList.add('is-dragging');
}

// 课程列表项拖拽结束
function handleCourseItemDragEnd(e) {
    e.target.classList.remove('dragging');

    const ttGrid = document.getElementById('ttGrid');
    if (ttGrid) ttGrid.classList.remove('is-dragging');
}

// 刷新课程列表
async function refreshCourseList() {
    await loadCourses();
}

function renderPalette() {
    const pal = document.getElementById('coursePalette');
    if (!pal) return;
    const ids = [...tt.selectedCourses];
    pal.innerHTML = ids.map(id => {
        const course = tt.courseObjs[id];
        const teacherName = course ? (tt.teacherLabelMap[course.teacher] || course.teacher_name || '未指定') : '未知';
        const courseName = tt.courseMap[id] || ('#' + id);
        const displayName = `${courseName}—${teacherName}`;
        return `<div class="drag-card" draggable="true" data-course="${id}">
            <div style="font-weight:500">${displayName}</div>
        </div>`;
    }).join('');

    pal.querySelectorAll('.drag-card').forEach(el => {
        el.addEventListener('dragstart', e => {
            e.dataTransfer.setData('text/plain', JSON.stringify({ course: Number(el.dataset.course) }));
            e.dataTransfer.effectAllowed = 'copy';
            const ttGrid = document.getElementById('ttGrid');
            if (ttGrid) ttGrid.classList.add('is-dragging');
        });
        el.addEventListener('dragend', () => {
            const ttGrid = document.getElementById('ttGrid');
            if (ttGrid) ttGrid.classList.remove('is-dragging');
        });
    });
}

// 更新选中数量显示
function updateSelectedCount() {
    const countEl = document.getElementById('selectedCount');
    if (countEl) {
        countEl.textContent = tt.selectedCourses.size;
    }

    // 更新全选复选框状态
    const selectAllCheckbox = document.getElementById('selectAllCourses');
    const container = document.getElementById('courseListContainer');
    if (selectAllCheckbox && container) {
        const allCheckboxes = container.querySelectorAll('.course-checkbox');
        const checkedCount = container.querySelectorAll('.course-checkbox:checked').length;

        if (allCheckboxes.length === 0) {
            selectAllCheckbox.checked = false;
            selectAllCheckbox.indeterminate = false;
        } else if (checkedCount === allCheckboxes.length) {
            selectAllCheckbox.checked = true;
            selectAllCheckbox.indeterminate = false;
        } else if (checkedCount > 0) {
            selectAllCheckbox.checked = false;
            selectAllCheckbox.indeterminate = true;
        } else {
            selectAllCheckbox.checked = false;
            selectAllCheckbox.indeterminate = false;
        }
    }
}

// 更新批量操作按钮状态
function updateBatchButtons() {
    const hasSelection = tt.selectedCourses.size > 0;
    const autoScheduleBtn = document.getElementById('autoScheduleBtn');
    const deleteSelectedBtn = document.getElementById('deleteSelectedBtn');

    if (autoScheduleBtn) {
        autoScheduleBtn.disabled = !hasSelection;
    }
    if (deleteSelectedBtn) {
        deleteSelectedBtn.disabled = !hasSelection;
    }
}

// 全选/取消全选
function toggleSelectAll() {
    const selectAllCheckbox = document.getElementById('selectAllCourses');
    const container = document.getElementById('courseListContainer');

    if (!selectAllCheckbox || !container) return;

    const allCheckboxes = container.querySelectorAll('.course-checkbox');
    const allItems = container.querySelectorAll('.course-list-item');

    if (selectAllCheckbox.checked) {
        // 全选
        allCheckboxes.forEach(checkbox => {
            const courseId = Number(checkbox.dataset.courseId);
            tt.selectedCourses.add(courseId);
            checkbox.checked = true;
        });
        allItems.forEach(item => item.classList.add('selected'));
    } else {
        // 取消全选
        tt.selectedCourses.clear();
        allCheckboxes.forEach(checkbox => {
            checkbox.checked = false;
        });
        allItems.forEach(item => item.classList.remove('selected'));
    }

    updateSelectedCount();
    updateBatchButtons();
    renderPalette();
}

// 删除选中的课程
async function deleteSelectedCourses() {
    const selectedIds = [...tt.selectedCourses];
    if (selectedIds.length === 0) {
        customAlert('请先选择要删除的课程', '提示', 'warning');
        return;
    }

    // 检查是否有课程安排使用了这些课程
    let scheduleCount = 0;
    if (currentTargetId) {
        try {
            // 查询当前班级的所有课程安排，检查是否有使用要删除的课程
            const schedules = await api(`/api/courses/schedules/?school_class=${currentTargetId}`);
            const schedulesArray = Array.isArray(schedules) ? schedules : (schedules.results || []);
            scheduleCount = schedulesArray.filter(s => selectedIds.includes(s.course)).length;
        } catch (e) {
            console.error('查询课程安排失败:', e);
        }
    }

    let confirmMessage = `确定要删除选中的 ${selectedIds.length} 门课程吗？\n\n`;
    if (scheduleCount > 0) {
        confirmMessage += `⚠️ 警告：这些课程在课程表中有 ${scheduleCount} 条安排，删除课程后这些安排也会被自动删除！\n\n`;
    }
    confirmMessage += `此操作不可恢复！`;

    if (!await customConfirm(confirmMessage, '确认删除')) {
        return;
    }

    let successCount = 0;
    let failCount = 0;

    for (const id of selectedIds) {
        try {
            await api(`/api/courses/courses/${id}/`, 'DELETE');
            successCount++;
        } catch (e) {
            failCount++;
            console.error(`删除课程 ${id} 失败:`, e);
        }
    }

    tt.selectedCourses.clear();
    await loadCourses();

    // 如果当前有选中的班级，刷新课程表以显示删除后的结果
    // 由于数据库设置了级联删除，删除课程时相关的课程安排会自动删除
    if (currentTargetId && currentViewMode === 'class') {
        await loadSchedule();
    }

    if (failCount > 0) {
        customAlert(`删除完成：成功 ${successCount} 门，失败 ${failCount} 门`, '删除结果', 'warning');
    } else {
        let message = `成功删除 ${successCount} 门课程`;
        if (scheduleCount > 0) {
            message += `\n\n已自动删除课程表中的 ${scheduleCount} 条相关安排`;
        }
        customAlert(message, '删除成功', 'success');
    }
}

// 为选中的课程自动排课
async function autoScheduleSelected() {
    const selectedIds = [...tt.selectedCourses];
    if (selectedIds.length === 0) {
        customAlert('请先选择要排课的课程', '提示', 'warning');
        return;
    }

    if (!currentTargetId || currentViewMode !== 'class') {
        customAlert('请先选择班级进行智能排课', '提示', 'warning');
        return;
    }

    // 确认智能排课
    if (!await customConfirm(`智能排课将为选中的 ${selectedIds.length} 门课程安排20周（周一至周五）的课表。\n\n注意：这将在现有课表基础上添加新的课程安排。\n\n是否继续？`, '确认智能排课')) {
        return;
    }

    showMessage('scheduleMsg', '正在进行智能排课，请稍候...', 'info');

    const payload = {
        school_class: currentTargetId,
        courses: selectedIds,
        start_week: 1,
        end_week: 20,
        week_mode: 'all'
    };

    try {
        const result = await api('/api/courses/schedules/auto', 'POST', payload);
        const successCount = result.created_count || 0;
        const failedCount = (result.items || []).filter(item => item.reason).length;

        let message = `智能排课完成：成功排课 ${successCount} 节`;
        if (failedCount > 0) {
            message += `，失败 ${failedCount} 节`;
        }

        showMessage('scheduleMsg', message, successCount > 0 ? 'success' : 'warning');
        loadSchedule();

        if (successCount > 0) {
            customAlert(message, '智能排课完成', 'success');
        } else {
            customAlert('智能排课失败，请检查课程和班级信息', '排课失败', 'warning');
        }
    } catch (e) {
        showMessage('scheduleMsg', e.message || '智能排课失败', 'error');
        customAlert('智能排课失败：' + (e.message || '未知错误'), '错误', 'error');
    }
}

// 编辑课程功能
let editCourseCtx = { id: null };

async function editCourse(id) {
    editCourseCtx.id = id;
    try {
        const course = await api(`/api/courses/courses/${id}/`);
        const modal = document.getElementById('editCourseModal');
        if (!modal) {
            customAlert('编辑功能未就绪，请刷新页面', '提示', 'warning');
            return;
        }

        // 填充表单
        document.getElementById('editCourseName').value = course.name || '';
        document.getElementById('editCourseType').value = course.course_type || 'required';
        document.getElementById('editTeacherSearch').value = '';

        // 加载学院、专业和教师选项
        await loadEditTeacherColleges();
        await loadEditTeacherOptions();
        document.getElementById('editCourseTeacher').value = course.teacher || '';

        // 显示模态框
        modal.style.display = 'flex';
    } catch (e) {
        customAlert('加载课程信息失败：' + (e.message || '未知错误'), '错误', 'error');
    }
}

async function loadEditTeacherOptions(searchQuery = '') {
    try {
        const params = new URLSearchParams();
        if (searchQuery) params.append('q', searchQuery);

        const collegeFilter = document.getElementById('editTeacherCollege')?.value || '';
        const deptFilter = document.getElementById('editTeacherDept')?.value || '';

        if (collegeFilter) params.append('college', collegeFilter);
        if (deptFilter) params.append('department', deptFilter);

        const response = await api('/api/accounts/teachers/?' + params.toString());
        const teachers = Array.isArray(response) ? response : (response.results || []);

        const select = document.getElementById('editCourseTeacher');
        if (select) {
            const currentVal = select.value;
            select.innerHTML = '<option value="">选择教师</option>' + teachers.map(t => {
                const name = (t.user_profile && t.user_profile.user && t.user_profile.user.first_name) || t.teacher_id || t.id;
                return `<option value="${t.id}">${name}</option>`;
            }).join('');
            if (currentVal) select.value = currentVal;
        }
    } catch (e) {
        console.error('加载教师列表失败:', e);
    }
}

async function loadEditTeacherColleges() {
    try {
        if (!cache.colleges) {
            cache.colleges = await api('/api/org/colleges?no_page=1');
        }
        const colleges = cache.colleges;
        const select = document.getElementById('editTeacherCollege');
        if (select) {
            select.innerHTML = '<option value="">全部学院</option>' + colleges.map(c =>
                `<option value="${c.id}">${c.name}</option>`
            ).join('');
        }
    } catch (e) {
        console.error('加载学院列表失败:', e);
    }
}

async function loadEditTeacherCollegeDepts(collegeId) {
    try {
        const url = collegeId ? `/api/org/departments?college=${collegeId}&no_page=1` : '/api/org/departments?no_page=1';
        const depts = await api(url);
        const select = document.getElementById('editTeacherDept');
        if (select) {
            select.innerHTML = '<option value="">全部专业</option>' + depts.map(d =>
                `<option value="${d.id}">${d.name}</option>`
            ).join('');
        }
        loadEditTeacherOptions();
    } catch (e) {
        console.error('加载专业列表失败:', e);
    }
}

async function saveEditCourse() {
    const id = editCourseCtx.id;
    const name = document.getElementById('editCourseName')?.value?.trim();
    const course_type = document.getElementById('editCourseType')?.value;
    const teacher = document.getElementById('editCourseTeacher')?.value;

    if (!name) {
        customAlert('请填写课程名称', '提示', 'warning');
        return;
    }

    if (!teacher) {
        customAlert('请选择课程教师', '提示', 'warning');
        return;
    }

    try {
        await api(`/api/courses/courses/${id}/`, 'PATCH', {
            name,
            course_type,
            teacher: Number(teacher)
        });

        closeEditCourse();
        loadCourses();

        // 如果当前有选中的班级，刷新课程表以显示更新后的教师信息
        if (currentTargetId) {
            await loadSchedule();
        }

        customAlert('修改成功！', '成功', 'success');
    } catch (e) {
        customAlert('保存失败：' + (e.message || '未知错误'), '错误', 'error');
    }
}

function closeEditCourse() {
    const modal = document.getElementById('editCourseModal');
    if (modal) modal.style.display = 'none';
}

async function addCourse() {
    const name = (document.getElementById('courseName') || {}).value || '';
    const course_type = (document.getElementById('courseType') || {}).value || '';
    const teacherVal = (document.getElementById('courseTeacher') || {}).value || '';
    const deptVal = (document.getElementById('courseTeacherDept') || {}).value || '';

    const teacher = teacherVal ? Number(teacherVal) : null;
    const department = deptVal ? Number(deptVal) : null; // 专业现在是可选的

    // 只验证必填项：课程名称、必修/选修、老师
    if (!name || !course_type || !teacher) {
        customAlert('请填写课程名称、选择必修/选修、选择课程老师', '提示', 'warning');
        return;
    }

    const payload = {
        name,
        course_type,
        teacher
    };

    // 如果选择了专业,才添加到payload
    if (department) {
        payload.department = department;
    }

    try {
        await api('/api/courses/courses/', 'POST', payload);
        document.getElementById('courseName').value = '';
        document.getElementById('courseType').value = 'required';
        document.getElementById('courseTeacher').value = '';
        if (document.getElementById('courseTeacherDept')) {
            document.getElementById('courseTeacherDept').value = '';
        }
        loadCourses();
        customAlert('新增成功！', '成功', 'success');
    } catch (e) {
        customAlert(e.message || '新增失败', '错误', 'error');
    }
}

async function loadTimeslots() {
    const r = await api('/api/courses/timeslots');
    const el = document.getElementById('timeslots');
    if (el) el.innerHTML = r.map(x => `#${x.id} 周${x.weekday} 第${x.index}节 ${x.start_time}-${x.end_time}`).join('<br>');
}

async function generateSlots() {
    try {
        const result = await api('/api/courses/timeslots/generate', 'POST', {});
        console.log('✅ 时间段生成结果:', result);

        // 重新加载时间段数据
        await initTimetable();

        // 重新加载时间段列表（如果页面有显示）
        if (typeof loadTimeslots === 'function') {
            await loadTimeslots();
        }

        // 验证时间段完整性
        const validation = validateTimeSlots();

        let message = `时间段生成成功！已创建 ${result.created || 0} 个时间段。`;
        if (validation.missing > 0) {
            message += `\n\n⚠️ 仍有 ${validation.missing} 个时间段缺失，请再次点击生成按钮。`;
        } else {
            message += `\n\n✅ 所有时间段完整（周一到周日，每节1-8）。`;
            // 清除警告标记，允许正常状态更新
            hasTimeslotWarning = false;
            // 更新状态显示成功信息
            updateFilterStatus(`✅ 所有时间段已完整生成！`, 'success', true);
        }

        customAlert(message, '时间段生成', validation.missing > 0 ? 'warning' : 'success');
    } catch (error) {
        console.error('❌ 生成时间段失败:', error);
        customAlert('生成时间段失败: ' + (error.message || '网络错误'), '错误', 'error');
    }
}

async function loadTeachers() {
    try {
        // We load ALL teachers for the global mapping, but we filter for the dropdown
        if (!cache.teachers) {
            const response = await api('/api/accounts/teachers/');
            // 处理可能的分页格式
            cache.teachers = Array.isArray(response) ? response : (response.results || []);
        }
        const r = cache.teachers;
        tt.teachers = r;
        tt.teacherMap = {};
        tt.teacherLabelMap = {};
        r.forEach(x => {
            const label = (x.user_profile && x.user_profile.user && (x.user_profile.user.first_name || x.user_profile.user.username)) || x.teacher_id || x.id;
            tt.teacherMap[x.id] = x.teacher_id || x.id;
            tt.teacherLabelMap[x.id] = label;
        });

        // Initial load for filter/view selectors
        updateTeacherSelect('ttTeacher', r);
        updateTeacherSelect('engineTeacher', r);
        // For Course Creation, we use Cascade, so we don't load all initially or we load all if no filter
        updateTeacherSelect('courseTeacher', r);

    } catch (e) {
        console.error('加载教师数据失败:', e);
    }
}

function updateTeacherSelect(elId, list) {
    const el = document.getElementById(elId);
    if (!el) return;
    const currentVal = el.value;
    el.innerHTML = '<option value="">选择老师</option>' + list.map(x => `<option value="${x.id}">${tt.teacherLabelMap[x.id]}</option>`).join('');
    if (currentVal) el.value = currentVal;
}

async function loadColleges() {
    try {
        if (!cache.colleges) {
            cache.colleges = await api('/api/org/colleges?no_page=1');
        }
        const r = cache.colleges;

        ['courseFilterCollege', 'courseTeacherCollege'].forEach(id => {
            const sel = document.getElementById(id);
            if (sel) {
                const currentVal = sel.value;
                sel.innerHTML = '<option value="">选择/筛选学院</option>' + r.map(x => `<option value="${x.id}">${x.name}</option>`).join('');
                if (currentVal) sel.value = currentVal;
            }
        });
    } catch (e) { }
}

async function loadDepartments() {
    try {
        if (!cache.departments) {
            cache.departments = await api('/api/org/departments?no_page=1');
        }
        const r = cache.departments;
        tt.departments = r;
        tt.deptMap = {};
        r.forEach(x => tt.deptMap[x.id] = x.name);

        // Initial load for Course List Filter
        updateDeptSelect('courseFilterDept', 'courseFilterCollege');
        // Initial load for Course Creation
        updateDeptSelect('courseTeacherDept', 'courseTeacherCollege');

    } catch (e) { }
}

function updateDeptSelect(elId, parentId) {
    const sel = document.getElementById(elId);
    if (!sel) return;
    const parentVal = (document.getElementById(parentId) || {}).value;

    const list = tt.departments.filter(x => {
        if (parentVal && String(x.college) !== String(parentVal)) return false;
        return true;
    });

    const currentVal = sel.value;
    sel.innerHTML = '<option value="">选择/筛选专业</option>' + list.map(x => `<option value="${x.id}">${x.name}</option>`).join('');
    if (currentVal) sel.value = currentVal;
}

// Helper to filter teachers based on Dept
function filterTeachersByDept() {
    const collegeVal = document.getElementById('courseTeacherCollege')?.value;
    const deptVal = document.getElementById('courseTeacherDept')?.value;
    const showAll = document.getElementById('showAllTeachers')?.checked;

    if (!tt.teachers) return;

    let list = tt.teachers;

    // 如果勾选了"显示所有教师"，则不进行筛选
    if (!showAll) {
        if (deptVal) {
            list = list.filter(x => String(x.department) === String(deptVal));
        } else if (collegeVal) {
            // We need to know which departments belong to this college
            // tt.departments has college info
            const validDepts = new Set(tt.departments.filter(d => String(d.college) === String(collegeVal)).map(d => d.id));
            list = list.filter(x => validDepts.has(x.department));
        }
    }

    updateTeacherSelect('courseTeacher', list);
}

// Toggle teacher filter
function toggleTeacherFilter() {
    const showAll = document.getElementById('showAllTeachers')?.checked;
    const collegeSelect = document.getElementById('courseTeacherCollege');
    const deptSelect = document.getElementById('courseTeacherDept');

    if (showAll) {
        // 禁用学院和专业选择器
        if (collegeSelect) collegeSelect.disabled = true;
        if (deptSelect) deptSelect.disabled = true;
        // 显示所有教师
        updateTeacherSelect('courseTeacher', tt.teachers);
    } else {
        // 启用学院和专业选择器
        if (collegeSelect) collegeSelect.disabled = false;
        if (deptSelect) deptSelect.disabled = false;
        // 根据当前筛选条件显示教师
        filterTeachersByDept();
    }
}

async function loadClasses() {
    try {
        if (!cache.classes) {
            cache.classes = await api('/api/org/classes?no_page=1');
        }
        const r = cache.classes;
        ['ttClass', 'engineClass', 'scClass'].forEach(id => {
            const sel = document.getElementById(id);
            if (sel) {
                const currentVal = sel.value;
                sel.innerHTML = '<option value="">选择班级</option>' + r.map(x => `<option value="${x.id}">${x.name}</option>`).join('');
                if (currentVal) sel.value = currentVal;
            }
        });
    } catch (e) { }
}

async function loadRooms() {
    try {
        if (!cache.rooms) {
            const response = await api('/api/org/classrooms/');
            // 处理可能的分页格式
            cache.rooms = Array.isArray(response) ? response : (response.results || []);
        }
        const r = cache.rooms;
        tt.rooms = r;
        tt.roomMap = {};
        r.forEach(x => { tt.roomMap[x.id] = `${x.building}-${x.room_number}`; });

        ['ttRoom', 'engineRoom', 'scRoom'].forEach(id => {
            const sel = document.getElementById(id);
            if (sel) {
                const currentVal = sel.value;
                sel.innerHTML = '<option value="">选择教室</option>' + r.map(x => `<option value="${x.id}">${x.building}-${x.room_number}(${x.capacity})</option>`).join('');
                if (currentVal) sel.value = currentVal;
            }
        });
    } catch (e) {
        console.error('加载教室数据失败:', e);
    }
}

async function loadSlots() {
    try {
        // Implement slot loading logic if needed
    } catch (e) { }
}

// Initialization
window.addEventListener('DOMContentLoaded', async () => {
    console.log('🚀 [DOMContentLoaded] 页面加载完成，开始初始化...');
    console.log('🚀 [DOMContentLoaded] 用户角色:', window.USER_ROLE);
    console.log('🚀 [DOMContentLoaded] IS_TEACHER:', window.IS_TEACHER, '类型:', typeof window.IS_TEACHER);
    console.log('🚀 [DOMContentLoaded] IS_ADMIN:', window.IS_ADMIN, '类型:', typeof window.IS_ADMIN);

    // 先初始化时间段数据（必须在加载课程之前）
    console.log('🚀 [DOMContentLoaded] 准备调用 initTimetable()...');
    await initTimetable();
    console.log('🚀 [DOMContentLoaded] initTimetable() 完成');
    console.log('🚀 [DOMContentLoaded] 时间段数量:', tt.slots.length);

    // 根据用户角色加载不同的数据
    // 注意：window.IS_TEACHER 可能是字符串 'true'/'false'，需要转换
    const isTeacher = window.IS_TEACHER === true || window.IS_TEACHER === 'true';
    const isAdmin = window.IS_ADMIN === true || window.IS_ADMIN === 'true';

    console.log('🚀 [DOMContentLoaded] 转换后 - isTeacher:', isTeacher, 'isAdmin:', isAdmin);

    if (isTeacher) {
        // 教师：只加载必要的数据和自动加载课程表
        console.log('🚀 [教师模式] 自动加载课程表...');
        console.log('🚀 [教师模式] 当前周次:', currentWeek);

        // 教师模式下不需要加载教师和班级列表，直接加载课程表
        // await Promise.all([
        //     loadTeachers(),
        //     loadClasses()
        // ]);

        // 教师自动加载自己的课程表（不需要筛选）
        const loadStartTime = performance.now();
        await loadSchedule();
        const loadTime = (performance.now() - loadStartTime).toFixed(0);
        console.log(`🚀 [教师模式] 课程表加载完成，总耗时: ${loadTime}ms`);
    } else if (window.USER_ROLE === 'student') {
        // 学生：只加载自己的课程表
        console.log('🚀 [学生模式] 自动加载课程表...');
        await loadSchedule();
    } else if (isAdmin) {
        // 管理员：加载所有数据
        console.log('🚀 [管理员模式] 开始加载所有数据...');
        await Promise.all([
            loadColleges(),
            loadDepartments(),
            loadTeachers(),
            loadClasses(),
            loadRooms(),
            loadCourses()
        ]);

        console.log('🚀 [管理员模式] 数据加载完成，初始化筛选器...');
        // 初始化四级筛选器
        await initFilters();

        // Bind Cascade Events for Course Management Area (左侧课程管理区)
        document.getElementById('courseFilterCollege')?.addEventListener('change', () => {
            updateDeptSelect('courseFilterDept', 'courseFilterCollege');
            loadCourses();
        });
        document.getElementById('courseFilterDept')?.addEventListener('change', loadCourses);

        document.getElementById('courseTeacherCollege')?.addEventListener('change', () => {
            updateDeptSelect('courseTeacherDept', 'courseTeacherCollege');
            filterTeachersByDept();
        });
        document.getElementById('courseTeacherDept')?.addEventListener('change', () => {
            filterTeachersByDept();
        });

        // 从URL参数中读取搜索关键词并预填充
        const urlParams = new URLSearchParams(window.location.search);
        const searchQuery = urlParams.get('q');
        const searchInput = document.getElementById('courseSearch');

        if (searchQuery && searchInput) {
            searchInput.value = decodeURIComponent(searchQuery);
        }

        // Search Input Listener
        document.getElementById('courseSearch')?.addEventListener('input', debounce(loadCourses, 300));

        // 如果有URL参数，重新加载课程列表
        if (searchQuery) {
            loadCourses();
        }
    }
});

// ==================== Timetable Display & Scheduling ====================

let currentWeek = 1;
let currentViewMode = 'class';  // 'class', 'teacher', or 'classroom'
let currentTargetId = null;
let hasTimeslotWarning = false;  // 标记是否有时间段警告，防止被其他状态信息覆盖

// ==================== 筛选条件记忆功能 ====================

const FILTER_STORAGE_KEY = 'courseScheduleFilters';

// 保存筛选条件到 localStorage
function saveFilterState() {
    const filterState = {
        collegeId: document.getElementById('filterCollege')?.value || '',
        majorId: document.getElementById('filterMajor')?.value || '',
        gradeId: document.getElementById('filterGrade')?.value || '',
        classId: document.getElementById('filterClass')?.value || '',
        week: currentWeek,
        timestamp: Date.now()
    };

    try {
        localStorage.setItem(FILTER_STORAGE_KEY, JSON.stringify(filterState));
        console.log('✓ 筛选条件已保存:', filterState);
    } catch (e) {
        console.error('保存筛选条件失败:', e);
    }
}

// 从 localStorage 读取筛选条件
function loadFilterState() {
    try {
        const saved = localStorage.getItem(FILTER_STORAGE_KEY);
        if (saved) {
            const filterState = JSON.parse(saved);
            console.log('✓ 读取到保存的筛选条件:', filterState);
            return filterState;
        }
    } catch (e) {
        console.error('读取筛选条件失败:', e);
    }
    return null;
}

// 清除筛选条件记忆
function clearFilterState() {
    try {
        localStorage.removeItem(FILTER_STORAGE_KEY);
        console.log('✓ 筛选条件记忆已清除');
    } catch (e) {
        console.error('清除筛选条件失败:', e);
    }
}

// 恢复筛选条件
async function restoreFilterState() {
    const savedState = loadFilterState();

    if (!savedState) {
        console.log('ℹ 没有保存的筛选条件');
        return false;
    }

    console.log('🔄 正在恢复筛选条件...', savedState);

    try {
        // 恢复学院
        if (savedState.collegeId) {
            const collegeSelect = document.getElementById('filterCollege');
            if (collegeSelect) {
                collegeSelect.value = savedState.collegeId;

                // 触发学院变化，加载专业（但不触发保存）
                const majorSelect = document.getElementById('filterMajor');
                const majors = cache.departments.filter(d => String(d.college) === String(savedState.collegeId));

                if (majors.length > 0) {
                    majors.sort((a, b) => a.name.localeCompare(b.name, 'zh-CN'));
                    majorSelect.innerHTML = '<option value="">请选择专业</option>' +
                        majors.map(m => `<option value="${m.id}">${m.name}</option>`).join('');

                    // 恢复专业
                    if (savedState.majorId) {
                        majorSelect.value = savedState.majorId;

                        // 触发专业变化，加载年级
                        const gradeSelect = document.getElementById('filterGrade');
                        const classes = cache.classes.filter(c => String(c.major) === String(savedState.majorId));

                        if (classes.length > 0) {
                            const grades = [...new Set(classes.map(c => c.enrollment_year))];
                            grades.sort((a, b) => b - a);
                            gradeSelect.innerHTML = '<option value="">请选择年级</option>' +
                                grades.map(g => `<option value="${g}">${g}级</option>`).join('');

                            // 恢复年级
                            if (savedState.gradeId) {
                                gradeSelect.value = savedState.gradeId;

                                // 触发年级变化，加载班级
                                const classSelect = document.getElementById('filterClass');
                                const filteredClasses = cache.classes.filter(c =>
                                    String(c.major) === String(savedState.majorId) &&
                                    String(c.enrollment_year) === String(savedState.gradeId)
                                );

                                if (filteredClasses.length > 0) {
                                    filteredClasses.sort((a, b) => (a.class_number || 0) - (b.class_number || 0));
                                    classSelect.innerHTML = '<option value="">请选择班级</option>' +
                                        filteredClasses.map(c => `<option value="${c.id}">${c.name}</option>`).join('');

                                    // 恢复班级
                                    if (savedState.classId) {
                                        classSelect.value = savedState.classId;
                                        currentTargetId = savedState.classId;
                                        currentViewMode = 'class';

                                        // 恢复周次
                                        if (savedState.week) {
                                            currentWeek = savedState.week;
                                            updateWeekLabel();
                                        }

                                        // 获取班级名称
                                        const className = classSelect.options[classSelect.selectedIndex].text;
                                        updateFilterStatus(`✓ 已恢复筛选条件: ${className}`, 'success');

                                        // 加载课表
                                        await loadSchedule();

                                        console.log('✅ 筛选条件恢复成功');
                                        return true;
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        console.log('ℹ 部分筛选条件无法恢复（数据可能已变更）');
        return false;
    } catch (e) {
        console.error('❌ 恢复筛选条件失败:', e);
        return false;
    }
}
let scheduleData = [];

// Initialize timetable grid with time slots
async function initTimetable() {
    try {
        console.log('🕐 [initTimetable] 开始加载时间段数据...');
        console.log('🕐 [initTimetable] API URL: /api/courses/timeslots/');

        const response = await api('/api/courses/timeslots/');
        console.log('🕐 [initTimetable] API原始响应:', response);

        // 处理可能的分页格式
        const r = Array.isArray(response) ? response : (response.results || []);

        console.log('📥 [initTimetable] 时间段API响应:', {
            isArray: Array.isArray(response),
            hasResults: response?.results !== undefined,
            count: r.length,
            sample: r[0],
            rawResponse: response
        });

        tt.slots = r;
        tt.slotByKey = {};
        tt.slotById = {};
        tt.maxIndex = 0;
        tt.indexLabel = {};

        if (r.length === 0) {
            console.warn('⚠️ [initTimetable] 警告: 时间段数据为空！');
            console.warn('⚠️ [initTimetable] 请检查后端是否已生成时间段。');
            console.warn('⚠️ [initTimetable] 可以运行: python generate_timeslots.py');
            console.warn('⚠️ [initTimetable] 或点击页面右上角"生成时间段"按钮');

            // 即使没有数据，也设置一个默认的maxIndex以便渲染网格
            tt.maxIndex = 8; // 默认8节课
            // 显示提示信息
            const statusEl = document.getElementById('filterStatus');
            if (statusEl) {
                statusEl.innerHTML = '<span style="color: #f59e0b;">⚠️ 时间段数据未加载！请点击右上角"生成时间段"按钮或联系管理员。</span>';
            }

            // 高亮显示生成按钮
            const generateBtn = document.querySelector('button[onclick="generateSlots()"]');
            if (generateBtn) {
                generateBtn.classList.add('btn-warning');
                generateBtn.classList.remove('btn-outline-warning');
                generateBtn.style.animation = 'pulse 2s infinite';
            }

            // 在控制台显示更详细的提示
            console.group('⚠️ 时间段数据缺失');
            console.log('当前时间段数量: 0');
            console.log('应该有的时间段: 周一到周日，每节1-8，共56个');
            console.log('解决方法:');
            console.log('  1. 点击页面右上角"生成时间段"按钮');
            console.log('  2. 或运行命令: python generate_timeslots.py');
            console.log('  3. 或通过API: POST /api/courses/timeslots/generate');
            console.groupEnd();
        } else {
            // 确保先清空，避免旧数据干扰
            tt.slotByKey = {};
            tt.slotById = {};

            r.forEach(s => {
                if (!s || !s.id) {
                    console.warn('⚠️ [initTimetable] 跳过无效的时间段数据:', s);
                    return;
                }

                const key = `${s.weekday}-${s.index}`;
                tt.slotByKey[key] = s;
                tt.slotById[s.id] = s;
                if (s.index > tt.maxIndex) tt.maxIndex = s.index;
                if (s.start_time && s.end_time) {
                    tt.indexLabel[s.index] = `${s.start_time.substring(0, 5)}-${s.end_time.substring(0, 5)}`;
                } else {
                    tt.indexLabel[s.index] = `第${s.index}节`;
                }
            });

            // 验证周五时间段是否存在
            const fridaySlots = Object.keys(tt.slotByKey).filter(k => k.startsWith('5-'));
            if (fridaySlots.length === 0) {
                console.warn('⚠️ [initTimetable] 警告：周五时间段缺失！');
            } else {
                console.log('✅ [initTimetable] 周五时间段数量:', fridaySlots.length);
            }
            console.log('✅ 时间段数据加载成功:', {
                total: r.length,
                maxIndex: tt.maxIndex,
                slotByKeyCount: Object.keys(tt.slotByKey).length,
                slotByIdCount: Object.keys(tt.slotById).length,
                slotByIdSample: Object.keys(tt.slotById).slice(0, 10)
            });

            // #region agent log - 检查周三3-3和周五的时间段
            const wed3 = tt.slotByKey['3-3'];
            const friSlots = Object.keys(tt.slotByKey).filter(k => k.startsWith('5-'));
            try {
                fetch('http://127.0.0.1:7242/ingest/b23c584d-8d7c-42cb-a198-4440966fe037', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ location: 'courses.js:initTimetable', message: 'Timeslot loading check', data: { wed3_exists: !!wed3, wed3_id: wed3?.id, fri_slots_count: friSlots.length, fri_slots: friSlots.slice(0, 8), all_slots_total: r.length, slotById_count: Object.keys(tt.slotById).length, slotById_sample: Object.keys(tt.slotById).slice(0, 10) }, timestamp: Date.now(), sessionId: 'debug-session' }) }).catch(() => { });
            } catch (e) { }
            // #endregion

            // 验证所有时间段是否完整（周一到周日，每节1-8）
            validateTimeSlots();
        }

        renderTimetableGrid();
        console.log('✅ [initTimetable] 初始化完成，时间段数量:', tt.slots.length);
    } catch (error) {
        console.error('❌ [initTimetable] 加载时间段数据失败:', error);
        console.error('❌ [initTimetable] 错误详情:', {
            message: error.message,
            stack: error.stack,
            error: error
        });

        // 即使失败也渲染网格，但显示错误提示
        tt.slots = [];
        tt.slotByKey = {};
        tt.slotById = {};
        tt.maxIndex = 8; // 默认8节课
        tt.indexLabel = {};

        const statusEl = document.getElementById('filterStatus');
        if (statusEl) {
            statusEl.innerHTML = '<span style="color: #ef4444;">❌ 时间段数据加载失败: ' + (error.message || '网络错误') + '<br>请检查网络连接或联系管理员。</span>';
        }

        renderTimetableGrid();
        console.log('⚠️ [initTimetable] 使用空数据渲染网格');
    }
}

// 验证所有时间段是否完整（周一到周日，每节1-8）
function validateTimeSlots() {
    const expectedWeekdays = [1, 2, 3, 4, 5, 6, 7]; // 周一到周日
    const expectedIndexes = [1, 2, 3, 4, 5, 6, 7, 8]; // 8节课
    const missing = [];
    const existing = [];

    for (const weekday of expectedWeekdays) {
        for (const index of expectedIndexes) {
            const slotKey = `${weekday}-${index}`;
            if (tt.slotByKey[slotKey]) {
                existing.push(slotKey);
            } else {
                missing.push({
                    weekday: weekday,
                    index: index,
                    weekdayName: tt.weekdayNames[weekday] || `周${weekday}`,
                    slotKey: slotKey
                });
            }
        }
    }

    console.log('🔍 时间段完整性验证:');
    console.log(`  ✅ 已存在: ${existing.length} 个`);
    console.log(`  ❌ 缺失: ${missing.length} 个`);

    if (missing.length > 0) {
        console.warn('⚠️ 缺失的时间段:', missing);

        // 按星期分组显示缺失的时间段
        const missingByWeekday = {};
        missing.forEach(m => {
            if (!missingByWeekday[m.weekday]) {
                missingByWeekday[m.weekday] = [];
            }
            missingByWeekday[m.weekday].push(m.index);
        });

        // 检查是否有某个工作日完全缺失（缺失8节课）
        const fullyMissingWeekdays = [];
        Object.keys(missingByWeekday).forEach(wd => {
            if (missingByWeekday[wd].length === 8) {
                fullyMissingWeekdays.push(parseInt(wd));
            }
        });

        let warningMsg = '⚠️ 时间段不完整！缺失的时间段：\n\n';
        Object.keys(missingByWeekday).sort((a, b) => parseInt(a) - parseInt(b)).forEach(wd => {
            const weekdayName = tt.weekdayNames[wd] || `周${wd}`;
            const indexes = missingByWeekday[wd].sort((a, b) => a - b);
            if (missingByWeekday[wd].length === 8) {
                warningMsg += `🔴 ${weekdayName}: 完全缺失（所有节次）\n`;
            } else {
                warningMsg += `${weekdayName}: 第${indexes.join('、')}节\n`;
            }
        });
        warningMsg += '\n请点击右上角"生成时间段"按钮补充缺失的时间段。';

        console.warn(warningMsg);

        // 如果有完全缺失的工作日（特别是周五），给出更明显的提示
        if (fullyMissingWeekdays.includes(5)) {
            console.error('🔴 周五时间段完全缺失！这会导致无法在周五拖拽排课。请立即点击"生成时间段"按钮！');
        }

        // 在界面上显示警告（时间段缺失是严重问题，优先显示）
        const statusEl = document.getElementById('filterStatus');
        if (statusEl) {
            hasTimeslotWarning = true;  // 设置警告标记
            statusEl.innerHTML = `<div style="color: #d97706; font-weight: bold; background: #fef3c7; padding: 10px 12px; border-radius: 6px; border-left: 4px solid #f59e0b; margin: 8px 0;">${warningMsg.replace(/\n/g, '<br>')}</div>`;
            statusEl.className = 'mt-2';  // 保持margin样式
        }

        // 如果有完全缺失的工作日（特别是周五），使用弹窗提示
        if (fullyMissingWeekdays.length > 0) {
            const missingDays = fullyMissingWeekdays.map(wd => tt.weekdayNames[wd] || `周${wd}`).join('、');
            const alertMsg = `⚠️ 严重警告：${missingDays}的时间段完全缺失！\n\n这会导致无法在这些日期拖拽排课。\n\n请立即点击右上角"生成时间段"按钮补充缺失的时间段。`;

            // 使用延迟提示，避免影响页面加载
            setTimeout(() => {
                if (typeof customAlert === 'function') {
                    customAlert(alertMsg, '时间段缺失警告', 'error');
                } else {
                    alert(alertMsg);
                }
            }, 1000);
        }

        // 高亮显示生成按钮
        const generateBtn = document.querySelector('button[onclick="generateSlots()"]');
        if (generateBtn) {
            generateBtn.classList.add('btn-warning');
            generateBtn.classList.remove('btn-outline-warning');
            // 如果有完全缺失的工作日，按钮更明显
            if (fullyMissingWeekdays.length > 0) {
                generateBtn.style.animation = 'pulse 1.5s infinite';
                generateBtn.style.fontWeight = 'bold';
            }
        }
    } else {
        console.log('✅ 所有时间段完整！周一到周日，每节1-8都已存在。');
        hasTimeslotWarning = false;  // 清除警告标记
    }

    return {
        total: expectedWeekdays.length * expectedIndexes.length,
        existing: existing.length,
        missing: missing.length,
        missingSlots: missing
    };
}

function renderTimetableGrid() {
    const grid = document.getElementById('timetableGrid');
    if (!grid) return;

    // Clear existing content except header
    const header = grid.innerHTML.split('<!-- Grid content generated by JS -->')[0];
    grid.innerHTML = header;

    // Generate rows for each time slot
    for (let idx = 1; idx <= tt.maxIndex; idx++) {
        // Time column
        const timeCell = document.createElement('div');
        timeCell.className = 'tt-time-col';
        timeCell.textContent = tt.indexLabel[idx] || `第${idx}节`;
        grid.appendChild(timeCell);

        // Cells for each weekday (1-7)
        for (let weekday = 1; weekday <= 7; weekday++) {
            const cell = document.createElement('div');
            cell.className = 'tt-cell';
            cell.dataset.weekday = weekday;
            cell.dataset.index = idx;

            // 检查时间段是否存在
            const slotKey = `${weekday}-${idx}`;
            const slotExists = !!tt.slotByKey[slotKey];

            // #region agent log - 检查周三3-3和周五的时间段
            if ((weekday === 3 && idx === 3) || weekday === 5) {
                try {
                    fetch('http://127.0.0.1:7242/ingest/b23c584d-8d7c-42cb-a198-4440966fe037', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ location: 'courses.js:renderTimetableGrid', message: 'Cell slot check', data: { weekday: weekday, index: idx, slotKey: slotKey, slotExists: slotExists, slotByKey_has: !!tt.slotByKey[slotKey], slotByKey_keys: Object.keys(tt.slotByKey).filter(k => k.startsWith(weekday + '-')).slice(0, 5) }, timestamp: Date.now(), sessionId: 'debug-session' }) }).catch(() => { });
                } catch (e) { }
            }
            // #endregion

            // 始终绑定拖拽事件，即使前端找不到时间段（后端会验证）
            // 这样可以确保即使前端时间段数据不完整，也能进行拖拽操作
            cell.addEventListener('dragover', handleDragOver);
            cell.addEventListener('drop', handleDrop);
            cell.addEventListener('dragleave', handleDragLeave);

            if (!slotExists) {
                // 时间段在前端不存在，添加警告样式（但不禁用拖拽）
                cell.classList.add('tt-cell-warning');
                cell.title = `${tt.weekdayNames[weekday] || `周${weekday}`}第${idx}节（前端未找到，但可以尝试拖拽）`;
                console.warn('⚠️ [renderTimetableGrid] 前端未找到时间段，但允许拖拽:', {
                    weekday: weekday,
                    index: idx,
                    slotKey: slotKey,
                    all_slots_count: tt.slots.length,
                    slotByKey_count: Object.keys(tt.slotByKey).length
                });
                // #region agent log
                if ((weekday === 3 && idx === 3) || weekday === 5) {
                    try {
                        fetch('http://127.0.0.1:7242/ingest/b23c584d-8d7c-42cb-a198-4440966fe037', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ location: 'courses.js:renderTimetableGrid', message: 'Cell warning - slot not found in frontend but drag enabled', data: { weekday: weekday, index: idx, slotKey: slotKey, all_slots_count: tt.slots.length, slotByKey_count: Object.keys(tt.slotByKey).length }, timestamp: Date.now(), sessionId: 'debug-session' }) }).catch(() => { });
                    } catch (e) { }
                }
                // #endregion
            }

            grid.appendChild(cell);
        }

        // Add midline after morning sessions
        if (idx === tt.config.morning) {
            const midline = document.createElement('div');
            midline.className = 'tt-midline';
            midline.style.gridColumn = '1 / -1';
            grid.appendChild(midline);
        }
    }

    loadSchedule();
}

// ==================== 四级级联筛选 ====================

// 初始化筛选器
async function initFilters() {
    console.log('🔧 initFilters 开始执行...');

    // 教师模式下不需要初始化筛选器
    const isTeacher = window.IS_TEACHER === true || window.IS_TEACHER === 'true';
    if (isTeacher) {
        console.log('⏭️ [教师模式] 跳过筛选器初始化');
        return;
    }

    try {
        updateFilterStatus('正在加载数据...', 'info');

        console.log('📥 准备加载数据，当前缓存状态:', {
            colleges: cache.colleges ? `已有${cache.colleges.length}个` : '空',
            departments: cache.departments ? `已有${cache.departments.length}个` : '空',
            classes: cache.classes ? `已有${cache.classes.length}个` : '空'
        });

        // 加载所有基础数据
        await Promise.all([
            loadCollegesData(),
            loadDepartmentsData(),
            loadClassesData()
        ]);

        console.log('✅ 数据加载完成:', {
            colleges: cache.colleges?.length || 0,
            departments: cache.departments?.length || 0,
            classes: cache.classes?.length || 0
        });

        // 初始化学院下拉框
        console.log('🎨 准备填充学院下拉框...');
        loadFilterColleges();

        if (!cache.colleges || cache.colleges.length === 0) {
            updateFilterStatus('⚠ 数据库中没有学院数据，请先创建学院', 'warning');
        } else {
            // 尝试恢复上次的筛选条件
            const restored = await restoreFilterState();

            if (!restored) {
                updateFilterStatus(`✓ 数据加载成功！找到 ${cache.colleges.length} 个学院，请选择学院开始筛选`, 'success');
            }
        }
    } catch (e) {
        console.error('❌ 初始化筛选器失败:', e);
        updateFilterStatus('✗ 加载数据失败: ' + (e.message || '网络错误'), 'danger');
    }
}

// 加载数据到缓存
async function loadCollegesData() {
    if (!cache.colleges) {
        try {
            cache.colleges = await api('/api/org/colleges?no_page=1');
            console.log(`✓ 加载学院数据: ${cache.colleges.length} 个`);
        } catch (e) {
            console.error('✗ 加载学院失败:', e);
            cache.colleges = [];
            throw new Error('加载学院数据失败');
        }
    }
}

async function loadDepartmentsData() {
    if (!cache.departments) {
        try {
            cache.departments = await api('/api/org/departments?no_page=1');
            console.log(`✓ 加载专业数据: ${cache.departments.length} 个`);
        } catch (e) {
            console.error('✗ 加载专业失败:', e);
            cache.departments = [];
            throw new Error('加载专业数据失败');
        }
    }
}

async function loadClassesData() {
    if (!cache.classes) {
        try {
            cache.classes = await api('/api/org/classes?no_page=1');
            console.log(`✓ 加载班级数据: ${cache.classes.length} 个`);
        } catch (e) {
            console.error('✗ 加载班级失败:', e);
            cache.classes = [];
            throw new Error('加载班级数据失败');
        }
    }
}

// 1. 加载学院列表
function loadFilterColleges() {
    const select = document.getElementById('filterCollege');
    console.log('loadFilterColleges 被调用:', {
        selectElement: select ? '存在' : '不存在',
        cacheColleges: cache.colleges ? `${cache.colleges.length}个` : '空',
        selectId: 'filterCollege'
    });

    if (!select) {
        console.error('❌ filterCollege 元素不存在！');
        return;
    }
    if (!cache.colleges) {
        console.error('❌ cache.colleges 为空！');
        return;
    }

    select.innerHTML = '<option value="">请选择学院</option>' +
        cache.colleges.map(c => `<option value="${c.id}">${c.name}</option>`).join('');

    console.log('✓ 学院下拉框已填充，共', cache.colleges.length, '个选项');
}

// 2. 学院变化 → 加载专业
function onCollegeChange() {
    const collegeId = document.getElementById('filterCollege').value;
    const majorSelect = document.getElementById('filterMajor');
    const gradeSelect = document.getElementById('filterGrade');
    const classSelect = document.getElementById('filterClass');

    // 重置后续选项
    majorSelect.innerHTML = '<option value="">请选择专业</option>';
    gradeSelect.innerHTML = '<option value="">请选择年级</option>';
    classSelect.innerHTML = '<option value="">请选择班级</option>';
    currentTargetId = null;
    clearTimetable();

    if (!collegeId) {
        updateFilterStatus('请选择学院');
        return;
    }

    // 筛选该学院的专业
    const majors = cache.departments.filter(d => String(d.college) === String(collegeId));

    if (majors.length === 0) {
        updateFilterStatus('该学院暂无专业', 'warning');
        return;
    }

    // 按专业名称排序
    majors.sort((a, b) => a.name.localeCompare(b.name, 'zh-CN'));

    majorSelect.innerHTML = '<option value="">请选择专业</option>' +
        majors.map(m => `<option value="${m.id}">${m.name}</option>`).join('');

    updateFilterStatus(`已选择学院，找到 ${majors.length} 个专业`, 'success');

    // 保存筛选状态
    saveFilterState();
}

// 3. 专业变化 → 加载年级
function onMajorChange() {
    const majorId = document.getElementById('filterMajor').value;
    const gradeSelect = document.getElementById('filterGrade');
    const classSelect = document.getElementById('filterClass');

    // 重置后续选项
    gradeSelect.innerHTML = '<option value="">请选择年级</option>';
    classSelect.innerHTML = '<option value="">请选择班级</option>';
    currentTargetId = null;
    clearTimetable();

    if (!majorId) {
        updateFilterStatus('请选择专业');
        return;
    }

    // 筛选该专业的所有班级
    const classes = cache.classes.filter(c => String(c.major) === String(majorId));

    if (classes.length === 0) {
        updateFilterStatus('该专业暂无班级', 'warning');
        return;
    }

    // 提取所有年级（去重）
    const grades = [...new Set(classes.map(c => c.enrollment_year))];
    grades.sort((a, b) => b - a); // 降序排列，新年级在前

    gradeSelect.innerHTML = '<option value="">请选择年级</option>' +
        grades.map(g => `<option value="${g}">${g}级</option>`).join('');

    updateFilterStatus(`已选择专业，找到 ${grades.length} 个年级`, 'success');

    // 保存筛选状态
    saveFilterState();
}

// 4. 年级变化 → 加载班级
function onGradeChange() {
    const majorId = document.getElementById('filterMajor').value;
    const grade = document.getElementById('filterGrade').value;
    const classSelect = document.getElementById('filterClass');

    // 重置班级选项
    classSelect.innerHTML = '<option value="">请选择班级</option>';
    currentTargetId = null;
    clearTimetable();

    if (!grade) {
        updateFilterStatus('请选择年级');
        return;
    }

    // 筛选该专业、该年级的班级
    const classes = cache.classes.filter(c =>
        String(c.major) === String(majorId) &&
        String(c.enrollment_year) === String(grade)
    );

    if (classes.length === 0) {
        updateFilterStatus('该年级暂无班级', 'warning');
        return;
    }

    // 按班级序号排序
    classes.sort((a, b) => (a.class_number || 0) - (b.class_number || 0));

    classSelect.innerHTML = '<option value="">请选择班级</option>' +
        classes.map(c => `<option value="${c.id}">${c.name}</option>`).join('');

    updateFilterStatus(`已选择年级，找到 ${classes.length} 个班级`, 'success');

    // 保存筛选状态
    saveFilterState();
}

// 5. 班级变化 → 加载课表
function onClassChange() {
    const classId = document.getElementById('filterClass').value;
    currentTargetId = classId;

    if (!classId) {
        updateFilterStatus('请选择班级');
        clearTimetable();
        return;
    }

    // 获取选中的班级名称
    const classSelect = document.getElementById('filterClass');
    const className = classSelect.options[classSelect.selectedIndex].text;

    updateFilterStatus(`正在加载 ${className} 的课表...`, 'info');

    // 设置视图模式为按班级
    currentViewMode = 'class';

    // 保存筛选状态
    saveFilterState();

    // 加载课表
    loadSchedule();
}

// 更新筛选状态提示
function updateFilterStatus(message, type = 'muted', force = false) {
    // 教师模式下使用专用的状态显示区域
    let statusEl = null;
    const isTeacher = window.IS_TEACHER === true || window.IS_TEACHER === 'true';
    const isStudent = window.USER_ROLE === 'student';
    if (isTeacher || isStudent) {
        statusEl = document.getElementById('teacherScheduleStatus');
    } else {
        statusEl = document.getElementById('filterStatus');
    }
    if (!statusEl) {
        console.warn('⚠️ [updateFilterStatus] 状态元素不存在');
        return;
    }

    // 如果有时间段警告且不是强制更新，则不覆盖警告信息
    if (hasTimeslotWarning && !force) {
        console.log('⏸️ 跳过状态更新，因为有时间段警告显示中');
        return;
    }

    const icons = {
        success: '✓',
        warning: '⚠',
        danger: '✗',
        info: 'ℹ',
        muted: '→'
    };

    const icon = icons[type] || icons.muted;
    statusEl.innerHTML = `${icon} ${message}`;
    statusEl.className = `mt-2 small text-${type}`;
    hasTimeslotWarning = false;  // 清除警告标记
}

// 清空所有筛选
function clearFilters() {
    document.getElementById('filterCollege').value = '';
    document.getElementById('filterMajor').innerHTML = '<option value="">请选择专业</option>';
    document.getElementById('filterGrade').innerHTML = '<option value="">请选择年级</option>';
    document.getElementById('filterClass').innerHTML = '<option value="">请选择班级</option>';

    currentTargetId = null;
    currentWeek = 1; // 重置为第1周
    updateWeekLabel();
    clearTimetable();
    clearFilterState(); // 清除记忆
    updateFilterStatus('已重置筛选，请重新选择', 'muted');
}

// 重置课程表（清除当前筛选班级的所有排课，保持筛选班级不变）
async function resetTimetable() {
    // 检查是否有选中的班级
    const classId = document.getElementById('filterClass')?.value;
    const classSelect = document.getElementById('filterClass');
    const className = classSelect?.options[classSelect?.selectedIndex]?.text || '当前班级';

    // 如果没有选中班级，提示用户先选择班级
    if (!classId || !currentTargetId) {
        customAlert('请先选择要重置的班级', '提示', 'warning');
        return;
    }

    // 确认删除该班级的所有排课
    const confirmDelete = await customConfirm(
        `确定要重置课程表吗？\n\n` +
        `当前选中班级：${className}\n\n` +
        `⚠️ 警告：点击"确定"将删除该班级的所有排课记录（所有周次），此操作不可恢复！\n\n` +
        `重置后，筛选条件将保持不变，您可以继续为该班级重新排课。`,
        '重置课程表 - 删除排课'
    );

    if (!confirmDelete) {
        // 用户取消，不执行任何操作
        return;
    }

    try {
        updateFilterStatus('正在删除排课，请稍候...', 'info');

        // 调用批量删除API，删除该班级的所有排课（不指定week_number，删除所有周次）
        const result = await api('/api/courses/schedules/bulk_delete/', 'POST', {
            school_class: classId
        });

        const deletedCount = result.deleted || 0;

        // 清空课程表显示
        clearTimetable();

        // 重新加载课表（显示空课表）
        await loadSchedule();

        // 更新状态提示
        updateFilterStatus(`✓ 已删除 ${className} 的 ${deletedCount} 条课程安排，筛选条件已保持`, 'success');

        // 显示成功提示
        customAlert(`重置成功！\n\n已删除 ${className} 的 ${deletedCount} 条课程安排。\n\n筛选条件已保持，您可以继续为该班级重新排课。`, '重置成功', 'success');
    } catch (e) {
        console.error('删除排课失败:', e);
        customAlert('删除排课失败：' + (e.message || '未知错误'), '错误', 'error');
        // 即使删除失败，也重新加载课表
        await loadSchedule();
    }
}

// Load schedule data based on current view
async function loadSchedule() {
    const startTime = performance.now();
    console.log('📥 [loadSchedule] 开始加载课表...');

    const isTeacher = window.IS_TEACHER === true || window.IS_TEACHER === 'true';
    const isAdmin = window.IS_ADMIN === true || window.IS_ADMIN === 'true';
    const isStudent = window.USER_ROLE === 'student';

    if (!isTeacher && !isStudent && !currentTargetId) {
        clearTimetable();
        updateFilterStatus('请先选择班级', 'warning');
        return;
    }

    // 确保week_number有值，默认第1周
    if (!currentWeek || currentWeek < 1) {
        currentWeek = 1;
    }

    const params = new URLSearchParams();
    params.append('week_number', currentWeek);

    // 只有管理员模式才需要指定班级
    if (currentTargetId && isAdmin) {
        params.append('school_class', currentTargetId);
    }

    const apiUrl = '/api/courses/schedules/?' + params.toString();
    console.log('📥 [loadSchedule] 请求URL:', apiUrl);

    try {
        // 设置超时：0.5秒
        const timeoutPromise = new Promise((_, reject) =>
            setTimeout(() => reject(new Error('请求超时：超过0.5秒')), 500)
        );

        // 创建API请求Promise
        const apiPromise = api(apiUrl);

        // 使用Promise.race实现超时控制
        const response = await Promise.race([apiPromise, timeoutPromise]);

        const loadTime = (performance.now() - startTime).toFixed(0);
        console.log(`📥 [loadSchedule] API响应成功，耗时: ${loadTime}ms`);

        // 处理可能的分页格式
        const r = Array.isArray(response) ? response : (response.results || []);
        scheduleData = r;

        // 调试：打印返回的数据格式，特别是周五的课程
        console.log('📥 [loadSchedule] 加载到的课程安排:', r.length, '个');
        if (r.length > 0) {
            console.log('📥 [loadSchedule] 第一条课程数据示例:', r[0]);
        }
        console.log('📥 [loadSchedule] 所有课程的weekday分布:', r.map(s => {
            if (typeof s.timeslot === 'object' && s.timeslot !== null) {
                return s.timeslot.weekday;
            }
            return 'unknown';
        }));

        const fridaySchedules = r.filter(s => {
            if (typeof s.timeslot === 'object' && s.timeslot !== null) {
                return Number(s.timeslot.weekday) === 5;
            }
            return false;
        });
        if (fridaySchedules.length > 0) {
            console.log('📥 [loadSchedule] 周五的课程安排:', fridaySchedules);
            fridaySchedules.forEach(s => {
                console.log('  - 课程ID:', s.id, 'timeslot:', s.timeslot, 'weekday:', s.timeslot?.weekday, 'index:', s.timeslot?.index);
            });
        } else {
            console.warn('⚠️ [loadSchedule] 没有找到周五的课程安排');
        }

        // #region agent log
        try {
            fetch('http://127.0.0.1:7242/ingest/b23c584d-8d7c-42cb-a198-4440966fe037', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ location: 'courses.js:loadSchedule', message: 'Load schedule response', data: { count: r.length, schedules: r.map(s => ({ id: s.id, timeslot: s.timeslot, weekday: s.timeslot?.weekday || 'N/A', index: s.timeslot?.index || 'N/A' })) }, timestamp: Date.now(), sessionId: 'debug-session' }) }).catch(() => { });
        } catch (e) { }
        // #endregion

        const renderStartTime = performance.now();

        if (r.length === 0) {
            clearTimetable();
            if (isTeacher) {
                updateFilterStatus('本周暂无课程安排', 'warning');
            } else {
                updateFilterStatus('该班级本周暂无课程安排', 'warning');
            }
        } else {
            console.log('📥 [loadSchedule] 准备渲染课程表，课程数量:', r.length);
            await renderSchedule(r);
            const renderTime = (performance.now() - renderStartTime).toFixed(0);
            const totalTime = (performance.now() - startTime).toFixed(0);
            console.log(`📥 [loadSchedule] 课程表渲染完成，渲染耗时: ${renderTime}ms，总耗时: ${totalTime}ms`);

            // 获取班级名称
            if (isTeacher) {
                updateFilterStatus(`✓ 已加载您的课表，共 ${r.length} 节课（${totalTime}ms）`, 'success');
            } else if (isStudent) {
                updateFilterStatus(`✓ 已加载您的课表，共 ${r.length} 节课`, 'success');
            } else {
                const classSelect = document.getElementById('filterClass');
                const className = classSelect?.options[classSelect.selectedIndex]?.text || '选中班级';
                updateFilterStatus(`已加载 ${className} 的课表，共 ${r.length} 节课`, 'success');
            }
        }
    } catch (e) {
        const totalTime = (performance.now() - startTime).toFixed(0);
        console.error('❌ 加载课程表失败:', e, `耗时: ${totalTime}ms`);
        clearTimetable();

        if (e.message && e.message.includes('超时')) {
            updateFilterStatus('✗ 加载超时，请刷新页面重试', 'danger');
        } else {
            updateFilterStatus('✗ 加载课表失败: ' + (e.message || '网络错误'), 'danger');
        }
    }
}

async function renderSchedule(schedules) {
    clearTimetable();

    console.log('🎨 [renderSchedule] 开始渲染', schedules.length, '个课程安排');
    console.log('🎨 [renderSchedule] tt.slotById keys:', Object.keys(tt.slotById).slice(0, 10));
    console.log('🎨 [renderSchedule] tt.slotById count:', Object.keys(tt.slotById).length);
    console.log('🎨 [renderSchedule] tt.slots count:', tt.slots.length);
    console.log('🎨 [renderSchedule] tt.slotByKey count:', Object.keys(tt.slotByKey).length);

    // 如果slotById为空或太少，重新从slots填充
    if (Object.keys(tt.slotById).length < tt.slots.length || tt.slots.length === 0) {
        console.warn('⚠️ [renderSchedule] slotById数据不完整，重新填充...', {
            slotById_count: Object.keys(tt.slotById).length,
            slots_count: tt.slots.length,
            slotById_keys: Object.keys(tt.slotById).slice(0, 10)
        });

        // 如果slots也为空，需要重新加载时间段数据
        if (tt.slots.length === 0) {
            console.warn('⚠️ [renderSchedule] tt.slots也为空，需要重新初始化时间段数据');
            await initTimetable();
        }

        // 重新填充slotById和slotByKey
        tt.slotById = {};
        tt.slotByKey = {};
        tt.slots.forEach(s => {
            if (s && s.id) {
                tt.slotById[s.id] = s;
                const key = `${s.weekday}-${s.index}`;
                tt.slotByKey[key] = s;
            }
        });
        console.log('✅ [renderSchedule] 重新填充完成，slotById count:', Object.keys(tt.slotById).length, 'slotByKey count:', Object.keys(tt.slotByKey).length);
    }

    // 统计渲染成功和失败的数量
    let renderedCount = 0;
    let failedCount = 0;
    const failedSchedules = [];

    schedules.forEach(sch => {
        // #region agent log
        try {
            fetch('http://127.0.0.1:7242/ingest/b23c584d-8d7c-42cb-a198-4440966fe037', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ location: 'courses.js:renderSchedule', message: 'Rendering schedule', data: { schedule_id: sch.id, timeslot: sch.timeslot, timeslot_type: typeof sch.timeslot, slotById_keys: Object.keys(tt.slotById).slice(0, 5) }, timestamp: Date.now(), sessionId: 'debug-session' }) }).catch(() => { });
        } catch (e) { }
        // #endregion

        // 处理timeslot：可能是对象或ID
        let slot = null;
        let weekday = null;
        let index = null;
        let timeslotId = null;

        if (typeof sch.timeslot === 'object' && sch.timeslot !== null) {
            // timeslot是对象，直接提取weekday和index
            timeslotId = sch.timeslot.id;
            // 确保weekday和index是数字类型
            weekday = Number(sch.timeslot.weekday);
            index = Number(sch.timeslot.index);

            console.log('🔍 [renderSchedule] timeslot是对象:', {
                schedule_id: sch.id,
                timeslot: sch.timeslot,
                weekday: weekday,
                index: index,
                weekday_type: typeof weekday,
                index_type: typeof index,
                timeslotId: timeslotId
            });

            // 尝试从slotById或slotByKey查找完整的slot对象
            if (timeslotId) {
                slot = tt.slotById[timeslotId];
            }
            if (!slot && weekday !== null && index !== null) {
                const slotKey = `${weekday}-${index}`;
                slot = tt.slotByKey[slotKey];
                // 如果找到了，也更新slotById
                if (slot && timeslotId) {
                    tt.slotById[timeslotId] = slot;
                    console.log('✅ [renderSchedule] 从slotByKey找到slot:', slotKey, slot);
                }
            }

            // 如果还是找不到，但weekday和index存在，创建一个临时slot对象
            if (!slot && weekday !== null && index !== null) {
                slot = {
                    id: timeslotId || 0,
                    weekday: weekday,
                    index: index,
                    start_time: sch.timeslot.start_time || '',
                    end_time: sch.timeslot.end_time || ''
                };
                console.log('✅ [renderSchedule] 使用timeslot对象中的weekday和index创建临时slot:', slot);
            }
        } else {
            // timeslot是ID，从slotById查找
            timeslotId = Number(sch.timeslot);
            slot = tt.slotById[timeslotId];

            // 如果找不到slot，尝试从slots数组直接查找
            if (!slot && tt.slots.length > 0) {
                slot = tt.slots.find(s => s.id === timeslotId);
                if (slot) {
                    // 如果找到了，更新slotById和slotByKey
                    tt.slotById[timeslotId] = slot;
                    const key = `${slot.weekday}-${slot.index}`;
                    tt.slotByKey[key] = slot;
                    console.log('✅ [renderSchedule] 从slots数组中找到时间段并更新:', timeslotId, key);
                }
            }

            if (slot) {
                weekday = Number(slot.weekday);
                index = Number(slot.index);
            }
        }

        // 如果仍然没有weekday和index，无法渲染
        if (weekday === null || index === null) {
            failedCount++;
            failedSchedules.push({
                id: sch.id,
                timeslotId: timeslotId,
                course: sch.course
            });
            console.warn('⚠️ [renderSchedule] 无法确定时间段位置:', {
                schedule_id: sch.id,
                timeslot: sch.timeslot,
                timeslotId: timeslotId,
                weekday: weekday,
                index: index,
                available_slots_count: Object.keys(tt.slotById).length,
                all_slots_count: tt.slots.length
            });
            // #region agent log
            try {
                fetch('http://127.0.0.1:7242/ingest/b23c584d-8d7c-42cb-a198-4440966fe037', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ location: 'courses.js:renderSchedule', message: 'Slot not found', data: { schedule_id: sch.id, timeslot: sch.timeslot, timeslotId: timeslotId, weekday: weekday, index: index, available_slots: Object.keys(tt.slotById) }, timestamp: Date.now(), sessionId: 'debug-session' }) }).catch(() => { });
            } catch (e) { }
            // #endregion
            return;
        }

        // 使用weekday和index直接查找单元格（不依赖slot对象）
        // 确保weekday和index是数字类型
        weekday = Number(weekday);
        index = Number(index);

        // 尝试多种方式查找单元格（兼容字符串和数字类型）
        let cell = document.querySelector(`.tt-cell[data-weekday="${weekday}"][data-index="${index}"]`);
        if (!cell) {
            // 尝试使用字符串形式查找
            cell = document.querySelector(`.tt-cell[data-weekday="${String(weekday)}"][data-index="${String(index)}"]`);
        }
        if (!cell) {
            // 尝试查找所有周五的单元格（用于调试）
            const allCells = document.querySelectorAll('.tt-cell');
            const fridayCells = document.querySelectorAll('.tt-cell[data-weekday="5"]');
            const matchingCells = Array.from(allCells).filter(c => {
                const cWeekday = Number(c.dataset.weekday);
                const cIndex = Number(c.dataset.index);
                return cWeekday === weekday && cIndex === index;
            });

            console.error('❌ [renderSchedule] 找不到单元格:', {
                weekday: weekday,
                index: index,
                weekday_type: typeof weekday,
                index_type: typeof index,
                schedule_id: sch.id,
                cell_selector: `.tt-cell[data-weekday="${weekday}"][data-index="${index}"]`,
                all_cells: allCells.length,
                friday_cells: fridayCells.length,
                matching_cells: matchingCells.length,
                matching_cells_info: matchingCells.map(c => ({
                    weekday: c.dataset.weekday,
                    index: c.dataset.index,
                    weekday_type: typeof c.dataset.weekday,
                    index_type: typeof c.dataset.index
                }))
            });

            // 如果找到了匹配的单元格但选择器失败，直接使用匹配的单元格
            if (matchingCells.length > 0) {
                cell = matchingCells[0];
                console.log('✅ [renderSchedule] 通过备用方法找到单元格:', cell);
            } else {
                // #region agent log
                try {
                    fetch('http://127.0.0.1:7242/ingest/b23c584d-8d7c-42cb-a198-4440966fe037', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ location: 'courses.js:renderSchedule', message: 'Cell not found', data: { weekday: weekday, index: index, schedule_id: sch.id }, timestamp: Date.now(), sessionId: 'debug-session' }) }).catch(() => { });
                } catch (e) { }
                // #endregion
                return;
            }
        }

        // 确保slot对象存在（用于createScheduleBlock）
        if (!slot) {
            slot = {
                id: timeslotId || 0,
                weekday: weekday,
                index: index
            };
        }

        const block = createScheduleBlock(sch, slot);
        cell.appendChild(block);
        renderedCount++;

        // 特别标记周五的课程渲染
        if (weekday === 5) {
            console.log('🎉 [renderSchedule] 周五课程渲染成功:', {
                schedule_id: sch.id,
                weekday: weekday,
                index: index,
                cell_found: !!cell,
                cell_weekday: cell?.dataset?.weekday,
                cell_index: cell?.dataset?.index
            });
        }
        console.log('✅ [renderSchedule] 已渲染课程:', sch.id, '到', slot.weekday, '第', slot.index, '节');
    });

    console.log(`✅ [renderSchedule] 渲染完成: 成功 ${renderedCount} 个, 失败 ${failedCount} 个`);

    // 如果有渲染失败的，尝试重新加载时间段数据
    if (failedCount > 0) {
        console.warn('⚠️ [renderSchedule] 部分课程渲染失败，尝试重新加载时间段数据...', failedSchedules);
        // 尝试重新初始化时间段数据
        try {
            await initTimetable();
            // 重新尝试渲染失败的课程
            const retrySchedules = schedules.filter(sch => {
                const timeslotId = typeof sch.timeslot === 'object' && sch.timeslot !== null ? sch.timeslot.id : Number(sch.timeslot);
                return failedSchedules.some(f => f.id === sch.id && f.timeslotId === timeslotId);
            });

            if (retrySchedules.length > 0) {
                console.log('🔄 [renderSchedule] 重新尝试渲染', retrySchedules.length, '个课程');
                retrySchedules.forEach(sch => {
                    let slot = null;
                    let weekday = null;
                    let index = null;

                    if (typeof sch.timeslot === 'object' && sch.timeslot !== null) {
                        weekday = sch.timeslot.weekday;
                        index = sch.timeslot.index;
                        const timeslotId = sch.timeslot.id;
                        slot = tt.slotById[timeslotId] || tt.slotByKey[`${weekday}-${index}`];
                        if (!slot && weekday !== null && index !== null) {
                            slot = {
                                id: timeslotId || 0,
                                weekday: weekday,
                                index: index
                            };
                        }
                    } else {
                        const timeslotId = Number(sch.timeslot);
                        slot = tt.slotById[timeslotId];
                        if (slot) {
                            weekday = slot.weekday;
                            index = slot.index;
                        }
                    }

                    if (weekday !== null && index !== null) {
                        const cell = document.querySelector(`.tt-cell[data-weekday="${weekday}"][data-index="${index}"]`);
                        if (cell && !cell.querySelector(`[data-schedule-id="${sch.id}"]`)) {
                            if (!slot) {
                                slot = { id: 0, weekday: weekday, index: index };
                            }
                            const block = createScheduleBlock(sch, slot);
                            cell.appendChild(block);
                            console.log('✅ [renderSchedule] 重试渲染成功:', sch.id);
                        }
                    }
                });
            }
        } catch (e) {
            console.error('❌ [renderSchedule] 重新加载时间段数据失败:', e);
        }
    }
}

function createScheduleBlock(sch, slot) {
    const block = document.createElement('div');
    block.className = 'tt-block';
    block.dataset.scheduleId = sch.id;
    // 只有管理员才能拖拽课程
    const isAdmin = window.IS_ADMIN === true || window.IS_ADMIN === 'true';
    block.draggable = isAdmin;

    // 优先使用后端返回的名称，如果没有则从本地映射获取
    const courseName = sch.course_name || tt.courseMap[sch.course] || `课程#${sch.course}`;
    const teacherName = sch.teacher_name || tt.teacherLabelMap[sch.teacher] || '-';
    const className = sch.class_name || '-';
    // 优先使用classroom_name，如果没有则使用classroom外键
    const roomName = sch.classroom_name || tt.roomMap[sch.classroom] || '-';

    // 根据用户角色显示不同的信息
    const isTeacher = window.IS_TEACHER === true || window.IS_TEACHER === 'true';

    let contentHtml = '';
    if (isTeacher) {
        // 教师模式：只显示班级和教室（不显示课程名称）
        contentHtml = `
            <div class="tt-course-name">${className}</div>
            <div class="tt-info">${roomName}</div>
        `;
    } else if (window.USER_ROLE === 'student') {
        // 学生模式：显示课程名称、教师、教室（不显示班级，因为就是看自己班的）
        contentHtml = `
            <div class="tt-course-name">${courseName}</div>
            <div class="tt-info">${teacherName}</div>
            <div class="tt-info">@${roomName}</div>
        `;
    } else {
        // 管理员模式：显示完整信息
        contentHtml = `
            <div class="tt-course-name">${courseName}</div>
            <div class="tt-info">班级: ${className}</div>
            <div class="tt-info">教师: ${teacherName}</div>
            <div class="tt-info">教室: ${roomName}</div>
        `;
    }

    // 只有管理员才显示删除按钮
    const actionsHtml = isAdmin ? `
        <div class="tt-actions">
            <span class="tt-del" onclick="deleteSchedule(${sch.id})">×</span>
        </div>
    ` : '';

    block.innerHTML = `
        ${contentHtml}
        ${actionsHtml}
    `;

    // 只有管理员才能拖拽（使用之前已声明的isAdmin变量）
    if (isAdmin) {
        block.addEventListener('dragstart', (e) => {
            e.dataTransfer.setData('text/plain', JSON.stringify({
                scheduleId: sch.id,
                isExisting: true
            }));
            e.dataTransfer.effectAllowed = 'move';
            document.getElementById('timetableGrid').classList.add('is-dragging');
        });

        block.addEventListener('dragend', () => {
            document.getElementById('timetableGrid').classList.remove('is-dragging');
        });
    }

    return block;
}

function clearTimetable() {
    document.querySelectorAll('.tt-cell').forEach(cell => {
        cell.innerHTML = '';
    });
}

// Drag and drop handlers
function handleDragOver(ev) {
    ev.preventDefault();
    ev.currentTarget.classList.add('dragover');
}

function handleDragLeave(ev) {
    ev.currentTarget.classList.remove('dragover');
}

async function handleDrop(ev) {
    ev.preventDefault();
    ev.currentTarget.classList.remove('dragover');

    const cell = ev.currentTarget;
    const weekday = Number(cell.dataset.weekday);
    const index = Number(cell.dataset.index);

    console.log('🎯 [handleDrop] 拖拽到单元格:', {
        weekday: weekday,
        index: index,
        slotKey: `${weekday}-${index}`,
        slotExists: !!tt.slotByKey[`${weekday}-${index}`]
    });

    // 不再提前检查时间段是否存在，直接尝试创建/移动
    // createSchedule/moveSchedule 函数会处理时间段查找和验证
    const data = JSON.parse(ev.dataTransfer.getData('text/plain'));

    if (data.isExisting) {
        // Moving existing schedule
        await moveSchedule(data.scheduleId, weekday, index);
    } else if (data.course) {
        // Creating new schedule from palette
        await createSchedule(data.course, weekday, index);
        // createSchedule内部已经调用了loadSchedule，这里不需要再次调用
        return;
    }

    // 如果是移动现有课程，需要刷新课程表
    await loadSchedule();
}

async function createSchedule(courseId, weekday, index) {
    if (!currentTargetId) {
        customAlert('请先选择班级/教师/教室', '提示', 'warning');
        return;
    }

    const slotKey = `${weekday}-${index}`;
    let slot = tt.slotByKey[slotKey];

    // 如果找不到slot，尝试从slots数组查找
    if (!slot && tt.slots.length > 0) {
        slot = tt.slots.find(s => s.weekday === weekday && s.index === index);
        if (slot) {
            // 更新slotByKey
            tt.slotByKey[slotKey] = slot;
            tt.slotById[slot.id] = slot;
            console.log('✅ [createSchedule] 从slots数组中找到时间段:', slotKey, slot);
        }
    }

    // 如果还是找不到slot，但仍然尝试创建（后端会验证时间段是否存在）
    if (!slot) {
        const weekdayName = tt.weekdayNames[weekday] || `周${weekday}`;
        console.warn('⚠️ [createSchedule] 前端找不到时间段，但继续尝试创建（后端会验证）:', {
            slotKey: slotKey,
            weekday: weekday,
            index: index,
            weekdayName: weekdayName
        });

        // 检查是否完全没有时间段数据
        if (tt.slots.length === 0) {
            customAlert('时间段数据未加载！\n\n系统尚未生成时间段数据，无法进行排课。\n\n请点击"生成标准时间段"按钮或联系管理员。', '时间段不存在', 'error');
            return;
        }

        // 创建一个临时的slot对象用于发送请求
        // 注意：这里使用一个占位ID，后端会根据weekday和index查找实际的时间段
        // 但实际上，我们需要知道真实的timeslot ID
        // 让我们先尝试从后端获取这个时间段
        try {
            // 尝试从后端获取该时间段
            const timeslots = await api('/api/courses/timeslots/');
            const timeslotsArray = Array.isArray(timeslots) ? timeslots : (timeslots.results || []);
            // 确保比较时类型一致（都转换为数字）
            const foundSlot = timeslotsArray.find(s => Number(s.weekday) === Number(weekday) && Number(s.index) === Number(index));

            if (foundSlot) {
                slot = foundSlot;
                // 更新前端缓存
                tt.slotByKey[slotKey] = slot;
                tt.slotById[slot.id] = slot;
                if (!tt.slots.find(s => s.id === slot.id)) {
                    tt.slots.push(slot);
                }
                console.log('✅ [createSchedule] 从后端获取到时间段:', slot);
            } else {
                const weekdayName = tt.weekdayNames[weekday] || `周${weekday}`;
                const availableSlots = timeslotsArray.filter(s => Number(s.weekday) === Number(weekday));
                let errorMsg = `${weekdayName}第${index}节不存在。`;
                if (availableSlots.length > 0) {
                    const availableIndexes = availableSlots.map(s => Number(s.index)).sort((a, b) => a - b);
                    errorMsg += `\n\n该天可用的时间段：第${availableIndexes.join('、')}节`;
                }
                customAlert(errorMsg, '时间段不存在', 'error');
                return;
            }
        } catch (e) {
            console.error('❌ [createSchedule] 无法从后端获取时间段:', e);
            customAlert('无法验证时间段，请刷新页面后重试', '错误', 'error');
            return;
        }
    }

    const course = tt.courseObjs[courseId];
    if (!course) return;

    // 检查课程是否有教师
    if (!course.teacher) {
        customAlert('该课程未指定授课教师，请先编辑课程添加教师后再排课', '提示', 'warning');
        return;
    }

    const payload = {
        course: courseId,
        timeslot: slot.id,
        week_number: currentWeek
    };

    // 如果课程有默认教室地址，复制到课程安排中
    if (course.classroom) {
        payload.classroom_name = course.classroom;
    }

    if (currentViewMode === 'class') {
        payload.school_class = currentTargetId;
        payload.teacher = course.teacher;
    } else if (currentViewMode === 'teacher') {
        payload.teacher = currentTargetId;
        customAlert('请先选择班级进行排课', '提示', 'warning');
        return;
    } else if (currentViewMode === 'classroom') {
        payload.classroom = currentTargetId;
        customAlert('请先选择班级进行排课', '提示', 'warning');
        return;
    }

    // 调试：打印创建请求的payload
    console.log('📤 [createSchedule] 准备创建课程，payload:', {
        ...payload,
        currentWeek: currentWeek,
        currentWeek_type: typeof currentWeek,
        slot_weekday: slot.weekday,
        slot_index: slot.index
    });

    try {
        const result = await api('/api/courses/schedules/', 'POST', payload);

        // 创建成功后只显示成功消息，不再询问是否复制
        showMessage('scheduleMsg', '排课成功', 'success');

        // 调试：打印创建结果
        console.log('✅ [createSchedule] 创建成功，返回结果:', result);
        if (result && result.timeslot) {
            const resultWeekday = typeof result.timeslot === 'object' ? result.timeslot.weekday : null;
            const resultIndex = typeof result.timeslot === 'object' ? result.timeslot.index : null;

            console.log('✅ [createSchedule] timeslot信息:', {
                timeslot: result.timeslot,
                weekday: resultWeekday,
                index: resultIndex,
                type: typeof result.timeslot
            });

            // 特别标记周五的课程创建
            if (Number(resultWeekday) === 5) {
                console.log('🎉 [createSchedule] 周五课程创建成功！准备刷新课程表...', {
                    schedule_id: result.id,
                    weekday: resultWeekday,
                    index: resultIndex,
                    timeslot_id: typeof result.timeslot === 'object' ? result.timeslot.id : result.timeslot
                });
            }
        }

        // #region agent log
        try {
            fetch('http://127.0.0.1:7242/ingest/b23c584d-8d7c-42cb-a198-4440966fe037', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ location: 'courses.js:createSchedule', message: 'Create schedule success', data: { result: result, payload: payload }, timestamp: Date.now(), sessionId: 'debug-session' }) }).catch(() => { });
        } catch (e) { }
        // #endregion

        // 如果用户选择不复制，或者不在第一周，显示成功消息
        if (!(currentWeek === 1 && result && result.id)) {
            showMessage('scheduleMsg', '排课成功', 'success');
        } else if (currentWeek === 1 && result && result.id) {
            // 已经在上面处理了复制逻辑，这里不需要再显示消息
        }

        // 调试：立即查询刚创建的课程，验证是否真的保存成功
        if (result && result.id) {
            try {
                const verifyResponse = await api(`/api/courses/schedules/${result.id}/`);
                console.log('🔍 [createSchedule] 验证查询刚创建的课程:', verifyResponse);

                // 再次查询所有课程，看看是否包含新创建的
                const allSchedules = await api(`/api/courses/schedules/?school_class=${currentTargetId}&week_number=${currentWeek}`);
                const allSchedulesArray = Array.isArray(allSchedules) ? allSchedules : (allSchedules.results || []);
                const foundNewSchedule = allSchedulesArray.find(s => s.id === result.id);
                if (foundNewSchedule) {
                    console.log('✅ [createSchedule] 验证成功：新创建的课程在查询结果中:', foundNewSchedule);
                } else {
                    console.error('❌ [createSchedule] 验证失败：新创建的课程不在查询结果中！', {
                        created_id: result.id,
                        created_teacher: result.teacher,
                        total_count: allSchedulesArray.length,
                        all_ids: allSchedulesArray.map(s => s.id),
                        all_teachers: allSchedulesArray.map(s => s.teacher),
                        created_timeslot: result.timeslot,
                        created_weekday: typeof result.timeslot === 'object' ? result.timeslot.weekday : 'N/A'
                    });

                    // 尝试不指定school_class查询，看看是否能找到
                    try {
                        const allSchedulesNoFilter = await api(`/api/courses/schedules/?week_number=${currentWeek}`);
                        const allSchedulesNoFilterArray = Array.isArray(allSchedulesNoFilter) ? allSchedulesNoFilter : (allSchedulesNoFilter.results || []);
                        const foundInNoFilter = allSchedulesNoFilterArray.find(s => s.id === result.id);
                        if (foundInNoFilter) {
                            console.warn('⚠️ [createSchedule] 不指定school_class时能找到，说明可能是权限过滤问题！', {
                                found: foundInNoFilter,
                                total_in_no_filter: allSchedulesNoFilterArray.length
                            });
                        } else {
                            console.error('❌ [createSchedule] 即使不指定school_class也找不到，可能是其他过滤问题！');
                        }
                    } catch (e) {
                        console.error('❌ [createSchedule] 查询失败:', e);
                    }
                }
            } catch (e) {
                console.error('❌ [createSchedule] 验证查询失败:', e);
            }
        }

        // 立即刷新课程表
        await loadSchedule();
    } catch (e) {
        // #region agent log
        try {
            fetch('http://127.0.0.1:7242/ingest/b23c584d-8d7c-42cb-a198-4440966fe037', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ location: 'courses.js:createSchedule', message: 'Create schedule error', data: { error: e.message, payload: payload }, timestamp: Date.now(), sessionId: 'debug-session' }) }).catch(() => { });
        } catch (e2) { }
        // #endregion
        showMessage('scheduleMsg', e.message || '排课失败', 'error');
    }
}

async function moveSchedule(scheduleId, weekday, index) {
    const slotKey = `${weekday}-${index}`;
    let slot = tt.slotByKey[slotKey];

    // 如果找不到slot，尝试从slots数组查找
    if (!slot && tt.slots.length > 0) {
        slot = tt.slots.find(s => s.weekday === weekday && s.index === index);
        if (slot) {
            tt.slotByKey[slotKey] = slot;
            tt.slotById[slot.id] = slot;
            console.log('✅ [moveSchedule] 从slots数组中找到时间段:', slotKey, slot);
        }
    }

    // 如果还是找不到，尝试从后端获取
    if (!slot) {
        console.warn('⚠️ [moveSchedule] 前端找不到时间段，尝试从后端获取:', {
            weekday: weekday,
            index: index,
            slotKey: slotKey
        });

        if (tt.slots.length === 0) {
            customAlert('时间段数据未加载！\n\n系统尚未生成时间段数据，无法移动课程。\n\n请点击"生成标准时间段"按钮或联系管理员。', '时间段不存在', 'error');
            return;
        }

        try {
            const timeslots = await api('/api/courses/timeslots/');
            const timeslotsArray = Array.isArray(timeslots) ? timeslots : (timeslots.results || []);
            // 确保比较时类型一致（都转换为数字）
            const foundSlot = timeslotsArray.find(s => Number(s.weekday) === Number(weekday) && Number(s.index) === Number(index));

            if (foundSlot) {
                slot = foundSlot;
                tt.slotByKey[slotKey] = slot;
                tt.slotById[slot.id] = slot;
                if (!tt.slots.find(s => s.id === slot.id)) {
                    tt.slots.push(slot);
                }
                console.log('✅ [moveSchedule] 从后端获取到时间段:', slot);
            } else {
                const weekdayName = tt.weekdayNames[weekday] || `周${weekday}`;
                const availableSlots = timeslotsArray.filter(s => Number(s.weekday) === Number(weekday));
                let errorMsg = `${weekdayName}第${index}节不存在，无法移动课程。`;
                if (availableSlots.length > 0) {
                    const availableIndexes = availableSlots.map(s => Number(s.index)).sort((a, b) => a - b);
                    errorMsg += `\n\n该天可用的时间段：第${availableIndexes.join('、')}节`;
                }
                customAlert(errorMsg, '时间段不存在', 'error');
                return;
            }
        } catch (e) {
            console.error('❌ [moveSchedule] 无法从后端获取时间段:', e);
            customAlert('无法验证时间段，请刷新页面后重试', '错误', 'error');
            return;
        }
    }

    try {
        await api(`/api/courses/schedules/${scheduleId}/`, 'PATCH', {
            timeslot: slot.id
        });
        showMessage('scheduleMsg', '移动成功', 'success');
        // 立即刷新课程表
        await loadSchedule();
    } catch (e) {
        customAlert(e.message || '移动失败', '错误', 'error');
    }
}

async function deleteSchedule(scheduleId) {
    if (!await customConfirm('确定删除这节课吗？', '确认删除')) return;

    try {
        await api(`/api/courses/schedules/${scheduleId}/`, 'DELETE');
        loadSchedule();
    } catch (e) {
        customAlert(e.message || '删除失败', '错误', 'error');
    }
}

// ==================== 双击编辑课程列表中的课程 ====================
let currentEditingCourse = null;
let allTeachersForEdit = []; // 存储所有教师数据用于实时筛选

async function openEditCourseFromList(courseId) {
    try {
        // 获取课程详情
        const course = await api(`/api/courses/courses/${courseId}/`);
        currentEditingCourse = course;

        // 填充表单
        document.getElementById('editScheduleCourseName').value = course.name || '';
        document.getElementById('editScheduleClassroom').value = course.classroom || '';
        document.getElementById('editScheduleTeacherSearch').value = ''; // 清空搜索框

        // 加载所有教师（使用no_page=1避免分页）
        const teachersData = await api('/api/accounts/teachers/?no_page=1');
        // 处理可能的分页响应
        allTeachersForEdit = Array.isArray(teachersData) ? teachersData : (teachersData.results || []);

        // 渲染教师列表
        renderTeacherList(allTeachersForEdit, course.teacher);

        // 修改模态框标题
        const modalTitle = document.querySelector('#editScheduleModal .modal-title');
        if (modalTitle) {
            modalTitle.innerHTML = '<i class="fa-solid fa-edit me-2"></i>编辑课程信息';
        }

        // 显示模态框
        document.getElementById('editScheduleModal').style.display = 'block';
    } catch (e) {
        customAlert(e.message || '加载课程信息失败', '错误', 'error');
    }
}

// 渲染教师列表
function renderTeacherList(teachers, selectedTeacherId = null) {
    const teacherSelect = document.getElementById('editScheduleTeacher');
    teacherSelect.innerHTML = '<option value="">选择教师</option>';

    if (Array.isArray(teachers)) {
        teachers.forEach(t => {
            const option = document.createElement('option');
            option.value = t.id;

            // 获取教师姓名：优先使用 name_display，然后是 user_profile.user.first_name，最后是 teacher_id
            const displayName = t.name_display ||
                t.user_profile?.user?.first_name ||
                t.user_profile?.user?.username ||
                t.teacher_id ||
                '未命名';

            // 获取工号
            const displayId = t.teacher_id || t.user_profile?.user?.username || '';

            // 显示格式：姓名 (工号)
            option.textContent = `${displayName} (${displayId})`;
            option.dataset.name = displayName.toLowerCase();
            option.dataset.id = displayId.toLowerCase();

            if (selectedTeacherId && t.id === selectedTeacherId) {
                option.selected = true;
            }
            teacherSelect.appendChild(option);
        });
    }
}

// 实时筛选教师
function filterTeachersRealtime() {
    const searchText = document.getElementById('editScheduleTeacherSearch').value.trim().toLowerCase();
    const teacherSelect = document.getElementById('editScheduleTeacher');
    const currentSelected = teacherSelect.value;

    if (!searchText) {
        // 如果搜索框为空，显示所有教师
        renderTeacherList(allTeachersForEdit, currentSelected);
        return;
    }

    // 筛选教师：姓名或工号包含搜索文本
    const filteredTeachers = allTeachersForEdit.filter(t => {
        // 获取教师姓名
        const name = (t.name_display ||
            t.user_profile?.user?.first_name ||
            t.user_profile?.user?.username ||
            t.teacher_id || '').toLowerCase();

        // 获取工号
        const id = (t.teacher_id || t.user_profile?.user?.username || '').toLowerCase();

        // 姓名或工号包含搜索文本即匹配
        return name.includes(searchText) || id.includes(searchText);
    });

    renderTeacherList(filteredTeachers, currentSelected);
}

function closeEditSchedule() {
    document.getElementById('editScheduleModal').style.display = 'none';
    currentEditingCourse = null;
    allTeachersForEdit = []; // 清空教师数据
}

async function saveEditSchedule() {
    if (!currentEditingCourse) return;

    const courseName = document.getElementById('editScheduleCourseName').value.trim();
    const teacherId = document.getElementById('editScheduleTeacher').value;
    const classroom = document.getElementById('editScheduleClassroom').value.trim();

    if (!courseName) {
        customAlert('请输入课程名称', '提示', 'warning');
        return;
    }

    try {
        // 更新课程信息（包括教室地址）
        const updateData = {
            name: courseName,
            classroom: classroom
        };

        if (teacherId) {
            updateData.teacher = parseInt(teacherId);
        }

        await api(`/api/courses/courses/${currentEditingCourse.id}/`, 'PATCH', updateData);

        customAlert('保存成功！', '成功', 'success', () => {
            closeEditSchedule();
            loadCourses();
        });
    } catch (e) {
        customAlert(e.message || '保存失败', '错误', 'error');
    }
}

// Week navigation
function prevWeek() {
    if (currentWeek > 1) {
        currentWeek--;
        updateWeekLabel();
        saveFilterState(); // 保存周次状态
        loadSchedule();
    }
}

function nextWeek() {
    if (currentWeek < 20) {
        currentWeek++;
        updateWeekLabel();
        saveFilterState(); // 保存周次状态
        loadSchedule();
    }
}

function updateWeekLabel() {
    const label = document.getElementById('currentWeekLabel');
    if (label) label.textContent = `第${currentWeek}周`;
}

// 显示保存课程安排对话框
function showSaveScheduleModal() {
    if (!currentTargetId || currentViewMode !== 'class') {
        customAlert('请先选择班级', '提示', 'warning');
        return;
    }

    const modal = document.getElementById('saveScheduleModal');
    const weekNumberEl = document.getElementById('saveWeekNumber');
    const syncHintEl = document.getElementById('syncHint');
    const syncCheckbox = document.getElementById('syncToOtherWeeks');

    if (modal && weekNumberEl) {
        weekNumberEl.textContent = currentWeek;

        // 根据当前周次更新提示信息
        if (syncHintEl) {
            if (currentWeek === 1) {
                syncHintEl.textContent = '勾选后将把第1周的课程安排复制到第2-20周';
            } else {
                syncHintEl.textContent = `勾选后将把第${currentWeek}周的课程安排复制到其他周次（会跳过已存在的课程）`;
            }
        }

        // 默认不勾选
        if (syncCheckbox) {
            syncCheckbox.checked = false;
        }

        modal.style.display = 'flex';
    }
}

// 关闭保存课程安排对话框
function closeSaveScheduleModal() {
    const modal = document.getElementById('saveScheduleModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// 确认保存课程安排
async function confirmSaveSchedule() {
    if (!currentTargetId || currentViewMode !== 'class') {
        customAlert('请先选择班级', '提示', 'warning');
        return;
    }

    const syncCheckbox = document.getElementById('syncToOtherWeeks');
    const shouldSync = syncCheckbox ? syncCheckbox.checked : false;

    // 关闭对话框
    closeSaveScheduleModal();

    // 获取当前周的所有课程安排
    try {
        const response = await api(`/api/courses/schedules/?school_class=${currentTargetId}&week_number=${currentWeek}`);
        const schedules = Array.isArray(response) ? response : (response.results || []);

        if (schedules.length === 0) {
            customAlert('当前周没有课程安排需要保存', '提示', 'info');
            return;
        }

        showMessage('scheduleMsg', '正在保存...', 'info');

        // 如果选择同步，复制到其他周
        if (shouldSync) {
            console.log(`📋 [confirmSaveSchedule] 开始同步第${currentWeek}周的课程到其他周...`);
            let successCount = 0;
            let failCount = 0;

            // 确定要同步的周次范围（排除当前周）
            const weeksToCreate = [];
            for (let week = 1; week <= 20; week++) {
                if (week !== currentWeek) {
                    weeksToCreate.push(week);
                }
            }

            // 为每个课程安排复制到其他周
            for (const schedule of schedules) {

                for (const week of weeksToCreate) {
                    const weekPayload = {
                        school_class: schedule.school_class,
                        course: schedule.course,
                        teacher: schedule.teacher,
                        timeslot: typeof schedule.timeslot === 'object' ? schedule.timeslot.id : schedule.timeslot,
                        week_number: week
                    };

                    // 如果有教室信息，也复制
                    if (schedule.classroom) {
                        weekPayload.classroom = schedule.classroom;
                    }
                    if (schedule.classroom_name) {
                        weekPayload.classroom_name = schedule.classroom_name;
                    }

                    try {
                        await api('/api/courses/schedules/', 'POST', weekPayload);
                        successCount++;
                    } catch (e) {
                        // 如果是冲突错误，不算失败（可能已经存在）
                        if (!e.message || (!e.message.includes('冲突') && !e.message.includes('已有课程安排'))) {
                            console.warn(`⚠️ [confirmSaveSchedule] 第${week}周创建失败:`, e.message);
                            failCount++;
                        }
                    }
                }
            }

            console.log(`✅ [confirmSaveSchedule] 同步完成: 成功${successCount}个, 失败${failCount}个`);

            if (failCount > 0) {
                showMessage('scheduleMsg', `同步完成：成功${successCount}个，失败${failCount}个`, 'warning');
                customAlert(`同步完成！\n\n成功同步：${successCount}个课程安排\n失败：${failCount}个`, '同步完成', 'warning');
            } else {
                showMessage('scheduleMsg', `同步完成：已同步${successCount}个课程安排`, 'success');
                customAlert(`同步完成！\n\n已成功同步${successCount}个课程安排到其他周次`, '同步完成', 'success');
            }
        } else {
            showMessage('scheduleMsg', '操作完成', 'success');
            customAlert('当前周的课程安排已保存。', '提示', 'info');
        }

        // 刷新课程表
        await loadSchedule();
    } catch (e) {
        console.error('❌ [confirmSaveSchedule] 保存失败:', e);
        showMessage('scheduleMsg', '保存失败：' + (e.message || '未知错误'), 'error');
        customAlert('保存失败：' + (e.message || '未知错误'), '错误', 'error');
    }
}

// Auto-schedule functionality (保留原有函数，内部调用新函数)
async function autoSchedule() {
    // 如果没有选中课程，提示用户先选择
    const selectedCourseIds = [...tt.selectedCourses];
    if (selectedCourseIds.length === 0) {
        customAlert('请先选择要排课的课程\n\n提示：在课程列表中勾选课程，或使用Ctrl+点击进行多选', '提示', 'warning');
        return;
    }

    // 调用新的自动排课函数
    await autoScheduleSelected();
}

// Conflict detection
async function checkConflicts() {
    if (!currentTargetId) {
        customAlert('请先选择查看对象', '提示', 'warning');
        return;
    }

    const params = new URLSearchParams();
    // 检测所有周的冲突

    if (currentViewMode === 'class') {
        params.append('school_class', currentTargetId);
    } else if (currentViewMode === 'teacher') {
        params.append('teacher', currentTargetId);
    } else if (currentViewMode === 'classroom') {
        params.append('classroom', currentTargetId);
    }

    try {
        const result = await api('/api/courses/schedules/conflicts/?' + params.toString());

        if (result.count === 0) {
            // 显示成功模态框
            showConflictModal([], true);
        } else {
            // 显示冲突详情模态框
            showConflictModal(result.items, false);
            highlightConflicts(result.items);
        }
    } catch (e) {
        customAlert('冲突检测失败：' + (e.message || '未知错误'), '错误', 'error');
    }
}

function showConflictModal(conflicts, isSuccess) {
    const modal = document.getElementById('conflictModal');
    if (!modal) {
        // 如果模态框不存在，使用简单alert
        if (isSuccess) {
            customAlert('未发现任何冲突，课程安排正常！', '✓ 冲突检测完成', 'success');
        } else {
            customAlert(`发现 ${conflicts.length} 处冲突\n\n请查看课表中标红的课程。`, '⚠ 冲突警告', 'warning');
        }
        return;
    }

    const title = document.getElementById('conflictModalTitle');
    const body = document.getElementById('conflictModalBody');
    const optimizeBtn = document.getElementById('optimizeConflictsBtn');

    if (isSuccess) {
        title.textContent = '✓ 检测完成 - 无冲突';
        body.innerHTML = '<div class="alert alert-success mb-0"><i class="fa fa-check-circle me-2"></i>未发现任何冲突，课程安排正常！</div>';
        if (optimizeBtn) optimizeBtn.style.display = 'none';
    } else {
        title.textContent = `⚠ 发现 ${conflicts.length} 处冲突`;

        let html = '<div class="alert alert-warning mb-3">';
        html += '<i class="fa fa-exclamation-triangle me-2"></i>';
        html += `检测到 ${conflicts.length} 处课程安排冲突，详情如下：`;
        html += '</div>';

        html += '<div style="max-height: 400px; overflow-y: auto;">';
        conflicts.forEach((c, index) => {
            const slot = tt.slotById[c.timeslot];
            const weekday = slot ? tt.weekdayNames[slot.weekday] : '未知';
            const time = slot ? `第${slot.index}节 (${slot.start_time}-${slot.end_time})` : '未知时间';

            html += `<div class="card border-danger mb-2">`;
            html += `<div class="card-body p-3">`;
            html += `<h6 class="text-danger mb-2">冲突 #${index + 1}</h6>`;
            html += `<p class="mb-1"><strong>时间：</strong>第${c.week_number}周 ${weekday} ${time}</p>`;
            html += `<p class="mb-1"><strong>冲突类型：</strong>${(c.conflict_types || []).join('、')}</p>`;
            html += `<p class="mb-0"><strong>涉及课程数：</strong>${c.count} 节</p>`;
            html += `</div></div>`;
        });
        html += '</div>';

        body.innerHTML = html;
        if (optimizeBtn) optimizeBtn.style.display = 'inline-block';
    }

    modal.style.display = 'flex';
}

function closeConflictModal() {
    const modal = document.getElementById('conflictModal');
    if (modal) modal.style.display = 'none';

    // 清除冲突高亮
    document.querySelectorAll('.tt-block.conflict').forEach(el => {
        el.classList.remove('conflict');
    });
}

async function optimizeConflicts() {
    if (!currentTargetId || currentViewMode !== 'class') {
        customAlert('只能对班级课表进行自动优化', '提示', 'warning');
        return;
    }

    if (!await customConfirm('自动优化将尝试调整冲突课程到其他可用时间段。\n\n是否继续？', '确认优化')) {
        return;
    }

    try {
        const result = await api('/api/courses/schedules/optimize-conflicts', 'POST', {
            school_class: currentTargetId
        });

        if (result.success) {
            customAlert(`已优化 ${result.optimized} 处冲突`, '✓ 优化成功！', 'success');
            closeConflictModal();
            loadSchedule();
        } else {
            let msg = `成功优化：${result.optimized} 处`;
            if (result.failed && result.failed.length > 0) {
                msg += `\n失败：${result.failed.length} 处`;
            }
            customAlert(msg, '部分优化完成', 'warning');
        }
    } catch (e) {
        customAlert('自动优化失败：' + (e.message || '未知错误'), '错误', 'error');
    }
}

function highlightConflicts(conflicts) {
    // Remove existing conflict highlights
    document.querySelectorAll('.tt-block.conflict').forEach(el => {
        el.classList.remove('conflict');
    });

    // Add conflict class to conflicting blocks
    conflicts.forEach(c => {
        c.schedule_ids.forEach(id => {
            const block = document.querySelector(`.tt-block[data-schedule-id="${id}"]`);
            if (block) block.classList.add('conflict');
        });
    });
}

function showMessage(elementId, message, type = 'info') {
    const el = document.getElementById(elementId);
    if (!el) return;

    el.textContent = message;
    el.className = `mt-2 small text-${type === 'success' ? 'success' : type === 'error' ? 'danger' : 'muted'}`;

    setTimeout(() => {
        el.textContent = '';
        el.className = 'mt-2 small text-muted';
    }, 3000);
}

// Update course
async function updateCourse() {
    customAlert('请先在课程列表中选择要更新的课程', '提示', 'info');
}

// Legacy drag drop handlers
function allowDrop(ev) {
    ev.preventDefault();
}

function drop(ev) {
    ev.preventDefault();
}

// Initialize on load (merged initialization)
// Note: This is called by the first DOMContentLoaded listener at line 350
async function initScheduleAndFilters() {
    // 初始化课程表网格
    await initTimetable();

    // 初始化筛选器（四级级联）
    await initFilters();

    // 设置默认视图模式为按班级
    currentViewMode = 'class';
}
