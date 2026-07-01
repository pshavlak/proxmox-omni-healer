<?php
$slug = 'village-life';
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
      <a href="<?php echo esc_url(zolo_url('')); ?>">Главная</a> / Жизнь села
    </div>
  </div>
</section>

<section class="content-section">
  <div class="container">

    <!-- История -->
    <h2><?php echo esc_html($c['history_title']); ?></h2>
    <?php echo wpautop(esc_html($c['history_text'])); ?>

    <!-- Выдающиеся земляки -->
    <h2><?php echo esc_html($c['residents_title']); ?></h2>
    <div class="pride-grid">
      <?php foreach ($c['notable_residents'] as $resident): ?>
        <div class="pride-card">
          <div class="pride-card__icon"><?php echo esc_html($resident['icon'] ?? '🎖️'); ?></div>
          <div class="pride-card__name"><?php echo esc_html($resident['name'] ?? ''); ?></div>
          <div class="pride-card__role"><?php echo esc_html($resident['role'] ?? ''); ?></div>
          <div class="pride-card__desc"><?php echo esc_html($resident['desc'] ?? ''); ?></div>
        </div>
      <?php endforeach; ?>
    </div>

    <!-- Дом Культуры -->
    <h2 id="culture"><?php echo esc_html($c['culture_title']); ?></h2>
    <p><?php echo esc_html($c['culture_description']); ?></p>

    <h3><?php echo esc_html($c['culture_events_title']); ?></h3>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Дата</th>
            <th>Мероприятие</th>
            <th>Время</th>
          </tr>
        </thead>
        <tbody>
          <?php foreach ($c['culture_events'] as $event): ?>
            <tr>
              <td><?php echo esc_html($event['date'] ?? ''); ?></td>
              <td><?php echo esc_html($event['event'] ?? ''); ?></td>
              <td><?php echo esc_html($event['time'] ?? ''); ?></td>
            </tr>
          <?php endforeach; ?>
        </tbody>
      </table>
    </div>

    <h3><?php echo esc_html($c['culture_circles_title']); ?></h3>
    <div class="cards-grid">
      <?php foreach ($c['culture_circles'] as $circle): ?>
        <div class="info-card">
          <div class="info-card__icon"><?php echo esc_html($circle['icon'] ?? '🎤'); ?></div>
          <h3 class="info-card__title"><?php echo esc_html($circle['title'] ?? ''); ?></h3>
          <p class="info-card__text"><?php echo esc_html($circle['text'] ?? ''); ?></p>
        </div>
      <?php endforeach; ?>
    </div>

    <!-- Доска объявлений -->
    <h2 id="bulletin"><?php echo esc_html($c['bulletin_title']); ?></h2>
    <p style="color: var(--color-text-light); margin-bottom: 16px;"><?php echo esc_html($c['bulletin_description']); ?></p>

    <?php
    $bulletin_q = new WP_Query([
        'post_type'      => 'bulletin_board',
        'posts_per_page' => (int) ($c['bulletin_count'] ?? 10),
        'post_status'    => 'publish',
    ]);
    while ($bulletin_q->have_posts()) : $bulletin_q->the_post();
        $tag = 'Продам';
        $terms = wp_get_post_terms(get_the_ID(), 'content_section');
        if (!empty($terms) && !is_wp_error($terms)) {
            $tag = $terms[0]->name;
        }
    ?>
    <div class="bulletin-item">
      <div class="bulletin-item__title"><?php the_title(); ?></div>
      <div class="bulletin-item__meta">
        <span class="bulletin-item__tag"><?php echo esc_html($tag); ?></span>
        <span>📅 <?php echo get_the_date('j F Y'); ?></span>
      </div>
      <div class="bulletin-item__text"><?php echo get_the_excerpt(); ?></div>
    </div>
    <?php endwhile; wp_reset_postdata(); ?>

  </div>
</section>
