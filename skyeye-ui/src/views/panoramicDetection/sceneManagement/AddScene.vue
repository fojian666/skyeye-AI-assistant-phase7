<template>
  <div class="add-container">
    <div class="left-content-body">
      <el-form :inline="true" size="small" :model="form" ref="form" :rules="rules">
        <el-form-item label="场景名称:" label-width="100px" prop="sceneName">
          <el-input v-model="form.sceneName" placeholder="请输入" clearable></el-input>
        </el-form-item>
        <el-form-item label="标签类别:" label-width="100px" prop="labels">
          <el-select v-model="form.labels" placeholder="请选择" multiple clearable>
            <el-option v-for="item in labelsCollection" :key="item.name" :label="item.name" :value="item.name"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="创建用户：" label-width="100px" prop="addPerson">
          <el-input v-model="form.addPerson" disabled></el-input>
        </el-form-item>
        <el-form-item class="button-container">
          <el-button type="primary" size="mini" @click="submitForm('form')">添加场景</el-button>
          <el-button type="info" size="mini" @click="resetForm">重置</el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script>
import { addSceneData, getEnumOptionApi } from '@/api/commonApi';

export default {
  name: 'SceneAddDialog',
  data() {
    return {
      labelsCollection: [],
      form: {
        sceneName: '',
        labels: [],
        addPerson: localStorage.getItem('username')
      }, //新增表单
      rules: {
        sceneName: [{ required: true, message: '请输入场景名称', trigger: 'blur' }],
        labels: [{ required: true, message: '请选择标签类别', trigger: 'blur' }]
      }
    };
  },
  methods: {
    //表单校验+提交
    submitForm(formName) {
      this.$refs[formName].validate(async (valid) => {
        if (valid) {
          await this.addScene();
        } else {
          console.log('error submit!!');
          return false;
        }
      });
    },
    //新增场景核心方法
    async addScene() {
      this.form.labels = JSON.stringify(this.form.labels);
      const res = await addSceneData(this.form);
      if (res.code !== 0) {
        this.$message.error(res.msg);
        return;
      }
      this.resetForm();
      // 核心：新增成功后向父组件发送事件，通知刷新表格
      this.$emit('success');
    },
    //重置表单数据+校验状态
    resetForm() {
      this.form.labels = [];
      this.form.sceneName = '';
      this.$refs.form?.resetFields();
    },
    //获取标签下拉选项
    async handleGetLabels() {
      const res = await getEnumOptionApi('Class_Name');
      if (res.code === 0) {
        this.labelsCollection = res.data.Class_Name;
      }
    }
  },
  created() {
    this.handleGetLabels();
  }
};
</script>

<style lang="scss" scoped>
.left-content-body {
  padding-top: 20px;
  width: 100%;
}

::v-deep .el-form .el-input {
  width: 300px;
}

::v-deep .el-form .el-select {
  width: 300px;
}

.button-container {
  display: flex;
  justify-content: center;
  margin-top:15px;
}

::v-deep .el-input__inner {
  background: rgba(255,255,255,0.1);
  border:1px solid #11A8ED;
  color:#fff;
}

::v-deep .el-select .el-input__inner {
  background: rgba(255,255,255,0.1);
  border:1px solid #11A8ED;
  color:#fff;
}

::v-deep .el-select-dropdown {
  background: #00092d;
  border:1px solid #11A8ED;
}

::v-deep .el-select-dropdown__item {
  color:#fff;
}

::v-deep .el-select-dropdown__item:hover {
  background: #108EE9;
}
</style>