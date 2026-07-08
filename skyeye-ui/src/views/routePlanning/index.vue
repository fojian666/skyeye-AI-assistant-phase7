<template>
  <div class="se-container">
    <div class="se-universal-left" v-if="showLeftBar">
      <ul>
        <li v-for="(item,index) in $store.state.currentMenuList" :title="item.caption" :key="item.url">
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
  name: "",
  components: {},

  data() {
    return {
      dataList: this.$store.state.currentMenuList,
    }
  },
  methods: {
    getImagePath(index) {
      // 根据 index 拼接图片路径
      if (index === 1 && this.dataList.length === 2) {
        index = 3
      }
      if (index === 7) index = 9
      return require(`@/assets/images/plan${index + 1}.png`);
    }

  },
  computed: {
    currentIndex() {
      return this.$store.state.currentMenuList.findIndex(
          (menu) => menu.url === this.$route.path
      );
    },
    showLeftBar() {
      return !(this.$route.query.withoutLeftBar && JSON.parse(this.$route.query.withoutLeftBar))
    }
  },
  mounted() {
  }
}
</script>

<style scoped>
.se-container {
  width: 100%;
  display: flex;
  position: relative;
}

.se-container .se-universal-left .panoramaUrl {
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