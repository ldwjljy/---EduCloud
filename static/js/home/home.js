function drawPie(ctx, data, colors) { const w = ctx.canvas.width, h = ctx.canvas.height; const r = Math.min(w, h) / 2 - 20; const cx = w / 2, cy = h / 2; const sum = data.reduce((a, b) => a + b.value, 0) || 1; let a = 0; for (let i = 0; i < data.length; i++) { const ang = data[i].value / sum * 2 * Math.PI; ctx.beginPath(); ctx.moveTo(cx, cy); ctx.arc(cx, cy, r, a, a + ang); ctx.closePath(); ctx.fillStyle = colors[i % colors.length]; ctx.fill(); a += ang } }
function drawLine(ctx, years, a1, a2) { const w = ctx.canvas.width, h = ctx.canvas.height; const pad = 32; const xs = years.length; const max = Math.max(...a1, ...a2, 1); ctx.clearRect(0, 0, w, h); ctx.strokeStyle = 'rgba(255,255,255,.2)'; ctx.beginPath(); ctx.moveTo(pad, h - pad); ctx.lineTo(w - pad, h - pad); ctx.moveTo(pad, pad); ctx.lineTo(pad, h - pad); ctx.stroke(); function line(arr, color) { ctx.strokeStyle = color; ctx.beginPath(); for (let i = 0; i < xs; i++) { const x = pad + (w - 2 * pad) * (i / (xs - 1)); const y = h - pad - (h - 2 * pad) * (arr[i] / max); if (i == 0) ctx.moveTo(x, y); else ctx.lineTo(x, y) } ctx.stroke() } line(a1, '#f97316'); line(a2, '#22c55e') }
function drawBar(ctx, data) { const w = ctx.canvas.width, h = ctx.canvas.height; const pad = 20; const bh = (h - 2 * pad) / data.length; const max = Math.max(...data.map(d => d.count), 1); ctx.clearRect(0, 0, w, h); for (let i = 0; i < data.length; i++) { const y = pad + i * bh; const val = data[i].count; const len = (w - 2 * pad) * (val / max); ctx.fillStyle = '#f97316'; ctx.fillRect(pad, y, Math.max(4, len), bh - 6); ctx.fillStyle = 'rgba(255,255,255,.8)'; ctx.font = '12px system-ui'; ctx.fillText(data[i].name, pad, y - 2) } }
function drawWeekCourseBar(ctx, data) {
  const w = ctx.canvas.width, h = ctx.canvas.height;
  const pad = 40;
  const barWidth = (w - 2 * pad) / 5; // 改为5天（周一到周五）
  const max = Math.max(...data.map(d => d.value || 0), 1);
  const barHeight = h - 2 * pad;
  
  ctx.clearRect(0, 0, w, h);
  
  // 绘制坐标轴
  ctx.strokeStyle = 'rgba(255,255,255,.3)';
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(pad, pad);
  ctx.lineTo(pad, h - pad);
  ctx.lineTo(w - pad, h - pad);
  ctx.stroke();
  
  // 绘制柱状图
  const colors = ['#f97316', '#fb923c', '#fdba74', '#fbbf24', '#f59e0b', '#d97706', '#92400e'];
  for (let i = 0; i < data.length; i++) {
    const x = pad + i * barWidth + barWidth * 0.1;
    const barW = barWidth * 0.8;
    const val = data[i].value || 0;
    const barH = (val / max) * barHeight;
    const y = h - pad - barH;
    
    // 绘制柱子
    ctx.fillStyle = colors[i % colors.length];
    ctx.fillRect(x, y, barW, barH);
    
    // 绘制数值标签
    ctx.fillStyle = 'rgba(255,255,255,.9)';
    ctx.font = 'bold 11px system-ui';
    ctx.textAlign = 'center';
    ctx.fillText(val, x + barW / 2, y - 5);
    
    // 绘制星期标签
    ctx.fillStyle = 'rgba(255,255,255,.7)';
    ctx.font = '10px system-ui';
    ctx.fillText(data[i].label || '', x + barW / 2, h - pad + 15);
  }
}
let currentSelectedDay = null;
function filterEventsForDay(events, monthStr, day) { const dayStr = String(day).padStart(2, '0'); const parts = monthStr.split('-'); const year = parts[0]; const month = parts[1]; const full = `${year}-${month}-${dayStr}`; const short = `${month}-${dayStr}`; const cn = `${month}月${dayStr}日`; const slash = `${month}/${dayStr}`; const today = new Date(); const isToday = year == String(today.getFullYear()) && month == String(today.getMonth() + 1).padStart(2, '0') && dayStr == String(today.getDate()).padStart(2, '0'); return events.filter(e => { const t = e.time || ''; const matchFull = t.startsWith(full) || t.includes(full); const matchShort = t.includes(short); const matchCn = t.includes(cn); const matchSlash = t.includes(slash); const m = t.match(/\d{4}-\d{2}-\d{2}/); const matchRegex = m ? m[0] === full : false; const matchTodayWord = isToday && (t.includes('今天') || t.includes('今日') || t.includes('当天')); return matchFull || matchShort || matchCn || matchSlash || matchRegex || matchTodayWord; }) }
function formatEventTime(e) { const s = e.published_at || e.start_time || e.time || ''; const r1 = s.match(/\d{4}-\d{2}-\d{2}(?:\s+\d{2}:\d{2})?/); if (r1) return r1[0]; const r2 = s.match(/\d{1,2}[\/\-]\d{1,2}(?:\s+\d{2}:\d{2})?/); if (r2) return r2[0]; const r3 = s.match(/\d{1,2}\.\d{1,2}/); if (r3) return r3[0]; if (s.includes('今天') || s.includes('今日') || s.includes('当天')) return '今天'; return s }
function legend(el, data, colors) { el.innerHTML = data.map((d, i) => `<span><span class="dot" style="background:${colors[i % colors.length]}"></span>${d.label || Object.keys(d)[0]} ${d.value || Object.values(d)[0]}</span>`).join(' ') }
async function load() {
  try {
    const r = await api('/api/stats/dashboard');
    document.getElementById('kpiStudents').textContent = r.cards.students_total;
    document.getElementById('kpiTeachers').textContent = r.cards.teachers_total;
    document.getElementById('kpiCourses').textContent = r.cards.courses_total;

    const gp = r.grade_distribution;
    const gc = ['#10b981', '#f59e0b', '#22d3ee', '#ef4444'];
    drawPie(document.getElementById('gradePie').getContext('2d'), gp, gc);
    legend(document.getElementById('gradeLegend'), gp, gc);

    // 绘制本周课程分布柱状图
    drawWeekCourseBar(document.getElementById('weekCourseBar').getContext('2d'), r.week_course_distribution);

    const pd = Object.entries(r.teacher_position_distribution).map(([k, v]) => ({ label: k, value: v }));
    const pc = ['#22c55e', '#0ea5e9', '#f97316', '#eab308', '#64748b'];
    drawPie(document.getElementById('positionPie').getContext('2d'), pd, pc);
    legend(document.getElementById('positionLegend'), pd, pc);

    renderHotCourses(r.hot_courses_top5);
    updateTodayWeekday(r.current_week, r.today_weekday, r.semester_total_weeks);
    updateTodayTotalClasses(r.today_total_classes);



    document.getElementById('monthLabel').textContent = r.calendar.month;
    const cal = document.getElementById('cal');
    const d = new Date(r.calendar.month + '-01T00:00:00');
    const first = d.getDay();
    const days = new Date(d.getFullYear(), d.getMonth() + 1, 0).getDate();

    cal.innerHTML = '';

    for (let i = 0; i < first; i++) {
      const x = document.createElement('div');
      x.className = 'day';
      x.textContent = '';
      cal.appendChild(x);
    }

    const upcoming = r.calendar.upcoming || [];
    for (let i = 1; i <= days; i++) {
      const x = document.createElement('div');
      x.className = 'day';
      x.textContent = i;
      if (r.calendar.days_with_events.includes(i)) {
        x.classList.add('active');
      }

      // Click Event
      x.addEventListener('click', () => {
        cal.querySelectorAll('.day').forEach(d => d.classList.remove('selected'));
        x.classList.add('selected');
        currentSelectedDay = i;
        const dayEvents = filterEventsForDay(upcoming, r.calendar.month, i);
        renderEventList(dayEvents);
      });

      cal.appendChild(x);
    }
    const today = new Date();
    const parts = r.calendar.month.split('-');
    const isSameMonth = Number(parts[0]) === today.getFullYear() && Number(parts[1]) === (today.getMonth() + 1);
    const selected = currentSelectedDay || (isSameMonth ? today.getDate() : null);
    if (selected) {
      const node = Array.from(cal.querySelectorAll('.day')).find(d => d.textContent === String(selected));
      if (node) {
        cal.querySelectorAll('.day').forEach(d => d.classList.remove('selected'));
        node.classList.add('selected');
        const dayEvents = filterEventsForDay(upcoming, r.calendar.month, selected);
        renderEventList(dayEvents);
      } else {
        renderEventList(upcoming);
      }
    } else {
      renderEventList(upcoming);
    }

  } catch (e) { console.error(e); }
}

