  <section class="page-header">
    <div class="container">
      <h1 class="page-header__title">🏘️ Жизнь села Золотаревка</h1>
      <div class="page-header__breadcrumb">
        <a href="<?php echo esc_url(zolo_url('')); ?>">Главная</a> / Жизнь села
      </div>
    </div>
  </section>

  <section class="content-section">
    <div class="container">

      <!-- История -->
      <h2>📜 История села</h2>
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
      <h2 id="culture">🎭 Дом Культуры</h2>
      <p>Дом Культуры села Золотаревка — центр культурной жизни. Здесь проходят праздники, концерты, работают кружки и секции для детей и взрослых.</p>

      <h3>📅 Афиша мероприятий</h3>
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

      <h3>🎨 Кружки и секции</h3>
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
      <h2 id="bulletin">📋 Доска объявлений</h2>
      <p style="color: var(--color-text-light); margin-bottom: 16px;">Куплю, продам, услуги местных мастеров.</p>

      <?php
      $bulletin_q = new WP_Query([
          'post_type'      => 'bulletin_board',
          'posts_per_page' => 10,
          'post_status'    => 'publish',
      ]);
      while ($bulletin_q->have_posts()) : $bulletin_q->the_post();
          // Determine tag from post meta or taxonomy
          $tag = 'Продам';
          $terms = wp_get_post_terms(get_the_ID(), 'content_section');
          if (!empty($terms) && !is_wp_error($terms)) {
              $tag = $terms[0]->name;
          }
      ?>
      <div class="bulletin-item">
        <div class="bulletin-item__title"><?php the_title(); ?></div>
        <div class="bulletin-item__meta">
          <span class="bulletin-item__tag"><?php echo esc_html($tag); ?></span>
          <span>📅 <?php echo get_the_date('j F Y'); ?></span>
        </div>
        <div class="bulletin-item__text"><?php echo get_the_excerpt(); ?></div>
      </div>
      <?php endwhile; wp_reset_postdata(); ?>

    </div>
  </section>

