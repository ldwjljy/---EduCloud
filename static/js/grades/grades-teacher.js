// 教师成绩管理（按课程+班级）前端逻辑

let teacherClasses = [];
let currentTeacherRole = null;
let selectedCourse = null;
let selectedClass = null;
let currentStudents = [];
let autoRefreshTimer = null; // 定时刷新定时器

document.addEventListener('DOMContentLoaded', () => {
    initTeacherGradesPage();
});

// 页面卸载时清除定时器
window.addEventListener('beforeunload', () => {
    if (autoRefreshTimer) {
        clearInterval(autoRefreshTimer);
    }
});

async function initTeacherGradesPage() {
    try {
        const me = await api('/api/accounts/me');
        currentTeacherRole = me.role || null;
        // 允许仍然承担授课任务的管理员角色（校长/副校长/院长/副院长）访问该页面，是否真有授课任务由后端根据课表判断
        const allowedRoles = ['teacher', 'head_teacher', 'super_admin', 'principal', 'vice_principal', 'dean', 'vice_dean'];
        if (!allowedRoles.includes(currentTeacherRole)) {
            showToast('当前页面仅供教师/班主任及仍有授课任务的管理人员使用', 'warning');
            const tbody = document.getElementById('teacherClassTableBody');
            if (tbody) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="8" class="text-center text-muted py-5">
                            <i class="fas fa-ban fa-3x mb-3"></i>
                            <p>只有教师/班主任可以查看授课班级成绩</p>
                        </td>
                    </tr>
                `;
            }
            return;
        }
        await loadTeacherClasses();
        
        // 启动定时自动刷新（每30秒刷新一次班级列表，更新及格率）
        startAutoRefresh();
    } catch (e) {
        console.error('初始化教师成绩页面失败:', e);
        showToast(e.message || '加载失败，请刷新重试', 'error');
    }
}

// 启动定时自动刷新
function startAutoRefresh() {
    // 清除之前的定时器
    if (autoRefreshTimer) {
        clearInterval(autoRefreshTimer);
    }
    
    // 每30秒自动刷新一次班级列表（更新及格率）
    autoRefreshTimer = setInterval(async () => {
        // 静默刷新，不显示加载提示
        try {
            const oldSelectedKey = currentSelectedClassKey;
            teacherClasses = await api('/api/grades/grades/teacher_classes/');
            if (teacherClasses && teacherClasses.length > 0) {
                renderTeacherClassTable();
                
                // 如果之前有选中的班级，刷新后自动重新选中
                if (oldSelectedKey) {
                    const index = teacherClasses.findIndex(item => 
                        `${item.course_id}_${item.class_id}` === oldSelectedKey
                    );
                    if (index >= 0) {
                        // 只更新数据，不重新加载学生列表（避免干扰用户操作）
                        const item = teacherClasses[index];
                        if (selectedCourse && selectedClass && 
                            selectedCourse.id === item.course_id && 
                            selectedClass.class_id === item.class_id) {
                            // 更新当前班级的学生人数（如果有变化）
                            document.getElementById('currentClassStudentCount').textContent = item.student_count || 0;
                        }
                    }
                }
            }
        } catch (e) {
            console.error('自动刷新班级列表失败:', e);
            // 静默失败，不显示错误提示
        }
    }, 30000); // 30秒刷新一次
}

// 停止定时自动刷新
function stopAutoRefresh() {
    if (autoRefreshTimer) {
        clearInterval(autoRefreshTimer);
        autoRefreshTimer = null;
    }
}

// 保存当前选中的班级信息，用于刷新后恢复选中状态
let currentSelectedClassKey = null;

// 加载教师授课班级列表（课程+班级维度）
async function loadTeacherClasses() {
    const tbody = document.getElementById('teacherClassTableBody');
    if (tbody) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center text-muted py-5">
                    <i class="fas fa-spinner fa-spin fa-3x mb-3"></i>
                    <p>正在加载您授课的班级...</p>
                </td>
            </tr>
        `;
    }

    try {
        // 保存当前选中的班级标识（用于刷新后恢复）
        if (selectedCourse && selectedClass) {
            currentSelectedClassKey = `${selectedCourse.id}_${selectedClass.class_id}`;
        }

        // 使用后端新的 teacher_classes 汇总接口
        teacherClasses = await api('/api/grades/grades/teacher_classes/');

        if (!teacherClasses || teacherClasses.length === 0) {
            if (tbody) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="8" class="text-center text-muted py-5">
                            <i class="fas fa-inbox fa-3x mb-3"></i>
                            <p>当前没有您的授课班级或尚未有成绩记录</p>
                        </td>
                    </tr>
                `;
            }
            return;
        }

        renderTeacherClassTable();

        // 如果之前有选中的班级，刷新后自动重新选中
        if (currentSelectedClassKey) {
            const index = teacherClasses.findIndex(item => 
                `${item.course_id}_${item.class_id}` === currentSelectedClassKey
            );
            if (index >= 0) {
                // 延迟一下，确保表格已渲染完成
                setTimeout(() => {
                    selectTeacherClass(index);
                }, 100);
            }
        }
    } catch (e) {
        console.error('加载教师授课班级失败:', e);
        if (tbody) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" class="text-center text-danger py-5">
                        <i class="fas fa-exclamation-triangle fa-3x mb-3"></i>
                        <p>${e.message || '加载失败，请稍后重试'}</p>
                    </td>
                </tr>
            `;
        }
        showToast(e.message || '加载授课班级失败', 'error');
    }
}

// 手动刷新班级列表（公开函数，供按钮调用）
async function refreshTeacherClasses() {
    await loadTeacherClasses();
    showToast('班级列表已刷新，及格率已更新', 'success');
}

function renderTeacherClassTable() {
    const tbody = document.getElementById('teacherClassTableBody');
    if (!tbody) return;

    tbody.innerHTML = '';
    teacherClasses.forEach((item, index) => {
        const tr = document.createElement('tr');
        const avgScore = (item.avg_score != null) ? Number(item.avg_score).toFixed(2) : '-';
        const passRate = (item.pass_rate != null) ? Number(item.pass_rate).toFixed(2) + '%' : '-';

        tr.innerHTML = `
            <td>${item.course_name || '-'}</td>
            <td>${item.class_name || '-'}</td>
            <td>${item.student_count || 0}</td>
            <td><strong>${avgScore}</strong></td>
            <td>
                <span class="badge bg-${item.pass_rate >= 60 ? 'success' : 'danger'}">
                    ${passRate}
                </span>
            </td>
            <td class="text-center">
                <button class="btn btn-sm btn-outline-primary" onclick="selectTeacherClass(${index})">
                    <i class="fas fa-arrow-right me-1"></i>进入
                </button>
            </td>
        `;

        tbody.appendChild(tr);
    });
}

// 选择某个课程+班级，加载学生成绩
async function selectTeacherClass(index) {
    const item = teacherClasses[index];
    if (!item) return;

    selectedCourse = {
        id: item.course_id,
        name: item.course_name,
    };
    selectedClass = {
        class_id: item.class_id,
        name: item.class_name,
    };

    // 更新顶部信息
    document.getElementById('currentCourseName').textContent = selectedCourse.name || '-';
    document.getElementById('currentClassName').textContent = selectedClass.name || '-';
    document.getElementById('currentClassStudentCount').textContent = item.student_count || 0;

    // 启用导出/保存按钮
    document.getElementById('btnExportTemplate').disabled = false;
    document.getElementById('btnSaveAll').disabled = false;

    await loadStudentsForCurrentClass();
}

// 加载当前课程+班级的学生成绩
async function loadStudentsForCurrentClass() {
    if (!selectedCourse || !selectedClass) return;
    const tbody = document.getElementById('teacherStudentTableBody');
    if (tbody) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center text-muted py-5">
                    <i class="fas fa-spinner fa-spin fa-3x mb-3"></i>
                    <p>正在加载学生成绩...</p>
                </td>
            </tr>
        `;
    }

    try {
        const url = `/api/grades/grades/class_students_grades/?course_id=${selectedCourse.id}&class_id=${encodeURIComponent(selectedClass.class_id)}`;
        currentStudents = await api(url);
        renderStudentTable();
    } catch (e) {
        console.error('加载学生成绩失败:', e);
        if (tbody) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" class="text-center text-danger py-5">
                        <i class="fas fa-exclamation-triangle fa-3x mb-3"></i>
                        <p>${e.message || '加载失败，请稍后重试'}</p>
                    </td>
                </tr>
            `;
        }
        showToast(e.message || '加载学生成绩失败', 'error');
    }
}

