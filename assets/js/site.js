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

// Planta baixa animada do topo:
// 1) traça as linhas da planta em 2D; 2) vira 3D (paredes sobem e a câmera gira); 3) recomeça.
// Se o 3D não carregar (sem internet, navegador sem WebGL), fica só a animação 2D.
const drawing = document.querySelector(".hero-drawing");
const canvas3d = document.querySelector(".hero-3d");
const scriptUrl = document.currentScript && document.currentScript.src;
if (drawing) {
  const parts = [...drawing.querySelectorAll(".d")];
  if (matchMedia("(prefers-reduced-motion: reduce)").matches) {
    drawing.classList.add("static");
  } else {
    const step = 0.09; // segundos entre o início de cada linha
    parts.forEach((el, i) => el.style.setProperty("--d", `${(i * step).toFixed(2)}s`));
    const drawTime = (parts.length * step + 1.3) * 1000;
    let hero3d = null;

    const cycle = () => {
      drawing.classList.remove("play", "fade");
      void drawing.getBoundingClientRect(); // reinicia as animações
      drawing.classList.add("play");
      setTimeout(() => {
        if (hero3d) {
          canvas3d.classList.add("on");     // planta 3D aparece em vista de cima, por cima da 2D
          drawing.classList.add("fade");    // e a 2D some
          hero3d.play(null, () => {
            canvas3d.classList.remove("on");
            setTimeout(() => { hero3d.reset(); cycle(); }, 1000);
          });
        } else {
          setTimeout(() => drawing.classList.add("fade"), 3000);
          setTimeout(cycle, 3000 + 1300);
        }
      }, drawTime + 1500);
    };

    if (canvas3d && scriptUrl) {
      const version = new URL(scriptUrl).search;
      window.addEventListener("load", () => {
        import(new URL(`hero3d.js${version}`, scriptUrl).href)
          .then((m) => { hero3d = m.createHero3D(canvas3d); })
          .catch(() => {}); // segue só com o 2D
      });
    }
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
