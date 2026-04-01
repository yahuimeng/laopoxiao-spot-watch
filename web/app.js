const stateEl = document.querySelector("#state");
const countsEl = document.querySelector("#counts");
const updatedAtEl = document.querySelector("#updatedAt");
const slotListEl = document.querySelector("#slotList");
const frameImageEl = document.querySelector("#frameImage");
const refreshFrameBtn = document.querySelector("#refreshFrameBtn");

async function fetchStatus() {
  const response = await fetch("/api/status");
  if (!response.ok) {
    throw new Error("状态获取失败");
  }
  return response.json();
}

function renderStatus(data) {
  const stateTextMap = {
    available: "有空位",
    full: "已满",
    offline: "摄像头离线",
  };

  stateEl.textContent = stateTextMap[data.state] ?? data.state;
  countsEl.textContent = `空位 ${data.free_slots} / 总数 ${data.total_slots}`;
  updatedAtEl.textContent = `更新时间：${data.last_updated}`;

  slotListEl.innerHTML = "";
  if (!data.slots.length) {
    slotListEl.innerHTML = '<p class="empty">当前没有可用车位配置</p>';
    return;
  }

  data.slots.forEach((slot) => {
    const item = document.createElement("div");
    item.className = `slot-item ${slot.occupied ? "occupied" : "free"}`;
    item.innerHTML = `
      <div>
        <strong>${slot.name}</strong>
        <span>ID: ${slot.id}</span>
      </div>
      <div class="slot-meta">
        <span>${slot.occupied ? "占用" : "空闲"}</span>
        <small>置信度 ${slot.confidence}</small>
      </div>
    `;
    slotListEl.appendChild(item);
  });
}

function refreshFrame() {
  frameImageEl.src = `/api/frame?t=${Date.now()}`;
}

async function refreshDashboard() {
  try {
    const data = await fetchStatus();
    renderStatus(data);
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
