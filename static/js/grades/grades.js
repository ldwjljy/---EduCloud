// 全局变量
let currentUser = null;
let currentRole = null;
let allGrades = [];
let currentPage = 1;
let pageSize = 30;
let gradeModal = null;
let batchAddModal = null;
let statisticsModal = null;
let classGradesModal = null;
let currentView = 'class'; // 'class' 或 'course'
let studentSearchTimeout = null;

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', function() {
    initModals();
    loadCurrentUser();
    
    // 全局错误处理：忽略第三方脚本错误（不影响功能）
    window.addEventListener('error', function(e) {
        // 忽略第三方监控脚本的错误
        if (e.filename && (
            e.filename.includes('aegis') || 
            e.filename.includes('rumt-zh.com') ||
            e.filename.includes('mcs.zijieapi.com') ||
            e.filename.includes('chrome-error://') ||
            e.filename.includes('main.7ee886d8.js') ||
            e.filename.includes('hybridaction') ||
            e.filename.includes('zybTracker')
        )) {
            e.preventDefault();
            return true;
        }
    }, true);
    
    // 忽略未捕获的Promise错误（来自扩展）
    window.addEventListener('unhandledrejection', function(e) {
        const reason = e.reason;
        if (reason && (
            (reason.message && (
                reason.message.includes('message channel closed') ||
                reason.message.includes('ERR_BLOCKED_BY_RESPONSE') ||
                reason.message.includes('ERR_CONNECTION_CLOSED')
            )) ||
            (reason.toString && reason.toString().includes('ERR_CONNECTION_CLOSED'))
        )) {
            e.preventDefault();
        }
    });
});

// 初始化分页按钮事件监听（使用事件委托，更可靠）
function initPageButtons() {
    // 使用事件委托，确保按钮点击可以正常工作
    document.body.addEventListener('click', function(e) {
        const target = e.target;
        const prevBtn = target.closest('#prevPageBtn');
        const nextBtn = target.closest('#nextPageBtn');
        
        if (prevBtn && !prevBtn.disabled) {
            e.preventDefault();
            e.stopPropagation();
            previousPage();
            return false;
        }
        
        if (nextBtn && !nextBtn.disabled) {
            e.preventDefault();
            e.stopPropagation();
            nextPage();
            return false;
        }
    }, true);
}

// 初始化模态框
function initModals() {
    const modalElements = {
        gradeModal: document.getElementById('gradeModal'),
        batchAddModal: document.getElementById('batchAddModal'),
        statisticsModal: document.getElementById('statisticsModal'),
        classGradesModal: document.getElementById('classGradesModal')
    };
    
    if (modalElements.gradeModal) {
        gradeModal = new bootstrap.Modal(modalElements.gradeModal);
    }
    if (modalElements.batchAddModal) {
        batchAddModal = new bootstrap.Modal(modalElements.batchAddModal);
    }
    if (modalElements.statisticsModal) {
        statisticsModal = new bootstrap.Modal(modalElements.statisticsModal);
    }
    if (modalElements.classGradesModal) {
        classGradesModal = new bootstrap.Modal(modalElements.classGradesModal);
    }
}

// 获取当前用户信息
async function loadCurrentUser() {
    try {
        const response = await fetch('/api/accounts/me', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });
        
        if (response.ok) {
            currentUser = await response.json();
            // 后端 /api/accounts/me 返回的角色字段在顶层：{ username, role, ... }
            // 之前错误地从 profile.role 读取，导致管理员（校长等）currentRole 为空，前端判断权限出错
            currentRole = currentUser.role || null;
            initializePageByRole();
        }
    } catch (error) {
        console.error('获取用户信息失败:', error);
        showToast('获取用户信息失败', 'error');
    }
}

