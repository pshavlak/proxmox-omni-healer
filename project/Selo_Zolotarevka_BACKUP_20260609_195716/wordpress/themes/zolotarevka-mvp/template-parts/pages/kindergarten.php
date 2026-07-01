  <?php $kindergarten_content = zolo_get_page_content('kindergarten'); ?>
  <section class="page-header"<?php if (!empty($kindergarten_content['page_image'])): ?> style="background:linear-gradient(rgba(0,0,0,0.5),rgba(0,0,0,0.5)),url('<?php echo esc_url($kindergarten_content['page_image']); ?>') center/cover no-repeat;"<?php endif; ?>>
    <div class="container">
      <h1 class="page-header__title"><?php echo esc_html($kindergarten_content['page_title'] ?? '🧸 Детский сад «Колосок»'); ?></h1>
      <div class="page-header__breadcrumb">
        <a href="<?php echo esc_url(zolo_url('')); ?>">Главная</a> / <a href="<?php echo esc_url(zolo_url('')); ?>#bento">Организации</a> / Детский сад
      </div>
    </div>
  </section>

  <section class="content-section">
    <div class="container">

      <h2><?php echo esc_html($kindergarten_content['news_section_title'] ?? '📰 Жизнь групп'); ?></h2>
      <?php
      $kg_news = zolo_get_recent_content_items(['kindergarten_news'], 3);
      if (empty($kg_news)) {
          $kg_news = [
              [
                  'icon' => '🌸',
                  'date' => '14 мая 2026',
                  'section' => 'Младшая группа',
                  'title' => 'Весенний утренник «Цветы для мамы»',
                  'excerpt' => 'Малыши подготовили трогательный концерт для своих мам. Было много стихов, песен и танцев!',
              ],
              [
                  'icon' => '🎨',
                  'date' => '7 мая 2026',
                  'section' => 'Средняя группа',
                  'title' => 'Занятие по рисованию «Наш двор»',
                  'excerpt' => 'Дети рисовали свой двор и дома. Лучшие работы украсили стенд в холле детского сада.',
              ],
              [
                  'icon' => '🌳',
                  'date' => '30 апреля 2026',
                  'section' => 'Старшая группа',
                  'title' => 'Экскурсия в парк',
                  'excerpt' => 'Старшая группа отправилась на прогулку в парк, где изучала первые весенние цветы и деревья.',
              ],
          ];
      }
      ?>
      <div class="news-grid">
        <?php foreach ($kg_news as $item): ?>
          <article class="news-card">
            <div class="news-card__img"><?php echo esc_html($item['icon'] ?? '🧸'); ?></div>
            <div class="news-card__body">
              <div class="news-card__meta"><span>📅 <?php echo esc_html($item['date'] ?? ''); ?></span><span>📂 <?php echo esc_html($item['section'] ?? 'Группа'); ?></span></div>
              <h3 class="news-card__title"><?php echo esc_html($item['title'] ?? ''); ?></h3>
              <p class="news-card__excerpt"><?php echo esc_html($item['excerpt'] ?? ''); ?></p>
            </div>
          </article>
        <?php endforeach; ?>
      </div>

      <h2>💡 Полезные советы родителям</h2>
      <div class="cards-grid">
        <div class="info-card">
          <div class="info-card__icon">📖</div>
          <h3 class="info-card__title">Как привить любовь к чтению</h3>
          <p class="info-card__text">Читайте вместе с ребенком каждый день по 15-20 минут. Обсуждайте прочитанное, задавайте вопросы.</p>
        </div>
        <div class="info-card">
          <div class="info-card__icon">🥗</div>
          <h3 class="info-card__title">Здоровое питание для детей</h3>
          <p class="info-card__text">Включайте в рацион больше овощей и фруктов. Ограничьте сладости и газированные напитки.</p>
        </div>
        <div class="info-card">
          <div class="info-card__icon">🎮</div>
          <h3 class="info-card__title">Развивающие игры дома</h3>
          <p class="info-card__text">Пазлы, конструкторы и настольные игры отлично развивают мелкую моторику и логическое мышление.</p>
        </div>
      </div>

      <h2><?php echo esc_html($kindergarten_content['gallery_title'] ?? '📸 Фотоотчеты'); ?></h2>
      <?php
      $kg_gallery = zolo_get_recent_content_items(['gallery'], 6);
      if (empty($kg_gallery)) {
          $kg_gallery = [
              ['icon' => '🌸', 'title' => 'Утренник'],
              ['icon' => '🎨', 'title' => 'Рисование'],
              ['icon' => '🌳', 'title' => 'Прогулка'],
              ['icon' => '🎭', 'title' => 'Театр'],
              ['icon' => '🏃', 'title' => 'Зарядка'],
              ['icon' => '🍎', 'title' => 'Обед'],
          ];
      }
      ?>
      <div class="gallery-grid">
        <?php foreach ($kg_gallery as $item): ?>
          <div class="gallery-item">
            <?php echo esc_html($item['icon'] ?? '📸'); ?> <?php echo esc_html($item['title'] ?? 'Фото'); ?>
          </div>
        <?php endforeach; ?>
      </div>

    </div>
  <!-- ===== DOCUMENTS ===== -->
  <?php
  $kindergarten_docs = $kindergarten_content['documents'] ?? [];
  if (!empty($kindergarten_docs)):
  ?>
  <section class="documents-section">
    <div class="container">
      <h2>📄 Документы</h2>
      <div class="documents-grid">
        <?php foreach ((array) $kindergarten_docs as $doc):
          if (empty($doc['file_url'])) continue;
          $doc_title = $doc['title'] ?? 'Документ';
          $doc_desc = $doc['description'] ?? '';
          $ext = strtolower(pathinfo($doc['file_url'], PATHINFO_EXTENSION));
          $icon = in_array($ext, ['pdf']) ? '📕' : (in_array($ext, ['doc', 'docx']) ? '📘' : (in_array($ext, ['xls', 'xlsx']) ? '📗' : '📄'));
        ?>
          <a href="<?php echo esc_url($doc['file_url']); ?>" class="doc-card" target="_blank" rel="noopener">
            <div class="doc-card__icon"><?php echo $icon; ?></div>
            <div class="doc-card__body">
              <strong><?php echo esc_html($doc_title); ?></strong>
              <?php if ($doc_desc): ?><p><?php echo esc_html($doc_desc); ?></p><?php endif; ?>
              <span class="doc-card__link">Скачать →</span>
            </div>
          </a>
        <?php endforeach; ?>
      </div>
    </div>
  </section>
  <?php endif; ?>

  </section>
