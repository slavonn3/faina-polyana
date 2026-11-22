/* ==========================================================================
   main.js — спільна поведінка всіх сторінок
   1) мобільне меню («шторка»); 2) AOS — анімації появи блоків; 3) GLightbox — збільшення фото.
   Бібліотеки підключені з CDN (defer); якщо CDN недоступний — сайт працює без ефектів.
   ========================================================================== */
(() => {
  'use strict';

  const t = (key, uk) => (window.FP ? window.FP.t(key, uk) : uk);

  /* ---------- 1. Мобільне меню ---------- */
  const menuBtn = document.getElementById('menuBtn');
  const mobileNav = document.getElementById('mobileNav');

  function setMenu(open) {
    mobileNav.classList.toggle('hidden', !open);
    menuBtn.setAttribute('aria-expanded', String(open));
    menuBtn.setAttribute('aria-label', open ? t('js.menu.close', 'Закрити меню') : t('js.menu.open', 'Відкрити меню'));
  }

  if (menuBtn && mobileNav) {
    menuBtn.addEventListener('click', () => setMenu(mobileNav.classList.contains('hidden')));
    // Закриваємо після вибору пункту, клавішею Esc і при переході на широкий екран
    mobileNav.addEventListener('click', (event) => { if (event.target.closest('a')) setMenu(false); });
    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape' && !mobileNav.classList.contains('hidden')) { setMenu(false); menuBtn.focus(); }
    });
    window.matchMedia('(min-width: 1024px)').addEventListener('change', (mq) => { if (mq.matches) setMenu(false); });
  }

  /* ---------- 2–3. Бібліотеки з CDN ---------- */
  window.addEventListener('load', () => {
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (window.AOS) {
      window.AOS.init({ once: true, duration: 600, offset: 60, disable: reduceMotion });
    }
    if (window.GLightbox && document.querySelector('.glightbox')) {
      window.GLightbox({ selector: '.glightbox', touchNavigation: true, loop: true });
    }
  });
})();