// 根据角色初始化页面
function initializePageByRole() {
    // 根据角色显示/隐藏不同的元素
    const isAdmin = ['super_admin', 'principal', 'vice_principal', 'dean', 'vice_dean'].includes(currentRole);
    const isTeacher = ['teacher', 'head_teacher'].includes(currentRole);
    const isStudent = currentRole === 'student';
    const isHeadTeacher = currentRole === 'head_teacher';
    
    // 显示/隐藏统计部分
    if (isAdmin) {
        document.getElementById('statisticsSection').style.display = 'block';
        document.getElementById('viewStatisticsBtn').style.display = 'block';
    }
    
    // 显示/隐藏筛选条件 - 所有用户都可以使用组织层级筛选
    document.getElementById('collegeFilterDiv').style.display = 'block';
    document.getElementById('majorFilterDiv').style.display = 'block';
    document.getElementById('classFilterDiv').style.display = 'block';
    
    // 显示/隐藏操作按钮
    if (isTeacher || isAdmin) {
        document.getElementById('actionButtons').style.display = 'block';
        document.getElementById('actionHeader').style.display = 'table-cell';
    }
    
    // 学生隐藏某些筛选
    if (isStudent) {
        document.getElementById('studentSearchDiv').style.display = 'none';
    }
    
    // 加载基础数据
    loadColleges();
    loadMajors();
    loadClasses();
    loadCourses();
    loadStudents();
    
    // 加载成绩数据
    loadGrades();
    
    // 显示视图切换按钮（已移除对应按钮，保留兼容代码）
    const viewToggleDiv = document.getElementById('viewToggleDiv');
    if (viewToggleDiv) {
        viewToggleDiv.style.display = 'block';
    }
    
    // 如果是管理员，加载统计数据
    if (isAdmin) {
        loadDashboardStatistics();
    }
}

// 加载学院列表
async function loadColleges() {
    try {
        const response = await fetch('/api/org/colleges/', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });
        
        if (response.ok) {
            let data = await response.json();
            // 处理分页数据
            const colleges = Array.isArray(data) ? data : (data.results || []);
            
            const selects = ['collegeFilter', 'statsCollege'];
            
            selects.forEach(selectId => {
                const select = document.getElementById(selectId);
                if (select) {
                    select.innerHTML = '<option value="">全部学院</option>';
                    colleges.forEach(college => {
                        const option = document.createElement('option');
                        option.value = college.id;
                        option.textContent = college.name;
                        select.appendChild(option);
                    });
                }
            });
        }
    } catch (error) {
        console.error('加载学院列表失败:', error);
    }
}

// 学院改变时加载专业
async function onCollegeChange() {
    const collegeId = document.getElementById('collegeFilter').value;
    
    // 清空专业、班级、课程选择
    document.getElementById('majorFilter').innerHTML = '<option value="">全部专业</option>';
    document.getElementById('classFilter').innerHTML = '<option value="">全部班级</option>';
    
    // 加载该学院的专业
    await loadMajors(collegeId);
    
    // 如果按课程视图，同时加载该学院的课程
    if (currentView === 'course') {
        await loadCoursesByCollege(collegeId);
    }
    
    loadGrades();
}

// 加载专业列表
async function loadMajors(collegeId = null) {
    try {
        let url = '/api/org/majors/';
        if (collegeId) {
            url += `?college=${collegeId}`;
        }
        
        const response = await fetch(url, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });
        
        if (response.ok) {
            let data = await response.json();
            // 处理分页数据
            const majors = Array.isArray(data) ? data : (data.results || []);
            
            const selects = ['majorFilter', 'statsMajor'];
            
            selects.forEach(selectId => {
                const select = document.getElementById(selectId);
                if (select) {
                    select.innerHTML = '<option value="">全部专业</option>';
                    majors.forEach(major => {
                        const option = document.createElement('option');
                        option.value = major.id;
                        option.textContent = major.name;
                        select.appendChild(option);
                    });
                }
            });
        }
    } catch (error) {
        console.error('加载专业列表失败:', error);
    }
}

// 专业改变时加载班级
async function onMajorChange() {
    const majorId = document.getElementById('majorFilter').value;
    
    // 清空班级选择
    document.getElementById('classFilter').innerHTML = '<option value="">全部班级</option>';
    
    // 加载该专业的班级
    await loadClasses(majorId);
    
    // 如果按课程视图，同时加载该专业的课程
    if (currentView === 'course') {
        await loadCoursesByMajor(majorId);
    }
    
    loadGrades();
}

