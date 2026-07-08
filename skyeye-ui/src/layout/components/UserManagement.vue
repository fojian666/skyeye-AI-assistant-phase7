
<template>
  <div class="userManagement">
    <div class="se-skin">
      <i class="iconfont icon-pifu" @click.stop="toggleSkinMenu"></i>
      <div class="se-skin-menu" v-show="skinMenuVisible" @click.stop>
        <div
          v-for="(skin, index) in skins"
          :key="index"
          class="skin-option"
          @click.stop="changeSkin(skin)"
        >
          {{ skin.name }}
        </div>
      </div>
    </div>
    <div class="se-user-info" @mouseenter="userOnshow" @mouseleave="startHideTimer">
      <img src="@/assets/images/user.png" class="se-user-avatar"/>
      <div class="user-text">
        <span>{{ showUserName }}</span>
        <div><i :class="icon"></i></div>
      </div>
    </div>
    <div class="user-manage" v-show="active" @mouseenter="clearHideTimer" @mouseleave="startHideTimer">
      <div v-for="(item, index) in pubmanageText" :key="index">
        <div class="pubmanage">
          <span class="manageText" @click="clickHandle(item.method)">{{
              item.name
            }}</span>
        </div>
      </div>
    </div>
    <ChangePassword :isChangePassword="isChangePassword"></ChangePassword>
  </div>
</template>

<script>
import ChangePassword from './ChangePassword.vue';
import {logout} from "@/utils/login";

export default {
  name: 'UserManagement',
  components: {
    ChangePassword
  },
  data() {
    return {
      active: false,
      icon: 'iconfont icon-zhankai',
      isChangePassword: false,
      hoverTimeout: null,
      skinMenuVisible: false,
      skins: [
        { name: '默认', class: 'dark' },
        { name: '亮色风格', class: 'light' },
        { name: '暗黑风格', class: 'dark' }
      ],
      pubmanageText: [
        {name: '修改密码', method: 'changePassword'},
        {name: '退出登录', method: 'login_out'}
      ]
    };
  },
  computed: {
    showUserName() {
      return localStorage.getItem('username');
    }
  },
  methods: {
    userOnshow: function () {
      this.clearHideTimer();
      this.active = true;
      this.icon = 'iconfont icon-shouqi';
    },
    startHideTimer: function () {
      this.clearHideTimer();
      this.hoverTimeout = window.setTimeout(() => {
        this.userOverhide();
      }, 200);
    },
    clearHideTimer: function () {
      if (this.hoverTimeout) {
        window.clearTimeout(this.hoverTimeout);
        this.hoverTimeout = null;
      }
    },
    userOverhide: function () {
      this.active = false;
      this.icon = 'iconfont icon-zhankai';
    },
    clickHandle(method) {
      this[method]();
    },
    changePassword() {
      this.isChangePassword = !this.isChangePassword;
    },
    login_out() {
      logout()
    },
    toggleSkinMenu() {
      this.skinMenuVisible = !this.skinMenuVisible;
    },
    changeSkin(skin) {
      this.skinMenuVisible = false;
      this.$store.commit('changeTheme', skin.class);
    }
  }
};
</script>

<style scoped lang="scss">
.userManagement {
  position: relative;
  height: 100%;
  display: flex;
  width: 200px;
  align-items: center;
}

.se-user-avatar {
  height: 24px;
  width: 24px;
  align-self: center;
}

.user-text {
  display: flex;
  justify-content: center;
  margin-left: 8px;
}



.se-user-info i {
  padding-left: 8px;
  font-size: 12px;
}

.user-manage {
  z-index: 99999;
  width: 8em;
  padding: 0.4em;
  position: absolute;
  top: 60px;
  background: #fff;
  border-radius: 0.4em;
  border: 1px solid #e4e7ed;
  right: 20px;
}

.pubmanage {
  display: inline-block;
  width: 100%;
  text-align: center;
  padding: 0.4em 0 0.4em 0em;
  font-family: Microsoft YaHei, Microsoft YaHei-Regular;
}

.manageText {
  cursor: pointer;
}

.pubmanage:hover {
  background-color: var(--global-neutral-color);
}




.skin-option {
  padding: 8px 12px;
  cursor: pointer;
  text-align: center;
}

.skin-option:hover {
  background-color: #f5f5f5;
}
</style>
