const stateEl = document.querySelector("#state");
const countsEl = document.querySelector("#counts");
const updatedAtEl = document.querySelector("#updatedAt");
const notificationStateEl = document.querySelector("#notificationState");
const slotListEl = document.querySelector("#slotList");
const frameImageEl = document.querySelector("#frameImage");
const refreshFrameBtn = document.querySelector("#refreshFrameBtn");
const weeklySummaryEl = document.querySelector("#weeklySummary");
const weekdayListEl = document.querySelector("#weekdayList");
const hourlySummaryEl = document.querySelector("#hourlySummary");
const hourlyListEl = document.querySelector("#hourlyList");

async function fetchJson(url) {
  const response = await fetch(url);
  if (response.ok === false) {
    throw new Error(url + " 请求失败");
  }
  return response.json();
}

function renderStatus(data) {
  const stateTextMap = { available: "有空位", full: "已满", offline: "摄像头离线" };
  stateEl.textContent = stateTextMap[data.state] || data.state;
  countsEl.textContent = "空位 " + data.free_slots + " / 总数 " + data.total_slots;
  updatedAtEl.textContent = "更新时间：" + data.last_updated;
  notificationStateEl.textContent = data.notification_enabled ? "微信提醒：已开启" : "微信提醒：未配置";

  slotListEl.innerHTML = "";
  if (data.slots.length === 0) {
    slotListEl.innerHTML = '<p class="empty">当前没有可用车位配置，或者摄像头暂时离线</p>';
    return;
  }

  data.slots.forEach(function (slot) {
    const item = document.createElement("div");
    item.className = "slot-item " + (slot.occupied ? "occupied" : "free");
    item.innerHTML = '<div><strong>' + slot.name + '</strong><span>ID: ' + slot.id + '</span></div>' +
      '<div class="slot-meta"><span>' + (slot.occupied ? "占用" : "空闲") + '</span><small>置信度 ' + slot.confidence + '</small></div>';
    slotListEl.appendChild(item);
  });
}

function renderAnalytics(data) {
  const best = data.best_weekdays.length ? data.best_weekdays.join("、") : "数据不足";
  const busy = data.busiest_weekdays.length ? data.busiest_weekdays.join("、") : "数据不足";
  weeklySummaryEl.textContent = "最近样本 " + data.total_records + " 条。相对更容易有空位：" + best + "；相对更紧张：" + busy + "。";

  const bestHours = data.hourly_stats
    .filter(function (item) { return item.sample_count > 0; })
    .sort(function (a, b) { return b.avg_free_slots - a.avg_free_slots; })
    .slice(0, 3)
    .map(function (item) { return item.label; })
    .join("、") || "数据不足";
  hourlySummaryEl.textContent = "最近更容易碰到空位的时段：" + bestHours + "。";

  weekdayListEl.innerHTML = "";
  data.weekday_stats.forEach(function (item) {
    const row = document.createElement("div");
    row.className = "trend-item";
    row.innerHTML = '<strong>' + item.label + '</strong><span>平均空位 ' + item.avg_free_slots + '</span><small>有空位概率 ' + Math.round(item.availability_rate * 100) + '%</small>';
    weekdayListEl.appendChild(row);
  });

  hourlyListEl.innerHTML = "";
  data.hourly_stats
    .filter(function (item) { return item.sample_count > 0; })
    .sort(function (a, b) { return b.avg_free_slots - a.avg_free_slots; })
    .slice(0, 8)
    .forEach(function (item) {
      const row = document.createElement("div");
      row.className = "trend-item";
      row.innerHTML = '<strong>' + item.label + '</strong><span>平均空位 ' + item.avg_free_slots + '</span><small>有空位概率 ' + Math.round(item.availability_rate * 100) + '%</small>';
      hourlyListEl.appendChild(row);
    });
}

function refreshFrame() {
  frameImageEl.src = "/api/frame?t=" + Date.now();
}

async function refreshDashboard() {
  try {
    const results = await Promise.all([fetchJson("/api/status"), fetchJson("/api/analytics?days=30")]);
    renderStatus(results[0]);
    renderAnalytics(results[1]);
    refreshFrame();
  } catch (error) {
    stateEl.textContent = "服务异常";
    countsEl.textContent = "请检查后端和摄像头连接";
    updatedAtEl.textContent = error.message;
  }
}

refreshFrameBtn.addEventListener("click", refreshFrame);
refreshDashboard();
setInterval(refreshDashboard, 3000);
