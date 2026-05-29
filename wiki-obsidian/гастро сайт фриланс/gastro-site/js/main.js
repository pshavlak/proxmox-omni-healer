/**
 * Гастро-лендинг — Основной JavaScript
 */

document.addEventListener('DOMContentLoaded', () => {

  // ===== Бургер-меню =====
  const burger = document.querySelector('.burger');
  const navMenu = document.querySelector('.nav-menu');

  if (burger && navMenu) {
    burger.addEventListener('click', () => {
      navMenu.classList.toggle('open');
      burger.innerHTML = navMenu.classList.contains('open')
        ? '<i class="fas fa-times"></i>'
        : '<i class="fas fa-bars"></i>';
    });

    // Закрыть меню при клике вне его
    document.addEventListener('click', (e) => {
      if (!e.target.closest('.header .container')) {
        navMenu.classList.remove('open');
        burger.innerHTML = '<i class="fas fa-bars"></i>';
      }
    });

    // Закрыть меню при выборе пункта
    navMenu.querySelectorAll('a').forEach(link => {
      link.addEventListener('click', () => {
        navMenu.classList.remove('open');
        burger.innerHTML = '<i class="fas fa-bars"></i>';
      });
    });
  }

  // ===== Лайтбокс для дипломов =====
  const lightbox = document.getElementById('lightbox');
  const lightboxImg = document.getElementById('lightbox-img');

  if (lightbox && lightboxImg) {
    document.querySelectorAll('.diploma-gallery a').forEach(link => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        lightboxImg.src = link.getAttribute('href');
        lightbox.classList.add('active');
      });
    });

    lightbox.addEventListener('click', () => {
      lightbox.classList.remove('active');
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') lightbox.classList.remove('active');
    });
  }

  // ===== Форма записи: скролл к форме при клике на «Заказать» / «Записаться» =====
  document.querySelectorAll('.btn-order, .scroll-to-form').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const form = document.getElementById('booking-form');
      if (form) {
        const serviceSelect = form.querySelector('select[name="service"]');
        if (serviceSelect && btn.dataset.service) {
          serviceSelect.value = btn.dataset.service;
        }
        form.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });

  // ===== Отправка формы (имитация / заглушка) =====
  const bookingForm = document.getElementById('booking-form');
  if (bookingForm) {
    bookingForm.addEventListener('submit', async (e) => {
      e.preventDefault();

      // Honeypot
      const honey = bookingForm.querySelector('input[name="_honey"]');
      if (honey && honey.value) return;

      const formData = new FormData(bookingForm);
      const btn = bookingForm.querySelector('button[type="submit"]');
      const originalText = btn.innerHTML;

      try {
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Отправка...';
        btn.disabled = true;

        const response = await fetch('send-form.php', {
          method: 'POST',
          body: formData
        });

        const result = await response.json();

        if (result.success) {
          bookingForm.style.display = 'none';
          document.querySelector('.form-success').style.display = 'block';
        } else {
          alert('Ошибка при отправке. Попробуйте позже или напишите в Telegram.');
        }
      } catch {
        // Если PHP нет, показываем успех (демо-режим)
        bookingForm.style.display = 'none';
        document.querySelector('.form-success').style.display = 'block';
      } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
      }
    });
  }

  // ===== Анимация появления при скролле =====
  const observerOptions = { threshold: 0.1, rootMargin: '0px 0px -50px 0px' };

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.style.opacity = '1';
        entry.target.style.transform = 'translateY(0)';
        observer.unobserve(entry.target);
      }
    });
  }, observerOptions);

  document.querySelectorAll('.service-card, .testimonial-card, .step-card, .stat-card').forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(20px)';
    el.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
    observer.observe(el);
  });
});
