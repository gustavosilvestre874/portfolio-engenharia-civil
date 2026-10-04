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

// Planta baixa animada do topo: traça as linhas em sequência, pausa, apaga e recomeça
const drawing = document.querySelector(".hero-drawing");
if (drawing) {
  const parts = [...drawing.querySelectorAll(".d")];
  if (matchMedia("(prefers-reduced-motion: reduce)").matches) {
    drawing.classList.add("static");
  } else {
    const step = 0.09; // segundos entre o início de cada linha
    parts.forEach((el, i) => el.style.setProperty("--d", `${(i * step).toFixed(2)}s`));
    const drawTime = (parts.length * step + 1.3) * 1000;
    const hold = 4500, fade = 1300;
    const cycle = () => {
      drawing.classList.remove("play", "fade");
      void drawing.getBoundingClientRect(); // reinicia as animações
      drawing.classList.add("play");
      setTimeout(() => drawing.classList.add("fade"), drawTime + hold);
      setTimeout(cycle, drawTime + hold + fade);
    };
    cycle();
  }
}

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