// 加载班级列表
async function loadClasses(majorId = null) {
    try {
        let url = '/api/org/classes/';
        if (majorId) {
            url += `?major=${majorId}`;
        }
        
        const response = await fetch(url, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });
        
        if (response.ok) {
            let data = await response.json();
            // 处理分页数据
            const classes = Array.isArray(data) ? data : (data.results || []);
            
            const select = document.getElementById('classFilter');
            if (select) {
                select.innerHTML = '<option value="">全部班级</option>';
                classes.forEach(cls => {
                    const option = document.createElement('option');
                    option.value = cls.class_id;
                    option.textContent = cls.name;
                    select.appendChild(option);
                });
            }
        }
    } catch (error) {
        console.error('加载班级列表失败:', error);
    }
}

// 加载课程列表
async function loadCourses() {
    try {
        const response = await fetch('/api/courses/courses/', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });
        
        if (response.ok) {
            let data = await response.json();
            // 处理分页数据
            const courses = Array.isArray(data) ? data : (data.results || []);
            
            const selects = ['courseFilter', 'gradeCourse', 'classGradeCourseFilter'];
            
            selects.forEach(selectId => {
                const select = document.getElementById(selectId);
                if (select) {
                    const isFilter = selectId.includes('Filter');
                    select.innerHTML = isFilter ? '<option value="">全部课程</option>' : '<option value="">请选择课程</option>';
                    
                    courses.forEach(course => {
                        const option = document.createElement('option');
                        option.value = course.id;
                        option.textContent = `${course.name} (${course.subject_id})`;
                        select.appendChild(option);
                    });
                }
            });
        }
    } catch (error) {
        console.error('加载课程列表失败:', error);
    }
}

// 按学院加载课程
async function loadCoursesByCollege(collegeId) {
    try {
        let url = '/api/courses/courses/';
        if (collegeId) {
            url += `?college=${collegeId}`;
        }
        
        const response = await fetch(url, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });
        
        if (response.ok) {
            let data = await response.json();
            const courses = Array.isArray(data) ? data : (data.results || []);
            
            const select = document.getElementById('courseFilter');
            if (select) {
                select.innerHTML = '<option value="">全部课程</option>';
                courses.forEach(course => {
                    const option = document.createElement('option');
                    option.value = course.id;
                    option.textContent = `${course.name} (${course.subject_id})`;
                    select.appendChild(option);
                });
            }
        }
    } catch (error) {
        console.error('按学院加载课程失败:', error);
    }
}

// 按专业加载课程
async function loadCoursesByMajor(majorId) {
    try {
        let url = '/api/courses/courses/';
        if (majorId) {
            url += `?department=${majorId}`;
        }
        
        const response = await fetch(url, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });
        
        if (response.ok) {
            let data = await response.json();
            const courses = Array.isArray(data) ? data : (data.results || []);
            
            const select = document.getElementById('courseFilter');
            if (select) {
                select.innerHTML = '<option value="">全部课程</option>';
                courses.forEach(course => {
                    const option = document.createElement('option');
                    option.value = course.id;
                    option.textContent = `${course.name} (${course.subject_id})`;
                    select.appendChild(option);
                });
            }
        }
    } catch (error) {
        console.error('按专业加载课程失败:', error);
    }
}

// 加载学生列表
async function loadStudents() {
    try {
        const response = await fetch('/api/accounts/students/', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });
        
        if (response.ok) {
            let data = await response.json();
            // 处理分页数据
            const students = Array.isArray(data) ? data : (data.results || []);
            
            const select = document.getElementById('gradeStudent');
            if (select) {
                select.innerHTML = '<option value="">请选择学生</option>';
                students.forEach(student => {
                    const option = document.createElement('option');
                    option.value = student.id;
                    // 使用 student 对象中的 name 或 user_profile 信息
                    const name = student.name || (student.user_profile && student.user_profile.user && (student.user_profile.user.first_name || student.user_profile.user.username)) || student.student_id;
                    option.textContent = `${name} (${student.student_id})`;
                    select.appendChild(option);
                });
            }
        }
    } catch (error) {
        console.error('加载学生列表失败:', error);
    }
}