function updateTodayWeekday(currentWeek, todayWeekday, totalWeeks) {
  const weekdayEl = document.getElementById('todayWeekday');
  if (!weekdayEl) return;
  
  const weekdays = ['', '周一', '周二', '周三', '周四', '周五', '周六', '周日'];
  const weekdayName = weekdays[todayWeekday] || '未知';
  const week = currentWeek || 1;
  const total = totalWeeks || 20;
  weekdayEl.textContent = `第${week}/${total}周 ${weekdayName}`;
}

function updateTodayTotalClasses(totalClasses) {
  const totalEl = document.getElementById('todayTotalClasses');
  if (!totalEl) return;
  
  const count = totalClasses || 0;
  totalEl.textContent = `共 ${count} 节`;
}

function renderHotCourses(courses) {
  const container = document.getElementById('hotCoursesList');
  if (!container) return;
  
  if (!courses || courses.length === 0) {
    container.innerHTML = `
      <div class="d-flex flex-column align-items-center justify-content-center py-4 text-secondary opacity-50">
        <div class="small">暂无热门课程数据</div>
      </div>`;
    return;
  }

  const maxCount = Math.max(...courses.map(c => c.count || 0), 1);
  
  container.innerHTML = courses.map((course, index) => {
    const percentage = maxCount > 0 ? ((course.count || 0) / maxCount * 100).toFixed(1) : 0;
    const courseName = course.name || '未知课程';
    const courseCount = course.count || 0;
    
    return `
      <div class="hot-course-item" data-index="${index}">
        <div class="hot-course-header">
          <div class="hot-course-name">${index + 1}. ${courseName}</div>
          <div class="hot-course-count">${courseCount} 节</div>
        </div>
        <div class="hot-course-progress-container">
          <div class="hot-course-progress-bar" style="width: 0%" data-target="${percentage}">
            <span class="hot-course-progress-text">${courseName}</span>
          </div>
        </div>
      </div>
    `;
  }).join('');

  // 动画效果：延迟启动每个进度条，实现动态跟进效果
  requestAnimationFrame(() => {
    container.querySelectorAll('.hot-course-progress-bar').forEach((bar, index) => {
      setTimeout(() => {
        const targetWidth = bar.getAttribute('data-target');
        // 重置宽度以确保动画重新开始
        bar.style.width = '0%';
        // 使用 requestAnimationFrame 确保样式重置后再开始动画
        requestAnimationFrame(() => {
          bar.style.width = targetWidth + '%';
        });
      }, index * 150); // 每个进度条延迟150ms启动，形成依次展开的效果
    });
  });
}

function renderEventList(events) {
  const list = document.getElementById('eventList');
  if (!events || events.length === 0) {
    list.innerHTML = `
            <div class="d-flex flex-column align-items-center justify-content-center py-4 text-secondary opacity-50">
                <div class="small">暂无日程</div>
            </div>`;
    return;
  }
  list.innerHTML = events.map((e, i) => `
        <div class="timeline-item">
            <div class="timeline-marker"></div>
            <div class="timeline-content">
                <div class="timeline-time">${formatEventTime(e)}</div>
                <div class="timeline-title">#${i + 1} ${e.content || e.description || e.title || ''}</div>
            </div>
        </div>`).join('');
}
function resize() { document.querySelectorAll('canvas.chart').forEach(c => { c.width = c.clientWidth * 2; c.height = c.clientHeight * 2 }) }
window.addEventListener('DOMContentLoaded', () => {
  resize();
  load();
  // Auto-refresh every 20s
  setInterval(load, 20000);
}); window.addEventListener('resize', () => { resize(); load() })
