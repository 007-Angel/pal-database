const searchForm = document.querySelector(".search-panel");
const searchInput = document.querySelector("#site-search");
const moduleCards = [...document.querySelectorAll(".module-card")];
const noResults = document.querySelector("#no-results");

function normalize(value) {
  return value.trim().toLowerCase();
}

function filterModules(query) {
  const keyword = normalize(query);
  let visibleCount = 0;

  moduleCards.forEach((card) => {
    const haystack = normalize(`${card.textContent} ${card.dataset.search || ""}`);
    const visible = !keyword || haystack.includes(keyword);
    card.hidden = !visible;
    if (visible) visibleCount += 1;
  });

  if (noResults) {
    noResults.hidden = visibleCount !== 0;
  }
}

if (searchInput) {
  searchInput.addEventListener("input", (event) => {
    filterModules(event.target.value);
  });
}

if (searchForm) {
  searchForm.addEventListener("submit", (event) => {
    event.preventDefault();
    filterModules(searchInput?.value || "");
  });
}

const currentPath = window.location.pathname.replace(/\\/g, "/").split("/").pop() || "index.html";

document.querySelectorAll(".side-nav a").forEach((link) => {
  const linkPath = link.getAttribute("href")?.split("/").pop();
  if (linkPath === currentPath) {
    link.classList.add("active");
  } else if (currentPath !== "index.html") {
    link.classList.remove("active");
  }
});

async function hydrateCounts() {
  const countNodes = [...document.querySelectorAll("[data-count-url]")];
  await Promise.all(
    countNodes.map(async (node) => {
      try {
        const response = await fetch(node.dataset.countUrl);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        const count = Array.isArray(data.records) ? data.records.length : 0;
        node.textContent = count > 0 ? `${count} 条资料` : "暂无数据";
      } catch {
        node.textContent = "读取失败";
      }
    })
  );
}

hydrateCounts();
