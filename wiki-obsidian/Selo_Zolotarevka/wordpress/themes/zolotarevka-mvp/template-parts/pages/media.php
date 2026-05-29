  <section class="page-header">
    <div class="container">
      <h1 class="page-header__title">📸 Медиа</h1>
      <div class="page-header__breadcrumb">
        <a href="<?php echo esc_url(zolo_url('')); ?>">Главная</a> / Медиа
      </div>
    </div>
  </section>

  <section class="content-section">
    <div class="container">

      <h2>🖼️ Фотогалерея села</h2>
      <p style="margin-bottom: 24px; color: var(--color-text-light);">Яркие моменты из жизни Золотаревки. Нажмите на фото для просмотра.</p>

      <div class="gallery-grid">
        <?php
        $photo_q = new WP_Query([
            'post_type'      => 'gallery',
            'posts_per_page' => 12,
            'post_status'    => 'publish',
        ]);
        while ($photo_q->have_posts()) : $photo_q->the_post();
        ?>
        <div class="gallery-item">📸 <?php the_title(); ?></div>
        <?php endwhile; wp_reset_postdata(); ?>
      </div>

      <h2 style="margin-top: 48px;">🎬 Видеогалерея</h2>
      <p style="margin-bottom: 24px; color: var(--color-text-light);">Видеозаписи мероприятий и событий села.</p>

      <div class="cards-grid">
        <?php
        $video_q = new WP_Query([
            'post_type'      => 'gallery',
            'posts_per_page' => 3,
            'post_status'    => 'publish',
            'offset'         => 12,
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

