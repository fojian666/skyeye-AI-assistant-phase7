<template>
    <div class="se-container">
        <div class="se-universal-left" v-if="showLeftBar">
            <ul>
                <li v-for="(item, index) in dataList" :title="item.caption" :key="item.url">
                    <div :class="{ active: currentIndex === index }" class="side-bar">
                        <router-link :to="item.url" class="panoramaUrl">
                            <i :class="'iconfont ' + item.icon" class="se-universal-left-icon"></i>
                            <span class="panoramaTitle">{{ item.caption }}</span>
                        </router-link>
                    </div>
                </li>
            </ul>
        </div>
        <div class="se-universal-right">
            <router-view></router-view>
        </div>
    </div>
</template>
<script>
export default {
    name: '',
    components: {},

    data() {
        return {
            currentComponent: 'MapViewIndex',
            dataList: this.$store.state.currentMenuList,
            name: ''
        };
    },
    methods: {
        getImagePath(index) {
            // 根据 index 拼接图片路径
            if (index === 1 && this.dataList.length === 2) {
                index = 3;
            }
            return require(`@/assets/images/left${index + 1}.png`);
        }
    },
    computed: {
        currentIndex() {
            const routerstr = this.$route.path;
            if (routerstr === '/pattern-verifiy/map_overview') {
                this.name = '图斑核实地图';
                return this.$store.state.currentMenuList.findIndex((menu) => menu.url === '/pattern-verifiy/task_management');
            } else {
                const filteredItems = this.$store.state.currentMenuList.filter((item) => item.url === routerstr);
                this.name = filteredItems.length > 0 ? filteredItems[0].name : null;
                return this.$store.state.currentMenuList.findIndex((menu) => menu.url === routerstr);
            }
        },
        showLeftBar() {
            return !(this.$route.query.withoutLeftBar && JSON.parse(this.$route.query.withoutLeftBar));
        }
    },
    mounted() {}
};
</script>

<style>
.se-universal-left .panoramaUrl {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
}

.se-pv-left ul li {
    width: 100%;
    margin: 0 auto;
    cursor: pointer;
}

.title-bg-tab {
    height: 46px;
    background-image: url('@/assets/images/navigation-bar/title-bg-tab.png');
    background-color: #00092d;
    background-size: 100% 100%;
    padding-left: 10px;
}

.title-bg-tab span {
    font-family: YouSheBiaoTiHei, serif;
    background: linear-gradient(180deg, #ffffff 60%, #a2b8f2 100%);
    -webkit-background-clip: text;
    color: transparent;
    font-size: 24px;
    line-height: 46px;
    text-align: left;
}
</style>
