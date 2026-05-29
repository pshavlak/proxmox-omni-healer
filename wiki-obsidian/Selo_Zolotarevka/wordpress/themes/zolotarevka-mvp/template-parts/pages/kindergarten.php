  <section class="page-header">
    <div class="container">
      <h1 class="page-header__title">🧸 Детский сад «Колосок»</h1>
      <div class="page-header__breadcrumb">
        <a href="<?php echo esc_url(zolo_url('')); ?>">Главная</a> / <a href="<?php echo esc_url(zolo_url('')); ?>#bento">Организации</a> / Детский сад
      </div>
    </div>
  </section>

  <section class="content-section">
    <div class="container">

      <h2>📰 Жизнь групп</h2>
      <div class="news-grid">
        <?php
        $kg_q = new WP_Query([
            'post_type'      => 'kindergarten_news',
            'posts_per_page' => 3,
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

      <h2>💡 Полезные советы родителям</h2>
      <div class="cards-grid">
        <div class="info-card">
          <div class="info-card__icon">📖</div>
          <h3 class="info-card__title">Как привить любовь к чтению</h3>
          <p class="info-card__text">Читайте вместе с ребенком каждый день по 15-20 минут. Обсуждайте прочитанное, задавайте вопросы.</p>
        </div>
        <div class="info-card">
          <div class="info-card__icon">🥗</div>
          <h3 class="info-card__title">Здоровое питание для детей</h3>
          <p class="info-card__text">Включайте в рацион больше овощей и фруктов. Ограничьте сладости и газированные напитки.</p>
        </div>
        <div class="info-card">
          <div class="info-card__icon">🎮</div>
          <h3 class="info-card__title">Развивающие игры дома</h3>
          <p class="info-card__text">Пазлы, конструкторы и настольные игры отлично развивают мелкую моторику и логическое мышление.</p>
        </div>
      </div>

      <h2>📸 Фотоотчеты</h2>
      <div class="gallery-grid">
        <?php
        $kg_gallery = new WP_Query([
            'post_type'      => 'gallery',
            'posts_per_page' => 6,
            'post_status'    => 'publish',
        ]);
        while ($kg_gallery->have_posts()) : $kg_gallery->the_post();
        ?>
        <div class="gallery-item">📸 <?php the_title(); ?></div>
        <?php endwhile; wp_reset_postdata(); ?>
      </div>

    </div>
  </section>

