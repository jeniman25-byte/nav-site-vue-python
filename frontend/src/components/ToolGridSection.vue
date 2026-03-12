<script setup>
defineProps({
  id: {
    type: String,
    required: true,
  },
  title: {
    type: String,
    required: true,
  },
  items: {
    type: Array,
    required: true,
  },
  variant: {
    type: String,
    default: "public",
  },
});

const emit = defineEmits(["focus-section"]);
</script>

<template>
  <section :id="id" class="tool-section" @mouseenter="emit('focus-section', id)">
    <div class="section-heading">
      <div>
        <p class="section-kicker">{{ variant === "private" ? "Private Category" : "Public Category" }}</p>
        <h3>{{ title }}</h3>
      </div>
      <span class="section-count">{{ items.length }} 个工具</span>
    </div>

    <div class="tool-grid">
      <a
        v-for="item in items"
        :key="item.id"
        :href="item.url"
        target="_blank"
        rel="noreferrer"
        class="tool-card"
        :class="{ 'tool-card-private': variant === 'private' }"
      >
        <div class="tool-icon">{{ item.title.slice(0, 1) }}</div>
        <div class="tool-copy">
          <strong>{{ item.title }}</strong>
          <p>{{ item.description || "暂无描述" }}</p>
        </div>
        <span class="tool-action">进入</span>
      </a>
    </div>
  </section>
</template>
