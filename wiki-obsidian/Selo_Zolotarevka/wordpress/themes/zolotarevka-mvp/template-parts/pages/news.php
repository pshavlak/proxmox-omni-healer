<?php
$slug = 'news';
$is_preview = isset($_GET['zolo_preview']) && $_GET['zolo_preview'] === $slug && current_user_can('zolo_edit_site_content');
$c = $is_preview ? zolo_get_page_content_draft($slug) : zolo_get_page_content($slug);
?>
<?php if ($is_preview): ?>
<div style="position:sticky;top:0;z-index:99999;background:#ffc107;color:#000;text-align:center;padding:8px;font-weight:bold;">
  👁 РЕЖИМ ПРЕДПРОСМОТРА — показан черновик
</div>
<?php endif; ?>

<section class="page-header">
  <div class="container">
    <h1 class="page-header__title"><?php echo esc_html($c['page_title']); ?></h1>
    <div class="page-header__breadcrumb">
      <a href="<?php echo esc_url(zolo_url('')); ?>">Главная</a> / Новости
    </div>
  </div>
</section>

<section class="content-section">
  <div class="container">

<?php
// Category filter mapping
$cat_map = [
  'school'       => ['school_news', 'kindergarten_news'],
  'kindergarten' => ['kindergarten_news'],
  'farm'         => ['farm_production', 'farm_vacancies'],
  'sports'       => ['sports_team', 'sports_match'],
  'village'      => ['bulletin_board', 'gallery'],
];

$cat_labels = [
  'school'       => '📚 Школа',
  'kindergarten' => '🧸 Детский сад',
  'farm'         => '🌾 Совхоз',
  'sports'       => '⚽ Спорт',
  'village'      => '🏘️ Село',
];

$icon_map = [
  'school_news'       => '🎓',
  'kindergarten_news' => '🧸',
  'farm_production'   => '🌾',
  'farm_vacancies'    => '🚜',
  'sports_team'       => '⚽',
  'sports_match'      => '🏆',
  'bulletin_board'    => '📋',
  'gallery'           => '📸',
];

$current_cat = isset($_GET['cat']) ? sanitize_key($_GET['cat']) : '';
$selected_types = ($current_cat && isset($cat_map[$current_cat])) ? $cat_map[$current_cat] : [];
$all_types = ['school_news', 'kindergarten_news', 'farm_production', 'farm_vacancies', 'sports_team', 'sports_match', 'bulletin_board', 'gallery'];
$post_types = !empty($selected_types) ? $selected_types : $all_types;

$paged = max(1, get_query_var('paged', 1));
$news_q = new WP_Query([
  'post_type'      => $post_types,
  'posts_per_page' => (int) ($c['news_per_page'] ?? 9),
  'paged'          => $paged,
  'post_status'    => 'publish',
]);
?>

      <!-- Фильтр по категориям -->
      <div style="display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 32px;">
        <span style="font-weight: 600; padding: 8px 0;">Категории:</span>
        <a href="<?php echo esc_url(zolo_url('news')); ?>" style="padding: 6px 16px; background: <?php echo $current_cat === '' ? 'var(--color-primary); color: white' : 'var(--color-bg-alt)'; ?>; border-radius: 20px; font-size: 0.9rem;">Все</a>
        <?php foreach ($cat_labels as $key => $label) : ?>
          <a href="?cat=<?php echo esc_attr($key); ?>" style="padding: 6px 16px; background: <?php echo $current_cat === $key ? 'var(--color-primary); color: white' : 'var(--color-bg-alt)'; ?>; border-radius: 20px; font-size: 0.9rem;"><?php echo esc_html($label); ?></a>
        <?php endforeach; ?>
      </div>

      <!-- Лента новостей -->
      <div class="news-grid">
        <?php while ($news_q->have_posts()) : $news_q->the_post();
            $pt = get_post_type();
        ?>
        <article class="news-card">
          <div class="news-card__img"><?php echo $icon_map[$pt] ?? '📰'; ?></div>
          <div class="news-card__body">
            <div class="news-card__meta">
              <span>📅 <?php echo get_the_date('j F Y'); ?></span>
              <span>📂 <?php echo isset($cat_labels[$current_cat]) ? $cat_labels[$current_cat] : get_post_type_object($pt)->labels->singular_name; ?></span>
            </div>
            <h3 class="news-card__title"><?php the_title(); ?></h3>
            <p class="news-card__excerpt"><?php echo get_the_excerpt(); ?></p>
            <a href="<?php the_permalink(); ?>" class="bento__card-link">Читать далее →</a>
          </div>
        </article>
        <?php endwhile; wp_reset_postdata(); ?>
      </div>

      <!-- Пагинация -->
      <?php if ($news_q->max_num_pages > 1) :
        $paginate_args = [
          'base'      => add_query_arg('paged', '%#%'),
          'format'    => '?paged=%#%',
          'current'   => $paged,
          'total'     => $news_q->max_num_pages,
          'prev_text' => '←',
          'next_text' => '→',
          'type'      => 'array',
        ];
        $links = paginate_links($paginate_args);
        if (is_array($links)) :
      ?>
      <div style="display: flex; justify-content: center; gap: 8px; margin-top: 40px;">
        <?php foreach ($links as $link) :
          $styled = str_replace(
            ['<a ', '<span aria-current="page"'],
            [
              '<a style="padding:10px 18px;background:var(--color-white);border-radius:var(--radius-sm);font-weight:600;box-shadow:var(--shadow-sm);text-decoration:none;" ',
              '<span style="padding:10px 18px;background:var(--color-primary);color:white;border-radius:var(--radius-sm);font-weight:600;" ',
            ],
            $link
          );
          echo $styled;
        endforeach; ?>
      </div>
      <?php endif; endif; ?>

    </div>
  </section>

  <!-- ===== SUGGEST NEWS ===== -->
  <section class="suggest-block">
    <div class="container">
      <h2 class="suggest-block__title"><?php echo esc_html($c['suggest_title']); ?></h2>
      <p class="suggest-block__text"><?php echo esc_html($c['suggest_text']); ?></p>
      <button class="suggest-block__btn" data-modal="suggestModal"><?php echo esc_html($c['suggest_btn_text']); ?></button>
    </div>
  </section>
