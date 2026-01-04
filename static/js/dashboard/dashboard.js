/* Modern Dashboard JS using ECharts - Light Theme */

let attendanceTrendChartInstance = null;
let catChartInstance = null;
let attendanceChartInstance = null;
let rangeDays = 30;

// 监听考勤更新通知（用于仪表盘页面实时更新考勤图表）
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
                console.log('仪表盘页面：收到考勤更新通知，立即刷新');
                // 立即刷新仪表盘数据（包括考勤图表）
                load();
            }
        });
    }

    // 监听 localStorage 变化（跨标签页，storage 事件）
    window.addEventListener('storage', (event) => {
        if (event.key === 'attendance_update_check' && event.newValue) {
            console.log('仪表盘页面：收到考勤更新通知（Storage事件），立即刷新');
            // 立即刷新仪表盘数据（包括考勤图表）
            load();
        }
    });

    // 监听自定义事件（同标签页）
    window.addEventListener('attendanceUpdated', (event) => {
        if (event.detail && (event.detail.type === 'attendance_updated' || event.detail.type === 'attendance_batch_updated')) {
            console.log('仪表盘页面：收到考勤更新通知（CustomEvent），立即刷新');
            // 立即刷新仪表盘数据（包括考勤图表）
            load();
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
                    console.log('仪表盘页面：收到考勤更新通知（轮询），立即刷新');
                    load();
                }
            }
        } catch (e) {
            // 忽略错误
        }
    }, 1000);
}

document.addEventListener('DOMContentLoaded', () => {
    // Initialize ECharts instances
    initCharts();

    // Load Filters
    loadDashColleges();
    loadDashDepts();
    onDashFiltersReady();

    // Initial Data Load
    load();

    // 设置考勤更新监听器
    setupAttendanceUpdateListener();

    // Auto-refresh every 20s
    setInterval(load, 20000);

    // Handle Resize
    window.addEventListener('resize', () => {
        attendanceTrendChartInstance?.resize();
        catChartInstance?.resize();
        attendanceChartInstance?.resize();
    });
});

function initCharts() {
    const trendChartEl = document.getElementById('regChart');
    if (trendChartEl) {
        attendanceTrendChartInstance = echarts.init(trendChartEl);
    }

    const catChartEl = document.getElementById('catChart');
    if (catChartEl) {
        catChartInstance = echarts.init(catChartEl);
    }

    const attChartEl = document.getElementById('attendanceChart');
    if (attChartEl) {
        attendanceChartInstance = echarts.init(attChartEl);
    }
}

function setRange(r) {
    switch (r) {
        case 'week': rangeDays = 7; break;
        case 'month': rangeDays = 30; break;
        case 'term': rangeDays = 120; break;
        default: rangeDays = 30;
    }
    // Update active button state
    document.querySelectorAll('.btn-group .btn').forEach(btn => {
        btn.classList.remove('active');
        // Simple check for text content
        if (btn.textContent.includes(r === 'week' ? '本周' : r === 'month' ? '本月' : '本学期')) {
            btn.classList.add('active');
        }
    });
    load();
}

async function load() {
    const p = new URLSearchParams();
    p.append('days', rangeDays);

    const fc = document.getElementById('dashFilterCollege');
    const fd = document.getElementById('dashFilterDept');
    const college = (fc && fc.value) || '';
    const dept = (fd && fd.value) || '';

    console.log('Dashboard filters:', { college, dept }); // 调试信息

    if (dept) p.append('department', dept);
    else if (college) p.append('college', college);

    const apiUrl = '/api/stats/dashboard?' + p.toString();
    console.log('API URL:', apiUrl); // 调试信息

    try {
        const dashboardData = await api(apiUrl);
        console.log('Dashboard data received:', dashboardData); // 调试信息

        // Update labels based on filter selection
        updateLabels(college, dept);
        updateStats(dashboardData.cards);
        updateAttendanceTrendChart(dashboardData);
        updateCatChart(dashboardData.course_distribution);
        updateRecentList(dashboardData.recent);

        // 今日考勤概览：从后端返回的 attendance_today 真实统计绘制
        updateAttendanceChart(dashboardData.attendance_today);

    } catch (e) {
        console.error("Failed to load dashboard data", e);
    }
}

