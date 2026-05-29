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
}
add_action('after_setup_theme', 'zolo_theme_setup');

function zolo_enqueue_assets() {
    wp_enqueue_style('zolo-style', get_template_directory_uri() . '/css/style.css', [], '0.1.0');
    wp_enqueue_script('zolo-main', get_template_directory_uri() . '/js/main.js', [], '0.1.0', true);
}
add_action('wp_enqueue_scripts', 'zolo_enqueue_assets');

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
