<script setup>
import { computed, onMounted, ref } from "vue";

const API_BASE = "http://127.0.0.1:8000/api";
const token = ref(localStorage.getItem("access_token") || "");
const currentUser = ref(null);
const publicCategories = ref([]);
const privateCategories = ref([]);
const loading = ref(false);
const authLoading = ref(false);
const errorMessage = ref("");
const loginForm = ref({
  username: "admin",
  password: "ChangeMe123!",
});

const isLoggedIn = computed(() => Boolean(token.value));

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
}

onMounted(() => {
  refreshData();
});
</script>

<template>
  <div class="shell">
    <section class="hero">
      <div>
        <p class="eyebrow">Vue + FastAPI Navigation Portal</p>
        <h1>公开与私有导航，按登录状态分层展示。</h1>
        <p class="hero-copy">
          未登录可浏览公共链接；登录后解锁团队内部资源。当前采用 JWT access token + SQLite。
        </p>
      </div>

      <div class="auth-card">
        <template v-if="isLoggedIn && currentUser">
          <p class="panel-title">已登录</p>
          <h2>{{ currentUser.username }}</h2>
          <p class="muted">角色：{{ currentUser.is_admin ? "管理员" : "普通用户" }}</p>
          <button class="secondary-btn" @click="logout">退出登录</button>
        </template>

        <template v-else>
          <p class="panel-title">账号登录</p>
          <label>
            用户名
            <input v-model="loginForm.username" autocomplete="username" />
          </label>
          <label>
            密码
            <input v-model="loginForm.password" type="password" autocomplete="current-password" />
          </label>
          <button :disabled="authLoading" @click="login">
            {{ authLoading ? "登录中..." : "登录查看私有导航" }}
          </button>
        </template>
      </div>
    </section>

    <p v-if="errorMessage" class="error-banner">{{ errorMessage }}</p>

    <section class="content">
      <div class="content-header">
        <div>
          <p class="section-kicker">Public</p>
          <h2>公共导航</h2>
        </div>
        <span class="tag">无需登录</span>
      </div>

      <p v-if="loading" class="muted">正在加载导航...</p>
      <div v-else class="category-grid">
        <article v-for="category in publicCategories" :key="category.id" class="category-card">
          <header>
            <h3>{{ category.name }}</h3>
          </header>
          <a
            v-for="item in category.items"
            :key="item.id"
            :href="item.url"
            target="_blank"
            rel="noreferrer"
            class="nav-link"
          >
            <div>
              <strong>{{ item.title }}</strong>
              <p>{{ item.description }}</p>
            </div>
            <span>Open</span>
          </a>
        </article>
      </div>
    </section>

    <section class="content private-section">
      <div class="content-header">
        <div>
          <p class="section-kicker">Private</p>
          <h2>私有导航</h2>
        </div>
        <span class="tag private-tag">{{ isLoggedIn ? "已解锁" : "需登录" }}</span>
      </div>

      <div v-if="!isLoggedIn" class="locked-card">
        <p>登录后可查看更多内部导航链接。</p>
      </div>

      <div v-else class="category-grid">
        <article v-for="category in privateCategories" :key="category.id" class="category-card private-card">
          <header>
            <h3>{{ category.name }}</h3>
          </header>
          <a
            v-for="item in category.items"
            :key="item.id"
            :href="item.url"
            target="_blank"
            rel="noreferrer"
            class="nav-link"
          >
            <div>
              <strong>{{ item.title }}</strong>
              <p>{{ item.description }}</p>
            </div>
            <span>Open</span>
          </a>
        </article>
      </div>
    </section>
  </div>
</template>

