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
        <article class="news-card">
          <div class="news-card__img">🎓</div>
          <div class="news-card__body">
            <div class="news-card__meta">
              <span>📅 12 мая 2026</span>
              <span>📂 Школьная жизнь</span>
            </div>
            <h3 class="news-card__title">Последний звонок — 2026</h3>
            <p class="news-card__excerpt">Торжественная линейка, посвященная последнему звонку для выпускников 11-го класса. Поздравляем ребят!</p>
          </div>
        </article>
        <article class="news-card">
          <div class="news-card__img">🏅</div>
          <div class="news-card__body">
            <div class="news-card__meta">
              <span>📅 5 мая 2026</span>
              <span>📂 Достижения</span>
            </div>
            <h3 class="news-card__title">Победа на районной олимпиаде по математике</h3>
            <p class="news-card__excerpt">Ученик 9-го класса занял 1-е место на районной олимпиаде. Гордимся нашими талантами!</p>
          </div>
        </article>
        <article class="news-card">
          <div class="news-card__img">🎨</div>
          <div class="news-card__body">
            <div class="news-card__meta">
              <span>📅 28 апреля 2026</span>
              <span>📂 Мероприятия</span>
            </div>
            <h3 class="news-card__title">Выставка рисунков «Весна в родном селе»</h3>
            <p class="news-card__excerpt">Ученики начальных классов представили яркие работы, посвященные красоте Золотаревки.</p>
          </div>
        </article>
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

  <!-- ===== FOOTER ===== -->