function renderStudentTable() {
    const tbody = document.getElementById('teacherStudentTableBody');
    if (!tbody) return;

    if (!currentStudents || currentStudents.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center text-muted py-5">
                    <i class="fas fa-inbox fa-3x mb-3"></i>
                    <p>该班级暂无学生</p>
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = '';
    currentStudents.forEach((stu, idx) => {
        const tr = document.createElement('tr');
        const total = stu.score != null ? Number(stu.score) : null;
        const statusPassed = (total != null && total >= 60);
        const totalText = total != null ? total.toFixed(2) : '';

        const regularVal = (stu.regular_score != null) ? stu.regular_score : '';
        const finalVal = (stu.final_score != null) ? stu.final_score : '';

        tr.innerHTML = `
            <td class="text-center fw-bold">${idx + 1}</td>
            <td class="fw-semibold">${stu.student_number || '-'}</td>
            <td class="fw-semibold">${stu.student_name || '-'}</td>
            <td>
                <input type="number"
                       class="form-control form-control-sm text-center"
                       id="regular_${stu.student_id}"
                       value="${regularVal}"
                       min="0" max="100" step="0.1"
                       placeholder="0-100"
                       oninput="recalculateStudentTotal(${stu.student_id})"
                       style="max-width: 110px;">
            </td>
            <td>
                <input type="number"
                       class="form-control form-control-sm text-center"
                       id="final_${stu.student_id}"
                       value="${finalVal}"
                       min="0" max="100" step="0.1"
                       placeholder="0-100"
                       oninput="recalculateStudentTotal(${stu.student_id})"
                       style="max-width: 110px;">
            </td>
            <td>
                <input type="text"
                       class="form-control form-control-sm text-center fw-bold ${statusPassed ? 'text-success' : (total != null ? 'text-danger' : '')}"
                       id="total_${stu.student_id}"
                       value="${totalText}"
                       readonly
                       style="max-width: 110px;">
            </td>
            <td class="text-center">
                <span id="status_${stu.student_id}" class="badge ${statusPassed ? 'bg-success' : (total != null ? 'bg-danger' : 'bg-secondary')}">
                    ${total == null ? '未录入' : (statusPassed ? '及格' : '不及格')}
                </span>
            </td>
        `;

        tbody.appendChild(tr);
    });
}

// 重新计算某个学生的总分和状态（前端实时展示，后端保存时会再次按 60/40 计算）
function recalculateStudentTotal(studentInternalId) {
    const regularInput = document.getElementById(`regular_${studentInternalId}`);
    const finalInput = document.getElementById(`final_${studentInternalId}`);
    const totalInput = document.getElementById(`total_${studentInternalId}`);
    const statusSpan = document.getElementById(`status_${studentInternalId}`);
    if (!regularInput || !finalInput || !totalInput || !statusSpan) return;

    const regular = parseFloat(regularInput.value);
    const finalScore = parseFloat(finalInput.value);

    if (!isNaN(regular) && !isNaN(finalScore)) {
        const total = regular * 0.6 + finalScore * 0.4;
        totalInput.value = total.toFixed(2);
        if (total >= 60) {
            totalInput.className = 'form-control form-control-sm text-center fw-bold text-success';
            statusSpan.className = 'badge bg-success';
            statusSpan.textContent = '及格';
        } else {
            totalInput.className = 'form-control form-control-sm text-center fw-bold text-danger';
            statusSpan.className = 'badge bg-danger';
            statusSpan.textContent = '不及格';
        }
    } else {
        totalInput.value = '';
        totalInput.className = 'form-control form-control-sm text-center fw-bold';
        statusSpan.className = 'badge bg-secondary';
        statusSpan.textContent = '未录入';
    }
}

// 保存当前班级所有学生成绩
async function saveAllGradesForCurrentClass() {
    if (!selectedCourse || !selectedClass) {
        showToast('请先选择上方的一个班级', 'warning');
        return;
    }
    if (!currentStudents || currentStudents.length === 0) {
        showToast('当前班级没有学生，无需保存', 'info');
        return;
    }

    const grades = [];
    let hasData = false;
    
    currentStudents.forEach(stu => {
        const regularInput = document.getElementById(`regular_${stu.student_id}`);
        const finalInput = document.getElementById(`final_${stu.student_id}`);
        if (!regularInput || !finalInput) return;

        const regularVal = regularInput.value.trim();
        const finalVal = finalInput.value.trim();

        const regular = regularVal === '' ? null : parseFloat(regularVal);
        const finalScore = finalVal === '' ? null : parseFloat(finalVal);

        if (regular !== null || finalScore !== null) {
            hasData = true;
            grades.push({
                student_id: stu.student_id,
                regular_score: regular,
                final_score: finalScore,
            });
        }
    });

    if (!hasData) {
        showToast('请至少录入一个学生的成绩', 'warning');
        return;
    }

    setTeacherGradesLoading(true);
    try {
        const requestData = {
            course_id: selectedCourse.id,
            class_id: selectedClass.class_id,
            regular_weight: 60,
            final_weight: 40,
            grades: grades,
        };
        
        const result = await api('/api/grades/grades/batch_save_grades/', 'POST', requestData);

        showToast(`成功保存 ${result.saved_count || 0} 条成绩记录`, 'success');
        if (result.errors && result.errors.length > 0) {
            console.error('部分成绩保存失败:', result.errors);
            showToast(`有 ${result.errors.length} 条记录保存失败`, 'warning');
        }
        // 刷新班级列表以更新及格率
        await loadTeacherClasses();
        // 刷新当前班级的学生成绩
        await loadStudentsForCurrentClass();
    } catch (e) {
        console.error('保存成绩失败:', e);
        showToast(e.message || '保存成绩失败', 'error');
    } finally {
        setTeacherGradesLoading(false);
    }
}

// 导出当前班级的成绩表模板（含现有数据）
// 确保函数在全局作用域中可访问
window.exportClassGradesTemplate = async function exportClassGradesTemplate() {
    if (!selectedCourse || !selectedClass) {
        showToast('请先选择上方的一个班级', 'warning');
        return;
    }
    
    console.log('开始导出，课程ID:', selectedCourse.id, '班级ID:', selectedClass.class_id);
    
    // 显示加载提示
    showToast('正在准备下载...', 'info');
    
    try {
        // 使用完整URL，避免相对路径在iframe等场景下解析错误
        const baseUrl = window.location.origin;
        const exportUrl = `${baseUrl}/api/grades/grades/class_grades_export/?course_id=${selectedCourse.id}&class_id=${encodeURIComponent(selectedClass.class_id)}`;
        
        console.log('导出URL:', exportUrl);
        
        // 使用 fetch 获取文件，这样可以更好地处理错误
        const response = await fetch(exportUrl, {
            method: 'GET',
            credentials: 'include',
            headers: {
                'X-CSRFToken': csrfToken() || ''
            }
        });
        
        console.log('响应状态:', response.status, response.statusText);
        console.log('响应头 Content-Type:', response.headers.get('content-type'));
        
        // 检查响应是否成功
        if (!response.ok) {
            // 尝试读取错误信息
            let errorMessage = '导出失败';
            try {
                const errorText = await response.text();
                console.error('错误响应:', errorText);
                try {
                    const errorObj = JSON.parse(errorText);
                    errorMessage = errorObj.error || errorObj.message || errorMessage;
                } catch (e) {
                    errorMessage = errorText || `导出失败: ${response.status} ${response.statusText}`;
                }
            } catch (e) {
                errorMessage = `导出失败: ${response.status} ${response.statusText}`;
            }
            throw new Error(errorMessage);
        }
        
        // 检查响应类型
        const contentType = response.headers.get('content-type') || '';
        if (!contentType.includes('spreadsheetml') && !contentType.includes('excel') && !contentType.includes('octet-stream')) {
            // 可能返回了错误信息
            const errorText = await response.text();
            console.error('非Excel响应:', errorText);
            let errorMessage = '服务器返回的不是Excel文件';
            try {
                const errorObj = JSON.parse(errorText);
                errorMessage = errorObj.error || errorObj.message || errorMessage;
            } catch (e) {
                errorMessage = errorText || errorMessage;
            }
            throw new Error(errorMessage);
        }
        
        // 获取文件数据
        const blob = await response.blob();
        console.log('Blob大小:', blob.size, 'bytes');
        
        if (blob.size === 0) {
            throw new Error('导出的文件为空，请检查数据');
        }
        
        // 创建下载链接
        const downloadUrl = URL.createObjectURL(blob);
        const link = document.createElement('a');
        const filename = `${selectedClass.name || selectedClass.class_id}_${selectedCourse.name || '课程'}_成绩表.xlsx`;
        link.href = downloadUrl;
        link.download = filename;
        link.style.display = 'none';
        
        // 添加到DOM并触发下载
        document.body.appendChild(link);
        link.click();
        
        // 清理
        setTimeout(() => {
            document.body.removeChild(link);
            URL.revokeObjectURL(downloadUrl);
        }, 100);
        
        showToast('成绩表下载成功', 'success');
        
    } catch (e) {
        console.error('导出成绩表失败:', e);
        const errorMsg = e.message || '导出成绩表失败，请检查网络连接或联系管理员';
        showToast(errorMsg, 'error');
        
        // 如果是权限问题，给出更明确的提示
        if (errorMsg.includes('403') || errorMsg.includes('权限') || errorMsg.includes('联系组织')) {
            showToast('您没有权限执行此操作，请联系管理员', 'error');
        }
    }
};

// 处理导入文件选择
function handleImportFileChange(event) {
    const file = event.target.files && event.target.files[0];
    if (!file) return;
    if (!selectedCourse || !selectedClass) {
        showToast('请先选择上方的一个班级，再导入成绩', 'warning');
        event.target.value = '';
        return;
    }

    importClassGradesFromExcel(file).finally(() => {
        event.target.value = '';
    });
}

// 调用后端导入接口（Excel 文件）
async function importClassGradesFromExcel(file) {
    if (!selectedCourse || !selectedClass) return;

    const formData = new FormData();
    formData.append('file', file);
    formData.append('course_id', selectedCourse.id);
    formData.append('class_id', selectedClass.class_id);

    setTeacherGradesLoading(true);
    try {
        const result = await api('/api/grades/grades/class_grades_import/', 'POST', formData);
        showToast(`导入成功 ${result.saved_count || 0} 条记录`, 'success');
        if (result.errors && result.errors.length > 0) {
            console.warn('部分记录导入失败:', result.errors);
            showToast(`有 ${result.errors.length} 条记录导入失败，请查看控制台详情`, 'warning');
        }
        // 刷新班级列表以更新及格率
        await loadTeacherClasses();
        // 刷新当前班级的学生成绩
        await loadStudentsForCurrentClass();
    } catch (e) {
        console.error('导入成绩失败:', e);
        showToast(e.message || '导入成绩失败', 'error');
    } finally {
        setTeacherGradesLoading(false);
    }
}

function setTeacherGradesLoading(isLoading) {
    const overlay = document.getElementById('teacherGradesLoadingOverlay');
    if (!overlay) return;
    overlay.style.display = isLoading ? 'flex' : 'none';
}

// 简单 Toast（如果全局 app.js 已有 showToast，可以复用；此处兜底实现）
function showToast(message, type = 'info') {
    if (window.showToast && showToast !== window.showToast) {
        window.showToast(message, type);
        return;
    }
    const toast = document.createElement('div');
    toast.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed`;
    toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    toast.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

