  <?php $home_content = zolo_get_page_content('home'); ?>
  <section class="hero"<?php if (!empty($home_content['hero_image'])): ?> style="background-image:url('<?php echo esc_url($home_content['hero_image']); ?>');background-size:cover;background-position:center;"<?php endif; ?>>
    <div class="hero__bg"<?php if (!empty($home_content['hero_image'])): ?> style="opacity:0.6;"<?php endif; ?>></div>
    <div class="hero__content">
      <h1 class="hero__title"><?php echo esc_html($home_content['hero_title'] ?? 'Добро пожаловать в Золотаревку!'); ?></h1>
      <p class="hero__subtitle"><?php echo esc_html($home_content['hero_subtitle'] ?? 'Неофициальный портал нашего села. Новости, события, спорт, история и многое другое.'); ?></p>
      <a href="<?php echo esc_url($home_content['hero_btn_url'] ?? '#bento'); ?>" class="hero__btn"><?php echo esc_html($home_content['hero_btn_text'] ?? 'Исследовать разделы →'); ?></a>
    </div>
  </section>

  <!-- ===== BENTO GRID (Плитки) ===== -->
  <section class="bento" id="bento">
    <div class="container">
      <h2 class="bento__title">Наши разделы</h2>
      <p class="bento__subtitle">Быстрый доступ к ключевым разделам портала</p>

      <div class="bento__grid">
        <!-- Школа -->
        <a href="<?php echo esc_url(zolo_url('school')); ?>" class="bento__card">
          <div class="bento__card-img" style="background: linear-gradient(135deg, #4a90d9, #357abd);">
            📚
            <div class="overlay"></div>
          </div>
          <div class="bento__card-body">
            <h3 class="bento__card-title">Школа</h3>
            <p class="bento__card-text">Новости классов, расписание автобуса, достижения учеников</p>
            <span class="bento__card-link">Перейти →</span>
          </div>
        </a>

        <!-- Детский сад -->
        <a href="<?php echo esc_url(zolo_url('kindergarten')); ?>" class="bento__card">
          <div class="bento__card-img" style="background: linear-gradient(135deg, #f093fb, #f5576c);">
            🧸
            <div class="overlay"></div>
          </div>
          <div class="bento__card-body">
            <h3 class="bento__card-title">Детский сад</h3>
            <p class="bento__card-text">Жизнь групп, полезные советы, фотоотчеты с утренников</p>
            <span class="bento__card-link">Перейти →</span>
          </div>
        </a>

        <!-- Совхоз -->
        <a href="<?php echo esc_url(zolo_url('farm')); ?>" class="bento__card">
          <div class="bento__card-img" style="background: linear-gradient(135deg, #43e97b, #38f9d7);">
            🌾
            <div class="overlay"></div>
          </div>
          <div class="bento__card-body">
            <h3 class="bento__card-title">Совхоз</h3>
            <p class="bento__card-text">История предприятия, вакансии, производимая продукция</p>
            <span class="bento__card-link">Перейти →</span>
          </div>
        </a>

        <!-- Футбольная команда -->
        <a href="<?php echo esc_url(zolo_url('sports')); ?>" class="bento__card">
          <div class="bento__card-img" style="background: linear-gradient(135deg, #fa709a, #fee140);">
            ⚽
            <div class="overlay"></div>
          </div>
          <div class="bento__card-body">
            <h3 class="bento__card-title">Футбольная команда</h3>
            <p class="bento__card-text">Состав, расписание матчей, турнирная таблица, фото с игр</p>
            <span class="bento__card-link">Перейти →</span>
          </div>
        </a>

        <!-- Жизнь села -->
        <a href="<?php echo esc_url(zolo_url('village-life')); ?>" class="bento__card">
          <div class="bento__card-img" style="background: linear-gradient(135deg, #a18cd1, #fbc2eb);">
            🏘️
            <div class="overlay"></div>
          </div>
          <div class="bento__card-body">
            <h3 class="bento__card-title">Жизнь села</h3>
            <p class="bento__card-text">История, Дом Культуры, доска объявлений, выдающиеся земляки</p>
            <span class="bento__card-link">Перейти →</span>
          </div>
        </a>

        <!-- Медиа -->
        <a href="<?php echo esc_url(zolo_url('media')); ?>" class="bento__card">
          <div class="bento__card-img" style="background: linear-gradient(135deg, #ffecd2, #fcb69f);">
            📸
            <div class="overlay"></div>
          </div>
          <div class="bento__card-body">
            <h3 class="bento__card-title">Медиа</h3>
            <p class="bento__card-text">Фото- и видеогалерея села, яркие моменты из жизни</p>
            <span class="bento__card-link">Перейти →</span>
          </div>
        </a>
      </div>
    </div>
  </section>

  <!-- ===== MATCH WIDGET ===== -->
  <section class="match-widget">
    <div class="container">
      <div class="match-widget__info">
        <div class="match-widget__label">⚽ Следующий матч</div>
        <h2 class="match-widget__title">ФК «Золотаревка» — ФК «Соседи»</h2>
        <div class="match-widget__details">
          <span>📅 Суббота, 15:00</span>
          <span>📍 Стадион «Центральный»</span>
        </div>
      </div>
      <div class="match-widget__countdown">
        <div class="match-widget__countdown-number">--</div>
        <div class="match-widget__countdown-label">до начала матча</div>
      </div>
    </div>
  </section>

  <!-- ===== NEWS SECTION ===== -->
  <section class="news-section">
    <div class="container">
      <div class="news-section__header">
        <h2 class="news-section__title"><?php echo esc_html($home_content['news_section_title'] ?? '📰 Последние новости'); ?></h2>
        <a href="<?php echo esc_url(zolo_url('news')); ?>" class="news-section__link"><?php echo esc_html($home_content['news_all_link_text'] ?? 'Все новости →'); ?></a>
      </div>

      <?php
      $home_news = zolo_get_recent_content_items(['school_news', 'kindergarten_news', 'farm_production', 'sports_match', 'bulletin_board'], 3);
      if (empty($home_news)) {
          $home_news = [
              [
                  'icon' => '🏆',
                  'date' => '15 мая 2026',
                  'section' => 'Спорт',
                  'title' => 'ФК «Золотаревка» одержал победу в районном турнире',
                  'excerpt' => 'Наша команда заняла первое место в ежегодном районном турнире по футболу. Поздравляем игроков и тренера!',
                  'link' => zolo_url('news'),
              ],
              [
                  'icon' => '🎓',
                  'date' => '12 мая 2026',
                  'section' => 'Школа',
                  'title' => 'Последний звонок — 2026',
                  'excerpt' => 'В школе прошла торжественная линейка, посвященная последнему звонку для выпускников 11-го класса.',
                  'link' => zolo_url('news'),
              ],
              [
                  'icon' => '🌾',
                  'date' => '10 мая 2026',
                  'section' => 'Совхоз',
                  'title' => 'Начало посевной кампании',
                  'excerpt' => 'Совхоз «Золотаревский» приступил к весенним полевым работам. В этом году планируется засеять более 500 гектаров.',
                  'link' => zolo_url('news'),
              ],
          ];
      }
      ?>
      <div class="news-grid">
        <?php foreach ($home_news as $item): ?>
          <article class="news-card">
            <div class="news-card__img"><?php echo esc_html($item['icon'] ?? '📰'); ?></div>
            <div class="news-card__body">
              <div class="news-card__meta">
                <span>📅 <?php echo esc_html($item['date'] ?? ''); ?></span>
                <span>📂 <?php echo esc_html($item['section'] ?? 'Новости'); ?></span>
              </div>
              <h3 class="news-card__title"><?php echo esc_html($item['title'] ?? ''); ?></h3>
              <p class="news-card__excerpt"><?php echo esc_html($item['excerpt'] ?? ''); ?></p>
              <a href="<?php echo esc_url($item['link'] ?? zolo_url('news')); ?>" class="bento__card-link">Читать далее →</a>
            </div>
          </article>
        <?php endforeach; ?>
      </div>
    </div>
  </section>

  <!-- ===== SUGGEST NEWS ===== -->
  <section class="suggest-block">
    <div class="container">
      <h2 class="suggest-block__title"><?php echo esc_html($home_content['suggest_title'] ?? '💡 Хотите предложить новость?'); ?></h2>
      <p class="suggest-block__text"><?php echo esc_html($home_content['suggest_text'] ?? 'Жители села могут присылать свои фото и истории. Лучшие публикации попадут на главную!'); ?></p>
      <button class="suggest-block__btn" data-modal="suggestModal"><?php echo esc_html($home_content['suggest_btn_text'] ?? 'Предложить новость'); ?></button>
    </div>
  </section>

  <!-- ===== FOOTER ===== -->