function updateLabels(college, dept) {
    const labelStu = document.getElementById('labelStu');
    const labelTea = document.getElementById('labelTea');
    const labelCou = document.getElementById('labelCou');

    if (dept) {
        // When department is selected, show department-specific labels
        if (labelStu) labelStu.textContent = '本专业学生数';
        if (labelTea) labelTea.textContent = '本专业教师数';
        if (labelCou) labelCou.textContent = '本专业课程数';
    } else if (college) {
        // When college is selected, show college-specific labels
        if (labelStu) labelStu.textContent = '本学院学生数';
        if (labelTea) labelTea.textContent = '本学院教师数';
        if (labelCou) labelCou.textContent = '本学院课程数';
    } else {
        // Default labels when no filter is selected
        if (labelStu) labelStu.textContent = '在校学生总数';
        if (labelTea) labelTea.textContent = '在职教师总数';
        if (labelCou) labelCou.textContent = '开设课程总数';
    }
}

function updateStats(cards) {
    if (!cards) return;
    animateValue('dStu', cards.students_total);
    animateValue('dTea', cards.teachers_total);
    animateValue('dCou', cards.courses_total);
}

function animateValue(id, end) {
    const obj = document.getElementById(id);
    if (!obj) return;
    if (end === undefined || end === null) {
        obj.textContent = '--';
        return;
    }
    obj.textContent = end;
}

function updateAttendanceTrendChart(data) {
    if (!attendanceTrendChartInstance) return;

    // Check if attendance trend data is available
    if (!data.attendance_trend) {
        // Fallback to empty if no data
        return;
    }

    const trend = data.attendance_trend;
    const dates = trend.dates;

    // Series data
    const sPresent = trend.series.present;
    const sLate = trend.series.late;
    const sAbsent = trend.series.absent;
    const sLeave = trend.series.leave;

    const option = {
        tooltip: {
            trigger: 'axis',
            backgroundColor: '#fff',
            textStyle: { color: '#2B3674' },
            extraCssText: 'box-shadow: 0 4px 20px rgba(0,0,0,0.1); border-radius: 10px; border: none;'
        },
        legend: {
            data: ['正常', '迟到', '旷课', '请假'],
            bottom: 0,
            icon: 'circle',
            itemWidth: 8,
            itemHeight: 8,
            textStyle: { color: '#A3AED0' }
        },
        grid: {
            left: '10px', right: '10px', bottom: '30px', top: '10px', containLabel: true
        },
        xAxis: {
            type: 'category',
            boundaryGap: false,
            data: dates,
            axisLine: { show: false },
            axisTick: { show: false },
            axisLabel: { color: '#A3AED0', fontSize: 12 }
        },
        yAxis: {
            type: 'value',
            axisLine: { show: false },
            axisTick: { show: false },
            splitLine: { show: true, lineStyle: { type: 'dashed', color: '#E0E5F2' } },
            axisLabel: { show: true, color: '#A3AED0' }
        },
        series: [
            {
                name: '正常',
                type: 'line',
                smooth: true,
                showSymbol: false,
                itemStyle: { color: '#05CD99' },
                lineStyle: { width: 3, color: '#05CD99' },
                data: sPresent
            },
            {
                name: '迟到',
                type: 'line',
                smooth: true,
                showSymbol: false,
                itemStyle: { color: '#FFC700' },
                lineStyle: { width: 3, color: '#FFC700' },
                data: sLate
            },
            {
                name: '旷课',
                type: 'line',
                smooth: true,
                showSymbol: false,
                itemStyle: { color: '#E31A1A' },
                lineStyle: { width: 3, color: '#E31A1A' },
                data: sAbsent
            },
            {
                name: '请假',
                type: 'line',
                smooth: true,
                showSymbol: false,
                itemStyle: { color: '#4318FF' },
                lineStyle: { width: 3, color: '#4318FF' },
                data: sLeave
            }
        ]
    };
    attendanceTrendChartInstance.setOption(option, true); // true to merge/not merge? actually true to not merge is safer to clear old data
}

function updateCatChart(distribution) {
    if (!catChartInstance || !distribution) return;

    const option = {
        tooltip: { trigger: 'item' },
        legend: { bottom: '0%', left: 'center', icon: 'circle', itemWidth: 8, itemHeight: 8 },
        series: [{
            name: '课程分布',
            type: 'pie',
            radius: ['50%', '70%'],
            center: ['50%', '45%'],
            avoidLabelOverlap: false,
            itemStyle: {
                borderRadius: 5,
                borderColor: '#fff',
                borderWidth: 2
            },
            label: { show: false, position: 'center' },
            emphasis: {
                label: { show: true, fontSize: 18, fontWeight: 'bold', color: '#2B3674' }
            },
            labelLine: { show: false },
            data: distribution
        }],
        color: ['#4318FF', '#6AD2FF', '#EFF4FB', '#85E0AB', '#FFD166']
    };
    catChartInstance.setOption(option);
}

