<script setup>
import { computed, onMounted, ref } from "vue";
import HeroBanners from "./components/HeroBanners.vue";
import SidebarNav from "./components/SidebarNav.vue";
import ToolGridSection from "./components/ToolGridSection.vue";

const API_BASE = import.meta.env.VITE_API_BASE || "/api";

const token = ref(localStorage.getItem("access_token") || "");
const currentUser = ref(null);
const publicCategories = ref([]);
const privateCategories = ref([]);
const loading = ref(false);
const authLoading = ref(false);
const errorMessage = ref("");
const sidebarOpen = ref(false);
const activeSection = ref("public-overview");
const loginForm = ref({
  username: "admin",
  password: "ChangeMe123!",
});

const heroBanners = [
  { title: "每日快讯", subtitle: "发现今天值得关注的新工具与新栏目", tone: "blue" },
  { title: "免费社群", subtitle: "整理可直接加入的公开频道与交流入口", tone: "green" },
  { title: "最新项目", subtitle: "持续补充高质量新站点，优先展示中文资源", tone: "lavender" },
  { title: "热门教程", subtitle: "把常用工作流、提示词与上手文档放在前排", tone: "cyan" },
];

const promoStrips = [
  "精选合集：面向中文用户的导航首页改版，突出分类浏览与快速到达。",
  "登录后自动解锁内部资源分组，公共与私有内容仍然严格分层。",
];

const isLoggedIn = computed(() => Boolean(token.value));

const publicSection = computed(() => ({
  id: "public-overview",
  title: "公共导航",
  badge: "全部可见",
  description: "无需登录即可访问的公开站点与工具集合。",
  kind: "public",
  categories: publicCategories.value,
}));

const privateSection = computed(() => ({
  id: "private-overview",
  title: "私有导航",
  badge: isLoggedIn.value ? "已解锁" : "登录后可见",
  description: isLoggedIn.value
    ? "已登录账号可见的内部资源、协作平台与运维工具。"
    : "当前隐藏具体内容，登录后会展示完整分类与站点卡片。",
  kind: "private",
  categories: privateCategories.value,
}));

const sidebarGroups = computed(() => {
  const publicLinks = publicCategories.value.map((category) => ({
    id: createCategoryId("public", category.name),
    label: category.name,
    meta: `${category.items.length} 个站点`,
  }));

  const privateLinks = isLoggedIn.value
    ? privateCategories.value.map((category) => ({
        id: createCategoryId("private", category.name),
        label: category.name,
        meta: `${category.items.length} 个站点`,
      }))
    : [];

  return [
    {
      title: "公共分组",
      links: [{ id: "public-overview", label: "公共导航总览", meta: "无需登录" }, ...publicLinks],
    },
    {
      title: "私有分组",
      links: [{ id: "private-overview", label: "私有导航总览", meta: isLoggedIn.value ? "已解锁" : "需登录" }, ...privateLinks],
    },
  ];
});

async function apiRequest(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (token.value) {
    headers.Authorization = `Bearer ${token.value}`;
  }

  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(data.detail || "Request failed");
  }

  return data;
}

