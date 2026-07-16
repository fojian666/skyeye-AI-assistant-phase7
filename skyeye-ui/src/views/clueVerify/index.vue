<template>
    <div class="se-container">
        <div class="gt-left">
            <ul>
                <li v-for="(item, index) in dataList" :title="item.caption" :key="item.url" :class="{ active: currentIndex === index }">
                    <div>
                        <router-link :to="item.url" class="panoramaUrl"><img :src="getImagePath(index)" /></router-link>
                    </div>
                </li>
            </ul>
        </div>
        <div class="gt-right">
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
            dataList: this.$store.state.currentMenuList
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
            // 返回当前激活的路由索引
            return this.$store.state.clueVerifyMenuList.findIndex((menu) => menu.url === this.$route.path);
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
}
.gt-left {
    width: 80px;
    background: #002061;
}

.gt-left img {
    width: 32px;
    height: 32px;
}
.gt-left ul li {
    width: 100%;
    display: flex;
    height: 60px;
    line-height: 60px;
    justify-content: center;
    align-items: center;
    text-align: center;
    margin: 0 auto;
    cursor: pointer;
}
.gt-right {
    flex: 1;
    width: calc(100% - 40px);
}
</style>
