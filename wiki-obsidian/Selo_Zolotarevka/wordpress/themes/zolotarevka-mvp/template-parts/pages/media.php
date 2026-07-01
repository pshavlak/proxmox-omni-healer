<?php
$slug = 'media';
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
      <a href="<?php echo esc_url(zolo_url('')); ?>">Главная</a> / Медиа
    </div>
  </div>
</section>

<section class="content-section">
  <div class="container">

    <h2><?php echo esc_html($c['gallery_title']); ?></h2>
    <p style="margin-bottom: 24px; color: var(--color-text-light);"><?php echo esc_html($c['gallery_description']); ?></p>

    <div class="gallery-grid">
      <?php
      $photo_q = new WP_Query([
          'post_type'      => 'gallery',
          'posts_per_page' => (int) ($c['gallery_count'] ?? 12),
          'post_status'    => 'publish',
      ]);
      while ($photo_q->have_posts()) : $photo_q->the_post();
      ?>
      <div class="gallery-item">📸 <?php the_title(); ?></div>
      <?php endwhile; wp_reset_postdata(); ?>
    </div>

    <h2 style="margin-top: 48px;"><?php echo esc_html($c['video_title']); ?></h2>
    <p style="margin-bottom: 24px; color: var(--color-text-light);"><?php echo esc_html($c['video_description']); ?></p>

    <div class="cards-grid">
      <?php
      $video_q = new WP_Query([
          'post_type'      => 'gallery',
          'posts_per_page' => (int) ($c['video_count'] ?? 3),
          'post_status'    => 'publish',
          'offset'         => (int) ($c['video_offset'] ?? 12),
      ]);
      while ($video_q->have_posts()) : $video_q->the_post();
      ?>
      <div class="info-card">
        <div class="info-card__icon">🎥</div>
        <h3 class="info-card__title"><?php the_title(); ?></h3>
        <p class="info-card__text"><?php echo get_the_excerpt(); ?></p>
      </div>
      <?php endwhile; wp_reset_postdata(); ?>
    </div>

  </div>
</section>
