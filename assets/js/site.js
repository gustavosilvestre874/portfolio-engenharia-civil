// Filtro de projetos por área (página inicial)
document.querySelectorAll(".filters").forEach((bar) => {
  const cards = document.querySelectorAll(".card[data-cat]");
  bar.addEventListener("click", (e) => {
    const btn = e.target.closest("button");
    if (!btn) return;
    bar.querySelectorAll("button").forEach((b) => b.setAttribute("aria-pressed", b === btn));
    const cat = btn.dataset.filter;
    cards.forEach((c) => (c.hidden = cat !== "todos" && c.dataset.cat !== cat));
  });
});

// Ampliar imagens (páginas de projeto)
const box = document.querySelector(".lightbox");
if (box) {
  const big = box.querySelector("img");
  const open = (src, alt) => { big.src = src; big.alt = alt || ""; box.classList.add("open"); };
  const close = () => { box.classList.remove("open"); big.src = ""; };
  document.querySelectorAll(".prose img, .cover img, .gallery img").forEach((img) =>
    img.parentElement.addEventListener("click", () => open(img.src, img.alt)));
  box.addEventListener("click", close);
  document.addEventListener("keydown", (e) => e.key === "Escape" && close());
}