// 加载成绩数据
async function loadGrades() {
    try {
        
        let url = '/api/grades/grades/';
        const params = new URLSearchParams();
        
        // 添加筛选参数
        const collegeId = document.getElementById('collegeFilter')?.value;
        const majorId = document.getElementById('majorFilter')?.value;
        const classId = document.getElementById('classFilter')?.value;
        const courseId = document.getElementById('courseFilter')?.value;
        const studentSearch = document.getElementById('studentSearch')?.value;
        const passedFilter = document.getElementById('passedFilter')?.value;
        
        if (collegeId) params.append('college_id', collegeId);
        if (majorId) params.append('major_id', majorId);
        if (classId) params.append('class_id', classId);
        if (courseId) params.append('course_id', courseId);
        if (studentSearch) params.append('student_name', studentSearch);
        
        // 成绩状态过滤
        if (passedFilter === 'excellent') {
            // 优秀：≥90分（前端过滤）
        } else if (passedFilter === 'passed') {
            // 及格：60-89分
            params.append('is_passed', 'true');
        } else if (passedFilter === 'failed') {
            // 不及格：<60分
            params.append('is_passed', 'false');
        }
        
        
        const queryString = params.toString();
        if (queryString) {
            url += '?' + queryString;
        }
        
        const response = await fetch(url, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });
        
        if (response.ok) {
            let data = await response.json();
            // 处理分页数据
            let grades = Array.isArray(data) ? data : (data.results || []);
            
            // 前端额外过滤：优秀（≥90分）和及格但不优秀（60-89分）
            const passedFilter = document.getElementById('passedFilter')?.value;
            if (passedFilter === 'excellent') {
                grades = grades.filter(g => g.score >= 90);
            } else if (passedFilter === 'passed') {
                grades = grades.filter(g => g.score >= 60 && g.score < 90);
            }
            
            allGrades = grades;
            displayGrades();
        } else {
            showToast('加载成绩失败', 'error');
        }
    } catch (error) {
        console.error('加载成绩失败:', error);
        showToast('加载成绩失败', 'error');
    }
}

// 显示成绩列表
function displayGrades() {
    const tbody = document.getElementById('gradeTableBody');
    const totalCount = document.getElementById('totalCount');
    
    if (!allGrades || allGrades.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="9" class="text-center text-muted py-5">
                    <i class="fas fa-inbox fa-3x mb-3"></i>
                    <p>暂无数据</p>
                </td>
            </tr>
        `;
        if (totalCount) {
            totalCount.textContent = '0';
        }
        // 更新总数显示
        const pageTotal = document.getElementById('pageTotal');
        if (pageTotal) {
            pageTotal.textContent = '0';
        }
        return;
    }
    
    totalCount.textContent = allGrades.length;
    
    // 直接显示所有数据，不分页
    tbody.innerHTML = '';
    allGrades.forEach(grade => {
        const row = document.createElement('tr');
        
        const isPassed = grade.score >= 60;
        const statusBadge = isPassed 
            ? '<span class="badge bg-success">及格</span>' 
            : '<span class="badge bg-danger">不及格</span>';
        
        let actionButtons = '';
        if (['teacher', 'head_teacher', 'super_admin', 'principal', 'vice_principal', 'dean', 'vice_dean'].includes(currentRole)) {
            actionButtons = `
                <td class="text-center">
                    <button class="btn btn-sm btn-outline-primary me-1" onclick="editGrade(${grade.id})" title="编辑">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteGrade(${grade.id})" title="删除">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            `;
        }
        
        row.innerHTML = `
            <td>${grade.student_id || '-'}</td>
            <td>${grade.student_name || grade.student_username || '-'}</td>
            <td>${grade.class_name || '-'}</td>
            <td>${grade.course_name || '-'}</td>
            <td>${grade.course_type || '-'}</td>
            <td><strong class="${isPassed ? 'text-success' : 'text-danger'}">${grade.score}</strong></td>
            <td>${statusBadge}</td>
            ${actionButtons}
        `;
        
        tbody.appendChild(row);
    });
    
    // 更新总数显示
    const pageTotal = document.getElementById('pageTotal');
    if (pageTotal) {
        pageTotal.textContent = allGrades.length;
    }
}

