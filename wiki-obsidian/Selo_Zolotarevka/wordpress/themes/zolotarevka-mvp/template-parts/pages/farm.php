<?php
$slug = 'farm';
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
      <a href="<?php echo esc_url(zolo_url('')); ?>">Главная</a> / <a href="<?php echo esc_url(zolo_url('')); ?>#bento">Организации</a> / Совхоз
    </div>
  </div>
</section>

<section class="content-section">
  <div class="container">

    <!-- История -->
    <h2><?php echo esc_html($c['history_title']); ?></h2>
    <?php echo wpautop(esc_html($c['history_text'])); ?>

    <!-- Гордость села -->
    <h2><?php echo esc_html($c['pride_title']); ?></h2>
    <div class="pride-grid">
      <?php foreach ($c['pride_people'] as $person): ?>
        <div class="pride-card">
          <div class="pride-card__icon"><?php echo esc_html($person['icon'] ?? '👨‍🌾'); ?></div>
          <div class="pride-card__name"><?php echo esc_html($person['name'] ?? ''); ?></div>
          <div class="pride-card__role"><?php echo esc_html($person['role'] ?? ''); ?></div>
          <div class="pride-card__desc"><?php echo esc_html($person['desc'] ?? ''); ?></div>
        </div>
      <?php endforeach; ?>
    </div>

    <!-- Продукция -->
    <h2><?php echo esc_html($c['products_title']); ?></h2>
    <div class="cards-grid">
      <?php
      $prod_q = new WP_Query([
          'post_type'      => 'farm_production',
          'posts_per_page' => (int) ($c['products_count'] ?? 10),
          'post_status'    => 'publish',
      ]);
      while ($prod_q->have_posts()) : $prod_q->the_post();
      ?>
      <div class="info-card">
        <div class="info-card__icon">🌾</div>
        <h3 class="info-card__title"><?php the_title(); ?></h3>
        <p class="info-card__text"><?php echo get_the_excerpt(); ?></p>
      </div>
      <?php endwhile; wp_reset_postdata(); ?>
    </div>

    <!-- Вакансии -->
    <h2><?php echo esc_html($c['vacancies_title']); ?></h2>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Должность</th>
            <th>Занятость</th>
            <th>Зарплата</th>
            <th>Контакты</th>
          </tr>
        </thead>
        <tbody>
          <?php
          $vac_q = new WP_Query([
              'post_type'      => 'farm_vacancies',
              'posts_per_page' => (int) ($c['vacancies_count'] ?? 10),
              'post_status'    => 'publish',
          ]);
          while ($vac_q->have_posts()) : $vac_q->the_post();
              $salary = get_post_meta(get_the_ID(), 'salary', true) ?: 'договорная';
              $phone = get_post_meta(get_the_ID(), 'phone', true) ?: '8 (999) 123-45-67';
              $employment = get_post_meta(get_the_ID(), 'employment', true) ?: 'Полная занятость';
          ?>
          <tr>
            <td><?php the_title(); ?></td>
            <td><?php echo esc_html($employment); ?></td>
            <td><?php echo esc_html($salary); ?></td>
            <td><?php echo esc_html($phone); ?></td>
          </tr>
          <?php endwhile; wp_reset_postdata(); ?>
        </tbody>
      </table>
    </div>

    <!-- Контакты -->
    <h2><?php echo esc_html($c['contacts_title']); ?></h2>
    <div class="cards-grid">
      <?php foreach ($c['contacts'] as $contact): ?>
        <div class="info-card">
          <div class="info-card__icon"><?php echo esc_html($contact['icon'] ?? '📍'); ?></div>
          <h3 class="info-card__title"><?php echo esc_html($contact['title'] ?? ''); ?></h3>
          <p class="info-card__text"><?php echo esc_html($contact['text'] ?? ''); ?></p>
        </div>
      <?php endforeach; ?>
    </div>

  </div>
</section>
