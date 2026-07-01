  <?php $news_content = zolo_get_page_content('news'); ?>
  <section class="page-header"<?php if (!empty($news_content['page_image'])): ?> style="background:linear-gradient(rgba(0,0,0,0.5),rgba(0,0,0,0.5)),url('<?php echo esc_url($news_content['page_image']); ?>') center/cover no-repeat;"<?php endif; ?>>
    <div class="container">
      <h1 class="page-header__title"><?php echo esc_html($news_content['page_title'] ?? '📰 Новости села'); ?></h1>
      <div class="page-header__breadcrumb">
        <a href="<?php echo esc_url(zolo_url('')); ?>">Главная</a> / Новости
      </div>
    </div>
  </section>

  <section class="content-section">
    <div class="container">

      <!-- Фильтр по категориям -->
      <div style="display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 32px;">
        <span style="font-weight: 600; padding: 8px 0;">Категории:</span>
        <a href="<?php echo esc_url(zolo_url('news')); ?>" style="padding: 6px 16px; background: var(--color-primary); color: white; border-radius: 20px; font-size: 0.9rem;">Все</a>
        <a href="?cat=school" style="padding: 6px 16px; background: var(--color-bg-alt); border-radius: 20px; font-size: 0.9rem;">📚 Школа</a>
        <a href="?cat=kindergarten" style="padding: 6px 16px; background: var(--color-bg-alt); border-radius: 20px; font-size: 0.9rem;">🧸 Детский сад</a>
        <a href="?cat=farm" style="padding: 6px 16px; background: var(--color-bg-alt); border-radius: 20px; font-size: 0.9rem;">🌾 Совхоз</a>
        <a href="?cat=sports" style="padding: 6px 16px; background: var(--color-bg-alt); border-radius: 20px; font-size: 0.9rem;">⚽ Спорт</a>
        <a href="?cat=village" style="padding: 6px 16px; background: var(--color-bg-alt); border-radius: 20px; font-size: 0.9rem;">🏘️ Село</a>
      </div>

      <!-- Лента новостей -->
      <?php
      $news_items = zolo_get_recent_content_items(['school_news', 'kindergarten_news', 'farm_production', 'sports_match', 'bulletin_board'], 9);
      if (empty($news_items)) {
          $news_items = [
              ['icon' => '🏆', 'date' => '15 мая 2026', 'section' => 'Спорт', 'title' => 'ФК «Золотаревка» одержал победу в районном турнире', 'excerpt' => 'Наша команда заняла первое место в ежегодном районном турнире по футболу. Поздравляем игроков и тренера!', 'link' => '#'],
              ['icon' => '🎓', 'date' => '12 мая 2026', 'section' => 'Школа', 'title' => 'Последний звонок — 2026', 'excerpt' => 'В школе прошла торжественная линейка, посвященная последнему звонку для выпускников 11-го класса.', 'link' => '#'],
              ['icon' => '🌾', 'date' => '10 мая 2026', 'section' => 'Совхоз', 'title' => 'Начало посевной кампании', 'excerpt' => 'Совхоз «Золотаревский» приступил к весенним полевым работам. В этом году планируется засеять более 500 гектаров зерновыми культурами.', 'link' => '#'],
              ['icon' => '🎭', 'date' => '9 мая 2026', 'section' => 'Село', 'title' => 'Праздничный концерт ко Дню Победы', 'excerpt' => 'В Доме Культуры прошел праздничный концерт, посвященный 81-й годовщине Победы в Великой Отечественной войне.', 'link' => '#'],
              ['icon' => '🧸', 'date' => '5 мая 2026', 'section' => 'Детский сад', 'title' => 'Весенний утренник в детском саду', 'excerpt' => 'Малыши из младшей группы порадовали родителей весенним концертом «Цветы для мамы».', 'link' => '#'],
              ['icon' => '🏅', 'date' => '2 мая 2026', 'section' => 'Школа', 'title' => 'Победа на районной олимпиаде', 'excerpt' => 'Ученик 9-го класса Иван Петров занял 1-е место на районной олимпиаде по математике. Поздравляем!', 'link' => '#'],
              ['icon' => '🚜', 'date' => '28 апреля 2026', 'section' => 'Совхоз', 'title' => 'Обновление парка техники', 'excerpt' => 'Совхоз приобрел новый трактор и сеялку. Это позволит увеличить производительность и сократить сроки посевной.', 'link' => '#'],
              ['icon' => '🎨', 'date' => '25 апреля 2026', 'section' => 'Село', 'title' => 'Субботник в Золотаревке', 'excerpt' => 'Жители села вышли на весенний субботник. Были очищены улицы, парк и пришкольная территория.', 'link' => '#'],
          ];
      }
      ?>
      <div class="news-grid">
        <?php foreach ($news_items as $item): ?>
          <article class="news-card">
            <div class="news-card__img"><?php echo esc_html($item['icon'] ?? '📰'); ?></div>
            <div class="news-card__body">
              <div class="news-card__meta">
                <span>📅 <?php echo esc_html($item['date'] ?? ''); ?></span>
                <span>📂 <?php echo esc_html($item['section'] ?? 'Новости'); ?></span>
              </div>
              <h3 class="news-card__title"><?php echo esc_html($item['title'] ?? ''); ?></h3>
              <p class="news-card__excerpt"><?php echo esc_html($item['excerpt'] ?? ''); ?></p>
              <a href="<?php echo esc_url($item['link'] ?? '#'); ?>" class="bento__card-link">Читать далее →</a>
            </div>
          </article>
        <?php endforeach; ?>
      </div>

      <!-- Пагинация -->
      <div style="display: flex; justify-content: center; gap: 8px; margin-top: 40px;">
        <span style="padding: 10px 18px; background: var(--color-primary); color: white; border-radius: var(--radius-sm); font-weight: 600;">1</span>
        <a href="#" style="padding: 10px 18px; background: var(--color-white); border-radius: var(--radius-sm); font-weight: 600; box-shadow: var(--shadow-sm);">2</a>
        <a href="#" style="padding: 10px 18px; background: var(--color-white); border-radius: var(--radius-sm); font-weight: 600; box-shadow: var(--shadow-sm);">3</a>
      </div>

    </div>
  </section>

  <!-- ===== SUGGEST NEWS ===== -->
  <section class="suggest-block">
    <div class="container">
      <h2 class="suggest-block__title"><?php echo esc_html($news_content['suggest_title'] ?? '💡 Хотите предложить новость?'); ?></h2>
      <p class="suggest-block__text"><?php echo esc_html($news_content['suggest_text'] ?? 'Жители села могут присылать свои фото и истории. Лучшие публикации попадут на главную!'); ?></p>
      <button class="suggest-block__btn" data-modal="suggestModal"><?php echo esc_html($news_content['suggest_btn_text'] ?? 'Предложить новость'); ?></button>
    </div>
  </section>
