<?php
if (!defined('ABSPATH')) {
    exit;
}

function zolo_url($slug = '') {
    $slug = trim((string) $slug, '/');
    return home_url($slug === '' ? '/' : '/' . $slug . '/');
}

function zolo_theme_setup() {
    add_theme_support('title-tag');
    add_theme_support('post-thumbnails');
    add_theme_support('html5', ['search-form', 'comment-form', 'comment-list', 'gallery', 'caption']);

    register_nav_menus([
        'primary' => 'Основное меню',
    ]);
}
add_action('after_setup_theme', 'zolo_theme_setup');

function zolo_enqueue_assets() {
    wp_enqueue_style('zolo-style', get_template_directory_uri() . '/css/style.css', [], '0.1.0');
    wp_enqueue_script('zolo-main', get_template_directory_uri() . '/js/main.js', [], '0.1.0', true);
}
add_action('wp_enqueue_scripts', 'zolo_enqueue_assets');

/**
 * Nav walker to match the theme's div-based nav markup.
 */
class Zolo_Nav_Walker extends Walker_Nav_Menu {
    public function start_el(&$output, $item, $depth = 0, $args = null, $id = 0) {
        $is_active = in_array('current-menu-item', $item->classes ?? []);
        $output .= '<div class="nav__item">';
        $output .= '<a href="' . esc_url($item->url) . '" class="nav__link' . ($is_active ? ' active' : '') . '">';
        $output .= esc_html($item->title);
        $output .= '</a>';
        $output .= '</div>';
    }

    public function end_el(&$output, $item, $depth = 0, $args = null) {}

    public function start_lvl(&$output, $depth = 0, $args = null) {}
    public function end_lvl(&$output, $depth = 0, $args = null) {}
}

function zolo_nav_items() {
    return [
        '' => 'Главная',
        'school' => 'Школа',
        'kindergarten' => 'Детский сад',
        'farm' => 'Совхоз',
        'sports' => 'Спорт',
        'village-life' => 'Жизнь села',
        'media' => 'Медиа',
        'news' => 'Новости',
    ];
}