function updateRecentList(recent) {
    const list = document.getElementById('recentList');
    if (!list) return;

    if (!recent || recent.length === 0) {
        list.innerHTML = '<div class="p-4 text-center text-secondary">暂无最近活动</div>';
        return;
    }

    list.innerHTML = recent.map(item => `
        <div class="d-flex align-items-center justify-content-between p-3 mb-2" style="background: #f4f7fe; border-radius: 12px;">
            <div class="d-flex align-items-center gap-3">
                <div style="width: 40px; height: 40px; border-radius: 10px; background: white; display: flex; align-items: center; justify-content: center; color: #4318FF;">
                    <i class="fa-solid fa-bell"></i>
                </div>
                <div>
                    <div style="font-weight: 600; color: #2B3674;">${item.title}</div>
                    <small style="color: #A3AED0;">${item.time}</small>
                </div>
            </div>
            <span class="badge rounded-pill" style="background: white; color: #4318FF; box-shadow: 0 2px 6px rgba(0,0,0,0.05);">${item.status}</span>
        </div>
    `).join('');
}

function updateAttendanceChart(todayStats) {
    if (!attendanceChartInstance) return;

    // todayStats 结构来自后端的 attendance_today：{present, late, absent, leave}
    const stats = todayStats || {};
    const present = stats.present || 0;
    const late = stats.late || 0;
    const absent = stats.absent || 0;
    const leave = stats.leave || 0;

    const option = {
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
        grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
        xAxis: {
            type: 'category',
            data: ['正常', '迟到', '缺勤', '请假'],
            axisLine: { show: false },
            axisTick: { show: false },
            axisLabel: { color: '#A3AED0' }
        },
        yAxis: {
            type: 'value',
            splitLine: { show: false },
            axisLabel: { show: false }
        },
        series: [{
            name: '人数',
            type: 'bar',
            barWidth: '40%',
            data: [present, late, absent, leave],
            itemStyle: {
                borderRadius: [20, 20, 0, 0],
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                    { offset: 0, color: '#00D2FF' },
                    { offset: 1, color: '#009BBF' }
                ])
            }
        }]
    };
    attendanceChartInstance.setOption(option);
}

// 打字机效果显示文本
function typeWriter(element, text, speed = 30, callback) {
    // 清除之前的定时器
    if (typeWriterTimer) {
        clearTimeout(typeWriterTimer);
        typeWriterTimer = null;
    }
    
    let i = 0;
    element.innerHTML = '';
    const cursor = '<span class="typing-cursor"></span>';
    
    // 将文本转换为HTML，处理换行符
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    function type() {
        if (i < text.length) {
            let currentText = text.substring(0, i + 1);
            // 将换行符转换为<br>，同时转义HTML
            currentText = escapeHtml(currentText).replace(/\n/g, '<br>');
            element.innerHTML = currentText + cursor;
            i++;
            typeWriterTimer = setTimeout(type, speed);
        } else {
            // 完成打字，移除光标，处理换行符
            let finalText = escapeHtml(text).replace(/\n/g, '<br>');
            element.innerHTML = finalText;
            typeWriterTimer = null;
            if (callback) callback();
        }
    }
    
    type();
}

// 停止打字机效果
function stopTypeWriter() {
    if (typeWriterTimer) {
        clearTimeout(typeWriterTimer);
        typeWriterTimer = null;
    }
}

