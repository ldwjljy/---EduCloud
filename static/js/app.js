function csrfToken() { const m = document.cookie.match(/csrftoken=([^;]+)/); return m ? m[1] : '' }

async function api(url, method = 'GET', data, opts = {}) {
    const o = { method, headers: {} };
    if (method !== 'GET' && method !== 'HEAD') {
        if (!(data instanceof FormData)) {
            o.headers['Content-Type'] = 'application/json';
            o.body = JSON.stringify(data || {})
        } else {
            o.body = data
        }
        o.headers['X-CSRFToken'] = csrfToken()
    }
    // 正确合并自定义 headers，避免覆盖已设置的 X-CSRFToken / Content-Type
    if (opts.headers) {
        Object.assign(o.headers, opts.headers);
        const { headers, ...rest } = opts;
        Object.assign(o, rest);
    } else {
        Object.assign(o, opts);
    }
    const r = await fetch(url, o);
    if (!r.ok) {
        const errorText = await r.text();
        let errorObj;
        try {
            errorObj = JSON.parse(errorText);
        } catch (e) {
            errorObj = { error: errorText, message: errorText };
        }
        const err = new Error(errorObj.error || errorObj.message || errorText);
        err.error = errorObj.error || errorObj;
        err.message = errorObj.message || errorObj.error || errorText;
        err.detail = errorObj.detail;
        throw err;
    }
    const ct = r.headers.get('Content-Type') || '';
    if (r.status === 204 || !ct.includes('application/json')) return {};
    return r.json()
}

async function initNav() {
    let role = 'anonymous';
    let user = null;
    try {
        user = await api('/api/accounts/me');
        role = user.role || 'anonymous';
    } catch (e) { }

    const show = (id, cond) => {
        const el = document.getElementById(id);
        if (el) {
            if (cond) {
                el.style.display = 'flex';
                el.style.visibility = 'visible';
                el.classList.remove('hidden-by-permission');
            } else {
                el.style.display = 'none';
                el.style.visibility = 'hidden';
                el.classList.add('hidden-by-permission');
            }
        }
    };

    const showBlock = (id, cond) => {
        const el = document.getElementById(id);
        if (el) {
            if (cond) {
                el.style.display = 'block';
                el.style.visibility = 'visible';
                el.classList.remove('hidden-by-permission');
            } else {
                el.style.display = 'none';
                el.style.visibility = 'hidden';
                el.classList.add('hidden-by-permission');
            }
        }
    };

    const isAdmin = ['super_admin', 'principal', 'vice_principal'].includes(role);
    const isDean = ['dean', 'vice_dean'].includes(role);
    const isTeacher = ['teacher', 'head_teacher'].includes(role);
    const isHeadTeacher = role === 'head_teacher';
    const isStudent = role === 'student';
    const isLoggedIn = role !== 'anonymous';

    // Sidebar Logic
    show('nav-dashboard', !isStudent && isLoggedIn);
    // 学生管理：只有管理员、院长和班主任可以看到，普通教师不能看到
    show('nav-students', isAdmin || isDean || isHeadTeacher);
    // 教师管理：只有管理员和院长可以看到，教师/班主任不能看到
    show('nav-teachers', isAdmin || isDean);
    show('nav-accounts', isLoggedIn);
    // 组织架构：只有管理员和院长可以看到，教师/班主任不能看到
    show('nav-org', isAdmin || isDean);
    show('nav-courses', isAdmin || isDean || isTeacher || isStudent);
    show('nav-attendance', isAdmin || isDean || isTeacher);
    show('nav-grades', isAdmin || isDean || isTeacher);
    // 通知公告：所有已认证用户都可以看到，但只能查看列表内容
    show('nav-notices', isLoggedIn);
    show('nav-calendar', isLoggedIn);
    show('nav-admin', isAdmin);

    show('nav-login', !isLoggedIn);
    show('nav-logout', isLoggedIn);

    // Mark navigation as initialized to show allowed items
    document.body.classList.add('nav-initialized');

    // Top Navbar Logic
    if (isLoggedIn) {
        show('topUserMenu', true);
        show('topLoginBtn', false);

        const nameEl = document.getElementById('topUserName');
        const roleEl = document.getElementById('topUserRole');
        if (nameEl && user) nameEl.textContent = user.username || 'User';
        if (roleEl) roleEl.textContent = getRoleDisplay(role);

        showBlock('topAdminLink', isAdmin);
    } else {
        show('topUserMenu', false);
        show('topLoginBtn', true);
    }
}

