<template>
    <div class="se-container">
        <div class="gt-left" v-if="showLeftBar">
            <ul>
                <li v-for="(item, index) in $store.state.currentMenuList" :title="item.caption" :key="item.url">
                    <div :class="{ active: currentIndex === index }" class="side-bar">
                        <router-link :to="item.url" class="panoramaUrl">
                            <i :class="'iconfont ' + item.icon" style="font-size: 24px; color: #fff"></i>
                            <span class="panoramaTitle">{{ item.caption }}</span>
                        </router-link>
                    </div>
                </li>
            </ul>
        </div>
        <div class="gt-right">
            <div class="gt-right-content">
                <router-view></router-view>
            </div>
        </div>
    </div>
</template>
<script>
export default {
    name: 'dataManagement',
    components: {},

    data() {
        return {
            currentComponent: 'MapViewIndex',
            dataList: this.$store.state.currentMenuList,
            batchNumber: 0,
            name: ''
        };
    },
    methods: {
        showComponent(item, index) {
            this.currentComponent = item.url;
            this.currentIndex = index;
        },
        handleTaskData(datamsg) {
            this.batchNumber = datamsg.batchNumber;
            this.currentComponent = 'VerifyClue';
        },
        handleClueReBack() {
            this.currentComponent = 'Task';
        },
        getImagePath(index) {
            // 根据 index 拼接图片路径
            if (index === 1 && this.dataList.length === 2) {
                index = 3;
            }
            if (index === 7) index = 9;
            return require(`@/assets/images/left${index + 1}.png`);
        }
    },
    computed: {
        currentIndex() {
            const routerstr = this.$route.path;
            const filteredItems = this.$store.state.currentMenuList.filter((item) => item.url === routerstr);
            this.name = filteredItems.length > 0 ? filteredItems[0].name : null;
            return this.$store.state.currentMenuList.findIndex((menu) => menu.url === routerstr);
        },
        showLeftBar() {
            return !(this.$route.query.withoutLeftBar && JSON.parse(this.$route.query.withoutLeftBar));
        }
    },
    mounted() {}
};
</script>

<style scoped>
.se-container {
    width: 100%;
    display: flex;
    position: relative;
}

.se-container .gt-left .panoramaUrl {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
}
.se-container .gt-left .panoramaTitle {
    font-size: 12px;
    color: #fff;
    text-align: center;
    display: inline-block;
    margin-top: 2px;
}

.gt-left {
    width: 95px;
    background: #00092d;
    border-right: 1px solid rgba(232, 234, 237, 0.2);
}

.gt-left img {
    width: 24px;
    height: 24px;
}

.gt-left ul li {
    width: 100%;
    margin: 0 auto;
    cursor: pointer;
}

.gt-right {
    flex: 1;
    width: calc(100% - 95px);
}

.side-bar {
    width: 70px;
    height: 70px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    margin: 16px 12px;
}

.gt-right-content {
    height: 100%;
}
</style>
