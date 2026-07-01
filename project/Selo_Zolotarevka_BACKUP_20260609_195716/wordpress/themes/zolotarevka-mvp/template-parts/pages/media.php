  <?php $media_content = zolo_get_page_content('media'); ?>
  <section class="page-header"<?php if (!empty($media_content['page_image'])): ?> style="background:linear-gradient(rgba(0,0,0,0.5),rgba(0,0,0,0.5)),url('<?php echo esc_url($media_content['page_image']); ?>') center/cover no-repeat;"<?php endif; ?>>
    <div class="container">
      <h1 class="page-header__title"><?php echo esc_html($media_content['page_title'] ?? '📸 Медиа'); ?></h1>
      <div class="page-header__breadcrumb">
        <a href="<?php echo esc_url(zolo_url('')); ?>">Главная</a> / Медиа
      </div>
    </div>
  </section>

  <section class="content-section">
    <div class="container">

      <h2><?php echo esc_html($media_content['gallery_title'] ?? '🖼️ Фотогалерея села'); ?></h2>
      <p style="margin-bottom: 24px; color: var(--color-text-light);"><?php echo esc_html($media_content['gallery_description'] ?? 'Яркие моменты из жизни Золотаревки. Нажмите на фото для просмотра.'); ?></p>

      <div class="gallery-grid">
        <div class="gallery-item">🌅 Вид на село</div>
        <div class="gallery-item">🏫 Школа</div>
        <div class="gallery-item">🧸 Детский сад</div>
        <div class="gallery-item">🌾 Поля</div>
        <div class="gallery-item">⚽ Футбол</div>
        <div class="gallery-item">🎭 Праздник в ДК</div>
        <div class="gallery-item">🏘️ Улица села</div>
        <div class="gallery-item">🌳 Парк</div>
        <div class="gallery-item">🏆 Награждение</div>
        <div class="gallery-item">🎨 Выставка</div>
        <div class="gallery-item">🚜 Совхоз</div>
        <div class="gallery-item">❄️ Зимний пейзаж</div>
      </div>

      <h2 style="margin-top: 48px;"><?php echo esc_html($media_content['video_title'] ?? '🎬 Видеогалерея'); ?></h2>
      <p style="margin-bottom: 24px; color: var(--color-text-light);"><?php echo esc_html($media_content['video_description'] ?? 'Видеозаписи мероприятий и событий села.'); ?></p>

      <?php
      $video_cards = class_exists('Zolotarevka_MVP_Backend') ? Zolotarevka_MVP_Backend::get_video_cards() : [];
      if (empty($video_cards)) {
          $video_cards = [
              [
                  'title' => 'Концерт ко Дню Победы',
                  'description' => 'Запись праздничного концерта в Доме Культуры. 9 мая 2026.',
                  'url' => 'https://rutube.ru/video/f88bb60a24105ee9be96884c07d5d315/',
                  'embed_url' => 'https://rutube.ru/play/embed/f88bb60a24105ee9be96884c07d5d315',
              ],
              [
                  'title' => 'Футбольный матч: Золотаревка — Соседи',
                  'description' => 'Обзор лучших моментов матча. 10 мая 2026.',
                  'url' => 'https://vk.com/video_ext.php?oid=162756656&id=171388096&hash=b82cc24232fe7f9f&hd=2',
                  'embed_url' => 'https://vk.com/video_ext.php?oid=162756656&id=171388096&hash=b82cc24232fe7f9f&hd=2',
              ],
              [
                  'title' => 'Последний звонок в школе',
                  'description' => 'Торжественная линейка и праздничный концерт. 12 мая 2026.',
                  'url' => 'https://rutube.ru/video/caafe83ff1c6ed38d394635b83ece578/',
                  'embed_url' => 'https://rutube.ru/play/embed/caafe83ff1c6ed38d394635b83ece578',
              ],
          ];
      }
      ?>
      <div class="video-grid">
        <?php foreach ($video_cards as $video): ?>
          <article class="video-card">
            <div class="video-card__frame">
              <?php if (!empty($video['embed_url'])): ?>
                <iframe
                  src="<?php echo esc_url($video['embed_url']); ?>"
                  title="<?php echo esc_attr($video['title'] ?? 'Видео'); ?>"
                  loading="lazy"
                  allow="clipboard-write; autoplay; encrypted-media; picture-in-picture; fullscreen"
                  allowfullscreen></iframe>
              <?php else: ?>
                <div class="video-card__fallback">
                  <div class="video-card__fallback-icon">🎬</div>
                  <a href="<?php echo esc_url($video['url'] ?? '#'); ?>" target="_blank" rel="noopener noreferrer">Открыть видео</a>
                </div>
              <?php endif; ?>
            </div>
            <div class="video-card__body">
              <h3 class="video-card__title"><?php echo esc_html($video['title'] ?? 'Видео'); ?></h3>
              <p class="video-card__text"><?php echo esc_html($video['description'] ?? ''); ?></p>
              <?php if (!empty($video['url'])): ?>
                <a class="video-card__link" href="<?php echo esc_url($video['url']); ?>" target="_blank" rel="noopener noreferrer">Смотреть на источнике →</a>
              <?php endif; ?>
            </div>
          </article>
        <?php endforeach; ?>
      </div>

    </div>
  <!-- ===== DOCUMENTS ===== -->
  <?php
  $media_docs = $media_content['documents'] ?? [];
  if (!empty($media_docs)):
  ?>
  <section class="documents-section">
    <div class="container">
      <h2>📄 Документы</h2>
      <div class="documents-grid">
        <?php foreach ((array) $media_docs as $doc):
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
