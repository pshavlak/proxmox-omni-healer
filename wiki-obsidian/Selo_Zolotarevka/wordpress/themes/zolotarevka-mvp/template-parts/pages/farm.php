  <section class="page-header">
    <div class="container">
      <h1 class="page-header__title">🌾 Совхоз «Золотаревский»</h1>
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
      <h2>📦 Производимая продукция</h2>
      <div class="cards-grid">
        <?php
        $prod_q = new WP_Query([
            'post_type'      => 'farm_production',
            'posts_per_page' => 10,
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
      <h2>💼 Вакансии</h2>
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
                'posts_per_page' => 10,
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
  </section>