// 生成数据报告
function generateDataReport(dashboardData) {
    const cards = dashboardData.cards || {};
    const attendanceToday = dashboardData.attendance_today || {};
    const attendanceTrend = dashboardData.attendance_trend || {};
    const courseDistribution = dashboardData.course_distribution || [];
    const recent = dashboardData.recent || [];
    
    const studentsTotal = cards.students_total || 0;
    const teachersTotal = cards.teachers_total || 0;
    const coursesTotal = cards.courses_total || 0;
    
    const present = attendanceToday.present || 0;
    const late = attendanceToday.late || 0;
    const absent = attendanceToday.absent || 0;
    const leave = attendanceToday.leave || 0;
    const totalAttendance = present + late + absent + leave;
    const attendanceRate = totalAttendance > 0 ? ((present / totalAttendance) * 100).toFixed(1) : 0;
    
    const now = new Date();
    const dateStr = now.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' });
    
    let report = `📊 教务数据智能分析报告\n\n`;
    report += `生成时间：${dateStr}\n`;
    report += `${'='.repeat(50)}\n\n`;
    
    report += `📈 核心数据概览\n`;
    report += `${'-'.repeat(50)}\n`;
    report += `• 在校学生总数：${studentsTotal.toLocaleString()} 人\n`;
    report += `• 在职教师总数：${teachersTotal.toLocaleString()} 人\n`;
    report += `• 开设课程总数：${coursesTotal.toLocaleString()} 门\n\n`;
    
    if (totalAttendance > 0) {
        report += `📋 今日考勤深度分析\n`;
        report += `${'-'.repeat(50)}\n`;
        report += `• 正常出勤：${present} 人 (${((present / totalAttendance) * 100).toFixed(1)}%)\n`;
        report += `• 迟到情况：${late} 人 (${((late / totalAttendance) * 100).toFixed(1)}%)\n`;
        report += `• 缺勤情况：${absent} 人 (${((absent / totalAttendance) * 100).toFixed(1)}%)\n`;
        report += `• 请假情况：${leave} 人 (${((leave / totalAttendance) * 100).toFixed(1)}%)\n`;
        report += `• 整体出勤率：${attendanceRate}%\n\n`;
        
        // 多维度出勤情况分析
        const presentRate = (present / totalAttendance) * 100;
        const lateRate = (late / totalAttendance) * 100;
        const absentRate = (absent / totalAttendance) * 100;
        const leaveRate = (leave / totalAttendance) * 100;
        
        report += `🔍 出勤情况评估：\n`;
        
        // 综合出勤率评估
        if (attendanceRate >= 98) {
            report += `✅ 出勤情况优秀！整体出勤率达到 ${attendanceRate}%，学生出勤状况非常良好，教学秩序井然。\n`;
        } else if (attendanceRate >= 95) {
            report += `✅ 出勤情况良好！整体出勤率达到 ${attendanceRate}%，学生出勤状况稳定，继续保持。\n`;
        } else if (attendanceRate >= 90) {
            report += `⚠️ 出勤情况基本正常，整体出勤率为 ${attendanceRate}%，但仍有优化空间。\n`;
        } else if (attendanceRate >= 85) {
            report += `⚠️ 出勤情况需要关注，整体出勤率为 ${attendanceRate}%，建议加强日常考勤管理。\n`;
        } else if (attendanceRate >= 75) {
            report += `❌ 出勤情况不佳，整体出勤率仅为 ${attendanceRate}%，需要立即采取有效措施改善。\n`;
        } else {
            report += `❌ 出勤情况严重，整体出勤率仅为 ${attendanceRate}%，建议紧急召开专题会议研究解决方案。\n`;
        }
        
        // 迟到情况分析
        if (lateRate > 10) {
            report += `⚠️ 迟到率偏高（${lateRate.toFixed(1)}%），建议：\n`;
            report += `   - 检查课程时间安排是否合理\n`;
            report += `   - 加强学生时间管理教育\n`;
            report += `   - 考虑设置迟到预警机制\n`;
        } else if (lateRate > 5) {
            report += `⚠️ 迟到率中等（${lateRate.toFixed(1)}%），建议关注迟到较多的班级或课程。\n`;
        } else if (lateRate > 0) {
            report += `✅ 迟到率较低（${lateRate.toFixed(1)}%），迟到情况控制良好。\n`;
        } else {
            report += `✅ 无迟到情况，表现优秀！\n`;
        }
        
        // 缺勤情况分析
        if (absentRate > 10) {
            report += `❌ 缺勤率严重（${absentRate.toFixed(1)}%），需要立即关注：\n`;
            report += `   - 深入调查缺勤原因（健康、学习兴趣、课程难度等）\n`;
            report += `   - 与缺勤学生及家长及时沟通\n`;
            report += `   - 建立缺勤预警和跟踪机制\n`;
        } else if (absentRate > 5) {
            report += `⚠️ 缺勤率偏高（${absentRate.toFixed(1)}%），建议：\n`;
            report += `   - 分析缺勤学生的共同特征\n`;
            report += `   - 加强课堂吸引力和教学质量\n`;
            report += `   - 完善请假审批流程\n`;
        } else if (absentRate > 2) {
            report += `⚠️ 缺勤率中等（${absentRate.toFixed(1)}%），建议持续关注缺勤学生情况。\n`;
        } else if (absentRate > 0) {
            report += `✅ 缺勤率较低（${absentRate.toFixed(1)}%），缺勤情况控制良好。\n`;
        } else {
            report += `✅ 无缺勤情况，表现优秀！\n`;
        }
        
        // 请假情况分析
        if (leaveRate > 15) {
            report += `⚠️ 请假率较高（${leaveRate.toFixed(1)}%），建议：\n`;
            report += `   - 审查请假审批是否过于宽松\n`;
            report += `   - 区分病假、事假等不同类型\n`;
            report += `   - 建立请假数据统计分析机制\n`;
        } else if (leaveRate > 8) {
            report += `⚠️ 请假率中等（${leaveRate.toFixed(1)}%），属于正常范围，建议保持关注。\n`;
        } else if (leaveRate > 0) {
            report += `✅ 请假率较低（${leaveRate.toFixed(1)}%），请假管理规范。\n`;
        } else {
            report += `✅ 无请假情况。\n`;
        }
        
        // 综合建议
        if (attendanceRate < 90) {
            report += `\n💡 综合改善建议：\n`;
            if (absentRate > lateRate && absentRate > 5) {
                report += `   - 优先解决缺勤问题，缺勤是影响出勤率的主要因素\n`;
            }
            if (lateRate > absentRate && lateRate > 5) {
                report += `   - 重点关注迟到问题，迟到可能影响学习效果\n`;
            }
            report += `   - 建立班级出勤排行榜，营造良好出勤氛围\n`;
            report += `   - 定期开展出勤数据分析，及时发现问题\n`;
            report += `   - 加强与学生、家长的沟通，了解真实原因\n`;
        }
        
        report += `\n`;
    }
    
    if (courseDistribution && courseDistribution.length > 0) {
        report += `📚 课程结构深度分析\n`;
        report += `${'-'.repeat(50)}\n`;
        
        // 过滤掉值为0的课程类型，只显示有实际数据的课程
        const validDistribution = courseDistribution.filter(item => (item.value || 0) > 0);
        
        if (validDistribution.length === 0) {
            report += `⚠️ 暂无有效的课程类型数据。\n\n`;
        } else {
            // 计算课程分布统计（使用真实数据）
            const sortedDistribution = [...validDistribution].sort((a, b) => (b.value || 0) - (a.value || 0));
            const topCourses = sortedDistribution.slice(0, 5);
            const totalDistributed = sortedDistribution.reduce((sum, item) => sum + (item.value || 0), 0);
        
        report += `课程类型分布（前5名）：\n`;
        topCourses.forEach((item, index) => {
            // 使用后端返回的真实字段名 label（不是 name）
            const name = item.label || item.name || '未知类型';
            const value = item.value || 0;
            const percentage = coursesTotal > 0 ? ((value / coursesTotal) * 100).toFixed(1) : 0;
            const barLength = Math.round((value / (topCourses[0].value || 1)) * 20);
            const bar = '█'.repeat(barLength);
            report += `${index + 1}. ${name.padEnd(12)} ${bar} ${value} 门 (${percentage}%)\n`;
        });
        
        // 课程分布均衡性分析
        if (topCourses.length > 0 && coursesTotal > 0) {
            const maxPercentage = (topCourses[0].value / coursesTotal) * 100;
            const avgPercentage = (totalDistributed / coursesTotal / topCourses.length) * 100;
            const variance = topCourses.reduce((sum, item) => {
                const p = (item.value / coursesTotal) * 100;
                return sum + Math.pow(p - avgPercentage, 2);
            }, 0) / topCourses.length;
            
            report += `\n📊 课程结构特点：\n`;
            
            // 使用后端返回的真实字段名 label
            const topCourseName = topCourses[0].label || topCourses[0].name || '主要类型';
            if (maxPercentage > 40) {
                report += `• 课程类型集中度较高，${topCourseName}占比达 ${maxPercentage.toFixed(1)}%\n`;
                report += `  建议：考虑增加课程类型多样性，平衡各类型课程比例\n`;
            } else if (maxPercentage > 25) {
                report += `• 课程类型分布相对集中，${topCourseName}为主要类型（${maxPercentage.toFixed(1)}%）\n`;
                report += `  优势：重点突出，有利于形成专业特色\n`;
            } else {
                report += `• 课程类型分布较为均衡，各类型课程比例合理\n`;
                report += `  优势：课程结构多元化，有利于学生全面发展\n`;
            }
            
            // 分析课程多样性（使用有效数据）
            if (validDistribution.length >= 5) {
                report += `• 课程类型丰富，共有 ${validDistribution.length} 种不同类型\n`;
                report += `  优势：课程体系完善，能够满足不同学习需求\n`;
            } else if (validDistribution.length >= 3) {
                report += `• 课程类型适中，共有 ${validDistribution.length} 种类型\n`;
                report += `  建议：可考虑适当增加课程类型，丰富课程体系\n`;
            } else {
                report += `• 课程类型较少，仅有 ${validDistribution.length} 种类型\n`;
                report += `  建议：建议增加课程类型，提升课程体系的完整性\n`;
            }
            
            // 课程结构合理性分析
            if (coursesTotal > 0 && studentsTotal > 0) {
                const coursesPerStudent = (coursesTotal / studentsTotal).toFixed(2);
                report += `• 人均可选课程：${coursesPerStudent} 门/人\n`;
                if (coursesPerStudent > 1.5) {
                    report += `  优势：课程资源充足，学生选择空间大\n`;
                } else if (coursesPerStudent > 1.0) {
                    report += `  正常：课程资源基本满足需求\n`;
                } else {
                    report += `  建议：可考虑增加课程数量，提升学生选择灵活性\n`;
                }
            }
            
            // 课程分布趋势建议
            if (variance > 100) {
                report += `\n💡 优化建议：\n`;
                report += `   - 课程分布差异较大，建议优化课程结构\n`;
                report += `   - 关注占比较低的课程类型，评估其必要性\n`;
                report += `   - 根据学生需求和就业趋势调整课程配置\n`;
            } else if (variance > 0) {
                report += `\n✅ 课程结构评估：课程分布相对均衡，结构合理。\n`;
            }
        } else if (coursesTotal === 0) {
            report += `\n⚠️ 暂无课程数据，无法进行结构分析。\n`;
        }
        }
        
        report += `\n`;
    }
    
    if (attendanceTrend && attendanceTrend.dates && attendanceTrend.dates.length > 0) {
        const dates = attendanceTrend.dates;
        const presentSeries = attendanceTrend.series?.present || [];
        const lateSeries = attendanceTrend.series?.late || [];
        const absentSeries = attendanceTrend.series?.absent || [];
        
        if (presentSeries.length > 0) {
            const avgPresent = (presentSeries.reduce((a, b) => a + b, 0) / presentSeries.length).toFixed(0);
            const maxPresent = Math.max(...presentSeries);
            const minPresent = Math.min(...presentSeries);
            
            report += `📊 考勤趋势分析（最近 ${dates.length} 天）\n`;
            report += `${'-'.repeat(50)}\n`;
            report += `• 平均正常出勤：${avgPresent} 人/天\n`;
            report += `• 最高正常出勤：${maxPresent} 人\n`;
            report += `• 最低正常出勤：${minPresent} 人\n`;
            
            if (maxPresent - minPresent > maxPresent * 0.2) {
                report += `⚠️ 考勤波动较大，建议分析原因并采取相应措施。\n\n`;
            } else {
                report += `✅ 考勤趋势稳定，波动在正常范围内。\n\n`;
            }
        }
    }
    
    if (recent && recent.length > 0) {
        report += `🕐 最近教务活动\n`;
        report += `${'-'.repeat(50)}\n`;
        recent.slice(0, 5).forEach((item, index) => {
            report += `${index + 1}. ${item.title || '未知活动'} - ${item.time || '未知时间'}\n`;
        });
        report += `\n`;
    }
    
    report += `💡 数据洞察与建议\n`;
    report += `${'-'.repeat(50)}\n`;
    
    if (studentsTotal > 0 && teachersTotal > 0) {
        const studentTeacherRatio = (studentsTotal / teachersTotal).toFixed(1);
        report += `• 师生比例：${studentTeacherRatio}:1\n`;
        if (studentTeacherRatio > 20) {
            report += `  建议：师生比例偏高，建议考虑增加教师资源。\n`;
        } else if (studentTeacherRatio < 10) {
            report += `  优势：师生比例合理，有利于教学质量提升。\n`;
        }
    }
    
    if (coursesTotal > 0 && studentsTotal > 0) {
        const coursePerStudent = (coursesTotal / studentsTotal).toFixed(2);
        report += `• 人均课程数：${coursePerStudent} 门/人\n`;
    }
    
    report += `\n`;
    report += `📌 总结\n`;
    report += `${'-'.repeat(50)}\n`;
    report += `根据当前数据分析，系统运行状态${attendanceRate >= 85 ? '良好' : '正常'}。`;
    if (attendanceRate < 85 && totalAttendance > 0) {
        report += `建议重点关注出勤管理，提升整体出勤率。`;
    }
    report += `建议定期查看数据报告，及时发现问题并采取相应措施。\n\n`;
    report += `报告生成完成。感谢使用智能分析功能！✨\n`;
    
    return report;
}

