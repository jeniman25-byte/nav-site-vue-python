<script setup>
import { computed, onMounted, onUnmounted, ref } from "vue";
import SidebarNav from "./components/SidebarNav.vue";
import ToolGridSection from "./components/ToolGridSection.vue";

const API_BASE = import.meta.env.VITE_API_BASE || "/api";
const HOME_PATH = "/";
const ADMIN_PATH = "/admin";

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
const activeSection = ref("filter-all");
const showLoginModal = ref(false);
const searchQuery = ref("");
const selectedCategoryKey = ref("all");
const currentPath = ref(window.location.pathname || HOME_PATH);
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

const isLoggedIn = computed(() => Boolean(token.value));
const isAdmin = computed(() => Boolean(currentUser.value?.is_admin));
const isAdminRoute = computed(() => currentPath.value === ADMIN_PATH);
const normalizedQuery = computed(() => searchQuery.value.trim().toLowerCase());

const filteredPublicCategories = computed(() => filterCategories(publicCategories.value, normalizedQuery.value));
const filteredPrivateCategories = computed(() => {
  if (!isLoggedIn.value) {
    return [];
  }
  return filterCategories(privateCategories.value, normalizedQuery.value);
});

const allVisibleCategories = computed(() => [
  ...filteredPublicCategories.value.map((category) => ({ ...category, scope: "public" })),
  ...filteredPrivateCategories.value.map((category) => ({ ...category, scope: "private" })),
]);

const hasVisibleResults = computed(() => {
  if (!normalizedQuery.value) {
    return allVisibleCategories.value.length > 0;
  }
  return allVisibleCategories.value.length > 0;
});

const displayedCategories = computed(() => {
  if (selectedCategoryKey.value === "all") {
    return allVisibleCategories.value;
  }

  const [scope, rawId] = selectedCategoryKey.value.split(":");
  const targetId = Number(rawId);
  return allVisibleCategories.value.filter((category) => category.scope === scope && category.id === targetId);
});

const sidebarGroups = computed(() => {
  if (isAdminRoute.value) {
    return [
      {
        title: "管理页面",
        links: [
          { id: "admin-overview", label: "分类列表", meta: `${adminCategories.value.length} 个分类` },
          { id: "admin-create-category", label: "新增分类", meta: "名称 + 私有属性" },
          { id: "admin-create-item", label: "新增导航项", meta: "录入标题 / URL / 描述 / 排序" },
        ],
      },
    ];
  }

  const categoryLinks = allVisibleCategories.value.map((category) => ({
    id: `filter-${category.scope}:${category.id}`,
    label: category.name,
    meta: `${category.items.length} 个站点`,
  }));

  return [
    {
      title: "分类筛选",
      links: [
        { id: "filter-all", label: "全部分类", meta: `${allVisibleCategories.value.length} 个分类` },
        ...categoryLinks,
      ],
    },
  ];
});

const groupedAdminCategories = computed(() => ({
  public: adminCategories.value.filter((category) => !category.is_private),
  private: adminCategories.value.filter((category) => category.is_private),
}));

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

function filterCategories(categories, query) {
  if (!query) {
    return categories;
  }

  return categories
    .map((category) => {
      const categoryMatch = category.name.toLowerCase().includes(query);
      const items = categoryMatch
        ? category.items
        : category.items.filter((item) => {
            const title = item.title?.toLowerCase() || "";
            const description = item.description?.toLowerCase() || "";
            return title.includes(query) || description.includes(query);
          });

      return { ...category, items };
    })
    .filter((category) => category.items.length > 0);
}

