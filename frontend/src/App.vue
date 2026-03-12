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
const adminCategories = ref([]);
const loading = ref(false);
const authLoading = ref(false);
const adminLoading = ref(false);
const categorySubmitting = ref(false);
const itemSubmitting = ref(false);
const errorMessage = ref("");
const adminMessage = ref("");
const sidebarOpen = ref(false);
const activeSection = ref("public-overview");
const showLoginModal = ref(false);
const adminPanelOpen = ref(false);
const loginForm = ref({
  username: "admin",
  password: "ChangeMe123!",
});
const categoryForm = ref({
  name: "",
  is_private: false,
});
const itemForm = ref({
  title: "",
  url: "",
  description: "",
  sort_order: 0,
  category_id: "",
});

const heroBanners = [
  { title: "每日快讯", subtitle: "发现今天值得关注的新工具与新栏目", tone: "blue" },
  { title: "免费社群", subtitle: "整理可直接加入的公开频道与交流入口", tone: "green" },
  { title: "最新项目", subtitle: "持续补充高质量新站点，优先展示中文资源", tone: "lavender" },
  { title: "热门教程", subtitle: "把常用工作流、提示词与上手文档放在前排", tone: "cyan" },
];

const promoStrips = [
  "精选合集：面向中文用户的导航首页改版，突出分类浏览与快速到达。",
  "管理员登录后可直接录入公共或私有导航，首页分组会立即同步刷新。",
];

const isLoggedIn = computed(() => Boolean(token.value));
const isAdmin = computed(() => Boolean(currentUser.value?.is_admin));

const publicSection = computed(() => ({
  id: "public-overview",
  title: "公共导航",
  badge: "全部可见",
  description: "无需登录即可访问的公开站点与工具集合。",
  categories: publicCategories.value,
}));

const privateSection = computed(() => ({
  id: "private-overview",
  title: "私有导航",
  badge: isLoggedIn.value ? "已解锁" : "登录后可见",
  description: isLoggedIn.value
    ? "已登录账号可见的内部资源、协作平台与运维工具。"
    : "当前隐藏具体内容，登录后会展示完整分类与站点卡片。",
  categories: privateCategories.value,
}));