// 防止重复点击的标志
let isGeneratingReport = false;
// 保存打字机效果的定时器ID，以便可以取消
let typeWriterTimer = null;

async function claimMyData() {
    // 防止重复点击
    if (isGeneratingReport) {
        console.log('报告正在生成中，请勿重复点击');
        return;
    }
    
    // 获取按钮元素
    const btn = document.querySelector('button[onclick="claimMyData()"]');
    const originalBtnContent = btn ? btn.innerHTML : '';
    
    try {
        // 设置处理中标志
        isGeneratingReport = true;
        
        // 禁用按钮并显示加载状态
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin me-2"></i>分析中...';
            btn.style.opacity = '0.7';
            btn.style.cursor = 'not-allowed';
        }
        
        // 显示模态窗口
        const modal = new bootstrap.Modal(document.getElementById('aiAnalysisModal'));
        const reportElement = document.getElementById('aiAnalysisReport');
        
        // 清空之前的内容
        reportElement.innerHTML = '<div class="text-center text-secondary"><i class="fa-solid fa-spinner fa-spin me-2"></i>正在分析数据，请稍候...</div>';
        
        // 显示模态窗口
        modal.show();
        
        // 获取当前仪表盘数据
        const p = new URLSearchParams();
        p.append('days', rangeDays || 30);
        
        const fc = document.getElementById('dashFilterCollege');
        const fd = document.getElementById('dashFilterDept');
        const college = (fc && fc.value) || '';
        const dept = (fd && fd.value) || '';
        
        if (dept) p.append('department', dept);
        else if (college) p.append('college', college);
        
        const apiUrl = '/api/stats/dashboard?' + p.toString();
        
        // 获取数据
        const dashboardData = await api(apiUrl);
        
        // 生成报告
        const report = generateDataReport(dashboardData);
        
        // 使用打字机效果显示报告
        reportElement.innerHTML = '';
        
        // 监听模态窗口关闭事件，确保按钮状态恢复并停止打字机效果
        const modalElement = document.getElementById('aiAnalysisModal');
        let modalHiddenHandler = null;
        
        const resetButtonState = () => {
            isGeneratingReport = false;
            stopTypeWriter(); // 停止打字机效果
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = originalBtnContent;
                btn.style.opacity = '1';
                btn.style.cursor = 'pointer';
            }
        };
        
        // 设置模态窗口关闭监听器
        if (modalElement) {
            modalHiddenHandler = () => {
                resetButtonState();
                // 移除事件监听器
                if (modalElement && modalHiddenHandler) {
                    modalElement.removeEventListener('hidden.bs.modal', modalHiddenHandler);
                }
            };
            modalElement.addEventListener('hidden.bs.modal', modalHiddenHandler);
        }
        
        typeWriter(reportElement, report, 20, () => {
            console.log('报告显示完成');
            // 报告显示完成后，恢复按钮状态
            resetButtonState();
            // 移除模态窗口关闭监听器（因为已经完成了）
            if (modalElement && modalHiddenHandler) {
                modalElement.removeEventListener('hidden.bs.modal', modalHiddenHandler);
            }
        });
        
    } catch (e) {
        console.error("智能分析失败", e);
        const reportElement = document.getElementById('aiAnalysisReport');
        reportElement.innerHTML = `<div class="alert alert-danger">生成报告时发生错误：${e.message || '未知错误'}</div>`;
        
        // 出错后恢复按钮状态
        isGeneratingReport = false;
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = originalBtnContent;
            btn.style.opacity = '1';
            btn.style.cursor = 'pointer';
        }
    }
}

