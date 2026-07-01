<?php
$slug = 'school';
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
      <a href="<?php echo esc_url(zolo_url('')); ?>">Главная</a> / <a href="<?php echo esc_url(zolo_url('')); ?>#bento">Организации</a> / Школа
    </div>
  </div>
</section>

<section class="content-section">
  <div class="container">

    <!-- Новости классов -->
    <h2><?php echo esc_html($c['news_section_title']); ?></h2>
    <div class="news-grid">
      <?php
      $school_q = new WP_Query([
          'post_type'      => 'school_news',
          'posts_per_page' => (int) ($c['news_count'] ?? 3),
          'post_status'    => 'publish',
      ]);
      while ($school_q->have_posts()) : $school_q->the_post();
      ?>
      <article class="news-card">
        <div class="news-card__img">📚</div>
        <div class="news-card__body">
          <div class="news-card__meta">
            <span>📅 <?php echo get_the_date('j F Y'); ?></span>
            <span>📂 Школьная жизнь</span>
          </div>
          <h3 class="news-card__title"><?php the_title(); ?></h3>
          <p class="news-card__excerpt"><?php echo get_the_excerpt(); ?></p>
        </div>
      </article>
      <?php endwhile; wp_reset_postdata(); ?>
    </div>

    <!-- Расписание автобуса -->
    <h2><?php echo esc_html($c['bus_schedule_title']); ?></h2>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Маршрут</th>
            <th>Утренний рейс</th>
            <th>Обратный рейс</th>
          </tr>
        </thead>
        <tbody>
          <?php foreach ($c['bus_schedule'] as $route): ?>
            <tr>
              <td><?php echo esc_html($route['route'] ?? ''); ?></td>
              <td><?php echo esc_html($route['morning'] ?? ''); ?></td>
              <td><?php echo esc_html($route['afternoon'] ?? ''); ?></td>
            </tr>
          <?php endforeach; ?>
        </tbody>
      </table>
    </div>

    <!-- Достижения учеников -->
    <h2><?php echo esc_html($c['achievements_title']); ?></h2>
    <div class="cards-grid">
      <?php foreach ($c['achievements'] as $ach): ?>
        <div class="info-card">
          <div class="info-card__icon"><?php echo esc_html($ach['icon'] ?? '🥇'); ?></div>
          <h3 class="info-card__title"><?php echo esc_html($ach['title'] ?? ''); ?></h3>
          <p class="info-card__text"><?php echo esc_html($ach['text'] ?? ''); ?></p>
        </div>
      <?php endforeach; ?>
    </div>

    <!-- Комментарии -->
    <?php if (!empty($c['comments_enabled'])): ?>
      <h2><?php echo esc_html($c['comments_title'] ?? '💬 Комментарии'); ?></h2>
      <?php comments_template(); ?>
    <?php endif; ?>
  </div>
</section>

<!-- ===== FOOTER ===== -->
