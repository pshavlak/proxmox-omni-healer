<?php
$slug = 'home';
$is_preview = isset($_GET['zolo_preview']) && $_GET['zolo_preview'] === $slug && current_user_can('zolo_edit_site_content');
$c = $is_preview ? zolo_get_page_content_draft($slug) : zolo_get_page_content($slug);
?>
<?php if ($is_preview): ?>
<div style="position:sticky;top:0;z-index:99999;background:#ffc107;color:#000;text-align:center;padding:8px;font-weight:bold;">
  👁 РЕЖИМ ПРЕДПРОСМОТРА — показан черновик главной страницы
</div>
<?php endif; ?>

<section class="hero">
  <div class="hero__bg"></div>
  <div class="hero__content">
    <h1 class="hero__title"><?php echo esc_html($c['hero_title']); ?></h1>
    <p class="hero__subtitle"><?php echo esc_html($c['hero_subtitle']); ?></p>
    <a href="<?php echo esc_attr($c['hero_btn_url']); ?>" class="hero__btn"><?php echo esc_html($c['hero_btn_text']); ?></a>
  </div>
</section>

<!-- ===== BENTO GRID (Плитки) ===== -->
<section class="bento" id="bento">
  <div class="container">
    <h2 class="bento__title"><?php echo esc_html($c['bento_section_title']); ?></h2>
    <p class="bento__subtitle"><?php echo esc_html($c['bento_section_subtitle']); ?></p>

    <div class="bento__grid">
      <?php foreach ($c['bento_cards'] as $card): ?>
        <a href="<?php echo esc_url(zolo_url($card['url'] ?? '')); ?>" class="bento__card">
          <div class="bento__card-img" style="background: <?php echo esc_attr($card['gradient'] ?? 'linear-gradient(135deg, #4a90d9, #357abd)'); ?>;">
            <?php echo esc_html($card['icon'] ?? '📄'); ?>
            <div class="overlay"></div>
          </div>
          <div class="bento__card-body">
            <h3 class="bento__card-title"><?php echo esc_html($card['title'] ?? ''); ?></h3>
            <p class="bento__card-text"><?php echo esc_html($card['text'] ?? ''); ?></p>
            <span class="bento__card-link">Перейти →</span>
          </div>
        </a>
      <?php endforeach; ?>
    </div>
  </div>
</section>

<!-- ===== MATCH WIDGET ===== -->
<?php if (!empty($c['match_active'])): ?>
<section class="match-widget">
  <div class="container">
    <div class="match-widget__info">
      <div class="match-widget__label">⚽ Следующий матч</div>
      <h2 class="match-widget__title"><?php echo esc_html($c['match_team_home']); ?> — <?php echo esc_html($c['match_team_away']); ?></h2>
      <div class="match-widget__details">
        <span>📅 <?php echo esc_html($c['match_date']); ?></span>
        <span>📍 <?php echo esc_html($c['match_location']); ?></span>
      </div>
    </div>
    <div class="match-widget__countdown">
      <div class="match-widget__countdown-number">--</div>
      <div class="match-widget__countdown-label">до начала матча</div>
    </div>
  </div>
</section>
<?php endif; ?>

<!-- ===== NEWS SECTION ===== -->
<section class="news-section">
  <div class="container">
    <div class="news-section__header">
      <h2 class="news-section__title"><?php echo esc_html($c['news_section_title']); ?></h2>
      <a href="<?php echo esc_url(zolo_url('news')); ?>" class="news-section__link"><?php echo esc_html($c['news_all_link_text']); ?></a>
    </div>

    <div class="news-grid">
      <?php
      $home_news = new WP_Query([
          'post_type'      => !empty($c['news_cpt_types']) ? $c['news_cpt_types'] : ['school_news', 'kindergarten_news', 'farm_production', 'sports_match', 'bulletin_board'],
          'posts_per_page' => (int) ($c['news_count'] ?? 3),
          'post_status'    => 'publish',
      ]);
      $cat_labels = [
          'school_news'      => '📂 Школа',
          'kindergarten_news'=> '📂 Детский сад',
          'farm_production'  => '📂 Совхоз',
          'sports_match'     => '📂 Спорт',
          'bulletin_board'   => '📂 Село',
      ];
      $icon_map = [
          'school_news'      => '🎓',
          'kindergarten_news'=> '🧸',
          'farm_production'  => '🌾',
          'sports_match'     => '⚽',
          'bulletin_board'   => '📋',
      ];
      while ($home_news->have_posts()) : $home_news->the_post();
          $pt = get_post_type();
      ?>
      <article class="news-card">
        <div class="news-card__img"><?php echo $icon_map[$pt] ?? '📰'; ?></div>
        <div class="news-card__body">
          <div class="news-card__meta">
            <span>📅 <?php echo get_the_date('j F Y'); ?></span>
            <span><?php echo $cat_labels[$pt] ?? '📂 Новости'; ?></span>
          </div>
          <h3 class="news-card__title"><?php the_title(); ?></h3>
          <p class="news-card__excerpt"><?php echo get_the_excerpt(); ?></p>
          <a href="<?php the_permalink(); ?>" class="bento__card-link">Читать далее →</a>
        </div>
      </article>
      <?php endwhile; wp_reset_postdata(); ?>
    </div>
  </div>
</section>

<!-- ===== SUGGEST NEWS ===== -->
<section class="suggest-block">
  <div class="container">
    <h2 class="suggest-block__title"><?php echo esc_html($c['suggest_title']); ?></h2>
    <p class="suggest-block__text"><?php echo esc_html($c['suggest_text']); ?></p>
    <button class="suggest-block__btn" data-modal="suggestModal"><?php echo esc_html($c['suggest_btn_text']); ?></button>
  </div>
</section>

<!-- ===== FOOTER ===== -->
