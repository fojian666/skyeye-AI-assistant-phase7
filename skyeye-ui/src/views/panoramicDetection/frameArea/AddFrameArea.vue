<template>
  <div class="add-container">
    <div class="left-content-body">
      <div class="excel-upload">
        <!--上传网格表单-->
        <el-form :inline="true" size="medium" :model="form" ref="form">
          <el-form-item label="上传文件" label-width="100px" style="display: flex">
            <el-input type="text" placeholder="请上传zip压缩包" v-model="form.shpZipFile">
              <template slot="append">
                <el-button icon="el-icon-folder-opened" size="medium" @click="checkShpZip"></el-button>
                <input type="file" id="excel" accept=".zip" style="display: none" @change="handleFileUpload" />
              </template>
            </el-input>
          </el-form-item>
          <el-form-item label="操作用户" label-width="100px">
            <el-input v-model="form.uploadPerson" disabled></el-input>
          </el-form-item>
          <el-form-item class="button-container">
            <el-button class="right-button" type="primary" size="mini" @click="handleSubmit">提交 </el-button>
            <el-button class="right-button" type="info" size="mini" @click="resetForm">重置</el-button>
          </el-form-item>
        </el-form>
      </div>
    </div>
  </div>
</template>

<script>
import { addFrameAreaDataApi } from '@/api/commonApi';

export default {
  name: 'FrameAddDialog',
  data() {
    return {
      upProgress: 0, //上传进度
      uploading: false, //上传进度表单控制
      form: {
        shpZipFile: '',
        uploadPerson: ''
      }, //上传表单
      uploadFile: null
    };
  },
  methods: {
    checkShpZip() {
      //网格标签点击事件
      document.querySelector('#excel').click();
    },
    handleFileUpload(event) {
      const file = event.target.files[0];
      if (file) {
        this.form.shpZipFile = file.name; // 设置文件名
        this.uploadFile = file;
        this.$message.success('文件选择成功');
      }
    },
    async handleSubmit() {
      let fileDom = document.getElementById('excel');
      if (fileDom.files[0] === undefined) {
        return this.$message.error('请先上传文件');
      }
      // 创建一个 FormData 对象
      const formData = new FormData();
      // 将文件添加到 FormData 对象中
      formData.append('file', this.uploadFile);
      formData.append('taskType', 1);
      try {
        const res = await addFrameAreaDataApi(formData);
        if (res.code === 0) {
          this.resetForm();
          // 核心：新增成功后向父组件发送事件
          this.$emit('success');
        } else {
          this.$message.error(res.msg);
        }
      } catch (error) {
        this.$message.error('上传失败，请重试');
      }
    },
    resetForm() {
      // 重置表单+清空文件域
      this.form.shpZipFile = '';
      this.uploadFile = null;
      document.getElementById('excel').value = '';
    }
  },
  mounted() {
    // 获取当前登录用户
    this.form.uploadPerson = localStorage.getItem('username');
  }
};
</script>

<style lang="scss" scoped>
.left-content-body {
  padding-top: 10px;
  width: 100%;
}

.button-container {
  display: flex;
  padding: 14px;
  align-items: center; /* 垂直居中 */
  text-align: center;
  justify-content: center;
  margin-top:10px;
}

::v-deep .el-input--medium .el-input__inner {
  height: 32px;
  line-height: 32px;
  background: rgba(255,255,255,0.1);
  border:1px solid #11A8ED;
  color:#fff;
}

::v-deep .el-form-item__content{
  width: 320px;
}

.el-icon-folder-opened {
  color: white;
}
</style>