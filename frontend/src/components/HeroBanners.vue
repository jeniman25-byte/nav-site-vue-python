<script setup>
defineProps({
  banners: {
    type: Array,
    required: true,
  },
  promos: {
    type: Array,
    required: true,
  },
});
</script>

<template>
  <section class="banner-stack">
    <div class="hero-banners">
      <article
        v-for="banner in banners"
        :key="banner.title"
        class="hero-card"
        :class="`tone-${banner.tone}`"
      >
        <p>{{ banner.title }}</p>
        <span>{{ banner.subtitle }}</span>
      </article>
    </div>

    <div class="promo-row">
      <article v-for="promo in promos" :key="promo" class="promo-card">
        {{ promo }}
      </article>
    </div>
  </section>
</template>
