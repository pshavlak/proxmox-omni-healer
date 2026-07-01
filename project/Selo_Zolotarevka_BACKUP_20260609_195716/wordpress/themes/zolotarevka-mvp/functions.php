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

function zolo_post_type_icon($post_type) {
    $icons = [
        'school_news' => '🎓',
        'kindergarten_news' => '🧸',
        'farm_production' => '🌾',
        'farm_vacancies' => '💼',
        'sports_team' => '⚽',
        'sports_match' => '🏆',
        'bulletin_board' => '📋',
        'gallery' => '📸',
    ];

    return $icons[$post_type] ?? '📰';
}

function zolo_post_type_label($post_type) {
    $labels = [
        'school_news' => 'Школа',
        'kindergarten_news' => 'Детский сад',
        'farm_production' => 'Совхоз',
        'farm_vacancies' => 'Совхоз',
        'sports_team' => 'Спорт',
        'sports_match' => 'Спорт',
        'bulletin_board' => 'Объявления',
        'gallery' => 'Медиа',
    ];

    return $labels[$post_type] ?? 'Новости';
}

function zolo_get_recent_content_items($post_types, $limit = 3) {
    $query = new WP_Query([
        'post_type' => (array) $post_types,
        'post_status' => 'publish',
        'posts_per_page' => max(1, absint($limit)),
        'orderby' => 'date',
        'order' => 'DESC',
        'no_found_rows' => true,
    ]);

    $items = [];
    foreach ($query->posts as $post) {
        $items[] = [
            'id' => $post->ID,
            'title' => get_the_title($post),
            'excerpt' => get_the_excerpt($post),
            'date' => get_the_date('j F Y', $post),
            'link' => get_permalink($post),
            'post_type' => $post->post_type,
            'icon' => zolo_post_type_icon($post->post_type),
            'section' => zolo_post_type_label($post->post_type),
        ];
    }

    return $items;
}
