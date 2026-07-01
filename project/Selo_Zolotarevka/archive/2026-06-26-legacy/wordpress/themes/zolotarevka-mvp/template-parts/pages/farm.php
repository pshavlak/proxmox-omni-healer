  <?php $farm_content = zolo_get_page_content('farm'); ?>
  <section class="page-header"<?php if (!empty($farm_content['page_image'])): ?> style="background:linear-gradient(rgba(0,0,0,0.5),rgba(0,0,0,0.5)),url('<?php echo esc_url($farm_content['page_image']); ?>') center/cover no-repeat;"<?php endif; ?>>
    <div class="container">
      <h1 class="page-header__title"><?php echo esc_html($farm_content['page_title'] ?? '🌾 Совхоз «Золотаревский»'); ?></h1>
      <div class="page-header__breadcrumb">
        <a href="<?php echo esc_url(zolo_url('')); ?>">Главная</a> / <a href="<?php echo esc_url(zolo_url('')); ?>#bento">Организации</a> / Совхоз
      </div>
    </div>
  </section>

  <section class="content-section">
    <div class="container">

      <!-- История -->
      <h2>📜 История предприятия</h2>
      <p>Совхоз «Золотаревский» был основан в 1960 году. За более чем 60 лет своей истории предприятие прошло славный путь от небольшого хозяйства до одного из ведущих сельскохозяйственных производителей района.</p>
      <p>Сегодня совхоз специализируется на выращивании зерновых культур, производстве молока и мяса. На предприятии трудятся более 200 человек, многие из которых — династиями.</p>

      <!-- Гордость села -->
      <h2>⭐ Гордость села</h2>
      <div class="pride-grid">
        <div class="pride-card">
          <div class="pride-card__icon">👨‍🌾</div>
          <div class="pride-card__name">Иван Петрович Смирнов</div>
          <div class="pride-card__role">Комбайнер, ветеран труда</div>
          <div class="pride-card__desc">Более 40 лет работает в совхозе. Неоднократный победитель районных соревнований по уборке урожая.</div>
        </div>
        <div class="pride-card">
          <div class="pride-card__icon">👩‍🌾</div>
          <div class="pride-card__name">Анна Васильевна Кузнецова</div>
          <div class="pride-card__role">Доярка, передовик производства</div>
          <div class="pride-card__desc">Лучшая доярка района 2024 года. Достигла рекордных надоев молока.</div>
        </div>
        <div class="pride-card">
          <div class="pride-card__icon">🚜</div>
          <div class="pride-card__name">Николай Сергеевич Орлов</div>
          <div class="pride-card__role">Тракторист, заслуженный работник</div>
          <div class="pride-card__desc">Награжден почетной грамотой Министерства сельского хозяйства за многолетний добросовестный труд.</div>
        </div>
      </div>

      <!-- Продукция -->
      <h2><?php echo esc_html($farm_content['products_title'] ?? '📦 Производимая продукция'); ?></h2>
      <?php
      $farm_products = zolo_get_recent_content_items(['farm_production'], 3);
      if (empty($farm_products)) {
          $farm_products = [
              ['icon' => '🌾', 'title' => 'Зерновые культуры', 'excerpt' => 'Пшеница, ячмень, овес, кукуруза. Ежегодный сбор — более 10 000 тонн.'],
              ['icon' => '🥛', 'title' => 'Молочная продукция', 'excerpt' => 'Молоко, сметана, творог, масло. Вся продукция — от собственного стада.'],
              ['icon' => '🥩', 'title' => 'Мясная продукция', 'excerpt' => 'Говядина, свинина, баранина. Мясо высшего качества, экологически чистое.'],
          ];
      }
      ?>
      <div class="cards-grid">
        <?php foreach ($farm_products as $item): ?>
          <div class="info-card">
            <div class="info-card__icon"><?php echo esc_html($item['icon'] ?? '🌾'); ?></div>
            <h3 class="info-card__title"><?php echo esc_html($item['title'] ?? 'Продукция'); ?></h3>
            <p class="info-card__text"><?php echo esc_html($item['excerpt'] ?? ''); ?></p>
          </div>
        <?php endforeach; ?>
      </div>

      <!-- Вакансии -->
      <h2><?php echo esc_html($farm_content['vacancies_title'] ?? '💼 Вакансии'); ?></h2>
      <?php
      $farm_vacancies = zolo_get_recent_content_items(['farm_vacancies'], 4);
      if (empty($farm_vacancies)) {
          $farm_vacancies = [
              ['icon' => '🚜', 'title' => 'Тракторист', 'section' => 'Полная занятость', 'excerpt' => 'от 45 000 ₽ · 8 (999) 123-45-67'],
              ['icon' => '🥛', 'title' => 'Доярка', 'section' => 'Полная занятость', 'excerpt' => 'от 40 000 ₽ · 8 (999) 123-45-67'],
              ['icon' => '🩺', 'title' => 'Ветеринар', 'section' => 'Полная занятость', 'excerpt' => 'от 50 000 ₽ · 8 (999) 123-45-67'],
              ['icon' => '🛠️', 'title' => 'Разнорабочий', 'section' => 'Сезонная', 'excerpt' => 'от 35 000 ₽ · 8 (999) 123-45-67'],
          ];
      }
      ?>
      <div class="cards-grid">
        <?php foreach ($farm_vacancies as $item): ?>
          <div class="info-card">
            <div class="info-card__icon"><?php echo esc_html($item['icon'] ?? '💼'); ?></div>
            <h3 class="info-card__title"><?php echo esc_html($item['title'] ?? 'Вакансия'); ?></h3>
            <p class="info-card__text"><?php echo esc_html(($item['section'] ?? 'Полная занятость') . ' · ' . ($item['excerpt'] ?? '')); ?></p>
          </div>
        <?php endforeach; ?>
      </div>

      <!-- Контакты -->
      <h2>📞 Контакты</h2>
      <div class="cards-grid">
        <div class="info-card">
          <div class="info-card__icon">📍</div>
          <h3 class="info-card__title">Адрес</h3>
          <p class="info-card__text">с. Золотаревка, ул. Совхозная, 1</p>
        </div>
        <div class="info-card">
          <div class="info-card__icon">📞</div>
          <h3 class="info-card__title">Телефон</h3>
          <p class="info-card__text">8 (999) 123-45-67</p>
        </div>
        <div class="info-card">
          <div class="info-card__icon">✉️</div>
          <h3 class="info-card__title">Email</h3>
          <p class="info-card__text">sovhoz@zolotarevka.ru</p>
        </div>
      </div>

    </div>
  <!-- ===== DOCUMENTS ===== -->
  <?php
  $farm_docs = $farm_content['documents'] ?? [];
  if (!empty($farm_docs)):
  ?>
  <section class="documents-section">
    <div class="container">
      <h2>📄 Документы</h2>
      <div class="documents-grid">
        <?php foreach ((array) $farm_docs as $doc):
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
