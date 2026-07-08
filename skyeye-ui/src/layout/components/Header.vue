<template>
    <div :class="[is_bg_show ? 'se-header' : 'se-header-index']" style="z-index: 10000">
        <div class="se-header-left">
            <span v-if="is_bg_show" class="se-header-time">{{ currentTime }}</span>
            <div class="nav nav--left">
                <ul>
                    <li v-for="(item, index) in leftNavMenuList" :key="'left-' + index" :class="{ menu_active: item.active }">
                        <div class="menu-3d-container">
                            <router-link :to="item.url" :class="{ menu_active: item.active }">
                                <i :class="'iconfont ' + item.icon"></i>{{ item.caption }}
                            </router-link>
                        </div>
                    </li>
                </ul>
            </div>
        </div>
        <div class="se-header-center">
            <div class="se-header-deco se-header-deco--left"></div>
            <a href="/index" class="se-header-title-link">
                <span class="se-header-title-text">{{ systemName }}</span>
            </a>
            <div class="se-header-deco se-header-deco--right"></div>
        </div>
        <div class="se-header-right" :class="[is_bg_show ? 'se-header-right-new' : '']">
            <div class="nav nav--right">
                <ul>
                    <li v-for="(item, index) in rightNavMenuList" :key="'right-' + index" :class="{ menu_active: item.active }">
                        <div class="menu-3d-container">
                            <router-link :to="item.url" :class="{ menu_active: item.active }">
                                <i :class="'iconfont ' + item.icon"></i>{{ item.caption }}
                            </router-link>
                        </div>
                    </li>
                </ul>
            </div>

            <div class="user-center">
                <user-management></user-management>
            </div>
        </div>
    </div>
</template>

<script>
import UserManagement from './UserManagement';
import { getSystemNameApi } from '@/api/commonApi';

export default {
    name: 'Header',
    components: {
        UserManagement
    },
    data() {
        return {
            menuList: this.$store.state.menuList,
            systemName: '',
            currentTime: this.formatDateTime(),
            timeTimer: null
        };
    },
    computed: {
        showUserName() {
            return localStorage.getItem('username');
        },
        is_bg_show() {
            return this.$route.path !== '/index';
        },
        navMenuList() {
            return this.$store.state.menuList || [];
        },
        leftNavMenuList() {
            return this.navMenuList.slice(0, 3);
        },
        rightNavMenuList() {
            return this.navMenuList.slice(3, 6);
        }
    },
    created() {
        this.$store.dispatch('menu_operation');
        this.getEnumOptionData();
        this.timeTimer = setInterval(() => {
            this.currentTime = this.formatDateTime();
        }, 1000);
    },
    beforeDestroy() {
        if (this.timeTimer) {
            clearInterval(this.timeTimer);
        }
    },
    methods: {
        formatDateTime() {
            const now = new Date();
            const pad = (n) => String(n).padStart(2, '0');
            return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())} ${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(
                now.getSeconds()
            )}`;
        },
        async getEnumOptionData() {
            const res = await getSystemNameApi();
            if (res.code === 0) {
                this.systemName = res.data.system_name;
                document.title = res.data.system_name;
            }
        }
    }
};
</script>

<style scoped lang="scss">
$black-darkest: #050505;
$black-darker: #0a0a0a;
$black-dark: #101010;
$black-medium: #1a1a1a;
$base-color: #1a202c;
$surface-color: #2d3748;
$accent-color: #4299e1;
$accent-light: #63b3ed;
$text-primary: #f7fafc;
$text-secondary: #cbd5e0;

$shadow-bottom: 0 4px 6px -1px rgba(0, 0, 0, 0.3), 0 2px 4px -1px rgba(0, 0, 0, 0.2);
$shadow-top: 0 -4px 6px -1px rgba(0, 0, 0, 0.3);
$shadow-inner: inset 0 2px 4px 0 rgba(0, 0, 0, 0.1);

// 过渡效果
$transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);

.se-header-index {
    z-index: 10;
    position: absolute;
    min-width: 60rem;
    width: 100%;
    height: 4rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 1rem;
    background: transparent;
    backdrop-filter: blur(10px);
}

.se-header-left {
    flex: 1;
    min-width: 0;
    height: 100%;
    display: flex;
    align-items: center;
    padding: 0 24px 0 0;
    gap: 12px;
}

.se-header-time {
    min-width: 120px;
    font-size: 13px;
    color: var(--text-secondary);
    line-height: 1.35;
    white-space: nowrap;
}

.se-header-center {
    flex: 0 1 auto;
    max-width: 42vw;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 16px;
    min-width: 0;
    padding: 0 12px;
    text-align: center;
}

.se-header-title-link {
    text-decoration: none;
    display: flex;
    align-items: center;
}

.se-header-deco {
    width: 72px;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--cyber-accent, #00e5ff));
    position: relative;
    flex-shrink: 0;

    &--right {
        background: linear-gradient(90deg, var(--cyber-accent, #00e5ff), transparent);
    }

    &::after {
        content: '';
        position: absolute;
        top: -3px;
        width: 8px;
        height: 8px;
        border: 1px solid var(--cyber-accent, #00e5ff);
        transform: rotate(45deg);
        box-shadow: 0 0 6px var(--cyber-accent-glow, rgba(0, 229, 255, 0.35));
    }

    &--left::after {
        right: 0;
    }
    &--right::after {
        left: 0;
    }
}

.se-header-right {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: flex-end;
    height: 100%;
    gap: 12px;
    min-width: 0;
    padding: 0 0 0 24px;
}

.nav {
    display: flex;
    align-items: center;
}

.nav--left {
    margin-left: 0;
}

.se-header-extra {
    display: flex;
    align-items: center;
    flex-shrink: 0;
}

.se-header-left ul,
.se-header-right ul {
    display: flex;
    align-items: center;
    margin: 0;
    padding: 0;
    list-style: none;
    gap: 0.75rem;
}

.se-header-left ul li,
.se-header-right ul li {
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
    white-space: nowrap;
    cursor: pointer;
    transition: $transition;
}

.se-header-left ul li a .iconfont,
.se-header-right ul li a .iconfont {
    font-size: 18px;
    transition: $transition;
    transform: translateZ(5px);
}

.user-center {
    display: flex;
    align-items: center;
    flex-shrink: 0;
    margin-left: 0.5rem;
}
</style>