function createCategoryId(scope, name) {
  return `${scope}-${name}`
    .toLowerCase()
    .replace(/[^a-z0-9\u4e00-\u9fa5]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function updateActiveSection(id) {
  activeSection.value = id;
}

function scrollToSection(id) {
  activeSection.value = id;
  sidebarOpen.value = false;
  const element = document.getElementById(id);
  if (element) {
    element.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

async function loadPublicNavigation() {
  publicCategories.value = await apiRequest("/nav/public");
}

async function loadPrivateNavigation() {
  if (!isLoggedIn.value) {
    privateCategories.value = [];
    return;
  }
  privateCategories.value = await apiRequest("/nav/private");
}

async function loadCurrentUser() {
  if (!isLoggedIn.value) {
    currentUser.value = null;
    return;
  }

  try {
    currentUser.value = await apiRequest("/auth/me");
  } catch (error) {
    logout();
    throw error;
  }
}

async function refreshData() {
  loading.value = true;
  errorMessage.value = "";

  try {
    await loadPublicNavigation();
    if (isLoggedIn.value) {
      await loadCurrentUser();
      await loadPrivateNavigation();
    } else {
      currentUser.value = null;
      privateCategories.value = [];
    }
  } catch (error) {
    errorMessage.value = error.message;
  } finally {
    loading.value = false;
  }
}

async function login() {
  authLoading.value = true;
  errorMessage.value = "";

  try {
    const data = await apiRequest("/auth/login", {
      method: "POST",
      body: JSON.stringify(loginForm.value),
    });
    token.value = data.access_token;
    localStorage.setItem("access_token", token.value);
    await refreshData();
  } catch (error) {
    errorMessage.value = error.message;
  } finally {
    authLoading.value = false;
  }
}

function logout() {
  token.value = "";
  currentUser.value = null;
  privateCategories.value = [];
  localStorage.removeItem("access_token");
  activeSection.value = "public-overview";
}

onMounted(() => {
  refreshData();
});
</script>

<template>
  <div class="page-shell">
    <aside class="sidebar-column" :class="{ open: sidebarOpen }">
      <SidebarNav
        :groups="sidebarGroups"
        :active-section="activeSection"
        :is-logged-in="isLoggedIn"
        :current-user="currentUser"
        @navigate="scrollToSection"
        @close="sidebarOpen = false"
      />
    </aside>

    <div class="content-column">
      <header class="topbar">
        <button class="sidebar-toggle" type="button" @click="sidebarOpen = !sidebarOpen">
          {{ sidebarOpen ? "收起分类" : "展开分类" }}
        </button>
        <div class="topbar-copy">
          <p class="topbar-label">中文导航站</p>
          <h1>高频工具、教程与内部资源集中入口</h1>
          <p>
            首页改为侧边栏 + 横幅 + 分组卡片结构，保留原有公共导航与登录解锁私有导航的产品逻辑。
          </p>
        </div>
      </header>

      <main class="main-layout">
        <section class="hero-panel">
          <HeroBanners :banners="heroBanners" :promos="promoStrips" />

          <section class="auth-panel">
            <div class="panel-heading">
              <div>
                <p class="panel-kicker">账号入口</p>
                <h2>{{ isLoggedIn && currentUser ? "已登录" : "登录后解锁更多分类" }}</h2>
              </div>
              <span class="status-pill" :class="{ unlocked: isLoggedIn }">
                {{ isLoggedIn ? "私有导航已开放" : "当前仅展示公共导航" }}
              </span>
            </div>

            <template v-if="isLoggedIn && currentUser">
              <div class="account-summary">
                <div class="account-avatar">{{ currentUser.username.slice(0, 1).toUpperCase() }}</div>
                <div>
                  <strong>{{ currentUser.username }}</strong>
                  <p>{{ currentUser.is_admin ? "管理员账号" : "普通账号" }}</p>
                </div>
              </div>
              <div class="quick-stats">
                <div class="stat-card">
                  <span>公共分类</span>
                  <strong>{{ publicCategories.length }}</strong>
                </div>
                <div class="stat-card">
                  <span>私有分类</span>
                  <strong>{{ privateCategories.length }}</strong>
                </div>
              </div>
              <button class="ghost-button" type="button" @click="logout">退出登录</button>
            </template>

            <template v-else>
              <form class="login-form" @submit.prevent="login">
                <label>
                  用户名
                  <input v-model="loginForm.username" autocomplete="username" />
                </label>
                <label>
                  密码
                  <input v-model="loginForm.password" type="password" autocomplete="current-password" />
                </label>
                <button type="submit" :disabled="authLoading">
                  {{ authLoading ? "登录中..." : "登录查看私有导航" }}
                </button>
              </form>
            </template>
          </section>
        </section>

        <p v-if="errorMessage" class="error-banner">{{ errorMessage }}</p>

        <section
          :id="publicSection.id"
          class="overview-card"
          @mouseenter="updateActiveSection(publicSection.id)"
        >
          <div>
            <p class="section-kicker">Public</p>
            <h2>{{ publicSection.title }}</h2>
            <p>{{ publicSection.description }}</p>
          </div>
          <span class="overview-badge">{{ publicSection.badge }}</span>
        </section>

        <p v-if="loading" class="loading-copy">正在加载导航数据...</p>
        <template v-else>
          <ToolGridSection
            v-for="category in publicSection.categories"
            :id="createCategoryId('public', category.name)"
            :key="`public-${category.id}`"
            :title="category.name"
            :items="category.items"
            variant="public"
            @focus-section="updateActiveSection"
          />

          <section
            :id="privateSection.id"
            class="overview-card private-overview"
            @mouseenter="updateActiveSection(privateSection.id)"
          >
            <div>
              <p class="section-kicker">Private</p>
              <h2>{{ privateSection.title }}</h2>
              <p>{{ privateSection.description }}</p>
            </div>
            <span class="overview-badge private-badge">{{ privateSection.badge }}</span>
          </section>

          <div v-if="!isLoggedIn" class="locked-panel">
            <div class="locked-copy">
              <h3>私有导航暂未解锁</h3>
              <p>登录后显示完整分类目录和工具卡片，仍与公共导航分区展示。</p>
            </div>
            <button type="button" @click="scrollToSection('private-overview')">查看登录入口</button>
          </div>

          <template v-else>
            <ToolGridSection
              v-for="category in privateSection.categories"
              :id="createCategoryId('private', category.name)"
              :key="`private-${category.id}`"
              :title="category.name"
              :items="category.items"
              variant="private"
              @focus-section="updateActiveSection"
            />
          </template>
        </template>
      </main>
    </div>
  </div>
</template>
