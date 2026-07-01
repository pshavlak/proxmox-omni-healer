  <?php $school_content = zolo_get_page_content('school'); ?>
  <section class="page-header"<?php if (!empty($school_content['page_image'])): ?> style="background:linear-gradient(rgba(0,0,0,0.5),rgba(0,0,0,0.5)),url('<?php echo esc_url($school_content['page_image']); ?>') center/cover no-repeat;"<?php endif; ?>>
    <div class="container">
      <h1 class="page-header__title"><?php echo esc_html($school_content['page_title'] ?? '📚 Школа села Золотаревка'); ?></h1>
      <div class="page-header__breadcrumb">
        <a href="<?php echo esc_url(zolo_url('')); ?>">Главная</a> / <a href="<?php echo esc_url(zolo_url('')); ?>#bento">Организации</a> / Школа
      </div>
    </div>
  </section>

  <!-- ===== CONTENT ===== -->
  <section class="content-section">
    <div class="container">

      <!-- Новости классов -->
      <h2><?php echo esc_html($school_content['news_section_title'] ?? '📰 Новости школы'); ?></h2>
      <?php
      $school_news = zolo_get_recent_content_items(['school_news'], 3);
      if (empty($school_news)) {
          $school_news = [
              [
                  'icon' => '🎓',
                  'date' => '12 мая 2026',
                  'section' => 'Школьная жизнь',
                  'title' => 'Последний звонок — 2026',
                  'excerpt' => 'Торжественная линейка, посвященная последнему звонку для выпускников 11-го класса. Поздравляем ребят!',
              ],
              [
                  'icon' => '🏅',
                  'date' => '5 мая 2026',
                  'section' => 'Достижения',
                  'title' => 'Победа на районной олимпиаде по математике',
                  'excerpt' => 'Ученик 9-го класса занял 1-е место на районной олимпиаде. Гордимся нашими талантами!',
              ],
              [
                  'icon' => '🎨',
                  'date' => '28 апреля 2026',
                  'section' => 'Мероприятия',
                  'title' => 'Выставка рисунков «Весна в родном селе»',
                  'excerpt' => 'Ученики начальных классов представили яркие работы, посвященные красоте Золотаревки.',
              ],
          ];
      }
      ?>
      <div class="news-grid">
        <?php foreach ($school_news as $item): ?>
          <article class="news-card">
            <div class="news-card__img"><?php echo esc_html($item['icon'] ?? '📰'); ?></div>
            <div class="news-card__body">
              <div class="news-card__meta">
                <span>📅 <?php echo esc_html($item['date'] ?? ''); ?></span>
                <span>📂 <?php echo esc_html($item['section'] ?? 'Школа'); ?></span>
              </div>
              <h3 class="news-card__title"><?php echo esc_html($item['title'] ?? ''); ?></h3>
              <p class="news-card__excerpt"><?php echo esc_html($item['excerpt'] ?? ''); ?></p>
            </div>
          </article>
        <?php endforeach; ?>
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
      <h2><?php echo esc_html($school_content['comments_title'] ?? '💬 Комментарии'); ?></h2>
      <p style="color: var(--color-text-light); margin-bottom: 16px;">Комментарии проходят премодерацию.</p>

      <div class="comment">
        <div class="comment__author">Елена Петрова</div>
        <div class="comment__date">12 мая 2026, 14:30</div>
        <div class="comment__text">Поздравляю всех выпускников! Удачи на экзаменах! 🎉</div>
      </div>
      <div class="comment">
        <div class="comment__author">Анна Иванова</div>
        <div class="comment__date">5 мая 2026, 10:15</div>
        <div class="comment__text">Молодцы, ребята! Так держать! 💪</div>
      </div>

      <form id="commentForm" style="margin-top: 24px;">
        <h3 style="margin-bottom: 12px;">Оставить комментарий</h3>
        <div class="form-group">
          <label for="commentName">Ваше имя</label>
          <input type="text" id="commentName" placeholder="Ваше имя" required>
        </div>
        <div class="form-group">
          <label for="commentText">Комментарий</label>
          <textarea id="commentText" placeholder="Напишите комментарий..." required></textarea>
        </div>
        <button type="submit" class="btn">Отправить (на модерации)</button>
      </form>
    </div>
  </section>


  <!-- ===== DOCUMENTS ===== -->
  <?php
  $school_docs = $school_content['documents'] ?? [];
  if (!empty($school_docs)):
  ?>
  <section class="documents-section">
    <div class="container">
      <h2>📄 Документы</h2>
      <div class="documents-grid">
        <?php foreach ((array) $school_docs as $doc):
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

  <!-- ===== FOOTER ===== -->
