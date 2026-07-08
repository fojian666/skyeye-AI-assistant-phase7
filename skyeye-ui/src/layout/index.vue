<template>
  <div class="full">
    <Header v-show="isShow && showHeader"></Header>
    <router-view :class="isShow && showHeader ? 'router-box' : 'router-box_index'"/>
    <ChatModel />
  </div>
</template>

<script>
import Header from './components/Header.vue';
import ChatModel from '@/components/chat/ChatModel.vue';

export default {
  name: 'Layout',
  components: {
    Header,
    ChatModel,
  },
  data() {
    return {
      currentIndex: 0,
    };
  },
  methods: {},
  watch: {
    '$route.path': {
      handler(newVal, oldVal) {
        this.$store.commit('toggleMenuActive', newVal);
      },
      immediate: true
    },
  },
  computed: {
    isShow() {
      const routerstr = this.$route.path;
      if (routerstr === '/data_overview_proto' || routerstr === '/login_demo') {
        return false
      } else {
        return true
      }
    },
    showHeader() {
      return this.$store.state.showHeader
    }
  },
  mounted() {
    if (this.$route.query.isIframe && JSON.parse(this.$route.query.isIframe)) {
      this.$store.commit('toggleShowHeaderBar', false);
    } else {
      this.$store.commit('toggleShowHeaderBar', true);
    }
  },
};

</script>

<style lang="scss" scoped>
.router-box {
  flex: 1;
}

.router-box_index {
  height: 100% !important;
}
</style>
