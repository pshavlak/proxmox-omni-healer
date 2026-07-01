<?php
if (!defined('ABSPATH')) {
    exit;
}
$current_slug = is_front_page() ? '' : (string) get_post_field('post_name', get_queried_object_id());
$settings = zolo_get_site_settings();
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
      <span>🌍 <?php echo esc_html($settings['topbar_region']); ?></span>
      <span>📅 <span id="currentDate"></span></span>
    </div>
    <div class="top-bar__social">
      <a href="<?php echo esc_url($settings['social_vk']); ?>" title="ВКонтакте">📘</a>
      <a href="<?php echo esc_url($settings['social_telegram']); ?>" title="Telegram">✈️</a>
      <a href="<?php echo esc_url($settings['social_ok']); ?>" title="Одноклассники">👥</a>
      <a href="<?php echo esc_url($settings['social_rss']); ?>" title="RSS">📡</a>
    </div>
  </div>
</div>

<header class="header">
  <div class="container">
    <a href="<?php echo esc_url(zolo_url('')); ?>" class="logo">
      <span class="logo__icon">🌾</span>
      <div class="logo__text">Золотаревка <small><?php echo esc_html($settings['site_tagline']); ?></small></div>
    </a>
    <button class="mobile-toggle" aria-label="Меню">☰</button>
    <nav class="nav">
      <?php if (has_nav_menu('primary')) : ?>
        <?php
        wp_nav_menu([
            'theme_location' => 'primary',
            'container'      => false,
            'menu_class'     => '',
            'depth'          => 1,
            'items_wrap'     => '%3$s',
            'walker'         => new Zolo_Nav_Walker(),
        ]);
        ?>
      <?php else : ?>
        <?php foreach (zolo_nav_items() as $slug => $label) : ?>
          <div class="nav__item">
            <a href="<?php echo esc_url(zolo_url($slug)); ?>" class="nav__link <?php echo $slug === $current_slug ? 'active' : ''; ?>">
              <?php echo esc_html($label); ?>
            </a>
          </div>
        <?php endforeach; ?>
      <?php endif; ?>
    </nav>
  </div>
</header>