function getRoleDisplay(role) {
    const map = {
        'super_admin': '超级管理员',
        'principal': '校长',
        'vice_principal': '副校长',
        'dean': '院长',
        'vice_dean': '副院长',
        'teacher': '教师',
        'head_teacher': '班主任',
        'student': '学生',
        'anonymous': '访客'
    };
    return map[role] || role;
}

function enhanceSelect(el) {
    if (el.dataset.ui === '1') return;
    if (!el.classList.contains('form-select')) {
        el.classList.add('form-select');
        // Removed bg-dark/text-white to match light theme
        el.classList.add('border-secondary');
    }
    el.dataset.ui = '1';
}

function initUISelects() {
    document.querySelectorAll('select').forEach(enhanceSelect);
}

window.addEventListener('DOMContentLoaded', initUISelects);

async function logout() {
    try {
        await fetch('/api-auth/logout/', { method: 'POST', headers: { 'X-CSRFToken': csrfToken() } });
    } catch (e) { }
    location.href = '/ui/login';
}

window.addEventListener('DOMContentLoaded', initNav);

let topNoticeLatestTs = 0;
async function loadTopNotices() {
    const listEl = document.getElementById('topNoticeList');
    const dotEl = document.getElementById('topNoticeDot');
    if (!listEl) return;
    let items = [];
    try {
        const r = await api('/api/notices/notices/?page=1');
        const list = Array.isArray(r) ? r : (r && r.results ? r.results : []);
        items = list.slice(0, 5);
    } catch (e) {
        // 如果是403错误，静默处理，避免在控制台产生干扰
        if (e.message && !e.message.includes('403')) {
            console.error('加载公告失败:', e);
        }
        items = [];
    }
    if (items.length === 0) {
        listEl.innerHTML = '<div class="p-3 text-center text-secondary">暂无公告</div>';
        if (dotEl) dotEl.style.display = 'none';
        return;
    }
    listEl.innerHTML = items.map(x => {
        const t = new Date(x.created_at);
        const time = isNaN(t.getTime()) ? '' : t.toLocaleString('zh-CN');
        return `<a href="#" class="list-group-item list-group-item-action" onclick="viewTopNotice(${x.id})">
            <div class="px-3 py-2">
                <div class="fw-bold">${x.title || ''}</div>
                <div class="text-muted small">${time}</div>
            </div>
        </a>`;
    }).join('');
    const maxTs = items.reduce((m, x) => {
        const t = Date.parse(x.created_at || '');
        return isNaN(t) ? m : Math.max(m, t);
    }, 0);
    topNoticeLatestTs = maxTs;
    const lastSeen = Number(localStorage.getItem('noticeLastSeen') || 0);
    if (dotEl) dotEl.style.display = (maxTs > lastSeen) ? '' : 'none';
}

function initTopNotices() {
    const btn = document.getElementById('topNoticeBtn');
    if (!btn) return;
    loadTopNotices();
    btn.addEventListener('click', function () {
        const dotEl = document.getElementById('topNoticeDot');
        if (dotEl) dotEl.style.display = 'none';
        const ts = topNoticeLatestTs || Date.now();
        localStorage.setItem('noticeLastSeen', String(ts));
    });
    setInterval(loadTopNotices, 60000);
}

window.addEventListener('DOMContentLoaded', initTopNotices);