// 更新分页
function updatePagination(total) {
    const totalPages = Math.ceil(total / pageSize);
    const pagination = document.getElementById('pagination');
    const pageStart = document.getElementById('pageStart');
    const pageEnd = document.getElementById('pageEnd');
    const pageTotal = document.getElementById('pageTotal');
    const currentPageDisplay = document.getElementById('currentPageDisplay');
    const prevPageBtn = document.getElementById('prevPageBtn');
    const nextPageBtn = document.getElementById('nextPageBtn');
    
    // 更新当前页码显示
    if (currentPageDisplay) {
        currentPageDisplay.textContent = total > 0 ? currentPage : 0;
    }
    
    // 更新上一页/下一页按钮状态
    if (prevPageBtn) {
        const isDisabled = currentPage === 1 || total === 0;
        prevPageBtn.disabled = isDisabled;
        if (isDisabled) {
            prevPageBtn.classList.add('disabled');
        } else {
            prevPageBtn.classList.remove('disabled');
        }
    }
    if (nextPageBtn) {
        const isDisabled = currentPage >= totalPages || total === 0;
        nextPageBtn.disabled = isDisabled;
        if (isDisabled) {
            nextPageBtn.classList.add('disabled');
        } else {
            nextPageBtn.classList.remove('disabled');
        }
    }
    
    pageStart.textContent = total > 0 ? ((currentPage - 1) * pageSize + 1) : 0;
    pageEnd.textContent = Math.min(currentPage * pageSize, total);
    pageTotal.textContent = total;
    
    if (totalPages <= 1) {
        pagination.innerHTML = '';
        return;
    }
    
    let html = '';
    
    // 上一页
    html += `
        <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="previousPage(); return false;" title="上一页 (← 或 PageUp)">
                <i class="fas fa-chevron-left"></i> 上一页
            </a>
        </li>
    `;
    
    // 页码
    for (let i = 1; i <= totalPages; i++) {
        if (i === 1 || i === totalPages || (i >= currentPage - 2 && i <= currentPage + 2)) {
            html += `
                <li class="page-item ${i === currentPage ? 'active' : ''}">
                    <a class="page-link" href="#" onclick="changePage(${i}); return false;">${i}</a>
                </li>
            `;
        } else if (i === currentPage - 3 || i === currentPage + 3) {
            html += '<li class="page-item disabled"><a class="page-link" href="#">...</a></li>';
        }
    }
    
    // 下一页
    html += `
        <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="nextPage(); return false;" title="下一页 (→ 或 PageDown)">
                下一页 <i class="fas fa-chevron-right"></i>
            </a>
        </li>
    `;
    
    pagination.innerHTML = html;
}

