const datasetMounts = [...document.querySelectorAll("[data-data-url]")];

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function renderSources(sources = []) {
  if (!sources.length) return "";

  return `
    <div class="source-strip" aria-label="资料来源">
      ${sources
        .map((source) => `<a href="${escapeHtml(source.url)}" target="_blank" rel="noreferrer">${escapeHtml(source.label)}</a>`)
        .join("")}
    </div>
  `;
}

function renderTable(data) {
  const columns = data.columns || [];
  const records = data.records || [];

  if (!columns.length) return "";

  if (!records.length) {
    return `
      <section class="data-empty" aria-label="空资料表">
        <div>
          <p class="eyebrow">资料表</p>
          <h2>${escapeHtml(data.title)}</h2>
          <p>当前栏目正在整理公开资料。</p>
          <div class="field-list">
            ${columns.map((column) => `<span>${escapeHtml(column.label)}</span>`).join("")}
          </div>
        </div>
      </section>
    `;
  }

  return `
    <section class="data-section" aria-label="${escapeHtml(data.title)}表格">
      <div class="table-tools">
        <label>
          <span>筛选</span>
          <input type="search" placeholder="输入关键词..." data-table-search>
        </label>
      </div>
      <div class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>${columns.map((column) => `<th>${escapeHtml(column.label)}</th>`).join("")}</tr>
          </thead>
          <tbody>
            ${records
              .map(
                (record) => `
                  <tr>
                    ${columns.map((column) => `<td>${escapeHtml(record[column.key] || "")}</td>`).join("")}
                  </tr>
                `
              )
              .join("")}
          </tbody>
        </table>
      </div>
    </section>
  `;
}

function bindTableSearch(mount) {
  const input = mount.querySelector("[data-table-search]");
  const rows = [...mount.querySelectorAll(".data-table tbody tr")];

  if (!input || !rows.length) return;

  input.addEventListener("input", () => {
    const keyword = input.value.trim().toLowerCase();
    rows.forEach((row) => {
      row.hidden = keyword && !row.textContent.toLowerCase().includes(keyword);
    });
  });
}

function renderDataset(mount, data) {
  const recordCount = Array.isArray(data.records) ? data.records.length : 0;
  mount.innerHTML = `
    <section class="data-hero">
      <div>
        <p class="eyebrow">资料库</p>
        <h2>${escapeHtml(data.title)}</h2>
        <p>${escapeHtml(data.description || "")}</p>
      </div>
      <div class="data-meta">
        <span class="status-pill">资料 ${recordCount} 条</span>
        <span class="status-pill">更新：${escapeHtml(data.lastVerified || "")}</span>
      </div>
    </section>
    ${renderTable(data)}
    ${renderSources(data.sources)}
  `;
  bindTableSearch(mount);
}

async function mountDatasets() {
  await Promise.all(
    datasetMounts.map(async (mount) => {
      const url = mount.dataset.dataUrl;
      try {
        const response = await fetch(url);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        renderDataset(mount, await response.json());
      } catch (error) {
        mount.innerHTML = `
          <section class="data-empty">
            <div>
              <p class="eyebrow">加载失败</p>
              <h2>资料文件暂时无法读取</h2>
              <p>请通过本地服务器或线上地址访问本站。错误：${escapeHtml(error.message)}</p>
            </div>
          </section>
        `;
      }
    })
  );
}

mountDatasets();
