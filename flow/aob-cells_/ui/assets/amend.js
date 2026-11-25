// An amendment page: a change marked on the page image and in the list together (ui-requirements U44).
(function(){
  const on = n => { document.querySelectorAll(".on").forEach(x => x.classList.remove("on"));
    if (n == null) return; document.querySelectorAll(`[data-c="${n}"]`).forEach(x => x.classList.add("on")); };
  document.querySelectorAll("[data-c]").forEach(el => {
    el.addEventListener("mouseenter", () => on(el.dataset.c));
    el.addEventListener("mouseleave", () => on(null));
  });
  document.querySelectorAll("a.bx").forEach(a => a.addEventListener("click", e => {
    e.preventDefault(); const c = document.getElementById("c" + a.dataset.c);
    if (c){ history.replaceState(null, "", "#c" + a.dataset.c); c.scrollIntoView({block: "center", behavior: "smooth"}); on(a.dataset.c); } }));
  const h = location.hash.match(/^#c(\d+)$/); if (h) on(h[1]);
})();
