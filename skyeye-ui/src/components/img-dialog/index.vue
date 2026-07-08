<template>
  <div>
    <a-modal
      title="预览图片"
      :visible="visible"
      :confirm-loading="confirmLoading"
      @cancel="handleCancel"
      footer=""
    >
      <div class="img-box">
        <img :src="url" />
      </div>
    </a-modal>
  </div>
</template>

<script>
export default {
  props: {
    url: {
      default: '',
      type: String
    }
  },
  data() {
    return {
      visible: false,
      confirmLoading: false
    };
  },
  methods: {
    open() {
      this.visible = true;
    },
    handleCancel(e) {
      this.visible = false;
    },
  }
};
</script>

<style scoped>
.img-box {
  display: flex;
  justify-content: center;
}
::v-deep(.ant-modal) {
  width: 50% !important;
}
img {
  width: 100%;
  height: 100%;
}
::v-deep(.ant-modal-body) {
  padding: 16px 25px 30px;
}
</style>
