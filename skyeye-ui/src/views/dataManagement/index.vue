<template>
  <div class="se-dm-container">
    <div class="se-universal-left"  v-if="showLeftBar">
      <ul>
        <li
            v-for="(item, index) in dataList"
            :title="item.caption"
            :key="item.url">
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
  },
  computed: {
    currentIndex() {
        return this.dataList.findIndex(
            (menu) => menu.url === this.$route.path
        );
      // const routerstr = this.$route.path;
      // const filteredItems = this.$store.state.dataMenuList.filter(item => item.url === this.$route.path);
      // this.name = filteredItems.length > 0 ? filteredItems[0].name : null;
      // if (routerstr === '/panoramic-detection/multiComparision' || routerstr === '/panoramic-detection/verifyClue') {
      //   return this.$store.state.dataMenuList.findIndex((menu) => menu.url === '/panoramic-detection/task-management');
      // } else {
      //   // 返回当前激活的路由索引
      //   return this.$store.state.dataMenuList.findIndex((menu) => menu.url === this.$route.path);
      // }
    },
    showLeftBar() {
      return !(this.$route.query.withoutLeftBar && JSON.parse(this.$route.query.withoutLeftBar))
    }
  },
  mounted() {
  }
};
</script>

<style scoped lang="scss">

.se-dm-container {
  width: 100%;
  display: flex;
  position: relative;
}

.se-dm-container .se-universal-left .panoramaUrl {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.se-universal-left img {
  width: 32px;
  height: 32px;
}

.se-universal-left ul li {
  width: 100%;
  margin: 0 auto;
  cursor: pointer;
}





</style>
