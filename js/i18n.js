/* ==========================================================================
   i18n.js — перемикач мови UA / EN
   Українська — у HTML (працює без JS і для пошуковиків). Англійська — у i18n/en.json
   (завантажується через fetch лише коли її обрано). Вибір зберігається в localStorage.
   Елементи з перекладом: data-i18n="ключ" (текст) і data-i18n-attr="attr:ключ;attr2:ключ2".
   Інші скрипти отримують переклад через window.FP.t(ключ, укр. текст)
   і слухають подію 'fp:lang', щоб перемалювати свій вміст.
   ========================================================================== */
(() => {
  'use strict';

  const STORAGE_KEY = 'fp-lang';
  const LANGS = ['uk', 'en'];
  const original = new Map(); // елемент → { text, attrs } українською (для повернення без перезавантаження)
  let dict = null;            // en.json після першого завантаження
  let lang = 'uk';

  const readStored = () => {
    try { return localStorage.getItem(STORAGE_KEY); } catch (e) { return null; }
  };
  const store = (value) => {
    try { localStorage.setItem(STORAGE_KEY, value); } catch (e) { /* приватний режим — без збереження */ }
  };

  // Запам'ятовуємо українські тексти один раз
  function snapshot() {
    document.querySelectorAll('[data-i18n], [data-i18n-attr]').forEach((el) => {
      if (original.has(el)) return;
      const attrs = {};
      (el.dataset.i18nAttr || '').split(';').filter(Boolean).forEach((pair) => {
        const [attr] = pair.split(':');
        attrs[attr] = el.getAttribute(attr);
      });
      original.set(el, { text: el.hasAttribute('data-i18n') ? el.textContent : null, attrs });
    });
  }

  async function loadDict() {
    if (dict) return dict;
    const response = await fetch('i18n/en.json', { cache: 'force-cache' });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    dict = await response.json();
    return dict;
  }

  function apply(target) {
    original.forEach((uk, el) => {
      if (uk.text !== null) {
        const key = el.dataset.i18n;
        el.textContent = target === 'en' && dict[key] ? dict[key] : uk.text; // лише textContent — без HTML-ін'єкцій
      }
      (el.dataset.i18nAttr || '').split(';').filter(Boolean).forEach((pair) => {
        const [attr, key] = pair.split(':');
        el.setAttribute(attr, target === 'en' && dict[key] ? dict[key] : uk.attrs[attr]);
      });
    });
    document.documentElement.lang = target === 'en' ? 'en' : 'uk';
    document.querySelectorAll('.lang-btn').forEach((btn) => {
      const active = btn.dataset.lang === target;
      btn.setAttribute('aria-pressed', String(active));
      btn.classList.toggle('bg-graphite', active);
      btn.classList.toggle('text-white', active);
    });
  }

  async function setLang(target, { save = true } = {}) {
    if (!LANGS.includes(target)) target = 'uk';
    snapshot();
    if (target === 'en') {
      try {
        await loadDict();
      } catch (error) {
        console.warn('[i18n] Не вдалося завантажити en.json:', error);
        target = 'uk'; // без перекладу лишаємо українську, сайт працює далі
      }
    }
    lang = target;
    apply(target);
    if (save) store(target);
    document.dispatchEvent(new CustomEvent('fp:lang', { detail: { lang } }));
  }

  // Публічний API для інших скриптів
  window.FP = {
    get lang() { return lang; },
    t: (key, ukText) => (lang === 'en' && dict && dict[key]) || ukText,
    locale: () => (lang === 'en' ? 'en-US' : 'uk-UA'),
    setLang
  };

  document.addEventListener('click', (event) => {
    const btn = event.target.closest('.lang-btn');
    if (btn) setLang(btn.dataset.lang);
  });

  // Старт: збережений вибір; інакше — англійська для браузерів не українською/російською мовою
  const stored = readStored();
  const browser = (navigator.language || 'uk').slice(0, 2);
  const initial = stored || (['uk', 'ru'].includes(browser) ? 'uk' : 'en');
  setLang(initial, { save: Boolean(stored) });
})();
