  <section class="page-header">
    <div class="container">
      <h1 class="page-header__title">📰 Новости села</h1>
      <div class="page-header__breadcrumb">
        <a href="<?php echo esc_url(zolo_url('')); ?>">Главная</a> / Новости
      </div>
    </div>
  </section>

  <section class="content-section">
    <div class="container">

      <!-- Фильтр по категориям -->
      <div style="display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 32px;">
        <span style="font-weight: 600; padding: 8px 0;">Категории:</span>
        <a href="<?php echo esc_url(zolo_url('news')); ?>" style="padding: 6px 16px; background: var(--color-primary); color: white; border-radius: 20px; font-size: 0.9rem;">Все</a>
        <a href="?cat=school" style="padding: 6px 16px; background: var(--color-bg-alt); border-radius: 20px; font-size: 0.9rem;">📚 Школа</a>
        <a href="?cat=kindergarten" style="padding: 6px 16px; background: var(--color-bg-alt); border-radius: 20px; font-size: 0.9rem;">🧸 Детский сад</a>
        <a href="?cat=farm" style="padding: 6px 16px; background: var(--color-bg-alt); border-radius: 20px; font-size: 0.9rem;">🌾 Совхоз</a>
        <a href="?cat=sports" style="padding: 6px 16px; background: var(--color-bg-alt); border-radius: 20px; font-size: 0.9rem;">⚽ Спорт</a>
        <a href="?cat=village" style="padding: 6px 16px; background: var(--color-bg-alt); border-radius: 20px; font-size: 0.9rem;">🏘️ Село</a>
      </div>

      <!-- Лента новостей -->
      <div class="news-grid">
        <article class="news-card">
          <div class="news-card__img">🏆</div>
          <div class="news-card__body">
            <div class="news-card__meta">
              <span>📅 15 мая 2026</span>
              <span>📂 Спорт</span>
            </div>
            <h3 class="news-card__title">ФК «Золотаревка» одержал победу в районном турнире</h3>
            <p class="news-card__excerpt">Наша команда заняла первое место в ежегодном районном турнире по футболу. Поздравляем игроков и тренера! В финальном матче со счетом 3:1 была обыграна команда «Соседи».</p>
            <a href="#" class="bento__card-link">Читать далее →</a>
          </div>
        </article>

        <article class="news-card">
          <div class="news-card__img">🎓</div>
          <div class="news-card__body">
            <div class="news-card__meta">
              <span>📅 12 мая 2026</span>
              <span>📂 Школа</span>
            </div>
            <h3 class="news-card__title">Последний звонок — 2026</h3>
            <p class="news-card__excerpt">В школе прошла торжественная линейка, посвященная последнему звонку для выпускников 11-го класса. Ребят поздравили учителя, родители и глава сельсовета.</p>
            <a href="#" class="bento__card-link">Читать далее →</a>
          </div>
        </article>

        <article class="news-card">
          <div class="news-card__img">🌾</div>
          <div class="news-card__body">
            <div class="news-card__meta">
              <span>📅 10 мая 2026</span>
              <span>📂 Совхоз</span>
            </div>
            <h3 class="news-card__title">Начало посевной кампании</h3>
            <p class="news-card__excerpt">Совхоз «Золотаревский» приступил к весенним полевым работам. В этом году планируется засеять более 500 гектаров зерновыми культурами.</p>
            <a href="#" class="bento__card-link">Читать далее →</a>
          </div>
        </article>

        <article class="news-card">
          <div class="news-card__img">🎭</div>
          <div class="news-card__body">
            <div class="news-card__meta">
              <span>📅 9 мая 2026</span>
              <span>📂 Село</span>
            </div>
            <h3 class="news-card__title">Праздничный концерт ко Дню Победы</h3>
            <p class="news-card__excerpt">В Доме Культуры прошел праздничный концерт, посвященный 81-й годовщине Победы в Великой Отечественной войне.</p>
            <a href="#" class="bento__card-link">Читать далее →</a>
          </div>
        </article>

        <article class="news-card">
          <div class="news-card__img">🧸</div>
          <div class="news-card__body">
            <div class="news-card__meta">
              <span>📅 5 мая 2026</span>
              <span>📂 Детский сад</span>
            </div>
            <h3 class="news-card__title">Весенний утренник в детском саду</h3>
            <p class="news-card__excerpt">Малыши из младшей группы порадовали родителей весенним концертом «Цветы для мамы». Было много стихов и песен.</p>
            <a href="#" class="bento__card-link">Читать далее →</a>
          </div>
        </article>

        <article class="news-card">
          <div class="news-card__img">🏅</div>
          <div class="news-card__body">
            <div class="news-card__meta">
              <span>📅 2 мая 2026</span>
              <span>📂 Школа</span>
            </div>
            <h3 class="news-card__title">Победа на районной олимпиаде</h3>
            <p class="news-card__excerpt">Ученик 9-го класса Иван Петров занял 1-е место на районной олимпиаде по математике. Поздравляем!</p>
            <a href="#" class="bento__card-link">Читать далее →</a>
          </div>
        </article>

        <article class="news-card">
          <div class="news-card__img">🚜</div>
          <div class="news-card__body">
            <div class="news-card__meta">
              <span>📅 28 апреля 2026</span>
              <span>📂 Совхоз</span>
            </div>
            <h3 class="news-card__title">Обновление парка техники</h3>
            <p class="news-card__excerpt">Совхоз приобрел новый трактор и сеялку. Это позволит увеличить производительность и сократить сроки посевной.</p>
            <a href="#" class="bento__card-link">Читать далее →</a>
          </div>
        </article>

        <article class="news-card">
          <div class="news-card__img">🎨</div>
          <div class="news-card__body">
            <div class="news-card__meta">
              <span>📅 25 апреля 2026</span>
              <span>📂 Село</span>
            </div>
            <h3 class="news-card__title">Субботник в Золотаревке</h3>
            <p class="news-card__excerpt">Жители села вышли на весенний субботник. Были очищены улицы, парк и пришкольная территория.</p>
            <a href="#" class="bento__card-link">Читать далее →</a>
          </div>
        </article>
      </div>

      <!-- Пагинация -->
      <div style="display: flex; justify-content: center; gap: 8px; margin-top: 40px;">
        <span style="padding: 10px 18px; background: var(--color-primary); color: white; border-radius: var(--radius-sm); font-weight: 600;">1</span>
        <a href="#" style="padding: 10px 18px; background: var(--color-white); border-radius: var(--radius-sm); font-weight: 600; box-shadow: var(--shadow-sm);">2</a>
        <a href="#" style="padding: 10px 18px; background: var(--color-white); border-radius: var(--radius-sm); font-weight: 600; box-shadow: var(--shadow-sm);">3</a>
      </div>

    </div>
  </section>

  <!-- ===== SUGGEST NEWS ===== -->
  <section class="suggest-block">
    <div class="container">
      <h2 class="suggest-block__title">💡 Хотите предложить новость?</h2>
      <p class="suggest-block__text">Жители села могут присылать свои фото и истории. Лучшие публикации попадут на главную!</p>
      <button class="suggest-block__btn" data-modal="suggestModal">Предложить новость</button>
    </div>
  </section>

