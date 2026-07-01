/* ============================================
   СЕЛО ЗОЛОТАРЕВКА — Основной JavaScript
   ============================================ */

document.addEventListener('DOMContentLoaded', function() {

  // ---------- Mobile Menu Toggle ----------
  const mobileToggle = document.querySelector('.mobile-toggle');
  const nav = document.querySelector('.nav');

  if (mobileToggle && nav) {
    mobileToggle.addEventListener('click', function() {
      nav.classList.toggle('open');
      mobileToggle.textContent = nav.classList.contains('open') ? '✕' : '☰';
    });

    // Close menu on link click (mobile)
    nav.querySelectorAll('.nav__link').forEach(link => {
      link.addEventListener('click', function(e) {
        // Don't close if it has a mega-menu (dropdown)
        const parent = this.closest('.nav__item');
        if (parent && parent.querySelector('.mega-menu')) {
          if (window.innerWidth <= 768) {
            e.preventDefault();
            parent.classList.toggle('open');
          }
        } else {
          nav.classList.remove('open');
          if (mobileToggle) mobileToggle.textContent = '☰';
        }
      });
    });
  }

  // ---------- Modal ----------
  const modalTriggers = document.querySelectorAll('[data-modal]');
  const modals = document.querySelectorAll('.modal');

  modalTriggers.forEach(trigger => {
    trigger.addEventListener('click', function() {
      const modalId = this.dataset.modal;
      const modal = document.getElementById(modalId);
      if (modal) {
        modal.classList.add('open');
        document.body.style.overflow = 'hidden';
      }
    });
  });

  modals.forEach(modal => {
    const closeBtn = modal.querySelector('.modal__close');
    if (closeBtn) {
      closeBtn.addEventListener('click', function() {
        modal.classList.remove('open');
        document.body.style.overflow = '';
      });
    }

    // Close on backdrop click
    modal.addEventListener('click', function(e) {
      if (e.target === this) {
        this.classList.remove('open');
        document.body.style.overflow = '';
      }
    });
  });

  // ---------- Match Countdown Timer ----------
  function updateCountdown() {
    const countdownEl = document.querySelector('.match-widget__countdown-number');
    if (!countdownEl) return;

    // Next match: next Saturday at 15:00
    const now = new Date();
    const nextMatch = new Date();
    nextMatch.setDate(now.getDate() + ((6 - now.getDay() + 7) % 7 || 7));
    nextMatch.setHours(15, 0, 0, 0);

    const diff = nextMatch - now;
    if (diff <= 0) return;

    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));

    countdownEl.textContent = `${days}д ${hours}ч ${minutes}м`;
  }

  updateCountdown();
  setInterval(updateCountdown, 60000);

  // ---------- Suggest News Form ----------
  const suggestForm = document.getElementById('suggestForm');
  if (suggestForm) {
    suggestForm.addEventListener('submit', function(e) {
      e.preventDefault();
      const btn = this.querySelector('.btn');
      if (btn) {
        btn.textContent = '✓ Отправлено! Спасибо!';
        btn.style.background = 'var(--color-success)';
        setTimeout(() => {
          btn.textContent = 'Отправить';
          btn.style.background = '';
          this.reset();
        }, 3000);
      }
    });
  }

  // ---------- Scroll Animation ----------
  const animateElements = document.querySelectorAll('.animate-on-scroll');

  const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
  };

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('animate');
        observer.unobserve(entry.target);
      }
    });
  }, observerOptions);

  animateElements.forEach(el => observer.observe(el));

  // ---------- Weather Widget (static demo) ----------
  const weatherWidgets = document.querySelectorAll('.weather-widget');
  weatherWidgets.forEach(widget => {
    const tempEl = widget.querySelector('.weather-widget__temp');
    const descEl = widget.querySelector('.weather-widget__desc');
    if (tempEl && descEl) {
      // Demo weather data
      const weatherData = [
        { temp: '+22°C', desc: 'Ясно, ветер 3 м/с' },
        { temp: '+20°C', desc: 'Переменная облачность' },
        { temp: '+18°C', desc: 'Небольшой дождь' }
      ];
      const data = weatherData[Math.floor(Math.random() * weatherData.length)];
      tempEl.textContent = data.temp;
      descEl.textContent = data.desc;
    }
  });

  // ---------- Gallery Lightbox (simple) ----------
  const galleryItems = document.querySelectorAll('.gallery-item');
  galleryItems.forEach(item => {
    item.addEventListener('click', function() {
      const text = this.textContent.trim() || 'Фото';
      alert(`🖼️ ${text}\n(В реальном сайте здесь откроется полноразмерное изображение)`);
    });
  });

  // ---------- Bulletin Board Tags ----------
  const bulletinItems = document.querySelectorAll('.bulletin-item');
  bulletinItems.forEach(item => {
    const tag = item.querySelector('.bulletin-item__tag');
    if (tag) {
      const text = tag.textContent.toLowerCase();
      if (text.includes('куплю')) tag.className = 'bulletin-item__tag tag-buy';
      else if (text.includes('продам')) tag.className = 'bulletin-item__tag tag-sell';
      else if (text.includes('услуги')) tag.className = 'bulletin-item__tag tag-service';
    }
  });

  // ---------- Comment Form ----------
  const commentForm = document.getElementById('commentForm');
  if (commentForm) {
    commentForm.addEventListener('submit', function(e) {
      e.preventDefault();
      const btn = this.querySelector('.btn');
      if (btn) {
        btn.textContent = '✓ На модерации';
        btn.style.background = 'var(--color-warning)';
        btn.style.color = '#000';
        setTimeout(() => {
          btn.textContent = 'Отправить';
          btn.style.background = '';
          btn.style.color = '';
          this.reset();
        }, 3000);
      }
    });
  }

  console.log('🌾 Село Золотаревка — сайт загружен!');
});