function createCategoryId(scope, name) {
  return `${scope}-${name}`
    .toLowerCase()
    .replace(/[^a-z0-9\u4e00-\u9fa5]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function syncPath() {
  currentPath.value = window.location.pathname || HOME_PATH;
  sidebarOpen.value = false;
  activeSection.value = isAdminRoute.value ? "admin-overview" : `filter-${selectedCategoryKey.value}`;
}

function navigateTo(path) {
  if (window.location.pathname === path) {
    return;
  }
  window.history.pushState({}, "", path);
  syncPath();
}

function updateActiveSection(id) {
  activeSection.value = id;
}

function scrollToSection(id) {
  activeSection.value = id;
  sidebarOpen.value = false;
  requestAnimationFrame(() => {
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  });
}

function handleSidebarNavigate(id) {
  if (isAdminRoute.value) {
    if (currentPath.value !== ADMIN_PATH) {
      navigateTo(ADMIN_PATH);
    }
    scrollToSection(id);
    return;
  }

  if (id === "filter-all") {
    selectedCategoryKey.value = "all";
  } else if (id.startsWith("filter-")) {
    selectedCategoryKey.value = id.replace("filter-", "");
  }
  activeSection.value = `filter-${selectedCategoryKey.value}`;
  sidebarOpen.value = false;
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
  showLoginModal.value = false;
  localStorage.removeItem("access_token");
  if (isAdminRoute.value) {
    navigateTo(HOME_PATH);
  } else {
    selectedCategoryKey.value = "all";
    activeSection.value = "filter-all";
  }
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
  syncPath();
  window.addEventListener("popstate", syncPath);
  await refreshData();
  resetAdminForms();
});

onUnmounted(() => {
  window.removeEventListener("popstate", syncPath);
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
        @navigate="handleSidebarNavigate"
        @close="sidebarOpen = false"
      />
    </aside>

    <div class="content-column">
      <header class="topbar">
        <div class="topbar-main">
          <div class="topbar-left">
            <button class="sidebar-toggle" type="button" @click="sidebarOpen = !sidebarOpen">
              {{ sidebarOpen ? "收起分类" : "展开分类" }}
            </button>
            <div class="topbar-copy compact">
              <p class="topbar-label">中文导航站</p>
              <h1>{{ isAdminRoute ? "后台管理" : "导航首页" }}</h1>
            </div>
          </div>

          <div class="topbar-actions">
            <button
              v-if="isAdmin"
              class="topbar-action ghost-button"
              type="button"
              @click="navigateTo(isAdminRoute ? HOME_PATH : ADMIN_PATH)"
            >
              {{ isAdminRoute ? "返回首页" : "后台管理" }}
            </button>
            <template v-if="isLoggedIn && currentUser">
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
        </div>

        <div v-if="!isAdminRoute" class="search-row">
          <label class="search-field">
            <span>搜索导航</span>
            <input
              v-model="searchQuery"
              type="search"
              placeholder="按标题、描述或分类名实时搜索"
            />
          </label>
        </div>
      </header>

      <p v-if="errorMessage" class="error-banner">{{ errorMessage }}</p>
      <p v-if="adminMessage" class="success-banner">{{ adminMessage }}</p>

      <main v-if="!isAdminRoute" class="main-layout">
        <section class="overview-card">
          <div>
            <p class="section-kicker">Navigation View</p>
            <h2>分类筛选</h2>
            <p>左侧选择分类后，右侧仅展示对应站点卡片；默认展示全部分类。</p>
          </div>
          <span class="overview-badge">{{ displayedCategories.length }} / {{ allVisibleCategories.length }} 个分类</span>
        </section>

        <section v-if="!isLoggedIn" class="locked-panel">
          <div class="locked-copy">
            <h3>当前为访客模式</h3>
            <p>已展示全部公共分类，登录后可在左侧继续筛选私有分类。</p>
          </div>
          <button type="button" class="login-button" @click="openLoginModal">立即登录</button>
        </section>

        <div v-if="loading" class="empty-state">
          <h3>正在加载导航数据</h3>
          <p class="loading-copy">请稍候，分类与卡片会同步更新。</p>
        </div>

        <div v-else-if="!hasVisibleResults" class="empty-state">
          <h3>没有找到匹配结果</h3>
          <p>当前关键词会匹配分类名、导航标题和描述，试试更短的词或其他别名。</p>
        </div>

        <div v-else-if="displayedCategories.length === 0" class="empty-state">
          <h3>当前分类暂无可展示站点</h3>
          <p>可切换到“全部分类”查看完整列表。</p>
        </div>

        <template v-else>
          <ToolGridSection
            v-for="category in displayedCategories"
            :id="`filter-${category.scope}:${category.id}`"
            :key="`${category.scope}-${category.id}`"
            :title="category.name"
            :items="category.items"
            :variant="category.scope"
            @focus-section="updateActiveSection"
          />
        </template>
      </main>

      <main v-else class="main-layout">
        <template v-if="!isLoggedIn">
          <section class="admin-empty-state">
            <p class="section-kicker">Admin Access</p>
            <h2>请先登录管理员账号</h2>
            <p>后台管理已经独立到前端路由 `/admin`，未登录状态不会展示录入表单。</p>
            <button type="button" class="topbar-action login-button" @click="openLoginModal">打开登录弹窗</button>
          </section>
        </template>

        <template v-else-if="!isAdmin">
          <section class="admin-empty-state">
            <p class="section-kicker">403 Forbidden</p>
            <h2>当前账号没有后台权限</h2>
            <p>后端管理员接口已要求管理员身份，非管理员访问会返回 403。</p>
            <button type="button" class="topbar-action ghost-button" @click="navigateTo(HOME_PATH)">返回首页</button>
          </section>
        </template>

        <template v-else>
          <section
            id="admin-overview"
            class="admin-panel"
            @mouseenter="updateActiveSection('admin-overview')"
          >
            <div class="admin-panel-header">
              <div>
                <p class="section-kicker">Admin Console</p>
                <h2>分类列表</h2>
                <p>管理员录入已从首页迁出，首页只保留浏览和搜索。</p>
              </div>
              <span class="overview-badge">管理员专用</span>
            </div>

            <div v-if="adminLoading" class="empty-state admin-inline-state">
              <h3>正在加载分类</h3>
              <p class="loading-copy">管理员分类列表稍后会显示在这里。</p>
            </div>
            <div v-else class="admin-lists">
              <section class="admin-card">
                <div class="section-heading compact">
                  <div>
                    <p class="section-kicker">Public Categories</p>
                    <h3>公共分类</h3>
                  </div>
                  <span class="section-count">{{ groupedAdminCategories.public.length }}</span>
                </div>
                <ul class="category-list">
                  <li v-for="category in groupedAdminCategories.public" :key="category.id">
                    <strong>{{ category.name }}</strong>
                    <span>{{ category.items.length }} 个导航项</span>
                  </li>
                </ul>
              </section>

              <section class="admin-card">
                <div class="section-heading compact">
                  <div>
                    <p class="section-kicker">Private Categories</p>
                    <h3>私有分类</h3>
                  </div>
                  <span class="section-count">{{ groupedAdminCategories.private.length }}</span>
                </div>
                <ul class="category-list">
                  <li v-for="category in groupedAdminCategories.private" :key="category.id">
                    <strong>{{ category.name }}</strong>
                    <span>{{ category.items.length }} 个导航项</span>
                  </li>
                </ul>
              </section>
            </div>
          </section>

          <div class="admin-grid">
            <section
              id="admin-create-category"
              class="admin-card"
              @mouseenter="updateActiveSection('admin-create-category')"
            >
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

            <section
              id="admin-create-item"
              class="admin-card"
              @mouseenter="updateActiveSection('admin-create-item')"
            >
              <div class="section-heading compact">
                <div>
                  <p class="section-kicker">Create Nav Item</p>
                  <h3>新增导航项</h3>
                </div>
              </div>
              <form class="admin-form" @submit.prevent="submitNavItem">
                <label>
                  所属分类
                  <select v-model="itemForm.category_id" required>
                    <option disabled value="">请选择分类</option>
                    <option v-for="category in adminCategories" :key="category.id" :value="category.id">
                      {{ category.name }} / {{ category.is_private ? "私有" : "公共" }}
                    </option>
                  </select>
                </label>
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
                <button type="submit" :disabled="itemSubmitting || adminCategories.length === 0">
                  {{ itemSubmitting ? "提交中..." : "新增导航项" }}
                </button>
              </form>
            </section>
          </div>
        </template>
      </main>
    </div>
  </div>

  <div v-if="showLoginModal" class="modal-overlay" @click.self="closeLoginModal">
    <section class="login-modal">
      <div class="modal-header">
        <div>
          <p class="section-kicker">Account Login</p>
          <h2>登录后可查看私有导航</h2>
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
</template>
