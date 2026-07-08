<template>
  <div class="container">
    <a-modal
        :visible="modelParams.visible"
        :title="modelParams.title"
        :maskClosable="modelParams.maskClosable"
        :centered="modelParams.centered"
        :footer="modelParams.footer"
        @cancel="handleCancel"
        :width="modelParams.width"
    >
      <a-form :model="user" v-bind="modelParams.layout">
        <a-form-model-item label="用户名:">
          <a-input v-model="user.name" disabled/>
        </a-form-model-item>
        <a-form-model-item label="旧密码">
          <a-input type="password" v-model="user.oldPassword"/>
        </a-form-model-item>
        <a-form-model-item label="新密码">
          <a-input type="password" v-model="user.newPassword"/>
        </a-form-model-item>
        <a-form-model-item label="确认密码">
          <a-input type="password" v-model="user.confirmPassword"/>
        </a-form-model-item>
      </a-form>
      <a-form-item class="btn-group">
        <a-button type="primary" @click="handleOk(user)"> 确认</a-button>
        <a-button @click="handleCancel"> 取消</a-button>
      </a-form-item>
    </a-modal>
  </div>
</template>

<script>
import {modifyPassword} from "@/api/commonApi";
const Base64 = require('js-base64').Base64;
import {mapState} from 'vuex';

export default {
  name: 'ChangePassword',
  data() {
    return {
      modelParams: {
        title: '修改密码',
        maskClosable: false,
        centered: true,
        footer: false,
        visible: false,
        layout: {
          labelCol: {span: 7},
          wrapperCol: {span: 17}
        },
        width: '20rem'
      },
      user: {
        name: localStorage.getItem('username'),
        oldPassword: '',
        newPassword: '',
        confirmPassword: ''
      }
    };
  },
  props: {
    isChangePassword: {
      type: Boolean,
      required: true
    }
  },
  watch: {
    isChangePassword() {
      this.modelParams.visible = true;
    }
  },
  methods: {
    resetForm() {
      // 重置表单
      this.user = {
        ...this.user,
        oldPassword: '',
        newPassword: '',
        confirmPassword: '',
      };
    },
    handleCancel() {
      this.modelParams.visible = false;
    },
    handleOk(v) {
      const params = {
        password: Base64.encode(v.newPassword),
        rawPwd: Base64.encode(v.oldPassword),
        confirmPwd: Base64.encode(v.confirmPassword),
        username: Base64.encode(this.currentUser.username),
        encryption: 'base',
      }
      modifyPassword(params).then((res) => {
        if (res.code === 0) {
          this.$message.success(res.msg, 2, () => {
          });
          this.resetForm()
          this.handleCancel()
        } else {
          try {
            this.$message.warning(JSON.parse(res.msg).message)
          } catch {
            this.$message.warning(res.msg, 3);
          }
          console.error(res);
        }
        return false;
      }).catch((error) => {
        console.log(error);
        this.$message.warning(error.response.data.msg, 3);
        console.error('服务注册-注册失败！');
        return false;
      });
    }
  },
  computed: {
    ...mapState('user', ['currentUser']),
  },
};
</script>

<style scoped lang="scss">
.container {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, 50%);
  color: red;
  z-index: 999;
}

.btn-group {
  display: flex;
  flex-direction: row;
  justify-content: space-between;
}

::v-deep(.ant-modal-body) {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  align-items: center;
}

::v-deep(.ant-form-item) {
  margin-bottom: 0.8rem;
}

::v-deep(.ant-btn-primary) {
  margin-right: 1rem;
}
</style>