async function viewTopNotice(id) {
    try {
        const x = await api('/api/notices/notices/' + id + '/');
        const mEl = document.getElementById('globalNoticeModal');
        if (!mEl) return;
        document.getElementById('globalNoticeModalTitle').textContent = x.title || '';
        document.getElementById('globalNoticeModalBody').textContent = x.content || '';
        const t = new Date(x.created_at);
        const time = isNaN(t.getTime()) ? '' : t.toLocaleString('zh-CN');
        const roleMap = { 'super_admin': '超级管理员', 'principal': '校长', 'vice_principal': '副校长', 'dean': '院长', 'vice_dean': '副院长', 'teacher': '教师', 'head_teacher': '班主任' };
        const meta = `${x.created_by_name || ''}（${roleMap[x.created_by_role] || (x.created_by_role || '')}） · ${(x.scope === 'all') ? '全校' : '教师范围'}${time ? (' · ' + time) : ''}`;
        document.getElementById('globalNoticeModalMeta').textContent = meta;
        const modal = new bootstrap.Modal(mEl);
        modal.show();
    } catch (e) {
        alert('加载失败');
    }
}

// Global Search Functionality
let searchTimeout = null;
let currentSearchResults = null;

function debounce(func, wait) {
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(searchTimeout);
            func(...args);
        };
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(later, wait);
    };
}

async function performGlobalSearch(query) {
    if (!query || query.length < 2) {
        hideSearchResults();
        return;
    }

    try {
        const results = await api(`/api/search?q=${encodeURIComponent(query)}&limit=5`);
        console.log('搜索结果:', results); // 调试信息
        currentSearchResults = results;
        displaySearchResults(results, query);
    } catch (e) {
        console.error('搜索失败:', e);
        const resultsEl = document.getElementById('globalSearchResults');
        if (resultsEl) {
            resultsEl.innerHTML = `
                <div class="p-3 text-center text-danger">
                    <i class="fa-solid fa-exclamation-circle me-2"></i>搜索失败，请稍后重试
                </div>
            `;
            resultsEl.style.display = 'block';
        }
    }
}

