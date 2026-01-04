// 全局变量
let currentStep = 1;
let selectedCourse = null;
let selectedClass = null;
let allCourses = [];
let studentsData = [];

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', function() {
    loadColleges();
    loadCourses();
});

// 加载学院列表
async function loadColleges() {
    try {
        // 使用全局 api 封装，走会话认证，避免 token 问题
        const data = await api('/api/org/colleges/?no_page=1');
        const colleges = Array.isArray(data) ? data : (data.results || []);
        
        const select = document.getElementById('filterCollege');
        select.innerHTML = '<option value="">全部学院</option>';
        colleges.forEach(college => {
            const option = document.createElement('option');
            option.value = college.id;
            option.textContent = college.name;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('加载学院列表失败:', error);
    }
}

// 学院改变时加载专业
async function onFilterCollegeChange() {
    const collegeId = document.getElementById('filterCollege').value;
    await loadMajors(collegeId);
    loadCourses();
}

// 加载专业列表
async function loadMajors(collegeId = null) {
    try {
        let url = '/api/org/majors/';
        if (collegeId) {
            url += `?college=${collegeId}`;
        }
        
        const data = await api(url + (url.includes('?') ? '&' : '?') + 'no_page=1');
        const majors = Array.isArray(data) ? data : (data.results || []);
        
        const select = document.getElementById('filterMajor');
        select.innerHTML = '<option value="">全部专业</option>';
        majors.forEach(major => {
            const option = document.createElement('option');
            option.value = major.id;
            option.textContent = major.name;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('加载专业列表失败:', error);
    }
}

// 加载课程列表
async function loadCourses() {
    try {
        const collegeId = document.getElementById('filterCollege').value;
        const majorId = document.getElementById('filterMajor').value;
        
        let url = '/api/courses/courses/';
        const params = new URLSearchParams();
        if (majorId) {
            params.append('department', majorId);
        } else if (collegeId) {
            params.append('college', collegeId);
        }
        
        const queryString = params.toString();
        if (queryString) {
            url += '?' + queryString;
        }
        
        const data = await api(url);
        // 处理分页数据
        allCourses = Array.isArray(data) ? data : (data.results || []);
        displayCourses(allCourses);
    } catch (error) {
        console.error('加载课程失败:', error);
        showToast('加载课程失败', 'error');
    }
}

// 显示课程列表
function displayCourses(courses) {
    const tbody = document.getElementById('courseTableBody');
    
    if (!courses || courses.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center text-muted py-5">
                    <i class="fas fa-inbox fa-3x mb-3"></i>
                    <p>暂无课程数据</p>
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = '';
    courses.forEach(course => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${course.subject_id || '-'}</td>
            <td>${course.name || '-'}</td>
            <td>${course.course_type_display || course.course_type || '-'}</td>
            <td>${course.department_name || '-'}</td>
            <td>${course.teacher_name || '-'}</td>
            <td>
                <button class="btn btn-primary btn-sm" onclick='selectCourse(${JSON.stringify(course).replace(/'/g, "&apos;")})'>
                    <i class="fas fa-arrow-right me-1"></i>选择
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

// 筛选课程
function filterCourses() {
    const searchText = document.getElementById('courseSearch').value.toLowerCase();
    
    if (!searchText) {
        displayCourses(allCourses);
        return;
    }
    
    const filtered = allCourses.filter(course => {
        const name = (course.name || '').toLowerCase();
        const code = (course.subject_id || '').toLowerCase();
        return name.includes(searchText) || code.includes(searchText);
    });
    
    displayCourses(filtered);
}

// 选择课程
function selectCourse(course) {
    selectedCourse = course;
    document.getElementById('selectedCourseName').textContent = course.name;
    document.getElementById('selectedCourseCode').textContent = course.subject_id;
    loadCourseClasses(course.id);
    goToStep(2);
}

// 加载课程的授课班级
async function loadCourseClasses(courseId) {
    try {
        const classes = await api(`/api/grades/grades/course_classes/?course_id=${courseId}`);
        displayClasses(classes);
    } catch (error) {
        console.error('加载班级列表失败:', error);
        showToast('加载班级列表失败', 'error');
    }
}

// 显示班级列表
function displayClasses(classes) {
    const container = document.getElementById('classCardsContainer');
    
    if (!classes || classes.length === 0) {
        container.innerHTML = `
            <div class="col-12 text-center text-muted py-5">
                <i class="fas fa-inbox fa-3x mb-3"></i>
                <p>该课程暂无授课班级</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = '';
    classes.forEach(cls => {
        const col = document.createElement('div');
        col.className = 'col-md-4 mb-3';
        col.innerHTML = `
            <div class="card class-card h-100" onclick='selectClass(${JSON.stringify(cls).replace(/'/g, "&apos;")})'>
                <div class="card-body">
                    <h5 class="card-title">${cls.name}</h5>
                    <p class="card-text">
                        <i class="fas fa-building me-2"></i>${cls.college_name}<br>
                        <i class="fas fa-graduation-cap me-2"></i>${cls.major_name}<br>
                        <i class="fas fa-calendar me-2"></i>${cls.enrollment_year}级
                    </p>
                    <button class="btn btn-primary btn-sm w-100">
                        <i class="fas fa-arrow-right me-1"></i>录入成绩
                    </button>
                </div>
            </div>
        `;
        container.appendChild(col);
    });
}

// 选择班级
function selectClass(cls) {
    selectedClass = cls;
    document.getElementById('entryCourseName').textContent = selectedCourse.name;
    document.getElementById('entryClassName').textContent = cls.name;
    loadClassStudents(selectedCourse.id, cls.class_id);
    goToStep(3);
}

// 加载班级学生成绩
async function loadClassStudents(courseId, classId) {
    try {
        studentsData = await api(`/api/grades/grades/class_students_grades/?course_id=${courseId}&class_id=${classId}`);
        document.getElementById('totalStudents').textContent = studentsData.length;
        
        // 如果有学生数据且有成绩，更新占比设置（已在后端锁死为 60/40，这里仅用于展示）
        if (studentsData.length > 0 && studentsData[0].grade_id) {
            document.getElementById('regularWeight').value = studentsData[0].regular_weight;
            document.getElementById('finalWeight').value = studentsData[0].final_weight;
            updateWeights();
        } else {
            updateWeights();
        }
        
        displayStudentsGrades();
    } catch (error) {
        console.error('加载学生列表失败:', error);
        showToast('加载学生列表失败', 'error');
    }
}

// 显示学生成绩录入表格
function displayStudentsGrades(data = studentsData) {
    const tbody = document.getElementById('gradesTableBody');
    
    if (!data || data.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center text-muted py-5">
                    <i class="fas fa-inbox fa-3x mb-3"></i>
                    <p>该班级暂无学生</p>
                </td>
            </tr>
        `;
        return;
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = '';
    data.forEach((student, index) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td class="text-center">${index + 1}</td>
            <td>${student.student_number}</td>
            <td>${student.student_name}</td>
            <td>
                <input type="number" 
                       class="form-control" 
                       id="regular_${student.student_id}" 
                       value="${student.regular_score !== null ? student.regular_score : ''}" 
                       min="0" max="100" step="0.1"
                       placeholder="0-100"
                       onchange="calculateTotal(${student.student_id})"
                       oninput="calculateTotal(${student.student_id})">
            </td>
            <td>
                <input type="number" 
                       class="form-control" 
                       id="final_${student.student_id}" 
                       value="${student.final_score !== null ? student.final_score : ''}" 
                       min="0" max="100" step="0.1"
                       placeholder="0-100"
                       onchange="calculateTotal(${student.student_id})"
                       oninput="calculateTotal(${student.student_id})">
            </td>
            <td>
                <input type="text" 
                       class="form-control bg-light text-center fw-bold" 
                       id="total_${student.student_id}" 
                       value="${student.score !== null ? student.score : ''}" 
                       readonly>
            </td>
        `;
        tbody.appendChild(row);
        
        // 初始计算一次总评
        if (student.regular_score !== null || student.final_score !== null) {
            calculateTotal(student.student_id);
        }
    });
}

// 按学号/姓名过滤当前班级学生（仅前端过滤）
function filterStudentsInTable() {
    const keyword = (document.getElementById('studentFilter').value || '').trim().toLowerCase();
    
    if (!keyword) {
        // 没有关键字，显示全部学生
        displayStudentsGrades(studentsData);
        return;
    }
    
    const filtered = studentsData.filter(student => {
        const number = String(student.student_number || '').toLowerCase();
        const name = String(student.student_name || '').toLowerCase();
        return number.includes(keyword) || name.includes(keyword);
    });
    
    displayStudentsGrades(filtered);
}

// 更新占比设置
function updateWeights() {
    const regularWeight = parseFloat(document.getElementById('regularWeight').value) || 0;
    const finalWeight = parseFloat(document.getElementById('finalWeight').value) || 0;
    const sum = regularWeight + finalWeight;
    
    // 更新徽章显示
    document.getElementById('regularWeightBadge').textContent = regularWeight + '%';
    document.getElementById('finalWeightBadge').textContent = finalWeight + '%';
    
    // 显示警告或成功提示
    const warning = document.getElementById('weightWarning');
    const success = document.getElementById('weightSuccess');
    
    if (sum !== 100) {
        warning.style.display = 'block';
        success.style.display = 'none';
    } else {
        warning.style.display = 'none';
        success.style.display = 'block';
    }
    
    // 重新计算所有学生的总评
    studentsData.forEach(student => {
        calculateTotal(student.student_id);
    });
}

// 实时计算总评
function calculateTotal(studentId) {
    const regularInput = document.getElementById(`regular_${studentId}`);
    const finalInput = document.getElementById(`final_${studentId}`);
    const totalInput = document.getElementById(`total_${studentId}`);
    
    const regularScore = parseFloat(regularInput.value);
    const finalScore = parseFloat(finalInput.value);
    const regularWeight = parseFloat(document.getElementById('regularWeight').value) || 50;
    const finalWeight = parseFloat(document.getElementById('finalWeight').value) || 50;
    
    // 如果两个成绩都有值，计算总评
    if (!isNaN(regularScore) && !isNaN(finalScore)) {
        const total = (regularScore * regularWeight / 100 + finalScore * finalWeight / 100);
        totalInput.value = total.toFixed(2);
        
        // 根据成绩设置颜色
        if (total >= 90) {
            totalInput.className = 'form-control bg-light text-center fw-bold text-success';
        } else if (total >= 60) {
            totalInput.className = 'form-control bg-light text-center fw-bold text-primary';
        } else {
            totalInput.className = 'form-control bg-light text-center fw-bold text-danger';
        }
    } else {
        totalInput.value = '';
        totalInput.className = 'form-control bg-light text-center fw-bold';
    }
}

// 保存所有成绩
async function saveAllGrades() {
    const regularWeight = parseFloat(document.getElementById('regularWeight').value) || 50;
    const finalWeight = parseFloat(document.getElementById('finalWeight').value) || 50;
    
    // 验证占比
    if (regularWeight + finalWeight !== 100) {
        showToast('平时分占比和期末分占比之和必须等于100%', 'error');
        return;
    }
    
    // 收集所有学生的成绩数据
    const grades = [];
    let hasData = false;
    
    studentsData.forEach(student => {
        const regularInput = document.getElementById(`regular_${student.student_id}`);
        const finalInput = document.getElementById(`final_${student.student_id}`);
        
        const regularScore = regularInput.value ? parseFloat(regularInput.value) : null;
        const finalScore = finalInput.value ? parseFloat(finalInput.value) : null;
        
        // 至少有一个成绩才收集
        if (regularScore !== null || finalScore !== null) {
            hasData = true;
            grades.push({
                student_id: student.student_id,
                regular_score: regularScore,
                final_score: finalScore
            });
        }
    });
    
    if (!hasData) {
        showToast('请至少录入一个学生的成绩', 'warning');
        return;
    }
    
    // 显示加载提示
    document.getElementById('loadingOverlay').style.display = 'flex';
    
    try {
        const result = await api('/api/grades/grades/batch_save_grades/', 'POST', {
            course_id: selectedCourse.id,
            class_id: selectedClass.class_id,
            regular_weight: regularWeight,
            final_weight: finalWeight,
            grades: grades
        });
        
        showToast(`成功保存 ${result.saved_count} || 0} 条成绩记录`, 'success');
        
        if (result.errors && result.errors.length > 0) {
            console.error('部分成绩保存失败:', result.errors);
            showToast(`有 ${result.errors.length} 条记录保存失败`, 'warning');
        }
        
        // 重新加载数据
        await loadClassStudents(selectedCourse.id, selectedClass.class_id);
    } catch (error) {
        console.error('保存成绩失败:', error);
        showToast(error.message || '保存成绩失败', 'error');
    } finally {
        document.getElementById('loadingOverlay').style.display = 'none';
    }
}

// 清空所有成绩
function clearAllGrades() {
    if (!confirm('确定要清空所有成绩输入吗？')) {
        return;
    }
    
    studentsData.forEach(student => {
        const regularInput = document.getElementById(`regular_${student.student_id}`);
        const finalInput = document.getElementById(`final_${student.student_id}`);
        const totalInput = document.getElementById(`total_${student.student_id}`);
        
        regularInput.value = '';
        finalInput.value = '';
        totalInput.value = '';
        totalInput.className = 'form-control bg-light text-center fw-bold';
    });
    
    showToast('已清空所有输入', 'info');
}

// 填充示例数据
function fillSampleData() {
    if (!confirm('确定要填充示例数据吗？这将覆盖当前输入。')) {
        return;
    }
    
    studentsData.forEach(student => {
        const regularInput = document.getElementById(`regular_${student.student_id}`);
        const finalInput = document.getElementById(`final_${student.student_id}`);
        
        // 生成随机成绩：60-100
        const randomRegular = (Math.random() * 40 + 60).toFixed(1);
        const randomFinal = (Math.random() * 40 + 60).toFixed(1);
        
        regularInput.value = randomRegular;
        finalInput.value = randomFinal;
        
        calculateTotal(student.student_id);
    });
    
    showToast('已填充示例数据', 'success');
}

// 切换步骤
function goToStep(step) {
    // 隐藏所有步骤
    document.getElementById('step1').style.display = 'none';
    document.getElementById('step2').style.display = 'none';
    document.getElementById('step3').style.display = 'none';
    
    // 显示目标步骤
    document.getElementById(`step${step}`).style.display = 'block';
    currentStep = step;
    
    // 滚动到顶部
    window.scrollTo(0, 0);
}

// 显示提示消息
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed`;
    toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    toast.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

