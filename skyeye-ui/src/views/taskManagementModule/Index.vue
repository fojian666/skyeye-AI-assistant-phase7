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
  name: 'TaskManagementModuleLayout',
  components: {},
  data() {
    return {
      currentComponent: 'MapViewIndex',
      batchNumber: 0,
      titleName: '',
    };
  },
  methods: {},
  computed: {
    dataList() {
      return this.$store.state.currentMenuList;
    },
    currentIndex() {
      const router = this.$route.path;
      if (router === '/task-mgmt/verify-clue') {
        return this.dataList.findIndex((menu) => menu.url === '/task-mgmt/verify-clue');
      }
      return this.dataList.findIndex((menu) => menu.url === router);
    },
    showLeftBar() {
      return !(this.$route.query.withoutLeftBar && JSON.parse(this.$route.query.withoutLeftBar));
    },
  },
  watch: {
    $route: {
      immediate: true,
      handler(route) {
        const router = route.path;
        if (router === '/task-mgmt/verify-clue') {
          this.titleName = '任务管理';
        } else {
          const filteredItems = this.dataList.filter((item) => item.url === router);
          this.titleName = filteredItems.length > 0 ? filteredItems[0].name : null;
        }
      },
    },
  },
  mounted() {},
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

.se-universal-left ul li {
  width: 100%;
  margin: 0 auto;
  cursor: pointer;
}
</style>