// 切换页码
function changePage(page) {
    if (!allGrades || allGrades.length === 0) return;
    if (page < 1) return;
    const totalPages = Math.ceil(allGrades.length / pageSize);
    if (page > totalPages) return;
    
    currentPage = page;
    displayGrades();
    
    // 滚动到表格顶部
    setTimeout(function() {
        const tableContainer = document.querySelector('.table-responsive');
        if (tableContainer) {
            tableContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }, 50);
}

// 上一页
function previousPage() {
    if (currentPage > 1 && allGrades && allGrades.length > 0) {
        changePage(currentPage - 1);
    }
}

// 下一页
function nextPage() {
    if (!allGrades || allGrades.length === 0) return;
    const totalPages = Math.ceil(allGrades.length / pageSize);
    if (currentPage < totalPages) {
        changePage(currentPage + 1);
    }
}

// 初始化键盘导航
function initKeyboardNavigation() {
    document.addEventListener('keydown', function(e) {
        // 检查是否在输入框中，如果是则不响应键盘事件
        const activeElement = document.activeElement;
        if (activeElement && (
            activeElement.tagName === 'INPUT' || 
            activeElement.tagName === 'TEXTAREA' || 
            activeElement.tagName === 'SELECT' ||
            activeElement.isContentEditable
        )) {
            return;
        }
        
        // 左箭头键或PageUp：上一页
        if (e.key === 'ArrowLeft' || e.key === 'PageUp') {
            e.preventDefault();
            previousPage();
        }
        // 右箭头键或PageDown：下一页
        else if (e.key === 'ArrowRight' || e.key === 'PageDown') {
            e.preventDefault();
            nextPage();
        }
        // Home键：第一页
        else if (e.key === 'Home') {
            e.preventDefault();
            changePage(1);
        }
        // End键：最后一页
        else if (e.key === 'End') {
            e.preventDefault();
            const totalPages = Math.ceil(allGrades.length / pageSize);
            changePage(totalPages);
        }
    });
}

// 改变每页显示数量
function changePageSize() {
    const select = document.getElementById('pageSizeSelect');
    if (select) {
        pageSize = parseInt(select.value);
        currentPage = 1; // 重置到第一页
        displayGrades();
    }
}

// 重置筛选
function resetFilters() {
    const filters = ['collegeFilter', 'majorFilter', 'classFilter', 'courseFilter', 'studentSearch', 'passedFilter'];
    filters.forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.value = '';
        }
    });
    currentPage = 1;
    
    // 重新加载专业、班级、课程列表
    loadMajors();
    loadClasses();
    loadCourses();
    
    loadGrades();
}

// 切换视图（班级/课程）
function switchView(view) {
    currentView = view;
    
    const viewByClassBtn = document.getElementById('viewByClass');
    const viewByCourseBtn = document.getElementById('viewByCourse');
    
    // 更新按钮状态 - 移除所有 active
    viewByClassBtn.classList.remove('active');
    viewByCourseBtn.classList.remove('active');
    
    // 添加 active 到当前视图
    if (view === 'class') {
        viewByClassBtn.classList.add('active');
    } else {
        viewByCourseBtn.classList.add('active');
    }
    
    // 显示当前视图提示
    showToast(`已切换到${view === 'class' ? '按班级' : '按课程'}查看`, 'success');
    
    // 重新加载数据
    loadGrades();
}

// 学生搜索实时过滤
function onStudentSearchChange() {
    clearTimeout(studentSearchTimeout);
    studentSearchTimeout = setTimeout(() => {
        loadGrades();
    }, 500); // 500ms 防抖
}

// 显示添加成绩模态框
function showAddGradeModal() {
    document.getElementById('gradeModalTitle').textContent = '录入成绩';
    document.getElementById('gradeForm').reset();
    document.getElementById('gradeId').value = '';
    gradeModal.show();
}

// 编辑成绩
async function editGrade(gradeId) {
    try {
        const response = await fetch(`/api/grades/grades/${gradeId}/`, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });
        
        if (response.ok) {
            const grade = await response.json();
            document.getElementById('gradeModalTitle').textContent = '编辑成绩';
            document.getElementById('gradeId').value = grade.id;
            document.getElementById('gradeStudent').value = grade.student;
            document.getElementById('gradeCourse').value = grade.course;
            document.getElementById('gradeScore').value = grade.score;
            gradeModal.show();
        } else {
            showToast('获取成绩信息失败', 'error');
        }
    } catch (error) {
        console.error('获取成绩信息失败:', error);
        showToast('获取成绩信息失败', 'error');
    }
}

// 保存成绩
async function saveGrade() {
    const gradeId = document.getElementById('gradeId').value;
    const studentId = document.getElementById('gradeStudent').value;
    const courseId = document.getElementById('gradeCourse').value;
    const score = document.getElementById('gradeScore').value;
    if (!studentId || !courseId || !score) {
        showToast('请填写必填项', 'warning');
        return;
    }
    
    if (score < 0 || score > 100) {
        showToast('成绩必须在0-100之间', 'warning');
        return;
    }
    
    const data = {
        student: parseInt(studentId),
        course: parseInt(courseId),
        score: parseFloat(score)
    };
    
    try {
        const url = gradeId 
            ? `/api/grades/grades/${gradeId}/`
            : '/api/grades/grades/';
        
        const method = gradeId ? 'PUT' : 'POST';
        
        // 使用全局 api() 封装，自动附带 CSRF Token，避免 CSRF 校验失败
        await api(url, method, data, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });

        showToast(gradeId ? '成绩更新成功' : '成绩录入成功', 'success');
        gradeModal.hide();
        loadGrades();
    } catch (error) {
        console.error('保存成绩失败:', error);
        showToast(error.message || '保存成绩失败', 'error');
    }
}

