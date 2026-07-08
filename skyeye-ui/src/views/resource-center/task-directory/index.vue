<template>
  <div class="content-box">
    <CpTab
        :cpTablList="taskList"
        :selectTab="taskSelectedTab"
        @cpTabItemClick="taskItemClick"
    ></CpTab>
    <a-form-model :model="form" ref="ruleForm">
      <a-row>
        <a-col :span="7">
          <a-form-model-item
              label="任务名称："
              prop="name"
              :label-col="{ span: 5 }"
              :wrapper-col="{ span: 16 }"
          >
            <a-input placeholder="请输入" v-model="form.name"/>
          </a-form-model-item>
        </a-col>
        <a-col :span="7">
          <a-form-model-item
              label="创建时间："
              prop="createDate"
              :label-col="{ span: 5 }"
              :wrapper-col="{ span: 16 }"
          >
            <a-date-picker
                v-model="form.createDate"
                style="width: 100%"
                valueFormat="YYYY-MM-DD"
                placeholder="请选择时间"
            />
          </a-form-model-item>
        </a-col>
        <a-col :span="6">
          <a-form-model-item
              label="所属行政区："
              prop="county"
              :label-col="{ span: 7 }"
              :wrapper-col="{ span: 16 }"
          >
            <a-select
                v-model="form.county"
                style="width: 100%"
                placeholder="请选择行政区"
            >
              <a-select-option v-for="item in selectOption" :key="item">
                {{ item }}
              </a-select-option>
            </a-select>
          </a-form-model-item>
        </a-col>
        <a-col :span="2" class="btn">
          <a-button type="primary" @click="search" class="search" icon="search"
          >搜索
          </a-button
          >
        </a-col>
        <a-col :span="2" class="btn">
          <a-button @click="resetForm" class="reset">
            <a-icon type="undo" :style="{ fontSize: '15px', color: '#08c' }"/>
            重置
          </a-button>
        </a-col>
      </a-row>
    </a-form-model>
    <CpTab
        :cpTablList="cpTablList"
        :selectTab="currentSelectedTab"
        :showButton="true"
        @cpTabClick="batchDeleteTask"
        @cpTabItemClick="cpTabItemClick"
    ></CpTab>
    <div class="list-content">
      <div class="content-card" v-for="item in taskListsData" :key="item.id">
        <a-checkbox @change="onChange($event, item.id)"></a-checkbox>
        <div @click="loadTaskDetails(item.id, item.taskType)">
          <img :src="item.img_url"/>
          <img
              src="@/assets/images/icon-new.png"
              class="newest"
              v-if="item.id === latest_task_id"
          />
          <h3>{{ item.name }}</h3>
          <p class="task-category">任务类别：{{ item.taskType }}</p>
          <p class="region">行政区：{{ item.county }}</p>
          <p class="service" v-if="item.nextImage && item.nextImage.serviceType">服务类别：{{
              item.nextImage.serviceType
            }}</p>
          <p class="service" v-if="item.path && item.path.serviceType">服务类别：{{ item.path.serviceType }}</p>
          <div class="task-content">
            <div class="content-item">
              <div class="ai-banner-title">
                <div></div>
                <p>注册时间</p>
              </div>
              <p>{{ item.createTime }}</p>
            </div>
            <div class="content-item">
              <div class="ai-banner-title">
                <div></div>
                <p>配置人员</p>
              </div>
              <p>{{ item.createPerson }}</p>
            </div>
            <div class="content-item right-module">
              <div class="ai-banner-title">
                <div></div>
                <p>生产时间</p>
              </div>
              <p>{{ item.appendTime }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="space"></div>
    <div class="pagination">
      <div class="pagination-describe">
        共 {{ total }} 条记录 第{{
          params.pageIndex + '/' + Math.ceil(total / params.pageSize)
        }}
        页
      </div>
      <div class="page-number">
        <a-pagination
            show-quick-jumper
            v-model="params.pageIndex"
            :total="total"
            :page-size="params.pageSize"
            @change="handleChange"
        />
      </div>
    </div>
  </div>
</template>

<script>
import CpTab from '@/components/cp-tab';
import {getTaskListsApi, deleteTaskByIds} from '@/api/commonApi';

export default {
  name: 'TaskDirectory',
  components: {CpTab},
  data() {
    return {
      form: {
        name: '',
        createDate: '',
        // county: null,
      },
      taskCategoryOptions: [
        {
          value: 'dlbhrw',
          label: '地类变化任务',
          click: 'dlbhrw',
          isColor: false,
        },
        {
          value: 'dlfgrw',
          label: '地类分割任务',
          click: 'dlfgrw',
          isColor: false,
        },
      ],
      taskListsData: [],
      params: {
        pageSize: 8,
        pageIndex: 1,
        orderField: 'CreateDate',
      },
      total: 0,
      cpTablList: [
        {
          name: '按时间排序',
          id: 'CreateDate',
          icon: 'arrow-down',
        },
        {
          name: '按名称排序',
          id: 'name',
          icon: 'arrow-down',
        },
      ],
      currentSelectedTab: 'CreateDate',
      checkedList: [],
      task_ids: [],
      taskList: [
        {
          name: '地类变化任务',
          id: 'dlbhrw',
        },
        {
          name: '地类分割任务',
          id: 'dlfgrw',
        },
      ],
      taskSelectedTab: '',
      img_url: '',
      selectOption: [],
      latest_task_id: 0
    };
  },
  watch: {
    'form.createDate': function (newVal) {
      if (!newVal) {
        this.form.createDate = '';
      }
    },
    'form.county': function (newVal) {
      if (!newVal) {
        this.form.county = '';
      }
    },
  },
  mounted() {
    this.taskLists();
  },
  methods: {
    common_event(event_name) {
      this[event_name]();
    },
    dlbhrw() {
      this.form.taskType = '地类变化';
      this.params = Object.assign(this.params, this.form);
      this.taskLists();
    },
    dlfgrw() {
      this.form.taskType = '地类分割';
      this.params = Object.assign(this.params, this.form);
      this.taskLists();
    },
    search() {
      this.params = Object.assign(this.params, this.form);
      this.taskLists();
    },
    resetForm() {
      this.$refs.ruleForm.resetFields();
      this.params = Object.assign(this.params, this.form);
      this.taskLists();
    },
    async taskLists() {
      let params = this.params;
      let res = await getTaskListsApi(params);
      if (res.code !== 0) {
        this.taskListsData = [];
        return this.$message.warning(res.msg);
      }
      res.data && res.data.forEach((item) => {
        if (item.task_type === '地类变化') {
          item.img_url = require('@/assets/images/tupian-renwu1.png');
        } else if (item.task_type === '地类分割') {
          item.img_url = require('@/assets/images/tupian-renwu2.png');
        } else {
          item.img_url = require('@/assets/images/tupian-renwu3.png');
        }
      });
      this.taskListsData = res.data;
      this.total = res.total;
      this.latest_task_id = res.data[0].latestID;
      this.selectOption = [...new Set(res.data.map((item) => item.county || null).filter(Boolean))];
    },
    //按时间 名称排序
    cpTabItemClick(obj) {
      this.currentSelectedTab = obj.key;
      this.params.orderField = obj.key;
      this.taskLists();
    },
    batchDeleteTask() {
      if (this.checkedList.length === 0)
        return this.$message.warning('请选择要删除的数据!');
      this.$confirm('此操作将永久删除, 是否继续?', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(async () => {
        let params = {
          idList: this.task_ids
        };
        const res = await deleteTaskByIds(params);
        if (res.code !== 0) {
          return this.$message.warning(res.msg);
        }
        this.$message.success(res.msg);
        this.checkedList = [];
        this.task_ids = [];
        this.taskLists();
      })
          .catch((error) => {
            this.$message.warning(error.response.data.msg);
          });
    },
    onChange(e, id) {
      if (e.target.checked && id) {
        this.checkedList.push(e.target.checked);
        this.task_ids.push(id);
      }
    },
    taskItemClick(obj) {
      this.taskSelectedTab = obj.key;
      this.params.pageIndex = 1;
      switch (obj.key) {
        case 'dlbhrw':
          this.dlbhrw();
          break;
        case 'dlfgrw':
          this.dlfgrw();
          break;
      }
    },
    handleChange(page, pageSize) {
      this.params.pageIndex = page;
      this.params.pageSize = pageSize;
      this.taskLists();
    },
    onShowSizeChange(current, pageSize) {
      this.pageSize = pageSize;
    },
    //查看详情
    loadTaskDetails(id, task_type) {
      this.$router.push({
        path: '/resource-center/task-directory/task-details',
        query: {id, task_type},
      });
    },
  },
};
</script>

<style scoped>
p {
  padding: 0;
  margin: 0;
}

.content-box {
  margin-top: 16px;
  padding: 20px 20px 10px;
  height: calc(100% - 20px);
  background: #fff;
  overflow: hidden;
  position: relative;
}

.search-bar {
  display: flex;
}

ul {
  margin-block-end: 0em;
}

ul li {
  list-style: none;
  float: left;
  margin-left: 20px;
  cursor: pointer;
}

.content-card {
  width: calc(25% - 16px);
  border: 1px solid #e9e9e9;
  position: relative;
  float: left;
  margin: 16px 16px 0 0;
  cursor: pointer;
}

.content-card:hover {
  border: 1px solid #1890ff;
}

.content-card img {
  width: 100%;
  height: 130px;
}

.content-card .newest {
  width: 22%;
  height: 30px;
  position: absolute;
  top: 0;
  right: 0;
}

.content-card h3 {
  font-weight: 700;
  font-size: 16px;
  position: absolute;
  left: 23px;
  top: 32px;
  text-overflow: ellipsis;
  overflow: hidden;
  white-space: nowrap;
  width: calc(100% - 40px);
  display: block;
  word-break: break-all;
  word-wrap: break-word;
}

.content-card .task-category {
  position: absolute;
  left: 23px;
  top: 61px;
}

.content-card .region {
  position: absolute;
  left: 23px;
  top: 82px;
}

.service {
  position: absolute;
  left: 23px;
  top: 103px;
}

.task-content {
  display: flex;
  height: 45px;
  margin: 16px 0;
}

.task-content .content-item {
  width: 33%;
  border-right: 1px solid #ededed;
  display: flex;
  align-items: center;
  flex-direction: column;
}

.content-item > p {
  margin-top: 3px;
}

.task-content .right-module {
  border-right: 0;
}

.ai-banner-title {
  display: flex;
  align-items: center;
  justify-content: center;
}

.ai-banner-title p {
  font-weight: 700;
  color: #000;
}

.ai-banner-title div {
  width: 5px;
  height: 5px;
  background-color: #0077e8;
  margin-right: 4px;
}

.ant-checkbox-wrapper {
  position: absolute;
  left: 6px;
  top: 6px;
}

.pagination-describe {
  margin-top: 5px;
  position: absolute;
  bottom: 20px;
  left: 20px;
}

.page-number {
  position: absolute;
  bottom: 20px;
  right: 10px;
}

.list-content {
  height: calc(100% - 270px);
  width: 100%;
  overflow: auto;
}

.space {
  width: 100%;
  height: 70px;
}

.ant-form {
  margin-top: 16px;
}

.search {
  /* margin-left: 40px; */
}

.reset {
  margin-left: 10px;
}

.ant-form {
  background-color: #f3f3f3;
  padding-top: 10px;
}

.ant-form-item {
  margin-bottom: 10px;
}

.btn {
  margin-top: 4px;
}
</style>

