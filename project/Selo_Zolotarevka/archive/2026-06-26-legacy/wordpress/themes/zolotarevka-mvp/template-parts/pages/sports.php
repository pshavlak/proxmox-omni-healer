  <?php $sports_content = zolo_get_page_content('sports'); ?>
  <section class="page-header"<?php if (!empty($sports_content['page_image'])): ?> style="background:linear-gradient(rgba(0,0,0,0.5),rgba(0,0,0,0.5)),url('<?php echo esc_url($sports_content['page_image']); ?>') center/cover no-repeat;"<?php endif; ?>>
    <div class="container">
      <h1 class="page-header__title"><?php echo esc_html($sports_content['page_title'] ?? '⚽ Спорт в Золотаревке'); ?></h1>
      <div class="page-header__breadcrumb">
        <a href="<?php echo esc_url(zolo_url('')); ?>">Главная</a> / Спорт
      </div>
    </div>
  </section>

  <section class="content-section">
    <div class="container">

      <!-- Футбольная команда -->
      <h2><?php echo esc_html($sports_content['team_section_title'] ?? '⚽ Футбольная команда «Золотаревка»'); ?></h2>

      <!-- Информер прошедшего матча -->
      <h3>📊 Прошедший матч</h3>
      <?php
      $sports_matches = zolo_get_recent_content_items(['sports_match'], 1);
      if (empty($sports_matches)) {
          $sports_matches = [
              ['icon' => '🏆', 'date' => '10 мая 2026', 'section' => 'Матч', 'title' => 'ФК «Золотаревка» 3 : 1 ФК «Соседи»', 'excerpt' => 'Голы: Иванов (15\'), Петров (32\', 67\') — Сидоров (55\')'],
          ];
      }
      $latest_match = $sports_matches[0];
      ?>
      <div class="info-card" style="border-left: 4px solid var(--color-primary); margin-bottom: 24px;">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
          <div>
            <strong><?php echo esc_html($latest_match['title'] ?? 'ФК «Золотаревка»'); ?></strong>
          </div>
          <div style="font-size: 0.9rem; color: var(--color-text-light);">
            📅 <?php echo esc_html($latest_match['date'] ?? ''); ?>
          </div>
        </div>
        <div style="margin-top: 12px; font-size: 0.9rem;">
          <?php echo esc_html($latest_match['excerpt'] ?? ''); ?>
        </div>
      </div>

      <!-- Состав команды -->
      <h3><?php echo esc_html($sports_content['team_subtitle'] ?? '👥 Состав команды'); ?></h3>
      <?php
      $team_players = zolo_get_recent_content_items(['sports_team'], 6);
      if (empty($team_players)) {
          $team_players = [
              ['icon' => '🧤', 'title' => 'Алексей Иванов', 'section' => '№1 • 28 лет', 'excerpt' => 'Вратарь'],
              ['icon' => '🛡️', 'title' => 'Дмитрий Петров', 'section' => '№4 • 26 лет', 'excerpt' => 'Защитник'],
              ['icon' => '⚡', 'title' => 'Сергей Смирнов', 'section' => '№8 • 24 года', 'excerpt' => 'Полузащитник'],
              ['icon' => '🎯', 'title' => 'Андрей Кузнецов', 'section' => '№10 • 27 лет', 'excerpt' => 'Нападающий'],
              ['icon' => '💪', 'title' => 'Максим Орлов', 'section' => '№3 • 29 лет', 'excerpt' => 'Защитник'],
              ['icon' => '🏃', 'title' => 'Иван Федоров', 'section' => '№7 • 22 года', 'excerpt' => 'Полузащитник'],
          ];
      }
      ?>
      <div class="cards-grid">
        <?php foreach ($team_players as $player): ?>
          <div class="player-card">
            <div class="player-card__avatar"><?php echo esc_html($player['icon'] ?? '⚽'); ?></div>
            <div class="player-card__info">
              <h4><?php echo esc_html($player['title'] ?? 'Игрок'); ?></h4>
              <p><?php echo esc_html($player['date'] ?? ($player['section'] ?? '')); ?></p>
              <span class="player-card__position"><?php echo esc_html($player['excerpt'] ?? ''); ?></span>
            </div>
          </div>
        <?php endforeach; ?>
      </div>

      <!-- Расписание матчей -->
      <h3>📅 Расписание матчей</h3>
      <?php
      $match_schedule = zolo_get_recent_content_items(['sports_match'], 3);
      if (empty($match_schedule)) {
          $match_schedule = [
              ['date' => '24 мая 2026, 15:00', 'title' => 'ФК «Соседи»', 'excerpt' => 'Дома', 'section' => 'Предстоящий'],
              ['date' => '31 мая 2026, 14:00', 'title' => 'ФК «Луч»', 'excerpt' => 'В гостях', 'section' => 'Предстоящий'],
              ['date' => '7 июня 2026, 15:00', 'title' => 'ФК «Восход»', 'excerpt' => 'Дома', 'section' => 'Предстоящий'],
          ];
      } else {
          foreach ($match_schedule as &$match) {
              $match['section'] = 'Матч';
          }
          unset($match);
      }
      ?>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Дата</th>
              <th>Соперник</th>
              <th>Место</th>
              <th>Статус</th>
            </tr>
          </thead>
          <tbody>
            <?php foreach ($match_schedule as $match): ?>
              <tr>
                <td><?php echo esc_html($match['date'] ?? ''); ?></td>
                <td><?php echo esc_html($match['title'] ?? ''); ?></td>
                <td><?php echo esc_html($match['excerpt'] ?? ''); ?></td>
                <td><?php echo esc_html($match['section'] ?? ''); ?></td>
              </tr>
            <?php endforeach; ?>
          </tbody>
        </table>
      </div>

      <!-- Турнирная таблица -->
      <h3>🏆 Турнирная таблица (Районная лига)</h3>
      <?php
      $season_query = new WP_Query([
          'post_type' => 'sports_season',
          'post_status' => 'publish',
          'posts_per_page' => 1,
          'orderby' => 'date',
          'order' => 'DESC',
          'no_found_rows' => true,
      ]);
      $standings = [];
      if ($season_query->have_posts()) {
          $season_query->the_post();
          $standings = get_post_meta(get_the_ID(), 'standings_data', true);
          if (!is_array($standings)) {
              $standings = [];
          }
          wp_reset_postdata();
      }
      if (empty($standings)) {
          $standings = [
              ['team' => 'ФК «Золотаревка»', 'gp' => 8, 'w' => 6, 'd' => 1, 'l' => 1, 'pts' => 19],
              ['team' => 'ФК «Луч»', 'gp' => 8, 'w' => 5, 'd' => 2, 'l' => 1, 'pts' => 17],
              ['team' => 'ФК «Восход»', 'gp' => 8, 'w' => 4, 'd' => 2, 'l' => 2, 'pts' => 14],
              ['team' => 'ФК «Соседи»', 'gp' => 8, 'w' => 3, 'd' => 1, 'l' => 4, 'pts' => 10],
              ['team' => 'ФК «Заря»', 'gp' => 8, 'w' => 2, 'd' => 0, 'l' => 6, 'pts' => 6],
          ];
      }
      ?>
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
            <?php foreach ($standings as $idx => $row): ?>
              <tr<?php echo $idx === 0 ? ' style="background: #d4edda;"' : ''; ?>>
                <td><?php echo (int) $idx + 1; ?></td>
                <td><?php echo esc_html($row['team'] ?? ''); ?></td>
                <td><?php echo (int) ($row['gp'] ?? 0); ?></td>
                <td><?php echo (int) ($row['w'] ?? 0); ?></td>
                <td><?php echo (int) ($row['d'] ?? 0); ?></td>
                <td><?php echo (int) ($row['l'] ?? 0); ?></td>
                <td><strong><?php echo (int) ($row['pts'] ?? 0); ?></strong></td>
              </tr>
            <?php endforeach; ?>
          </tbody>
        </table>
      </div>

      <!-- Фото с игр -->
      <h3>📸 Фото с игр</h3>
      <?php
      $sports_gallery = zolo_get_recent_content_items(['gallery'], 6);
      if (empty($sports_gallery)) {
          $sports_gallery = [
              ['icon' => '⚽', 'title' => 'Матч 1'],
              ['icon' => '⚽', 'title' => 'Матч 2'],
              ['icon' => '⚽', 'title' => 'Матч 3'],
              ['icon' => '⚽', 'title' => 'Матч 4'],
              ['icon' => '⚽', 'title' => 'Матч 5'],
              ['icon' => '⚽', 'title' => 'Матч 6'],
          ];
      }
      ?>
      <div class="gallery-grid">
        <?php foreach ($sports_gallery as $item): ?>
          <div class="gallery-item"><?php echo esc_html($item['icon'] ?? '📸'); ?> <?php echo esc_html($item['title'] ?? 'Фото'); ?></div>
        <?php endforeach; ?>
      </div>

      <!-- Другие секции -->
      <h2 id="other"><?php echo esc_html($sports_content['other_sections_title'] ?? '🏐 Другие секции'); ?></h2>
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
  <!-- ===== DOCUMENTS ===== -->
  <?php
  $sports_docs = $sports_content['documents'] ?? [];
  if (!empty($sports_docs)):
  ?>
  <section class="documents-section">
    <div class="container">
      <h2>📄 Документы</h2>
      <div class="documents-grid">
        <?php foreach ((array) $sports_docs as $doc):
          if (empty($doc['file_url'])) continue;
          $doc_title = $doc['title'] ?? 'Документ';
          $doc_desc = $doc['description'] ?? '';
          $ext = strtolower(pathinfo($doc['file_url'], PATHINFO_EXTENSION));
          $icon = in_array($ext, ['pdf']) ? '📕' : (in_array($ext, ['doc', 'docx']) ? '📘' : (in_array($ext, ['xls', 'xlsx']) ? '📗' : '📄'));
        ?>
          <a href="<?php echo esc_url($doc['file_url']); ?>" class="doc-card" target="_blank" rel="noopener">
            <div class="doc-card__icon"><?php echo $icon; ?></div>
            <div class="doc-card__body">
              <strong><?php echo esc_html($doc_title); ?></strong>
              <?php if ($doc_desc): ?><p><?php echo esc_html($doc_desc); ?></p><?php endif; ?>
              <span class="doc-card__link">Скачать →</span>
            </div>
          </a>
        <?php endforeach; ?>
      </div>
    </div>
  </section>
  <?php endif; ?>

  </section>