function displaySearchResults(results, query) {
    const resultsEl = document.getElementById('globalSearchResults');
    if (!resultsEl) return;

    const totalCount = (results.pages?.length || 0) +
        (results.students?.length || 0) +
        (results.teachers?.length || 0) +
        (results.courses?.length || 0) +
        (results.classes?.length || 0) +
        (results.classrooms?.length || 0) +
        (results.notices?.length || 0);

    if (totalCount === 0) {
        resultsEl.innerHTML = `
            <div class="p-3 text-center text-muted">
                <i class="fa-solid fa-search me-2"></i>未找到相关结果
            </div>
        `;
        resultsEl.style.display = 'block';
        return;
    }

    let html = '<div class="p-2">';

    // 管理页面结果（优先显示）
    if (results.pages && results.pages.length > 0) {
        html += '<div class="mb-2"><div class="text-muted small fw-bold px-2 py-1"><i class="fa-solid fa-window-maximize me-1"></i>管理页面</div>';
        results.pages.forEach(page => {
            html += `
                <a href="${page.url}" class="d-block px-2 py-2 text-decoration-none text-dark search-result-item" 
                   style="border-radius: 8px; transition: background 0.2s; display: block;"
                   tabindex="0">
                    <div class="fw-bold"><i class="fa-solid fa-arrow-right me-2 text-primary"></i>${highlightText(page.name, query)}</div>
                    <div class="text-muted small">${page.description || ''}</div>
                </a>
            `;
        });
        html += '</div>';
    }

    // 学生结果
    if (results.students && results.students.length > 0) {
        html += '<div class="mb-2"><div class="text-muted small fw-bold px-2 py-1"><i class="fa-solid fa-user-graduate me-1"></i>学生</div>';
        results.students.forEach(s => {
            html += `
                <a href="${s.url}" class="d-block px-2 py-2 text-decoration-none text-dark search-result-item" 
                   style="border-radius: 8px; transition: background 0.2s; display: block;"
                   tabindex="0">
                    <div class="fw-bold">${highlightText(s.name, query)}</div>
                    <div class="text-muted small">学号: ${highlightText(s.student_id, query)} · ${s.class_name}</div>
                </a>
            `;
        });
        html += '</div>';
    }

    // 教师结果
    if (results.teachers && results.teachers.length > 0) {
        html += '<div class="mb-2"><div class="text-muted small fw-bold px-2 py-1"><i class="fa-solid fa-chalkboard-user me-1"></i>教师</div>';
        results.teachers.forEach(t => {
            html += `
                <a href="${t.url}" class="d-block px-2 py-2 text-decoration-none text-dark search-result-item"
                   style="border-radius: 8px; transition: background 0.2s; display: block;"
                   tabindex="0">
                    <div class="fw-bold">${highlightText(t.name, query)}</div>
                    <div class="text-muted small">工号: ${highlightText(t.teacher_id, query)} · ${t.title}</div>
                </a>
            `;
        });
        html += '</div>';
    }

    // 课程结果
    if (results.courses && results.courses.length > 0) {
        html += '<div class="mb-2"><div class="text-muted small fw-bold px-2 py-1"><i class="fa-solid fa-book-open me-1"></i>课程</div>';
        results.courses.forEach(c => {
            html += `
                <a href="${c.url}" class="d-block px-2 py-2 text-decoration-none text-dark search-result-item"
                   style="border-radius: 8px; transition: background 0.2s; display: block;"
                   tabindex="0">
                    <div class="fw-bold">${highlightText(c.name, query)}</div>
                    <div class="text-muted small">${c.department}</div>
                </a>
            `;
        });
        html += '</div>';
    }

    // 班级结果
    if (results.classes && results.classes.length > 0) {
        html += '<div class="mb-2"><div class="text-muted small fw-bold px-2 py-1"><i class="fa-solid fa-users me-1"></i>班级</div>';
        results.classes.forEach(cls => {
            html += `
                <a href="${cls.url}" class="d-block px-2 py-2 text-decoration-none text-dark search-result-item"
                   style="border-radius: 8px; transition: background 0.2s; display: block;"
                   tabindex="0">
                    <div class="fw-bold">${highlightText(cls.name, query)}</div>
                    <div class="text-muted small">${cls.major} · ${cls.college}</div>
                </a>
            `;
        });
        html += '</div>';
    }

    // 教室结果
    if (results.classrooms && results.classrooms.length > 0) {
        html += '<div class="mb-2"><div class="text-muted small fw-bold px-2 py-1"><i class="fa-solid fa-door-open me-1"></i>教室</div>';
        results.classrooms.forEach(room => {
            html += `
                <a href="${room.url}" class="d-block px-2 py-2 text-decoration-none text-dark search-result-item"
                   style="border-radius: 8px; transition: background 0.2s; display: block;"
                   tabindex="0">
                    <div class="fw-bold">${highlightText(room.name, query)}</div>
                    <div class="text-muted small">${room.location} · 容量: ${room.capacity}</div>
                </a>
            `;
        });
        html += '</div>';
    }

    // 通知结果
    if (results.notices && results.notices.length > 0) {
        html += '<div class="mb-2"><div class="text-muted small fw-bold px-2 py-1"><i class="fa-solid fa-bullhorn me-1"></i>通知公告</div>';
        results.notices.forEach(notice => {
            html += `
                <a href="${notice.url}" class="d-block px-2 py-2 text-decoration-none text-dark search-result-item"
                   style="border-radius: 8px; transition: background 0.2s; display: block;"
                   tabindex="0">
                    <div class="fw-bold">${highlightText(notice.title, query)}</div>
                    <div class="text-muted small">${notice.content}</div>
                </a>
            `;
        });
        html += '</div>';
    }

    // 添加"查看全部结果"链接
    html += `
        <div class="border-top p-2 text-center">
            <a href="/search?q=${encodeURIComponent(query)}" class="text-primary small text-decoration-none fw-bold">
                <i class="fa-solid fa-arrow-right me-1"></i>查看全部搜索结果
            </a>
        </div>
    `;

    html += '</div>';
    resultsEl.innerHTML = html;
    resultsEl.style.display = 'block';
}

