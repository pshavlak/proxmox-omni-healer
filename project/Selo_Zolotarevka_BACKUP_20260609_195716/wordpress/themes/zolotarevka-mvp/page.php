<?php
get_header();

$slug = (string) get_post_field('post_name', get_queried_object_id());
$known = ['school', 'kindergarten', 'farm', 'sports', 'village-life', 'media', 'news'];

if (in_array($slug, $known, true)) {
    get_template_part('template-parts/pages/' . $slug);
} else {
    ?>
    <section class="page-header">
      <div class="container">
        <h1 class="page-header__title"><?php the_title(); ?></h1>
      </div>
    </section>
    <section class="content-section">
      <div class="container">
        <?php
        while (have_posts()) {
            the_post();
            the_content();
        }
        ?>
      </div>
    </section>
    <?php
}

get_footer();
