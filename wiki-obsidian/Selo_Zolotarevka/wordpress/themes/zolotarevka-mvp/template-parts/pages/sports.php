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

      <?php
      // ──────────────────────────────────────────────────────
      // Календарь и турнирная таблица из sports_season
      // ──────────────────────────────────────────────────────
      $seasons = new WP_Query([
          'post_type'      => 'sports_season',
          'posts_per_page' => 20,
          'post_status'    => 'publish',
          'orderby'        => 'date',
          'order'          => 'DESC',
      ]);

      if ($seasons->have_posts()) :
          while ($seasons->have_posts()) : $seasons->the_post();
              $season_id   = get_the_ID();
              $calendar    = Zolotarevka_MVP_Backend::get_calendar_for_display($season_id);
              $standings   = Zolotarevka_MVP_Backend::get_standings_for_display($season_id);
              $season_title = get_the_title();
      ?>

      <!-- ════════════════════════ -->
      <!-- Календарь турнира       -->
      <!-- ════════════════════════ -->
      <?php if (!empty($calendar)) : ?>
      <h2 style="margin-top:40px;">📅 Календарь турнира: <?php echo esc_html($season_title); ?></h2>

      <?php foreach ($calendar as $circle => $rounds):
          $circle_label = ((string) $circle === '1') ? '1 круг' : '2 круг';
      ?>
      <h3 style="margin-top:24px;">🔄 <?php echo $circle_label; ?></h3>
        <?php foreach ($rounds as $round):
            $round_num = $round['round'] ?? '';
            $round_date = $round['date'] ?? '';
            $matches = $round['matches'] ?? [];
        ?>
        <div style="margin-bottom:20px; border:1px solid #e0e0e0; border-radius:8px; padding:12px 16px; background:#fafafa;">
          <div style="font-weight:600; font-size:1.05rem; margin-bottom:8px; color:#2d6a4f;">
            Тур <?php echo esc_html($round_num); ?>
            <?php if ($round_date): ?>
              <span style="font-weight:400; font-size:0.9rem; color:#666; margin-left:8px;">— <?php echo esc_html($round_date); ?></span>
            <?php endif; ?>
          </div>
          <div class="table-wrap">
            <table style="font-size:0.9rem;">
              <thead>
                <tr>
                  <th style="width:36px;">#</th>
                  <th>Матч</th>
                  <th style="width:110px;">Статус</th>
                </tr>
              </thead>
              <tbody>
                <?php foreach ($matches as $m_idx => $m):
                    $home = $m['home'] ?? '';
                    $away = $m['away'] ?? '';
                    $score_h = $m['score_h'] ?? '';
                    $score_a = $m['score_a'] ?? '';
                    $status = $m['status'] ?? 'scheduled';

                    if (!$home && !$away) continue;

                    $has_score = ($score_h !== '' && $score_a !== '');
                    $status_label = 'Запланирован';
                    $status_class = 'scheduled';
                    if ($status === 'played') {
                        $status_label = 'Сыгран';
                        $status_class = 'played';
                    } elseif ($status === 'postponed') {
                        $status_label = 'Перенесён';
                        $status_class = 'postponed';
                    }
                ?>
                <tr>
                  <td style="text-align:center; color:#888; width:36px;"><?php echo $m_idx + 1; ?></td>
                  <td style="text-align:center;">
                    <span style="display:inline-flex; align-items:center; justify-content:center; gap:12px;">
                      <span style="flex:1; text-align:right;"><strong><?php echo esc_html($home); ?></strong></span>
                      <?php if ($has_score): ?>
                        <span style="background:#e8f5e9; padding:2px 12px; border-radius:4px; font-weight:700; white-space:nowrap;"><?php echo (int) $score_h; ?> : <?php echo (int) $score_a; ?></span>
                      <?php else: ?>
                        <span style="color:#bbb; padding:0 4px; font-weight:400;">– : –</span>
                      <?php endif; ?>
                      <span style="flex:1; text-align:left;"><strong><?php echo esc_html($away); ?></strong></span>
                    </span>
                  </td>
                  <td>
                    <span style="display:inline-block; padding:2px 8px; border-radius:4px; font-size:0.8rem;
                      <?php echo $status_class === 'played' ? 'background:#d4edda; color:#155724;' : ($status_class === 'postponed' ? 'background:#fff3cd; color:#856404;' : 'background:#e2e3e5; color:#383d41;'); ?>">
                      <?php echo $status_label; ?>
                    </span>
                  </td>
                </tr>
                <?php endforeach; ?>
              </tbody>
            </table>
          </div>
        </div>
        <?php endforeach; ?>
      <?php endforeach; ?>
      <?php endif; ?>

      <!-- ════════════════════════ -->
      <!-- Турнирная таблица       -->
      <!-- ════════════════════════ -->
      <?php if (!empty($standings)) : ?>
      <h2 style="margin-top:40px;">🏆 Турнирная таблица: <?php echo esc_html($season_title); ?></h2>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th style="width:30px;">#</th>
              <th>Команда</th>
              <th style="width:40px;">И</th>
              <th style="width:36px;">В</th>
              <th style="width:36px;">Н</th>
              <th style="width:36px;">П</th>
              <th style="width:40px;">ЗМ</th>
              <th style="width:40px;">ПМ</th>
              <th style="width:36px;">±</th>
              <th style="width:36px;">О</th>
            </tr>
          </thead>
          <tbody>
            <?php foreach ((array) $standings as $i => $row):
                $gf = (int) ($row['gf'] ?? 0);
                $ga = (int) ($row['ga'] ?? 0);
                $gd = $gf - $ga;
            ?>
            <tr<?php echo $i === 0 ? ' style="background:#d4edda;"' : ''; ?>>
              <td><?php echo $i + 1; ?></td>
              <td><strong><?php echo esc_html($row['team'] ?? ''); ?></strong></td>
              <td><?php echo esc_html($row['gp'] ?? '0'); ?></td>
              <td><?php echo esc_html($row['w'] ?? '0'); ?></td>
              <td><?php echo esc_html($row['d'] ?? '0'); ?></td>
              <td><?php echo esc_html($row['l'] ?? '0'); ?></td>
              <td><?php echo $gf; ?></td>
              <td><?php echo $ga; ?></td>
              <td style="font-weight:600; <?php echo $gd > 0 ? 'color:#00a32a;' : ($gd < 0 ? 'color:#d63638;' : ''); ?>">
                <?php echo $gd > 0 ? '+' : ''; ?><?php echo $gd; ?>
              </td>
              <td><strong><?php echo esc_html($row['pts'] ?? '0'); ?></strong></td>
            </tr>
            <?php endforeach; ?>
          </tbody>
        </table>
      </div>
      <p style="font-size:0.85rem; color:#666; margin-top:4px;">Очки: победа — 3, ничья — 1, поражение — 0. ЗМ — забито, ПМ — пропущено.</p>
      <?php endif; ?>

      <!-- ════════════════════════ -->
      <!-- Результаты по турам     -->
      <!-- ════════════════════════ -->
      <?php if (!empty($calendar)) :
          // Collect played matches from all circles
          $played_matches = [];
          foreach ($calendar as $circle => $rounds) {
              $circle_label = ((string) $circle === '1') ? '1 круг' : '2 круг';
              foreach ($rounds as $round) {
                  $matches = $round['matches'] ?? [];
                  foreach ($matches as $m) {
                      if (($m['status'] ?? '') === 'played' && ($m['score_h'] ?? '') !== '' && ($m['score_a'] ?? '') !== '') {
                          $m['_circle'] = $circle_label;
                          $m['_round'] = $round['round'] ?? '';
                          $m['_date'] = $round['date'] ?? '';
                          $played_matches[] = $m;
                      }
                  }
              }
          }
          if (!empty($played_matches)) :
      ?>
      <h2 style="margin-top:40px;">📊 Результаты прошедших матчей</h2>
      <div class="cards-grid" style="display:grid; grid-template-columns:repeat(auto-fill, minmax(280px, 1fr)); gap:12px;">
        <?php foreach ($played_matches as $m): ?>
        <div class="info-card" style="border-left:4px solid #2d6a4f; padding:12px 16px;">
          <div style="font-size:0.85rem; color:#666; margin-bottom:6px;">
            Тур <?php echo (int) ($m['_round'] ?? 0); ?> • <?php echo esc_html($m['_circle']); ?> — <?php echo esc_html($m['_date']); ?>
          </div>
          <div style="display:flex; align-items:center; justify-content:center; gap:16px; font-size:1.1rem;">
            <span style="flex:1; text-align:right; padding-right:4px;"><strong><?php echo esc_html($m['home'] ?? ''); ?></strong></span>
            <span style="background:#2d6a4f; color:#fff; padding:6px 18px; border-radius:8px; font-weight:700; white-space:nowrap;">
              <?php echo (int) ($m['score_h'] ?? 0); ?> : <?php echo (int) ($m['score_a'] ?? 0); ?>
            </span>
            <span style="flex:1; text-align:left; padding-left:4px;"><strong><?php echo esc_html($m['away'] ?? ''); ?></strong></span>
          </div>
        </div>
        <?php endforeach; ?>
      </div>
      <?php endif; ?>
      <?php endif; ?>

      <?php
          endwhile;
      else :
      ?>
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

      <h3>🏆 Турнирная таблица</h3>
      <p>Пока нет данных о сезонах. Данные добавляются в административной панели.</p>
      <?php
      endif;
      wp_reset_postdata();
      ?>

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