// 删除成绩
async function deleteGrade(gradeId) {
    if (!confirm('确定要删除这条成绩记录吗？')) {
        return;
    }
    
    try {
        // 使用 api()，自动附带 CSRF Token
        await api(`/api/grades/grades/${gradeId}/`, 'DELETE', null, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });
        
        showToast('删除成功', 'success');
        loadGrades();
    } catch (error) {
        console.error('删除失败:', error);
        showToast(error.message || '删除失败', 'error');
    }
}

// 显示批量导入模态框
function showBatchAddModal() {
    document.getElementById('batchData').value = '';
    document.getElementById('batchFile').value = '';
    batchAddModal.show();
}

// 批量导入
async function batchImport() {
    const batchData = document.getElementById('batchData').value;
    
    if (!batchData.trim()) {
        showToast('请输入要导入的数据', 'warning');
        return;
    }
    
    const lines = batchData.trim().split('\n');
    const grades = [];
    
    for (const line of lines) {
        const parts = line.split(',');
        if (parts.length < 3) {
            continue;
        }
        
        const grade = {
            student: parseInt(parts[0].trim()),
            course: parseInt(parts[1].trim()),
            score: parseFloat(parts[2].trim()),
            approved: false
        };
        
        
        grades.push(grade);
    }
    
    if (grades.length === 0) {
        showToast('没有有效的数据', 'warning');
        return;
    }
    
    try {
        // 使用 api()，自动附带 CSRF Token
        const result = await api('/api/grades/grades/batch_create/', 'POST', { grades: grades }, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });
        
        showToast(`导入成功 ${result.created} 条，失败 ${result.failed} 条`, 'success');
        batchAddModal.hide();
        loadGrades();
    } catch (error) {
        console.error('批量导入失败:', error);
        showToast(error.message || '批量导入失败', 'error');
    }
}

// 导出成绩
async function exportGrades() {
    try {
        let url = '/api/grades/grades/export/';
        const params = new URLSearchParams();
        
        const collegeId = document.getElementById('collegeFilter')?.value;
        const majorId = document.getElementById('majorFilter')?.value;
        const classId = document.getElementById('classFilter')?.value;
        const courseId = document.getElementById('courseFilter')?.value;
        
        if (collegeId) params.append('college_id', collegeId);
        if (majorId) params.append('major_id', majorId);
        if (classId) params.append('class_id', classId);
        if (courseId) params.append('course_id', courseId);
        
        const queryString = params.toString();
        if (queryString) {
            url += '?' + queryString;
        }
        
        const response = await fetch(url, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            downloadJSON(data, '成绩数据.json');
            showToast('导出成功', 'success');
        } else {
            showToast('导出失败', 'error');
        }
    } catch (error) {
        console.error('导出失败:', error);
        showToast('导出失败', 'error');
    }
}

// 显示统计模态框
function showStatisticsModal() {
    loadStatistics();
    statisticsModal.show();
}

// 加载统计数据
async function loadStatistics() {
    const level = document.getElementById('statsLevel').value;
    const collegeId = document.getElementById('statsCollege').value;
    const majorId = document.getElementById('statsMajor')?.value;
    
    // 根据统计维度显示/隐藏筛选项
    if (level === 'major' || level === 'class') {
        document.getElementById('statsMajorDiv').style.display = 'block';
    } else {
        document.getElementById('statsMajorDiv').style.display = 'none';
    }
    
    try {
        let url = `/api/grades/grades/statistics/?level=${level}`;
        if (collegeId) url += `&college_id=${collegeId}`;
        if (majorId && level !== 'college') url += `&major_id=${majorId}`;
        
        const response = await fetch(url, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });
        
        if (response.ok) {
            const statistics = await response.json();
            displayStatistics(statistics, level);
        } else {
            showToast('加载统计数据失败', 'error');
        }
    } catch (error) {
        console.error('加载统计数据失败:', error);
        showToast('加载统计数据失败', 'error');
    }
}

