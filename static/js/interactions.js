// Weichie-style interactions & animations
document.addEventListener('DOMContentLoaded', () => {
  // --- Drawer and Cart toggles ---
  const open = (sel) => {
    const el = document.querySelector(sel);
    if (el) {
      el.classList.add('is-open');
      el.setAttribute('aria-hidden', 'false');
    }
  };

  const close = (sel) => {
    const el = document.querySelector(sel);
    if (el) {
      el.classList.remove('is-open');
      el.setAttribute('aria-hidden', 'true');
    }
  };

  // Drawer menu triggers
  document.querySelector('[data-menu-open]')?.addEventListener('click', () => open('.drawer'));
  document.querySelector('[data-menu-close]')?.addEventListener('click', () => close('.drawer'));
  document.querySelectorAll('.drawer__list a').forEach(link => {
    link.addEventListener('click', () => close('.drawer'));
  });

  // Cart drawer triggers
  document.querySelector('[data-cart-open]')?.addEventListener('click', () => open('.cart-drawer'));
  document.querySelectorAll('[data-cart-close]').forEach(btn => {
    btn.addEventListener('click', () => close('.cart-drawer'));
  });

  // Escape key closes open drawers
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      close('.drawer');
      close('.cart-drawer');
    }
  });

  // --- IntersectionObserver for Scroll Reveal ---
  const io = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.classList.add('is-visible');
        io.unobserve(e.target);
      }
    });
  }, { threshold: 0.12 });

  document.querySelectorAll('[data-reveal]').forEach(el => io.observe(el));
});
