<script setup>
defineProps({
  groups: {
    type: Array,
    required: true,
  },
  activeSection: {
    type: String,
    required: true,
  },
  isLoggedIn: {
    type: Boolean,
    required: true,
  },
  currentUser: {
    type: Object,
    default: null,
  },
});

const emit = defineEmits(["navigate", "close"]);
</script>

<template>
  <div class="sidebar">
    <div class="brand-block">
      <div class="brand-mark">导</div>
      <div>
        <p class="brand-subtitle">AI 工具导航</p>
        <h2>中文导航站</h2>
      </div>
      <button class="close-sidebar" type="button" @click="emit('close')">关闭</button>
    </div>

    <div class="user-chip" :class="{ logged: isLoggedIn }">
      <strong>{{ isLoggedIn && currentUser ? currentUser.username : "访客模式" }}</strong>
      <span>{{ isLoggedIn ? "已登录，可查看私有导航" : "未登录，仅显示公共导航" }}</span>
    </div>

    <nav class="sidebar-nav">
      <section v-for="group in groups" :key="group.title" class="sidebar-group">
        <p class="sidebar-title">{{ group.title }}</p>
        <button
          v-for="link in group.links"
          :key="link.id"
          class="sidebar-link"
          :class="{ active: activeSection === link.id }"
          type="button"
          @click="emit('navigate', link.id)"
        >
          <span>{{ link.label }}</span>
          <small>{{ link.meta }}</small>
        </button>
      </section>
    </nav>
  </div>
</template>