// 复制报告功能
function copyReport() {
    const reportText = document.getElementById('aiAnalysisReport').textContent;
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(reportText).then(() => {
            const btn = document.getElementById('copyReportBtn');
            const originalText = btn.innerHTML;
            btn.innerHTML = '<i class="fa-solid fa-check me-2"></i>已复制';
            btn.classList.remove('btn-primary');
            btn.classList.add('btn-success');
            setTimeout(() => {
                btn.innerHTML = originalText;
                btn.classList.remove('btn-success');
                btn.classList.add('btn-primary');
            }, 2000);
        }).catch(err => {
            console.error('复制失败:', err);
            alert('复制失败，请手动选择文本复制');
        });
    } else {
        // 降级方案
        const textarea = document.createElement('textarea');
        textarea.value = reportText;
        document.body.appendChild(textarea);
        textarea.select();
        try {
            document.execCommand('copy');
            const btn = document.getElementById('copyReportBtn');
            const originalText = btn.innerHTML;
            btn.innerHTML = '<i class="fa-solid fa-check me-2"></i>已复制';
            btn.classList.remove('btn-primary');
            btn.classList.add('btn-success');
            setTimeout(() => {
                btn.innerHTML = originalText;
                btn.classList.remove('btn-success');
                btn.classList.add('btn-primary');
            }, 2000);
        } catch (err) {
            alert('复制失败，请手动选择文本复制');
        }
        document.body.removeChild(textarea);
    }
}

