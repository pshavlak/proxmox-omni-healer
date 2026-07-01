  <?php $village_content = zolo_get_page_content('village-life'); ?>
  <section class="page-header"<?php if (!empty($village_content['page_image'])): ?> style="background:linear-gradient(rgba(0,0,0,0.5),rgba(0,0,0,0.5)),url('<?php echo esc_url($village_content['page_image']); ?>') center/cover no-repeat;"<?php endif; ?>>
    <div class="container">
      <h1 class="page-header__title"><?php echo esc_html($village_content['page_title'] ?? '🏘️ Жизнь села Золотаревка'); ?></h1>
      <div class="page-header__breadcrumb">
        <a href="<?php echo esc_url(zolo_url('')); ?>">Главная</a> / Жизнь села
      </div>
    </div>
  </section>

  <section class="content-section">
    <div class="container">

      <!-- История -->
      <h2><?php echo esc_html($village_content['history_title'] ?? '📜 История села'); ?></h2>
      <p>Село Золотаревка было основано в середине XIX века переселенцами из центральных губерний России. Название село получило благодаря живописным золотистым полям пшеницы, которые окружают его со всех сторон.</p>
      <p>В разные годы Золотаревка была центром сельсовета, здесь располагалась усадьба помещика, а после революции — коллективное хозяйство. Сегодня село продолжает развиваться, сохраняя свои традиции и самобытность.</p>

      <!-- Выдающиеся земляки -->
      <h2>⭐ Выдающиеся земляки</h2>
      <div class="pride-grid">
        <div class="pride-card">
          <div class="pride-card__icon">🎖️</div>
          <div class="pride-card__name">Иван Алексеевич Новиков</div>
          <div class="pride-card__role">Герой Социалистического Труда</div>
          <div class="pride-card__desc">Уроженец села, награжден за выдающиеся достижения в сельском хозяйстве.</div>
        </div>
        <div class="pride-card">
          <div class="pride-card__icon">📖</div>
          <div class="pride-card__name">Мария Петровна Соколова</div>
          <div class="pride-card__role">Заслуженный учитель РФ</div>
          <div class="pride-card__desc">Более 50 лет проработала в школе села, воспитала не одно поколение золотаревцев.</div>
        </div>
        <div class="pride-card">
          <div class="pride-card__icon">🎭</div>
          <div class="pride-card__name">Николай Дмитриевич Белов</div>
          <div class="pride-card__role">Художественный руководитель ДК</div>
          <div class="pride-card__desc">Основал народный хор, который выступал на областных сценах.</div>
        </div>
      </div>

      <!-- Дом Культуры -->
      <h2 id="culture"><?php echo esc_html($village_content['culture_title'] ?? '🎭 Дом Культуры'); ?></h2>
      <p>Дом Культуры села Золотаревка — центр культурной жизни. Здесь проходят праздники, концерты, работают кружки и секции для детей и взрослых.</p>

      <h3><?php echo esc_html($village_content['culture_events_title'] ?? '📅 Афиша мероприятий'); ?></h3>
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
            <tr>
              <td>1 июня 2026</td>
              <td>День защиты детей — праздничный концерт</td>
              <td>11:00</td>
            </tr>
            <tr>
              <td>12 июня 2026</td>
              <td>День России — гуляния на площади</td>
              <td>14:00</td>
            </tr>
            <tr>
              <td>20 июня 2026</td>
              <td>Выставка местных художников и мастеров</td>
              <td>16:00</td>
            </tr>
          </tbody>
        </table>
      </div>

      <h3><?php echo esc_html($village_content['culture_circles_title'] ?? '🎨 Кружки и секции'); ?></h3>
      <div class="cards-grid">
        <div class="info-card">
          <div class="info-card__icon">🎤</div>
          <h3 class="info-card__title">Вокальный кружок</h3>
          <p class="info-card__text">Занятия по вторникам и четвергам в 17:00. Руководитель: Белов Н.Д.</p>
        </div>
        <div class="info-card">
          <div class="info-card__icon">💃</div>
          <h3 class="info-card__title">Танцевальный кружок</h3>
          <p class="info-card__text">Занятия по понедельникам, средам и пятницам в 18:00.</p>
        </div>
        <div class="info-card">
          <div class="info-card__icon">🎨</div>
          <h3 class="info-card__title">Изостудия</h3>
          <p class="info-card__text">Рисование для детей и взрослых. Суббота в 14:00.</p>
        </div>
        <div class="info-card">
          <div class="info-card__icon">🧶</div>
          <h3 class="info-card__title">Рукоделие</h3>
          <p class="info-card__text">Вязание, вышивка, лоскутное шитье. Среда и пятница в 15:00.</p>
        </div>
      </div>

      <!-- Доска объявлений -->
      <h2 id="bulletin"><?php echo esc_html($village_content['bulletin_title'] ?? '📋 Доска объявлений'); ?></h2>
      <p style="color: var(--color-text-light); margin-bottom: 16px;">Куплю, продам, услуги местных мастеров.</p>

      <?php
      $bulletins = zolo_get_recent_content_items(['bulletin_board'], 5);
      if (empty($bulletins)) {
          $bulletins = [
              ['icon' => '📋', 'date' => '15 мая 2026', 'section' => 'Продам', 'title' => 'Продам велосипед', 'excerpt' => 'Продам горный велосипед, 26 колеса, в хорошем состоянии. Цена: 8 000 ₽.'],
              ['icon' => '📋', 'date' => '12 мая 2026', 'section' => 'Куплю', 'title' => 'Куплю щенка', 'excerpt' => 'Ищу щенка овчарки для частного дома. Рассмотрю любые предложения.'],
              ['icon' => '📋', 'date' => '10 мая 2026', 'section' => 'Услуги', 'title' => 'Ремонт бытовой техники', 'excerpt' => 'Ремонтирую стиральные машины, холодильники, микроволновки. Выезд на дом. Недорого.'],
              ['icon' => '📋', 'date' => '8 мая 2026', 'section' => 'Продам', 'title' => 'Продам куриные яйца', 'excerpt' => 'Домашние куриные яйца. 100 ₽ за десяток. Свежие, от своих кур.'],
              ['icon' => '📋', 'date' => '5 мая 2026', 'section' => 'Услуги', 'title' => 'Услуги электрика', 'excerpt' => 'Электромонтажные работы любой сложности. Розетки, проводка, щитки. Гарантия.'],
          ];
      }
      ?>
      <?php foreach ($bulletins as $bulletin): ?>
        <div class="bulletin-item">
          <div class="bulletin-item__title"><?php echo esc_html($bulletin['title'] ?? ''); ?></div>
          <div class="bulletin-item__meta">
            <span class="bulletin-item__tag"><?php echo esc_html($bulletin['section'] ?? 'Объявление'); ?></span>
            <span>📅 <?php echo esc_html($bulletin['date'] ?? ''); ?></span>
          </div>
          <div class="bulletin-item__text"><?php echo esc_html($bulletin['excerpt'] ?? ''); ?></div>
        </div>
      <?php endforeach; ?>

    </div>
  <!-- ===== DOCUMENTS ===== -->
  <?php
  $village_docs = $village_content['documents'] ?? [];
  if (!empty($village_docs)):
  ?>
  <section class="documents-section">
    <div class="container">
      <h2>📄 Документы</h2>
      <div class="documents-grid">
        <?php foreach ((array) $village_docs as $doc):
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