function highlightText(text, query) {
    if (!text || !query) return text || '';
    const regex = new RegExp(`(${query})`, 'gi');
    return String(text).replace(regex, '<mark style="background: #fff3cd; padding: 0;">$1</mark>');
}

function hideSearchResults() {
    const resultsEl = document.getElementById('globalSearchResults');
    if (resultsEl) {
        resultsEl.style.display = 'none';
    }
}

function initGlobalSearch() {
    const searchInput = document.getElementById('globalSearchInput');
    const searchContainer = document.getElementById('globalSearchContainer');

    if (!searchInput || !searchContainer) return;

    const debouncedSearch = debounce(performGlobalSearch, 300);

    // 输入搜索
    searchInput.addEventListener('input', function (e) {
        const query = e.target.value.trim();
        if (query.length >= 2) {
            debouncedSearch(query);
        } else {
            hideSearchResults();
        }
    });

    // 聚焦时显示已有结果
    searchInput.addEventListener('focus', function (e) {
        const query = e.target.value.trim();
        if (query.length >= 2) {
            performGlobalSearch(query);
        }
    });

    // 点击外部关闭搜索结果
    document.addEventListener('click', function (e) {
        if (searchContainer && !searchContainer.contains(e.target)) {
            hideSearchResults();
        }
    });

    // 键盘导航和快捷键
    searchInput.addEventListener('keydown', function (e) {
        const resultsEl = document.getElementById('globalSearchResults');
        if (!resultsEl || resultsEl.style.display === 'none') {
            // 如果结果未显示，按Enter键执行搜索
            if (e.key === 'Enter') {
                const query = e.target.value.trim();
                if (query.length >= 2) {
                    window.location.href = `/search?q=${encodeURIComponent(query)}`;
                }
            }
            return;
        }

        const items = resultsEl.querySelectorAll('.search-result-item');
        const currentIndex = Array.from(items).findIndex(item => item === document.activeElement);

        if (e.key === 'ArrowDown') {
            e.preventDefault();
            const nextIndex = currentIndex < items.length - 1 ? currentIndex + 1 : 0;
            if (items[nextIndex]) {
                items[nextIndex].focus();
                items[nextIndex].scrollIntoView({ block: 'nearest', behavior: 'smooth' });
            }
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            const prevIndex = currentIndex > 0 ? currentIndex - 1 : items.length - 1;
            if (items[prevIndex]) {
                items[prevIndex].focus();
                items[prevIndex].scrollIntoView({ block: 'nearest', behavior: 'smooth' });
            } else {
                searchInput.focus();
            }
        } else if (e.key === 'Escape') {
            hideSearchResults();
            searchInput.blur();
        } else if (e.key === 'Enter') {
            // 如果焦点在搜索结果项上，点击它
            const focusedItem = document.activeElement;
            if (focusedItem && focusedItem.classList.contains('search-result-item')) {
                e.preventDefault();
                focusedItem.click();
            }
        }
    });

    // 为搜索结果项添加焦点和悬停样式
    searchContainer.addEventListener('mouseover', function (e) {
        const item = e.target.closest('.search-result-item');
        if (item && document.activeElement !== item) {
            item.style.background = '#f4f7fe';
        }
    });

    searchContainer.addEventListener('mouseout', function (e) {
        const item = e.target.closest('.search-result-item');
        if (item && document.activeElement !== item) {
            item.style.background = 'transparent';
        }
    });

    // 为搜索结果项添加焦点样式
    searchContainer.addEventListener('focusin', function (e) {
        const item = e.target.closest('.search-result-item');
        if (item) {
            item.style.background = '#f4f7fe';
            item.style.outline = '2px solid #0d6efd';
            item.style.outlineOffset = '-2px';
        }
    });

    searchContainer.addEventListener('focusout', function (e) {
        const item = e.target.closest('.search-result-item');
        if (item) {
            item.style.background = 'transparent';
            item.style.outline = 'none';
        }
    });
}

window.addEventListener('DOMContentLoaded', initGlobalSearch);