async function loadDashColleges() {
    try {
        const r = await api('/api/org/colleges');
        console.log('Colleges API response:', r); // 调试信息

        // 处理分页数据或直接数组
        const colleges = Array.isArray(r) ? r : (r.results || []);
        console.log('Colleges data:', colleges); // 调试信息

        const s = document.getElementById('dashFilterCollege');
        if (s) {
            s.innerHTML = '<option value="">筛选学院</option>' +
                colleges.map(x => `<option value="${x.id}">${x.name}</option>`).join('');
            console.log('College select populated with', colleges.length, 'items'); // 调试信息
        } else {
            console.error('College select element not found'); // 调试信息
        }
    } catch (e) {
        console.error('Failed to load colleges:', e);
        console.error('Error details:', e.message, e.error);
    }
}

async function loadDashDepts() {
    try {
        const fc = document.getElementById('dashFilterCollege');
        const cid = (fc && fc.value) || '';
        let url = '/api/org/departments';
        if (cid) url += '?college=' + cid;

        console.log('Loading departments from:', url); // 调试信息
        const r = await api(url);
        console.log('Departments API response:', r); // 调试信息

        // 处理分页数据或直接数组
        const departments = Array.isArray(r) ? r : (r.results || []);
        console.log('Departments data:', departments); // 调试信息

        const s = document.getElementById('dashFilterDept');
        if (s) {
            const currentValue = s.value;
            s.innerHTML = '<option value="">筛选专业</option>' +
                departments.map(x => `<option value="${x.id}">${x.name}</option>`).join('');

            // Reset department selection when college changes
            if (cid) {
                s.value = '';
            }
            console.log('Department select populated with', departments.length, 'items'); // 调试信息
        } else {
            console.error('Department select element not found'); // 调试信息
        }
    } catch (e) {
        console.error('Failed to load departments:', e);
        console.error('Error details:', e.message, e.error);
    }
}

function onDashFiltersReady() {
    const fc = document.getElementById('dashFilterCollege');
    const fd = document.getElementById('dashFilterDept');

    console.log('Filter elements:', { college: !!fc, dept: !!fd }); // 调试信息

    if (fc) {
        fc.addEventListener('change', () => {
            console.log('College filter changed to:', fc.value); // 调试信息
            loadDashDepts();
            load();
        });
        console.log('College filter listener added'); // 调试信息
    } else {
        console.error('College filter element not found'); // 调试信息
    }

    if (fd) {
        fd.addEventListener('change', () => {
            console.log('Department filter changed to:', fd.value); // 调试信息
            load();
        });
        console.log('Department filter listener added'); // 调试信息
    } else {
        console.error('Department filter element not found'); // 调试信息
    }
}
