/* ==========================================================================
   calculator.js — «Калькулятор заробітку» на сторінці «Приймання ягід»
   Дані (ціни, надбавки за довідку, ліміти, пункти приймання) — data/data.json, завантаження через fetch.
   Також рендерить картки цін (спершу популярні ягоди, решта — за кнопкою «Показати ще»).
   Формули:
     ціна за кг        = базова ціна + (надбавка за довідку, якщо є довідка)
     отримати зараз    = ціна за кг × вага
     у кінці сезону    = зараз × (1 + memberBonusRate)   // 50% — лише для членів кооперативу
     вигода            = у кінці сезону − зараз
   Вивід — тільки через textContent. IIFE без глобальних змінних.
   ========================================================================== */
(() => {
  'use strict';

  const form = document.getElementById('calcForm');
  if (!form) return;

  const els = {
    berry: document.getElementById('calcBerry'),
    weight: document.getElementById('calcWeight'),
    cert: document.getElementById('calcCert'),
    berryErr: document.getElementById('calcBerryErr'),
    weightErr: document.getElementById('calcWeightErr'),
    formErr: document.getElementById('calcError'),
    price: document.getElementById('resPrice'),
    now: document.getElementById('resNow'),
    season: document.getElementById('resSeason'),
    gain: document.getElementById('resGain'),
    priceCards: document.getElementById('priceCards'),
    priceMore: document.getElementById('priceMore'),
    pointsMore: document.getElementById('pointsMore'),
    pointsBody: document.getElementById('pointsBody')
  };

  const t = (key, uk) => (window.FP ? window.FP.t(key, uk) : uk);
  const lang = () => (window.FP ? window.FP.lang : 'uk');
  const locale = () => (window.FP ? window.FP.locale() : 'uk-UA');

  // Число: «12,5», «12.5», « 12 » → 12.5; порожньо → null; сміття → NaN
  const REGEX_WEIGHT = /^\d{1,4}(?:[.,]\d{1,2})?$/;
  let data = null;
  let touched = false;     // показуємо помилки лише після першої взаємодії
  let showAll = false;     // «Показати ще» для менш популярних ягід

  let showAllPoints = false; // «Показати всі пункти»
  const POINTS_PREVIEW = 6;

  const money = (value) => `${Math.round(value).toLocaleString(locale())} ${t('js.calc.uah', 'грн')}`;
  const perKg = (value) => `${value.toLocaleString(locale())} ${t('js.calc.perKg', 'грн/кг')}`;
  const berryName = (b) => (lang() === 'en' ? b.en : b.uk);

  function cell(row, text, cls) {
    const td = document.createElement('td');
    td.textContent = text;
    if (cls) td.className = cls;
    row.appendChild(td);
    return td;
  }

  /* ---------- Рендер таблиць і списку ягід ---------- */
  function el(tag, cls, text) {
    const node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  // Картка ягоди: іконка, назва, ціна, ціна з довідкою, «Розрахувати» (обирає ягоду в калькуляторі).
  // Колір ягоди (data.json → color) іде в CSS-змінну --berry: верхня смуга картки й підсвічування при наведенні.
  function priceCard(b) {
    const card = el('article', 'card berry-card p-6 flex flex-col');
    card.style.setProperty('--berry', b.color);
    const head = el('div', 'flex items-center gap-4 mb-4');
    const icon = el('img', 'h-14 w-14 shrink-0 transition-transform duration-300');
    icon.src = b.icon; icon.alt = ''; icon.width = 56; icon.height = 56; icon.loading = 'lazy'; icon.decoding = 'async';
    const title = el('div', 'min-w-0');
    title.append(el('h3', 'font-slab font-bold text-xl', berryName(b)));
    head.append(icon, title);
    const price = el('p', 'font-slab font-bold text-4xl text-graphite');
    price.append(document.createTextNode(b.price.toLocaleString(locale())), el('span', 'text-base font-normal text-muted', ` ${t('js.calc.perKg', 'грн/кг')}`));
    const cert = el('p', 'mt-2 text-body');
    cert.append(document.createTextNode(`${t('js.prices.withCert', 'З довідкою про дохід')}: `), el('b', 'text-leafdk', perKg(b.price + b.certBonus)));
    const btn = el('button', 'mt-5 self-start font-bold text-berrydk hover:text-berrytx underline underline-offset-4', `${t('js.prices.calc', 'Розрахувати')} →`);
    btn.type = 'button';
    btn.addEventListener('click', () => {
      els.berry.value = b.id;
      calculate();
      document.getElementById('calc').scrollIntoView({ behavior: 'smooth', block: 'start' });
      els.weight.focus({ preventScroll: true });
    });
    card.append(head, price, cert, btn);
    return card;
  }

  function renderPrices() {
    const popular = data.berries.filter((b) => b.popular);
    const rest = data.berries.filter((b) => !b.popular);
    els.priceCards.replaceChildren(...(showAll ? data.berries : popular).map(priceCard));
    if (rest.length) {
      els.priceMore.classList.remove('hidden');
      els.priceMore.setAttribute('aria-expanded', String(showAll));
      els.priceMore.textContent = showAll
        ? t('js.prices.less', 'Згорнути асортимент')
        : `${t('js.prices.more', 'Показати повний асортимент')} (+${rest.length})`;
    }
  }

  function renderPoints() {
    if (!els.pointsBody) return;
    const list = showAllPoints ? data.points : data.points.slice(0, POINTS_PREVIEW);
    els.pointsBody.replaceChildren(...list.map((p) => {
      const tr = document.createElement('tr');
      cell(tr, lang() === 'en' ? p.en : p.uk, 'font-medium');
      cell(tr, lang() === 'en' ? p.addressEn : p.addressUk);
      cell(tr, p.hours, 'whitespace-nowrap');
      cell(tr, p.phone, 'whitespace-nowrap');
      return tr;
    }));
    if (els.pointsMore && data.points.length > POINTS_PREVIEW) {
      els.pointsMore.classList.remove('hidden');
      els.pointsMore.setAttribute('aria-expanded', String(showAllPoints));
      els.pointsMore.textContent = showAllPoints
        ? t('js.points.less', 'Згорнути список')
        : `${t('js.points.more', 'Показати всі пункти')} (${data.points.length})`;
    }
  }

  function renderOptions() {
    const selected = els.berry.value;
    const placeholder = els.berry.options[0]; // «Оберіть ягоду» перекладає i18n.js
    els.berry.replaceChildren(placeholder, ...data.berries.map((b) => {
      const opt = document.createElement('option');
      opt.value = b.id;
      opt.textContent = `${berryName(b)} — ${perKg(b.price)}`;
      return opt;
    }));
    els.berry.value = selected;
  }

  /* ---------- Валідація ---------- */
  function readWeight() {
    const raw = els.weight.value.trim();
    if (raw === '') return { error: t('js.calc.errEmpty', 'Вкажіть вагу в кілограмах.') };
    if (!REGEX_WEIGHT.test(raw)) return { error: t('js.calc.errNaN', 'Вага має бути числом, наприклад 12,5') };
    const kg = Number(raw.replace(',', '.'));
    if (kg < data.meta.minKg) return { error: t('js.calc.errMin', 'Вкажіть вагу щонайменше 1 кг.') };
    if (kg > data.meta.maxKg) return { error: t('js.calc.errMax', 'За один раз приймаємо до 500 кг. Для більших партій зателефонуйте нам.') };
    return { kg };
  }

  function showError(input, box, message) {
    box.textContent = message || '';
    input.setAttribute('aria-invalid', message ? 'true' : 'false');
  }

  function clearResult() {
    [els.price, els.now, els.season, els.gain].forEach((el) => { el.textContent = '—'; });
  }

  /* ---------- Розрахунок ---------- */
  function calculate() {
    if (!data) return;
    const berry = data.berries.find((b) => b.id === els.berry.value);
    const weight = readWeight();

    if (touched) {
      showError(els.berry, els.berryErr, berry ? '' : t('js.calc.errBerry', 'Оберіть ягоду зі списку.'));
      showError(els.weight, els.weightErr, weight.error || '');
    }
    if (!berry || weight.error) { clearResult(); return; }

    const price = berry.price + (els.cert.checked ? berry.certBonus : 0);
    const now = price * weight.kg;
    const season = now * (1 + data.meta.memberBonusRate);

    els.price.textContent = perKg(price);
    els.now.textContent = money(now);
    els.season.textContent = money(season);
    els.gain.textContent = `+${money(season - now)}`;
  }

  /* ---------- Події ---------- */
  form.addEventListener('submit', (event) => {
    event.preventDefault();
    touched = true;
    calculate();
    const firstInvalid = form.querySelector('[aria-invalid="true"]');
    if (firstInvalid) firstInvalid.focus();
  });
  ['input', 'change'].forEach((type) => form.addEventListener(type, (event) => {
    if (event.type === 'change' || event.target === els.weight) touched = touched || event.target.value !== '';
    calculate();
  }));
  els.priceMore.addEventListener('click', () => { showAll = !showAll; renderPrices(); });
  if (els.pointsMore) els.pointsMore.addEventListener('click', () => { showAllPoints = !showAllPoints; renderPoints(); });
  document.addEventListener('fp:lang', () => {
    if (!data) return;
    renderPrices(); renderPoints(); renderOptions(); calculate();
  });

  /* ---------- Завантаження даних ---------- */
  async function init() {
    try {
      const response = await fetch('data/data.json', { cache: 'no-cache' });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      data = await response.json();
      if (!Array.isArray(data.berries) || !data.berries.length) throw new Error('Порожній список ягід');
      renderPrices(); renderPoints(); renderOptions();
    } catch (error) {
      console.error('[calculator] Помилка завантаження даних:', error);
      const msg = t('js.calc.errLoad', 'Не вдалося завантажити ціни. Спробуйте оновити сторінку.');
      els.formErr.textContent = msg;
      els.priceCards.replaceChildren(el('p', 'text-dangerText', msg));
      if (els.pointsBody) {
        const tr = document.createElement('tr');
        cell(tr, msg, 'text-dangerText').colSpan = 4;
        els.pointsBody.replaceChildren(tr);
      }
      form.querySelectorAll('input, select, button').forEach((el) => { el.disabled = true; });
    }
  }

  init();
})();