// 显示统计数据
function displayStatistics(statistics, level) {
    const tbody = document.getElementById('statisticsTableBody');
    
    if (!statistics || statistics.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" class="text-center text-muted py-4">暂无统计数据</td></tr>';
        return;
    }
    
    tbody.innerHTML = '';
    statistics.forEach(stat => {
        const row = document.createElement('tr');
        
        let name = '';
        if (level === 'college') {
            name = stat.college_name;
        } else if (level === 'major') {
            name = stat.major_name;
        } else if (level === 'class') {
            name = stat.class_name;
        }
        
        row.innerHTML = `
            <td>${name}</td>
            <td>${stat.total_students}</td>
            <td>${stat.total_grades}</td>
            <td><strong>${stat.average_score}</strong></td>
            <td><span class="badge bg-${stat.pass_rate >= 90 ? 'success' : stat.pass_rate >= 60 ? 'info' : 'danger'}">${stat.pass_rate}%</span></td>
            <td><span class="badge bg-warning">${stat.excellent_rate}%</span></td>
            <td><span class="badge bg-info">${stat.good_rate}%</span></td>
            <td class="text-success">${stat.passed_count}</td>
            <td class="text-danger">${stat.failed_count}</td>
        `;
        
        tbody.appendChild(row);
    });
}

// 加载仪表板统计数据
async function loadDashboardStatistics() {
    try {
        const response = await fetch('/api/grades/grades/statistics/?level=college', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });
        
        if (response.ok) {
            const statistics = await response.json();
            
            if (statistics && statistics.length > 0) {
                // 计算总体统计
                let totalStudents = 0;
                let totalGrades = 0;
                let totalScore = 0;
                let totalPassed = 0;
                let totalExcellent = 0;
                
                statistics.forEach(stat => {
                    totalStudents += stat.total_students;
                    totalGrades += stat.total_grades;
                    totalScore += stat.average_score * stat.total_grades;
                    totalPassed += stat.passed_count;
                    totalExcellent += Math.round(stat.total_grades * stat.excellent_rate / 100);
                });
                
                const avgScore = totalGrades > 0 ? (totalScore / totalGrades).toFixed(2) : 0;
                const passRate = totalGrades > 0 ? ((totalPassed / totalGrades) * 100).toFixed(2) : 0;
                const excellentRate = totalGrades > 0 ? ((totalExcellent / totalGrades) * 100).toFixed(2) : 0;
                
                document.getElementById('totalStudents').textContent = totalStudents;
                document.getElementById('avgScore').textContent = avgScore;
                document.getElementById('passRate').textContent = passRate + '%';
                document.getElementById('excellentRate').textContent = excellentRate + '%';
            }
        }
    } catch (error) {
        console.error('加载仪表板统计失败:', error);
    }
}

// 导出统计数据
function exportStatistics() {
    const tbody = document.getElementById('statisticsTableBody');
    const rows = tbody.querySelectorAll('tr');
    
    if (rows.length === 0 || rows[0].cells.length === 1) {
        showToast('没有可导出的数据', 'warning');
        return;
    }
    
    const data = [];
    rows.forEach(row => {
        const cells = row.cells;
        data.push({
            名称: cells[0].textContent,
            学生总数: cells[1].textContent,
            成绩记录数: cells[2].textContent,
            平均分: cells[3].textContent,
            及格率: cells[4].textContent,
            优秀率: cells[5].textContent,
            良好率: cells[6].textContent,
            及格人数: cells[7].textContent,
            不及格人数: cells[8].textContent
        });
    });
    
    downloadJSON(data, '成绩统计.json');
    showToast('导出成功', 'success');
}

// 下载JSON文件
function downloadJSON(data, filename) {
    const json = JSON.stringify(data, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
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
