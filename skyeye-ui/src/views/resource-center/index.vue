<template>
    <div class="se-usercenter">
        <a-layout id="components-layout-demo-side">
            <a-layout-sider v-model="collapsed" collapsible v-if="showLeftBar">
                <div class="logo" />
                <a-menu mode="inline" @click="handleClick" :openKeys="currentOpenKeys" :selectedKeys="[$route.path]">
                    <a-sub-menu v-for="item in dataList" :key="item.url">
                        <span slot="title">
                            <i
                                :class="'iconfont ' + item.icon"
                                style="margin-right: 8px"
                                :style="collapsed ? collapsedIconAfter : collapsedIconBefore"></i>
                            <span :style="collapsed ? collapsedSpanAfter : collapsedSpanBefore">{{ item.caption }}</span>
                        </span>
                        <a-menu-item :key="subItem.url" v-for="subItem in item.children">
                            {{ subItem.caption }}
                        </a-menu-item>
                    </a-sub-menu>
                </a-menu>
            </a-layout-sider>
            <a-layout :style="{ width: formBoxWidth, height: '100%' }">
                <router-view id="side-content"></router-view>
            </a-layout>
        </a-layout>
    </div>
</template>

<script>
export default {
    name: 'ResourceCenter',
    data() {
        return {
            dataList: this.$store.state.currentMenuList,
            collapsed: false,
            // 页面高度
            formBoxWidth: document.body.clientWidth - 200 + 'px',
            resourceFlag: false,
            taskFlag: false,
            role_id: '',
            collapsedSpanAfter: {
                display: 'none'
            },
            collapsedSpanBefore: {
                display: 'contents'
            },
            collapsedIconAfter: {
                'font-size': '20px'
            },
            collapsedIconBefore: {
                'font-size': '16px'
            }
        };
    },
    methods: {
        handleClick(e) {
            if (e.key !== this.$route.path) {
                this.$router.push(e.key);
            }
        }
    },
    watch: {
        '$route.path': {
            handler(newVal, oldVal) {
                if (newVal.includes(oldVal)) {
                    if (newVal === '/resource-center/system-management/user-info') {
                        this.resourceFlag = true;
                    } else if (newVal === '/resource-center/task-directory/task-details') {
                        this.taskFlag = true;
                    }
                } else {
                    this.resourceFlag = false;
                    this.taskFlag = false;
                }
            }
        }
    },
    computed: {
        showLeftBar() {
            return !(this.$route.query.withoutLeftBar && JSON.parse(this.$route.query.withoutLeftBar));
        },
        currentOpenKeys() {
            // 展开所有子菜单
            return this.dataList.map((item) => item.url);
        }
    },
    mounted() {
        this.role_id = localStorage.getItem('role_id');
        window.addEventListener(
            'resize',
            () => {
                this.formBoxWidth = document.body.clientWidth - 200 + 'px';
            },
            false
        );
    }
};
</script>

<style scoped>
::v-deep(.ant-layout-sider) {
    background-color: #ffffff;
}

::v-deep(.ant-layout-sider-trigger) {
    background-color: #ffffff;
    color: #002140;
}

#side-content {
    margin: 10px 5px;
    height: calc(100% - 20px);
    width: 99%;
}

.se-usercenter {
    width: 100%;
    height: calc(100% - 4rem);
}

.ant-layout {
    height: 100%;
}

::v-deep(.ant-layout-sider-children) {
    overflow-y: auto;
    overflow-x: hidden;
}
</style>
