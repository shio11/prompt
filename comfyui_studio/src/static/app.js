const API_BASE = "/api";

function switchTab(tabName) {
  document.querySelectorAll(".tab-button").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.tab === tabName);
  });
  document.querySelectorAll(".tab-panel").forEach((panel) => {
    panel.classList.toggle("active", panel.id === `tab-${tabName}`);
  });
}

document.querySelectorAll(".tab-button").forEach((btn) => {
  btn.addEventListener("click", () => switchTab(btn.dataset.tab));
});

async function postJSON(url, body) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const detail = await response.json().catch(() => ({}));
    throw new Error(detail.detail || `リクエストに失敗しました (${response.status})`);
  }
  return response.json();
}

function renderJobResult(container, job) {
  const filesHtml = job.output_paths.length
    ? `<ul>${job.output_paths.map((p) => `<li>${p}</li>`).join("")}</ul>`
    : "";
  container.innerHTML = `
    <p>ジョブID: ${job.id}</p>
    <p>ステータス: ${job.status}</p>
    ${job.error_message ? `<p class="error">${job.error_message}</p>` : ""}
    ${filesHtml}
  `;
}

function bindGenerationForm(formId, endpoint, resultId, numberFields) {
  const form = document.getElementById(formId);
  const result = document.getElementById(resultId);
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    result.textContent = "生成中です…(ComfyUIサーバーの処理を待っています)";
    const formData = new FormData(form);
    const payload = {};
    for (const [key, value] of formData.entries()) {
      payload[key] = numberFields.includes(key) ? Number(value) : value;
    }
    try {
      const job = await postJSON(`${API_BASE}${endpoint}`, payload);
      renderJobResult(result, job);
    } catch (err) {
      result.innerHTML = `<p class="error">${err.message}</p>`;
    }
  });
}

bindGenerationForm("form-image", "/generate/image", "result-image", [
  "width",
  "height",
  "steps",
  "cfg_scale",
]);
bindGenerationForm("form-video", "/generate/video", "result-video", [
  "width",
  "height",
  "frame_count",
  "fps",
  "motion_bucket_id",
]);
bindGenerationForm("form-upscale", "/upscale", "result-upscale", []);
bindGenerationForm("form-interpolate", "/interpolate", "result-interpolate", [
  "multiplier",
]);

let chatSessionId = null;
const chatLog = document.getElementById("chat-log");
const chatForm = document.getElementById("form-chat");

function appendChatMessage(role, content) {
  const div = document.createElement("div");
  div.className = `chat-message chat-${role}`;
  div.textContent = content;
  chatLog.appendChild(div);
  chatLog.scrollTop = chatLog.scrollHeight;
}

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const input = chatForm.elements["message"];
  const message = input.value.trim();
  if (!message) return;
  appendChatMessage("user", message);
  input.value = "";
  try {
    const data = await postJSON(`${API_BASE}/chat`, {
      session_id: chatSessionId,
      message,
    });
    chatSessionId = data.session_id;
    appendChatMessage("assistant", data.reply);
  } catch (err) {
    appendChatMessage("assistant", `エラー: ${err.message}`);
  }
});
