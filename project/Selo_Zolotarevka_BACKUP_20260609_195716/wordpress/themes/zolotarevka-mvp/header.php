<?php
if (!defined('ABSPATH')) {
    exit;
}
$current_slug = is_front_page() ? '' : (string) get_post_field('post_name', get_queried_object_id());
?>
<!DOCTYPE html>
<html <?php language_attributes(); ?>>
<head>
  <meta charset="<?php bloginfo('charset'); ?>">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <?php wp_head(); ?>
</head>
<body <?php body_class(); ?>>
<?php wp_body_open(); ?>

<div class="top-bar">
  <div class="container">
    <div class="top-bar__info">
      <span>🌍 Золотаревка, Россия</span>
      <span>📅 <span id="currentDate"></span></span>
    </div>
    <div class="top-bar__social">
      <a href="#" title="ВКонтакте">📘</a>
      <a href="#" title="Telegram">✈️</a>
      <a href="#" title="Одноклассники">👥</a>
      <a href="#" title="RSS">📡</a>
    </div>
  </div>
</div>

<header class="header">
  <div class="container">
    <a href="<?php echo esc_url(zolo_url('')); ?>" class="logo">
      <span class="logo__icon">🌾</span>
      <div class="logo__text">Золотаревка <small>Неофициальный портал села</small></div>
    </a>
    <button class="mobile-toggle" aria-label="Меню">☰</button>
    <nav class="nav">
      <?php foreach (zolo_nav_items() as $slug => $label) : ?>
        <div class="nav__item">
          <a href="<?php echo esc_url(zolo_url($slug)); ?>" class="nav__link <?php echo $slug === $current_slug ? 'active' : ''; ?>">
            <?php echo esc_html($label); ?>
          </a>
        </div>
      <?php endforeach; ?>
    </nav>
  </div>
</header>
