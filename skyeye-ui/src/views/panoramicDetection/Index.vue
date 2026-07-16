<template>
    <div class="se-content">
        <div class="se-content-left" v-if="showLeftBar" :class="{ collapse: isCollapse }">
            <ul>
                <li v-for="(item, index) in dataList" :title="item.caption" :key="item.url">
                    <div :class="{ active: currentIndex === index }" class="side-bar1">
                        <router-link :to="item.url" class="panoramaUrl">
                            <i :class="'iconfont ' + item.icon" class="se-icon"></i>
                            <span class="panoramaTitle">{{ item.caption }}</span>
                        </router-link>
                    </div>
                </li>
            </ul>
            <div class="se-line"></div>
            <!-- 左侧菜单栏底部固定 收缩/展开按钮 -->
            <div class="collapse-btn" @click="isCollapse = !isCollapse">
                <i :class="isCollapse ? 'el-icon-arrow-right' : 'el-icon-arrow-left'"></i>
            </div>
        </div>
        <div class="se-content-right">
            <router-view></router-view>
        </div>
    </div>
</template>
<script>
export default {
    name: 'LayoutContainer',
    components: {},
    data() {
        return {
            currentComponent: 'MapViewIndex',
            batchNumber: 0,
            titleName: '',
            isCollapse: false // 控制侧边栏收缩/展开状态 false=展开 true=收缩
        };
    },
    methods: {},
    computed: {
        // 优化：菜单列表改为计算属性，响应式更新
        dataList() {
            return this.$store.state.currentMenuList;
        },
        currentIndex() {
            const router = this.$route.path;
            if (router === '/panoramic-detection/verifyClue') {
                return this.dataList.findIndex((menu) => menu.url === '/panoramic-detection/task-management');
            } else {
                return this.dataList.findIndex((menu) => menu.url === router);
            }
        },
        showLeftBar() {
            return !(this.$route.query.withoutLeftBar && JSON.parse(this.$route.query.withoutLeftBar));
        }
    },
    watch: {
        // 修复原语法问题：路由变化修改标题，不在computed里改data，避免vue警告
        $route: {
            immediate: true,
            handler(route) {
                const router = route.path;
                if (router === '/panoramic-detection/verifyClue') {
                    this.titleName = '线索查询';
                } else {
                    const filteredItems = this.dataList.filter((item) => item.url === router);
                    this.titleName = filteredItems.length > 0 ? filteredItems[0].name : null;
                }
            }
        }
    },
    mounted() {}
};
</script>

<style scoped lang="scss">
/* 主容器样式 */
.se-content {
    width: 100%;
    flex: 1;
    display: flex;
    max-height: calc(100% - 64px);
    position: relative;
}

/* 左侧菜单栏核心样式 - 带收缩过渡动画 */
.se-content-left {
    width: 140px;
    min-width: 60px;
    box-sizing: border-box;
    transition: width 0.3s ease-in-out; /* 宽度收缩展开平滑过渡 */
    position: relative;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    height: 100%;
}
/* 收缩状态样式 - 窄宽度+隐藏文字 */
.se-content-left.collapse {
    width: 60px;
}

.se-content-left ul {
    list-style: none;
    padding: 0;
    margin: 0;
    flex: 1;
    overflow-y: auto;
    overflow-x: hidden;
}
/* 滚动条美化 */
.se-content-left ul::-webkit-scrollbar {
    width: 2px;
}
.se-content-left ul::-webkit-scrollbar-thumb {
    background: #11a8ed;
    border-radius: 2px;
}

.se-content-left ul li {
    width: 100%;
    margin: 6px auto;
    cursor: pointer;
    border-radius: 8px;
    transition: all 0.2s ease;
}
/* 菜单链接样式 */
.se-content .se-content-left .panoramaUrl {
    width: 100%;
    height: 100%;
    display: flex;
    gap: 12px;
    align-items: center;
    justify-content: flex-start;
    padding: 12px 20px;
    box-sizing: border-box;
    text-decoration: none;
}

/* 菜单文字 - 收缩时隐藏，带过渡动画 */
.se-content .se-content-left .panoramaTitle {
    font-size: 12px;
    text-align: center;
    display: inline-block;
    margin-top: 2px;
    white-space: nowrap;
    transition: all 0.2s ease;
}
/* 收缩状态隐藏文字 */
.se-content-left.collapse .panoramaTitle {
    display: none;
}

.se-icon {
    font-size: 20px;
    flex-shrink: 0; /* 图标不被压缩 */
}

.se-line {
    width: 100%;
    height: 1px;
    background-color: rgba(232, 234, 237, 0.1);
}

.side-bar {
    justify-content: center;
    align-items: center;
}
</style>
