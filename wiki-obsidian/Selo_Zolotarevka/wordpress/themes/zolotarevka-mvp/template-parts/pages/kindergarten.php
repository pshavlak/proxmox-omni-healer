<?php
$slug = 'kindergarten';
$is_preview = isset($_GET['zolo_preview']) && $_GET['zolo_preview'] === $slug && current_user_can('zolo_edit_site_content');
$c = $is_preview ? zolo_get_page_content_draft($slug) : zolo_get_page_content($slug);
?>
<?php if ($is_preview): ?>
<div style="position:sticky;top:0;z-index:99999;background:#ffc107;color:#000;text-align:center;padding:8px;font-weight:bold;">
  👁 РЕЖИМ ПРЕДПРОСМОТРА — показан черновик
</div>
<?php endif; ?>

<section class="page-header">
  <div class="container">
    <h1 class="page-header__title"><?php echo esc_html($c['page_title']); ?></h1>
    <div class="page-header__breadcrumb">
      <a href="<?php echo esc_url(zolo_url('')); ?>">Главная</a> / <a href="<?php echo esc_url(zolo_url('')); ?>#bento">Организации</a> / Детский сад
    </div>
  </div>
</section>

<section class="content-section">
  <div class="container">

    <h2><?php echo esc_html($c['news_section_title']); ?></h2>
    <div class="news-grid">
      <?php
      $kg_q = new WP_Query([
          'post_type'      => 'kindergarten_news',
          'posts_per_page' => (int) ($c['news_count'] ?? 3),
          'post_status'    => 'publish',
      ]);
      while ($kg_q->have_posts()) : $kg_q->the_post();
      ?>
      <article class="news-card">
        <div class="news-card__img">🧸</div>
        <div class="news-card__body">
          <div class="news-card__meta"><span>📅 <?php echo get_the_date('j F Y'); ?></span><span>📂 Группа</span></div>
          <h3 class="news-card__title"><?php the_title(); ?></h3>
          <p class="news-card__excerpt"><?php echo get_the_excerpt(); ?></p>
        </div>
      </article>
      <?php endwhile; wp_reset_postdata(); ?>
    </div>

    <h2><?php echo esc_html($c['parenting_tips_title']); ?></h2>
    <div class="cards-grid">
      <?php foreach ($c['parenting_tips'] as $tip): ?>
        <div class="info-card">
          <div class="info-card__icon"><?php echo esc_html($tip['icon'] ?? '📖'); ?></div>
          <h3 class="info-card__title"><?php echo esc_html($tip['title'] ?? ''); ?></h3>
          <p class="info-card__text"><?php echo esc_html($tip['text'] ?? ''); ?></p>
        </div>
      <?php endforeach; ?>
    </div>

    <h2><?php echo esc_html($c['gallery_title']); ?></h2>
    <div class="gallery-grid">
      <?php
      $kg_gallery = new WP_Query([
          'post_type'      => 'gallery',
          'posts_per_page' => (int) ($c['gallery_count'] ?? 6),
          'post_status'    => 'publish',
      ]);
      while ($kg_gallery->have_posts()) : $kg_gallery->the_post();
      ?>
      <div class="gallery-item">📸 <?php the_title(); ?></div>
      <?php endwhile; wp_reset_postdata(); ?>
    </div>

  </div>
</section>
