<template>
  <div class="container">
    <div class="container-title">请选择报告范围</div>
    <a-tree
      checkable
      :tree-data="treeData"
      :replaceFields="replaceFields"
      @check="onCheck"
    />
    <div class="select-container">
      <a-button type="primary" class="btn" @click="confirm">确定</a-button>
      <a-button class="btn" @click="cancel">取消</a-button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'downloadOption',
  props: {
    treeDataList: {
      type: Object,
      default: () => {
        return {};
      }
    }
  },
  data() {
    return {
      treeData: [],
      selectOption: [],
      replaceFields: {
        children: 'county_data',
        title: 'county',
        key: 'county'
      }
    };
  },
  watch: {
    treeDataList: {
      handler(newName, oldName) {
        this.treeData = [newName];
      },
      immediate: true
    }
  },
  methods: {
    onCheck(checkedKeys) {
      this.selectOption = checkedKeys;
    },
    confirm() {
      this.$emit('confirm', this.selectOption);
    },
    cancel() {
      this.$emit('close');
    }
  }
};
</script>

<style scoped>
.container {
  width: 20rem;
  margin: 1rem;
  position: fixed;
  top: 27%;
  left: 86%;
  transform: translate(-50%, -50%);
  /*border: 0.1rem solid #464646;*/
  /* display: flex;
  flex-direction: column;
  align-items: center; */
  background-color: white;
  border-radius: 0.5rem;
  z-index: 2;
}
.container-title {
  font-size: 1rem;
  background-color: #3989ca;
  color: white;
  width: 100%;
  padding: 0.5rem;
  border-radius: 0.5rem 0.5rem 0 0;
  margin-bottom: 1rem;
}
.select-container {
  margin-top: 1rem;
  margin-bottom: 1rem;
  display: flex;
  justify-content: center;
}

.btn {
  margin: 0 1rem;
}
.ant-tree {
  padding-left: 30px;
}
</style>
