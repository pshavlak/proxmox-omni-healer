  <section class="page-header">
    <div class="container">
      <h1 class="page-header__title">📚 Школа села Золотаревка</h1>
      <div class="page-header__breadcrumb">
        <a href="<?php echo esc_url(zolo_url('')); ?>">Главная</a> / <a href="<?php echo esc_url(zolo_url('')); ?>#bento">Организации</a> / Школа
      </div>
    </div>
  </section>

  <!-- ===== CONTENT ===== -->
  <section class="content-section">
    <div class="container">

      <!-- Новости классов -->
      <h2>📰 Новости школы</h2>
      <div class="news-grid">
        <?php
        $school_q = new WP_Query([
            'post_type'      => 'school_news',
            'posts_per_page' => 3,
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
      <h2>🚌 Расписание школьного автобуса</h2>
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
            <tr>
              <td>Золотаревка — Школа (ул. Центральная)</td>
              <td>07:30</td>
              <td>13:00</td>
            </tr>
            <tr>
              <td>Золотаревка — Школа (ул. Садовая)</td>
              <td>07:45</td>
              <td>13:15</td>
            </tr>
            <tr>
              <td>Золотаревка — Школа (ул. Полевая)</td>
              <td>07:50</td>
              <td>13:10</td>
            </tr>
            <tr>
              <td>Золотаревка — Школа (д. Сосновка)</td>
              <td>07:15</td>
              <td>13:30</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Достижения учеников -->
      <h2>🏆 Достижения учеников</h2>
      <div class="cards-grid">
        <div class="info-card">
          <div class="info-card__icon">🥇</div>
          <h3 class="info-card__title">Районная олимпиада по математике</h3>
          <p class="info-card__text">Иванов Петр, 9 класс — 1 место. Апрель 2026.</p>
        </div>
        <div class="info-card">
          <div class="info-card__icon">🥇</div>
          <h3 class="info-card__title">Соревнования по легкой атлетике</h3>
          <p class="info-card__text">Команда школы — 2 место в эстафете. Март 2026.</p>
        </div>
        <div class="info-card">
          <div class="info-card__icon">🥇</div>
          <h3 class="info-card__title">Конкурс чтецов «Родное слово»</h3>
          <p class="info-card__text">Сидорова Анна, 7 класс — 1 место. Февраль 2026.</p>
        </div>
      </div>

      <!-- Комментарии -->
      <h2>💬 Комментарии</h2>
      <?php comments_template(); ?>
    </div>
  </section>

  <!-- ===== FOOTER ===== -->