const groupedAdminCategories = computed(() => ({
  public: adminCategories.value.filter((category) => !category.is_private),
  private: adminCategories.value.filter((category) => category.is_private),
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

  const groups = [
    {
      title: "公共分组",
      links: [{ id: "public-overview", label: "公共导航总览", meta: "无需登录" }, ...publicLinks],
    },
    {
      title: "私有分组",
      links: [
        {
          id: "private-overview",
          label: "私有导航总览",
          meta: isLoggedIn.value ? "已解锁" : "需登录",
        },
        ...privateLinks,
      ],
    },
  ];

  if (isAdmin.value) {
    groups.push({
      title: "管理",
      links: [{ id: "admin-console", label: "管理后台", meta: "分类与导航录入" }],
    });
  }

  return groups;
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
  if (id === "admin-console") {
    adminPanelOpen.value = true;
  }
  activeSection.value = id;
  sidebarOpen.value = false;
  requestAnimationFrame(() => {
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  });
}

function openLoginModal() {
  errorMessage.value = "";
  showLoginModal.value = true;
}

function closeLoginModal() {
  showLoginModal.value = false;
}

function resetAdminForms() {
  categoryForm.value = {
    name: "",
    is_private: false,
  };
  itemForm.value = {
    title: "",
    url: "",
    description: "",
    sort_order: 0,
    category_id: adminCategories.value[0]?.id ?? "",
  };
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

async function loadAdminCategories() {
  if (!isAdmin.value) {
    adminCategories.value = [];
    return;
  }

  adminLoading.value = true;

  try {
    adminCategories.value = await apiRequest("/admin/categories");
    if (!itemForm.value.category_id && adminCategories.value.length > 0) {
      itemForm.value.category_id = adminCategories.value[0].id;
    }
  } finally {
    adminLoading.value = false;
  }
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
      await loadAdminCategories();
    } else {
      currentUser.value = null;
      privateCategories.value = [];
      adminCategories.value = [];
      adminPanelOpen.value = false;
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
    closeLoginModal();
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
  adminCategories.value = [];
  adminPanelOpen.value = false;
  showLoginModal.value = false;
  localStorage.removeItem("access_token");
  activeSection.value = "public-overview";
}

async function submitCategory() {
  categorySubmitting.value = true;
  adminMessage.value = "";
  errorMessage.value = "";

  try {
    await apiRequest("/admin/categories", {
      method: "POST",
      body: JSON.stringify({
        name: categoryForm.value.name.trim(),
        is_private: categoryForm.value.is_private,
      }),
    });
    await refreshData();
    adminMessage.value = "分类已创建并同步到首页。";
    resetAdminForms();
  } catch (error) {
    errorMessage.value = error.message;
  } finally {
    categorySubmitting.value = false;
  }
}

async function submitNavItem() {
  itemSubmitting.value = true;
  adminMessage.value = "";
  errorMessage.value = "";

  try {
    await apiRequest("/admin/nav-items", {
      method: "POST",
      body: JSON.stringify({
        title: itemForm.value.title.trim(),
        url: itemForm.value.url.trim(),
        description: itemForm.value.description.trim() || null,
        sort_order: Number(itemForm.value.sort_order) || 0,
        category_id: Number(itemForm.value.category_id),
      }),
    });
    await refreshData();
    adminMessage.value = "导航项已创建并刷新首页分组。";
    itemForm.value = {
      title: "",
      url: "",
      description: "",
      sort_order: 0,
      category_id: adminCategories.value[0]?.id ?? "",
    };
  } catch (error) {
    errorMessage.value = error.message;
  } finally {
    itemSubmitting.value = false;
  }
}

onMounted(async () => {
  await refreshData();
  resetAdminForms();
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
        <div class="topbar-left">
          <button class="sidebar-toggle" type="button" @click="sidebarOpen = !sidebarOpen">
            {{ sidebarOpen ? "收起分类" : "展开分类" }}
          </button>
          <div class="topbar-copy">
            <p class="topbar-label">中文导航站</p>
            <h1>高频工具、教程与内部资源集中入口</h1>
            <p>右上角统一处理登录与管理员入口，公共/私有导航与后台录入能力保持同一套 JWT 权限体系。</p>
          </div>
        </div>

        <div class="topbar-actions">
          <template v-if="isLoggedIn && currentUser">
            <button
              v-if="isAdmin"
              class="topbar-action ghost-button"
              type="button"
              @click="scrollToSection('admin-console')"
            >
              管理后台
            </button>
            <div class="account-chip">
              <div class="account-avatar small">{{ currentUser.username.slice(0, 1).toUpperCase() }}</div>
              <div>
                <strong>{{ currentUser.username }}</strong>
                <p>{{ currentUser.is_admin ? "管理员" : "普通用户" }}</p>
              </div>
            </div>
            <button class="topbar-action logout-button" type="button" @click="logout">退出</button>
          </template>
          <button v-else class="topbar-action login-button" type="button" @click="openLoginModal">登录</button>
        </div>
      </header>

      <main class="main-layout">
        <section class="hero-panel">
          <HeroBanners :banners="heroBanners" :promos="promoStrips" />

          <section class="auth-panel">
            <div class="panel-heading">
              <div>
                <p class="panel-kicker">账号状态</p>
                <h2>{{ isLoggedIn && currentUser ? "登录状态正常" : "登录后解锁私有导航" }}</h2>
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
                  <p>{{ currentUser.is_admin ? "管理员账号，可录入导航" : "普通账号，可查看私有导航" }}</p>
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
              <p class="auth-note" v-if="isAdmin">右上角已显示“管理后台”入口，可新增分类和导航项。</p>
            </template>

            <template v-else>
              <div class="auth-callout">
                <p>登录按钮已移到页面右上角，点击后会以弹窗方式完成账号密码登录。</p>
                <button type="button" class="login-button inline-login" @click="openLoginModal">打开登录弹窗</button>
              </div>
            </template>
          </section>
        </section>

        <p v-if="errorMessage" class="error-banner">{{ errorMessage }}</p>
        <p v-if="adminMessage" class="success-banner">{{ adminMessage }}</p>

        <section
          v-if="isAdmin && adminPanelOpen"
          id="admin-console"
          class="admin-panel"
          @mouseenter="updateActiveSection('admin-console')"
        >
          <div class="admin-panel-header">
            <div>
              <p class="section-kicker">Admin Console</p>
              <h2>后台录入导航</h2>
              <p>管理员可新增公共/私有分类，并向分类中录入导航项。</p>
            </div>
            <span class="overview-badge">管理员专用</span>
          </div>

          <div class="admin-grid">
            <section class="admin-card">
              <div class="section-heading compact">
                <div>
                  <p class="section-kicker">Create Category</p>
                  <h3>新增分类</h3>
                </div>
              </div>
              <form class="admin-form" @submit.prevent="submitCategory">
                <label>
                  分类名称
                  <input v-model="categoryForm.name" required placeholder="例如：Design Resources" />
                </label>
                <label>
                  分类类型
                  <select v-model="categoryForm.is_private">
                    <option :value="false">公共</option>
                    <option :value="true">私有</option>
                  </select>
                </label>
                <button type="submit" :disabled="categorySubmitting">
                  {{ categorySubmitting ? "提交中..." : "新增分类" }}
                </button>
              </form>
            </section>

            <section class="admin-card">
              <div class="section-heading compact">
                <div>
                  <p class="section-kicker">Create Nav Item</p>
                  <h3>新增导航项</h3>
                </div>
              </div>
              <form class="admin-form" @submit.prevent="submitNavItem">
                <label>
                  标题
                  <input v-model="itemForm.title" required placeholder="例如：Figma" />
                </label>
                <label>
                  URL
                  <input v-model="itemForm.url" required type="url" placeholder="https://example.com" />
                </label>
                <label>
                  描述
                  <input v-model="itemForm.description" placeholder="一句简短描述" />
                </label>
                <label>
                  排序
                  <input v-model="itemForm.sort_order" type="number" min="0" />
                </label>
                <label>
                  所属分类
                  <select v-model="itemForm.category_id" required>
                    <option disabled value="">请选择分类</option>
                    <option v-for="category in adminCategories" :key="category.id" :value="category.id">
                      {{ category.name }} / {{ category.is_private ? "私有" : "公共" }}
                    </option>
                  </select>
                </label>
                <button type="submit" :disabled="itemSubmitting || adminCategories.length === 0">
                  {{ itemSubmitting ? "提交中..." : "新增导航项" }}
                </button>
              </form>
            </section>
          </div>

          <div class="admin-lists">
            <section class="admin-card">
              <div class="section-heading compact">
                <div>
                  <p class="section-kicker">Public Categories</p>
                  <h3>公共分类列表</h3>
                </div>
                <span class="section-count">{{ groupedAdminCategories.public.length }} 个分类</span>
              </div>
              <p v-if="adminLoading">正在读取分类...</p>
              <ul v-else class="category-list">
                <li v-for="category in groupedAdminCategories.public" :key="`admin-public-${category.id}`">
                  <strong>{{ category.name }}</strong>
                  <span>{{ category.items.length }} 个导航项</span>
                </li>
              </ul>
            </section>

            <section class="admin-card">
              <div class="section-heading compact">
                <div>
                  <p class="section-kicker">Private Categories</p>
                  <h3>私有分类列表</h3>
                </div>
                <span class="section-count">{{ groupedAdminCategories.private.length }} 个分类</span>
              </div>
              <p v-if="adminLoading">正在读取分类...</p>
              <ul v-else class="category-list">
                <li v-for="category in groupedAdminCategories.private" :key="`admin-private-${category.id}`">
                  <strong>{{ category.name }}</strong>
                  <span>{{ category.items.length }} 个导航项</span>
                </li>
              </ul>
            </section>
          </div>
        </section>

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
              <p>右上角登录后显示完整分类目录和工具卡片，公共与私有分区仍然独立展示。</p>
            </div>
            <button type="button" @click="openLoginModal">立即登录</button>
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

    <div v-if="showLoginModal" class="modal-overlay" @click.self="closeLoginModal">
      <section class="login-modal">
        <div class="modal-header">
          <div>
            <p class="panel-kicker">Sign In</p>
            <h2>账号密码登录</h2>
          </div>
          <button class="modal-close" type="button" @click="closeLoginModal">关闭</button>
        </div>
        <form class="login-form" @submit.prevent="login">
          <label>
            用户名
            <input v-model="loginForm.username" autocomplete="username" required />
          </label>
          <label>
            密码
            <input v-model="loginForm.password" type="password" autocomplete="current-password" required />
          </label>
          <button type="submit" :disabled="authLoading">
            {{ authLoading ? "登录中..." : "登录" }}
          </button>
        </form>
      </section>
    </div>
  </div>
</template>
