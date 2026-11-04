const bagCount = document.querySelector('.bag-count');
const menuToggle = document.querySelector('.menu-toggle');
const navLinks = document.querySelector('.nav-links');

function dismissNotice(notice) {
  if (!notice || notice.classList.contains('is-dismissing')) return;
  notice.classList.add('is-dismissing');
  window.setTimeout(() => notice.remove(), 650);
}

for (const notice of document.querySelectorAll('.site-notice')) {
  notice.querySelector('.site-notice-dismiss')?.addEventListener('click', () => dismissNotice(notice));
  window.setTimeout(() => dismissNotice(notice), 5000);
}

function readBag() {
  try {
    const items = JSON.parse(localStorage.getItem('apple-bag') || '[]');
    return Array.isArray(items) ? items.filter((item) => item && typeof item === 'object' && !Array.isArray(item)) : [];
  } catch {
    return [];
  }
}

function renderBagCount() {
  const items = readBag();
  if (bagCount) bagCount.textContent = items.reduce((total, item) => {
    const quantity = Number(item.quantity);
    return total + (Number.isSafeInteger(quantity) && quantity > 0 && quantity <= 99 ? quantity : 0);
  }, 0);
}

for (const button of document.querySelectorAll('.add-to-bag')) {
  button.addEventListener('click', () => {
    const items = readBag();
    const existing = items.find((item) => String(item.id) === button.dataset.productId);
    if (existing) existing.quantity += 1;
    else items.push({ id: Number(button.dataset.productId), name: button.dataset.product, price: Number(button.dataset.price), quantity: 1 });
    localStorage.setItem('apple-bag', JSON.stringify(items));
    renderBagCount();
    button.classList.add('added');
    window.setTimeout(() => button.classList.remove('added'), 650);
  });
}

const bagButton = document.querySelector('.bag-button');
bagButton?.addEventListener('click', () => { window.location.href = '/cart/'; });

menuToggle?.addEventListener('click', () => {
  const expanded = menuToggle.getAttribute('aria-expanded') === 'true';
  menuToggle.setAttribute('aria-expanded', String(!expanded));
  navLinks?.classList.toggle('is-open', !expanded);
});

renderBagCount();
