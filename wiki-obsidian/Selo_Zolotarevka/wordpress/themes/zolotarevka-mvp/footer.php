<?php
if (!defined('ABSPATH')) {
    exit;
}
?>
<footer class="footer">
  <div class="container">
    <div class="footer__grid">
      <div class="footer__col">
        <h4 class="footer__col-title">🌾 Золотаревка</h4>
        <ul class="footer__links">
          <li><a href="<?php echo esc_url(zolo_url('')); ?>">Главная</a></li>
          <li><a href="<?php echo esc_url(zolo_url('news')); ?>">Новости</a></li>
          <li><a href="<?php echo esc_url(zolo_url('media')); ?>">Медиа</a></li>
        </ul>
      </div>
      <div class="footer__col">
        <h4 class="footer__col-title">Организации</h4>
        <ul class="footer__links">
          <li><a href="<?php echo esc_url(zolo_url('school')); ?>">Школа</a></li>
          <li><a href="<?php echo esc_url(zolo_url('kindergarten')); ?>">Детский сад</a></li>
          <li><a href="<?php echo esc_url(zolo_url('farm')); ?>">Совхоз</a></li>
        </ul>
      </div>
      <div class="footer__col">
        <h4 class="footer__col-title">Активности</h4>
        <ul class="footer__links">
          <li><a href="<?php echo esc_url(zolo_url('sports')); ?>">Спорт</a></li>
          <li><a href="<?php echo esc_url(zolo_url('village-life')); ?>">Жизнь села</a></li>
          <li><a href="<?php echo esc_url(zolo_url('village-life')); ?>#bulletin">Доска объявлений</a></li>
        </ul>
      </div>
      <div class="footer__col">
        <h4 class="footer__col-title">Контакты</h4>
        <ul class="footer__links">
          <li><a href="#" data-modal="suggestModal">Предложить новость</a></li>
          <li><a href="mailto:info@zolotarevka.ru">info@zolotarevka.ru</a></li>
        </ul>
      </div>
    </div>
    <div class="footer__bottom">
      <p>© 2026 Неофициальный портал села Золотаревка. Сделано с ❤️ для земляков.</p>
    </div>
  </div>
</footer>

<div class="modal" id="suggestModal">
  <div class="modal__content">
    <button class="modal__close">&times;</button>
    <h3 class="modal__title">💡 Предложить новость</h3>
    <form id="suggestForm" method="post" action="<?php echo esc_url(admin_url('admin-post.php')); ?>">
      <input type="hidden" name="action" value="zolo_submit_news">
      <?php wp_nonce_field('zolo_submit_news'); ?>
      <input type="text" name="website" value="" tabindex="-1" autocomplete="off" aria-hidden="true" style="position:absolute;left:-9999px;">
      <div class="form-group">
        <label for="suggestName">Ваше имя</label>
        <input type="text" id="suggestName" placeholder="Иван Иванов" required>
      </div>
      <div class="form-group">
        <label for="suggestEmail">Email для связи</label>
        <input type="email" id="suggestEmail" placeholder="ivan@example.com" required>
      </div>
      <div class="form-group">
        <label for="suggestCategory">Категория</label>
        <select id="suggestCategory">
          <option>Новость</option>
          <option>Событие</option>
          <option>Фото</option>
          <option>Другое</option>
        </select>
      </div>
      <div class="form-group">
        <label for="news_title">Заголовок новости</label>
        <input type="text" id="news_title" name="news_title" placeholder="Короткий заголовок" maxlength="140" required>
      </div>
      <div class="form-group">
        <label for="news_text">Текст новости</label>
        <textarea id="news_text" name="news_text" placeholder="Опишите вашу новость..." maxlength="5000" required></textarea>
      </div>
      <button type="submit" class="btn">Отправить на модерацию</button>
    </form>
  </div>
</div>

<script>
  document.addEventListener('DOMContentLoaded', function () {
    var dateNode = document.getElementById('currentDate');
    if (dateNode) {
      dateNode.textContent = new Date().toLocaleDateString('ru-RU', {
        day: 'numeric', month: 'long', year: 'numeric'
      });
    }
  });
</script>
<?php wp_footer(); ?>

<?php if (isset($_GET['submitted']) && $_GET['submitted'] === '1') : ?>
<div style="position:fixed;bottom:24px;left:50%;transform:translateX(-50%);background:var(--color-primary,#2d6a4f);color:#fff;padding:16px 32px;border-radius:12px;box-shadow:0 8px 24px rgba(0,0,0,0.2);z-index:9999;font-size:1.1rem;">
  ✓ Спасибо! Ваша новость отправлена на модерацию.
</div>
<script>
setTimeout(function() {
  var el = document.querySelector('[style*="z-index:9999"]');
  if (el) el.style.display = 'none';
}, 5000);
</script>
<?php endif; ?>
</body>
</html>
