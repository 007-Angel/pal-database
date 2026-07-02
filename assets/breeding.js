const breedingRoot = document.querySelector("[data-breeding-url]");

function safeText(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function optionLabel(pal) {
  return `${pal.key} ${pal.name}`;
}

function populateSelect(select, pals) {
  const current = select.value;
  select.innerHTML = `<option value="">不限</option>${pals
    .map((pal) => `<option value="${safeText(pal.key)}">${safeText(optionLabel(pal))}</option>`)
    .join("")}`;
  select.value = current;
}

function renderRows(rows, total) {
  if (!rows.length) {
    return `
      <section class="data-empty">
        <div>
          <p class="eyebrow">查询结果</p>
          <h2>没有匹配组合</h2>
          <p>可以放宽父代或目标子代条件后再查。</p>
        </div>
      </section>
    `;
  }

  return `
    <section class="data-section" aria-label="配种查询结果">
      <div class="section-heading compact">
        <p class="eyebrow">查询结果</p>
        <h2>匹配 ${total} 组</h2>
      </div>
      <div class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>父代 A</th>
              <th>父代 B</th>
              <th>子代</th>
            </tr>
          </thead>
          <tbody>
            ${rows
              .map(
                (row) => `
                  <tr>
                    <td>${safeText(row.parentALabel)}</td>
                    <td>${safeText(row.parentBLabel)}</td>
                    <td>${safeText(row.childLabel)}</td>
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

function pairMatches(row, parentA, parentB) {
  if (!parentA && !parentB) return true;
  if (parentA && parentB) {
    return (
      (row.parentA === parentA && row.parentB === parentB) ||
      (row.parentA === parentB && row.parentB === parentA)
    );
  }
  const only = parentA || parentB;
  return row.parentA === only || row.parentB === only;
}

function mountBreeding(data) {
  const pals = data.pals || [];
  const pairs = data.pairs || [];

  breedingRoot.innerHTML = `
    <section class="data-hero">
      <div>
        <p class="eyebrow">配种资料</p>
        <h2>${safeText(data.title)}</h2>
        <p>${safeText(data.description)}</p>
      </div>
      <div class="data-meta">
        <span class="status-pill">帕鲁 ${pals.length} 只</span>
        <span class="status-pill">组合 ${pairs.length} 组</span>
      </div>
    </section>
    <section class="tool-panel">
      <div class="breeding-controls">
        <label>
          <span>父代 A</span>
          <select data-parent-a></select>
        </label>
        <label>
          <span>父代 B</span>
          <select data-parent-b></select>
        </label>
        <label>
          <span>目标子代</span>
          <select data-child></select>
        </label>
        <button type="button" data-reset-breeding>重置</button>
      </div>
    </section>
    <div data-breeding-results></div>
  `;

  const parentA = breedingRoot.querySelector("[data-parent-a]");
  const parentB = breedingRoot.querySelector("[data-parent-b]");
  const child = breedingRoot.querySelector("[data-child]");
  const results = breedingRoot.querySelector("[data-breeding-results]");
  const reset = breedingRoot.querySelector("[data-reset-breeding]");

  [parentA, parentB, child].forEach((select) => populateSelect(select, pals));

  function update() {
    const a = parentA.value;
    const b = parentB.value;
    const c = child.value;
    const matched = pairs.filter((row) => pairMatches(row, a, b) && (!c || row.child === c));
    results.innerHTML = renderRows(matched.slice(0, 80), matched.length);
  }

  [parentA, parentB, child].forEach((select) => select.addEventListener("change", update));
  reset.addEventListener("click", () => {
    parentA.value = "";
    parentB.value = "";
    child.value = "";
    update();
  });
  update();
}

async function initBreeding() {
  if (!breedingRoot) return;
  try {
    const response = await fetch(breedingRoot.dataset.breedingUrl);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    mountBreeding(await response.json());
  } catch (error) {
    breedingRoot.innerHTML = `
      <section class="data-empty">
        <div>
          <p class="eyebrow">加载失败</p>
          <h2>配种资料暂时无法读取</h2>
          <p>请通过本地服务器或线上地址访问本站。错误：${safeText(error.message)}</p>
        </div>
      </section>
    `;
  }
}

initBreeding();
