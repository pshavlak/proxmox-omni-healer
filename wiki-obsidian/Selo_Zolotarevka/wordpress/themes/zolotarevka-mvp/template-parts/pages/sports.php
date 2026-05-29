  <section class="page-header">
    <div class="container">
      <h1 class="page-header__title">⚽ Спорт в Золотаревке</h1>
      <div class="page-header__breadcrumb">
        <a href="<?php echo esc_url(zolo_url('')); ?>">Главная</a> / Спорт
      </div>
    </div>
  </section>

  <section class="content-section">
    <div class="container">

      <!-- Футбольная команда -->
      <h2>⚽ Футбольная команда «Золотаревка»</h2>

      <!-- Информер прошедшего матча -->
      <h3>📊 Прошедший матч</h3>
      <?php
      $last_match = new WP_Query([
          'post_type'      => 'sports_match',
          'posts_per_page' => 1,
          'post_status'    => 'publish',
      ]);
      if ($last_match->have_posts()) : $last_match->the_post();
      ?>
      <div class="info-card" style="border-left: 4px solid var(--color-primary); margin-bottom: 24px;">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
          <div>
            <strong><?php the_title(); ?></strong>
          </div>
          <div style="font-size: 0.9rem; color: var(--color-text-light);">
            📅 <?php echo get_the_date('j F Y'); ?>
          </div>
        </div>
        <div style="margin-top: 12px; font-size: 0.9rem;">
          <?php the_excerpt(); ?>
        </div>
      </div>
      <?php endif; wp_reset_postdata(); ?>

      <!-- Состав команды -->
      <h3>👥 Состав команды</h3>
      <div class="cards-grid">
        <?php
        $team_q = new WP_Query([
            'post_type'      => 'sports_team',
            'posts_per_page' => 20,
            'post_status'    => 'publish',
        ]);
        while ($team_q->have_posts()) : $team_q->the_post();
            $number = get_post_meta(get_the_ID(), 'number', true) ?: '';
            $age    = get_post_meta(get_the_ID(), 'age', true) ?: '';
            $position = get_the_excerpt() ?: '';
        ?>
        <div class="player-card">
          <div class="player-card__avatar">⚽</div>
          <div class="player-card__info">
            <h4><?php the_title(); ?></h4>
            <p><?php echo $number ? '№' . esc_html($number) : ''; ?><?php echo $age ? ' • ' . esc_html($age) . ' лет' : ''; ?></p>
            <span class="player-card__position"><?php echo esc_html($position); ?></span>
          </div>
        </div>
        <?php endwhile; wp_reset_postdata(); ?>
      </div>

      <!-- Расписание матчей -->
      <h3>📅 Расписание матчей</h3>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Матч</th>
              <th>Дата</th>
              <th>Статус</th>
            </tr>
          </thead>
          <tbody>
            <?php
            $schedule_q = new WP_Query([
                'post_type'      => 'sports_match',
                'posts_per_page' => 5,
                'post_status'    => 'publish',
                'offset'         => 1,
            ]);
            while ($schedule_q->have_posts()) : $schedule_q->the_post();
            ?>
            <tr>
              <td><?php the_title(); ?></td>
              <td><?php echo get_the_date('j F Y'); ?></td>
              <td>Запланирован</td>
            </tr>
            <?php endwhile; wp_reset_postdata(); ?>
          </tbody>
        </table>
      </div>

      <!-- Турнирная таблица -->
      <h3>🏆 Турнирная таблица (Районная лига)</h3>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>#</th>
              <th>Команда</th>
              <th>И</th>
              <th>В</th>
              <th>Н</th>
              <th>П</th>
              <th>О</th>
            </tr>
          </thead>
          <tbody>
            <tr style="background: #d4edda;">
              <td>1</td>
              <td>ФК «Золотаревка»</td>
              <td>8</td>
              <td>6</td>
              <td>1</td>
              <td>1</td>
              <td><strong>19</strong></td>
            </tr>
            <tr>
              <td>2</td>
              <td>ФК «Луч»</td>
              <td>8</td>
              <td>5</td>
              <td>2</td>
              <td>1</td>
              <td><strong>17</strong></td>
            </tr>
            <tr>
              <td>3</td>
              <td>ФК «Восход»</td>
              <td>8</td>
              <td>4</td>
              <td>2</td>
              <td>2</td>
              <td><strong>14</strong></td>
            </tr>
            <tr>
              <td>4</td>
              <td>ФК «Соседи»</td>
              <td>8</td>
              <td>3</td>
              <td>1</td>
              <td>4</td>
              <td><strong>10</strong></td>
            </tr>
            <tr>
              <td>5</td>
              <td>ФК «Заря»</td>
              <td>8</td>
              <td>2</td>
              <td>0</td>
              <td>6</td>
              <td><strong>6</strong></td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Фото с игр -->
      <h3>📸 Фото с игр</h3>
      <div class="gallery-grid">
        <?php
        $sports_gallery = new WP_Query([
            'post_type'      => 'gallery',
            'posts_per_page' => 6,
            'post_status'    => 'publish',
        ]);
        while ($sports_gallery->have_posts()) : $sports_gallery->the_post();
        ?>
        <div class="gallery-item">⚽ <?php the_title(); ?></div>
        <?php endwhile; wp_reset_postdata(); ?>
      </div>

      <!-- Другие секции -->
      <h2 id="other">🏐 Другие секции</h2>
      <div class="cards-grid">
        <div class="info-card">
          <div class="info-card__icon">🏐</div>
          <h3 class="info-card__title">Волейбол</h3>
          <p class="info-card__text">Тренировки по вторникам и четвергам в 18:00 в спортзале школы. Тренер: Сергей Иванович.</p>
        </div>
        <div class="info-card">
          <div class="info-card__icon">♟️</div>
          <h3 class="info-card__title">Шахматы</h3>
          <p class="info-card__text">Кружок работает в Доме Культуры по средам и пятницам в 17:00. Все возрасты приветствуются.</p>
        </div>
        <div class="info-card">
          <div class="info-card__icon">🏃</div>
          <h3 class="info-card__title">Легкая атлетика</h3>
          <p class="info-card__text">Тренировки на стадионе «Центральный» ежедневно в 07:00 утра. Присоединяйтесь!</p>
        </div>
      </div>

    </div>
  </section>

