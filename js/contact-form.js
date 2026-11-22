/* ==========================================================================
   contact-form.js — клієнтська валідація форми заявки партнера (contacts.html)
   Два режими: «Покупець продукції» і «Інвестор, фонд або донор» — перемикач показує свій набір полів
   (неактивний fieldset вимкнений і не перевіряється). Режим можна задати посиланням ?type=investor.
   Регулярні вирази + маска телефону в міжнародному форматі. Демо: дані нікуди не надсилаються.
   Перевірка: на blur (після першого дотику), на input для вже позначених полів, повна — на submit.
   Захист від ботів: приховане поле-пастка website (honeypot).
   ========================================================================== */
(() => {
  'use strict';

  const form = document.getElementById('partnerForm');
  if (!form) return;

  const t = (key, uk) => (window.FP ? window.FP.t(key, uk) : uk);

  /* ---------- 1. Правила ---------- */
  // Літери латиниці та кирилиці (укр.), для імен і назв компаній
  const L = 'A-Za-zÀ-ÖØ-öø-ÿĀ-žА-ЩЬЮЯҐЄІЇа-щьюяґєії';
  const REGEX_COMPANY = new RegExp(`^[${L}0-9][${L}0-9 &.,'’"«»()\\-]{1,79}$`);
  const REGEX_PERSON = new RegExp(`^[${L}]+(?:['’ʼ\\- ][${L}]+)*$`);
  const REGEX_EMAIL = /^[A-Za-z0-9_%+-]+(?:\.[A-Za-z0-9_%+-]+)*@(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,24}$/;
  const REGEX_PHONE = /^\+[1-9]\d{7,14}$/;  // E.164: «+», код країни, загалом 8–15 цифр
  const REGEX_VOLUME = /^[1-9]\d{0,5}$/;    // ціле 1–999999, далі перевіряємо межу 100 000

  const MSG = {
    required: () => t('js.form.required', 'Це поле обов’язкове.'),
    company: () => t('js.form.company', 'Від 2 до 80 символів: літери, цифри, пробіли та & . , \' " ( ) -'),
    person: () => t('js.form.person', 'Мінімум 2 літери; можна апостроф, дефіс і пробіл.'),
    email: () => t('js.form.email', 'Перевірте формат: name@company.com'),
    phone: () => t('js.form.phone', 'Міжнародний формат: + код країни і 8–15 цифр, наприклад +380671234567'),
    country: () => t('js.form.country', 'Оберіть країну.'),
    volume: () => t('js.form.volume', 'Ціле число від 1 до 100 000.'),
    message: () => t('js.form.message', 'Напишіть щонайменше 10 символів або залиште поле порожнім.'),
    consent: () => t('js.form.consent', 'Підтвердьте згоду на обробку даних.'),
    org: () => t('js.form.org', 'Оберіть тип організації.'),
    fix: () => t('js.form.fix', 'Виправте позначені поля.')
  };

  // Кожне поле → функція, що повертає текст помилки або ''
  const RULES = {
    company: (v) => (!v ? MSG.required() : REGEX_COMPANY.test(v) ? '' : MSG.company()),
    person: (v) => (!v ? MSG.required() : v.length >= 2 && v.length <= 60 && REGEX_PERSON.test(v) ? '' : MSG.person()),
    position: (v) => (!v || v.length <= 60 ? '' : MSG.person()),
    country: (v) => (v ? '' : MSG.country()),
    email: (v) => (!v ? MSG.required() : v.length <= 100 && REGEX_EMAIL.test(v) ? '' : MSG.email()),
    phone: (v) => (!v ? MSG.required() : REGEX_PHONE.test(v.replace(/\s/g, '')) ? '' : MSG.phone()),
    ctype: () => '',
    orgType: (v) => (v ? '' : MSG.org()),
    budget: () => '',
    project: () => '',
    volume: (v) => (!v ? '' : REGEX_VOLUME.test(v) && Number(v) <= 100000 ? '' : MSG.volume()),
    message: (v) => (!v || (v.length >= 10 && v.length <= 1000) ? '' : MSG.message()),
    consent: (_, el) => (el.checked ? '' : MSG.consent())
  };

  const fields = Object.keys(RULES).map((name) => form.elements.namedItem(name));
  const submitBtn = document.getElementById('formSubmit');
  const dialog = document.getElementById('formDialog');
  const touchedSet = new Set();

  /* ---------- 1a. Режим форми: покупець / інвестор ---------- */
  const groups = { buyer: document.getElementById('buyerFields'), investor: document.getElementById('investorFields') };
  function applyMode() {
    const mode = form.elements.namedItem('ptype').value || 'buyer';
    Object.entries(groups).forEach(([name, box]) => {
      const active = name === mode;
      box.hidden = !active;
      box.disabled = !active;
    });
    form.dataset.mode = mode;
  }
  form.querySelectorAll('input[name="ptype"]').forEach((radio) => radio.addEventListener('change', applyMode));
  const requested = new URLSearchParams(window.location.search).get('type');
  if (requested === 'investor' || requested === 'buyer') {
    form.querySelector(`input[name="ptype"][value="${requested}"]`).checked = true;
  }
  applyMode();

  /* ---------- 2. Маска телефону ---------- */
  // Лишаємо «+» і цифри; групуємо для читабельності: +380 67 123 45 67 / +46 70 123 45 67
  function formatPhone(raw) {
    let digits = raw.replace(/[^\d]/g, '');
    if (!digits) return raw.trim().startsWith('+') ? '+' : '';
    if (raw.trim().startsWith('00')) digits = digits.slice(2);           // 0046… → +46…
    else if (/^0\d{9}$/.test(digits)) digits = `38${digits}`;            // 0671234567 → +380671234567
    digits = digits.slice(0, 15);
    const cc = digits.startsWith('380') ? 3 : digits.startsWith('1') || digits.startsWith('7') ? 1 : 2;
    const parts = [digits.slice(0, cc)];
    let rest = digits.slice(cc);
    const sizes = cc === 1 ? [3, 3, 4] : [2, 3, 2, 2, 3]; // США/Канада: +1 212 555 0100
    for (const size of sizes) { if (!rest) break; parts.push(rest.slice(0, size)); rest = rest.slice(size); }
    if (rest) parts.push(rest);
    return `+${parts.join(' ')}`;
  }

  /* ---------- 3. Показ помилок ---------- */
  function check(el) {
    if (el.matches(':disabled')) return true; // поле іншого режиму — не перевіряємо
    const value = el.type === 'checkbox' ? '' : el.value.trim();
    const error = RULES[el.name](value, el);
    const box = document.getElementById(`${el.id}Err`);
    if (box) box.textContent = error;
    el.setAttribute('aria-invalid', error ? 'true' : 'false');
    return !error;
  }

  fields.forEach((el) => {
    el.addEventListener('blur', () => { touchedSet.add(el.name); check(el); });
    el.addEventListener(el.tagName === 'SELECT' || el.type === 'checkbox' ? 'change' : 'input', () => {
      if (el.name === 'phone') {
        const caretAtEnd = el.selectionStart === el.value.length;
        const formatted = formatPhone(el.value);
        if (caretAtEnd && formatted !== el.value) el.value = formatted;
      }
      if (touchedSet.has(el.name) || el.getAttribute('aria-invalid') === 'true') check(el);
    });
  });

  // Повторно показуємо тексти помилок мовою, яку щойно обрали
  document.addEventListener('fp:lang', () => {
    fields.forEach((el) => { if (el.getAttribute('aria-invalid') === 'true') check(el); });
  });

  /* ---------- 4. Відправка (демо) ---------- */
  form.addEventListener('submit', (event) => {
    event.preventDefault();
    const phone = form.elements.namedItem('phone');
    phone.value = formatPhone(phone.value);
    const results = fields.map((el) => { touchedSet.add(el.name); return check(el); });
    if (results.includes(false)) {
      const first = fields.find((el) => el.getAttribute('aria-invalid') === 'true');
      if (first) first.focus();
      return;
    }
    if (form.elements.namedItem('website').value) return; // бот заповнив пастку — тихо ігноруємо

    submitBtn.disabled = true;
    const label = submitBtn.textContent;
    submitBtn.textContent = t('js.form.sending', 'Перевіряємо…');
    setTimeout(() => {
      submitBtn.disabled = false;
      submitBtn.textContent = label;
      form.reset();
      applyMode();
      touchedSet.clear();
      fields.forEach((el) => el.removeAttribute('aria-invalid'));
      if (dialog && typeof dialog.showModal === 'function') dialog.showModal();
      else alert(t('c.dlg.t', 'Дякуємо! Запит отримано'));
    }, 600);
  });
})();
