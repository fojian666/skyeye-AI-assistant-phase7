<template>
  <div>
    <div class="form-box-title">
      <a-tabs v-model:activeKey="activeKey" @change="resetForm()">
        <a-tab-pane key="地类变化" tab="地类变化"></a-tab-pane>
        <a-tab-pane key="地类分割" tab="地类分割"></a-tab-pane>
      </a-tabs>
    </div>
    <div class="form-box-content">
      <a-form-model
          ref="ruleForm"
          :model="form"
          :rules="rules"
          :label-col="labelCol"
          :wrapper-col="wrapperCol"
      >
        <a-form-model-item ref="name" label="任务名称" prop="name">
          <a-input
              placeholder="请输入任务名称"
              v-model:value="form.name"
              @blur="
              () => {
                $refs.name.onFieldBlur();
              }
            "
          />
        </a-form-model-item>
        <a-form-model-item ref="country" class="spacing" label="行 政 区" prop="county">
          <a-select
              show-search
              v-model:value="form.county"
              placeholder="请先输入行政区检索关键字"
              :default-active-first-option="false"
              :show-arrow="false"
              :filter-option="false"
              :not-found-content="null"
              @search="filterCounty"
              @change="filterCounty"
              @select="selectRegion"
          >
            <a-select-option
                @blur="() => {$refs.county.onFieldBlur();}"
                v-for="d in filterCountyData"
                :key="d.value + '(' + d.key + ')'"
                :data-code="d.key">
              {{ d.value + '(' + d.key + ')' }}
            </a-select-option>
          </a-select>
        </a-form-model-item>

        <a-form-model-item
            label="前景影像"
            prop="prev_id"
            v-if="activeKey == '地类变化'"
        >
          <a-select v-model:value="form.prev_id" placeholder="请选择前景影像">
            <a-select-opt-group v-for="items in resListsObj.imagesList">
              <span slot="label" style="font-size: 16px; color: #42b4f2">
                <i
                    class="iconfont icon-groai-base"
                    style="margin-right: 8px"
                />{{ items.name }}
              </span>
              <a-select-option
                  v-for="item in items.values"
                  :value="item.id"
                  :disabled="form.county === items.name ? false : true"
              >
                {{ item.name }}
              </a-select-option>
            </a-select-opt-group>
          </a-select>
        </a-form-model-item>

        <a-form-model-item
            label="后景影像"
            prop="next_id"
            v-if="activeKey == '地类变化'"
        >
          <a-select v-model:value="form.next_id" placeholder="请选择后景影像">
            <a-select-opt-group v-for="items in resListsObj.imagesList">
              <span slot="label" style="font-size: 16px; color: #42b4f2">
                <i
                    class="iconfont icon-groai-base"
                    style="margin-right: 8px"
                />{{ items.name }}
              </span>
              <a-select-option
                  v-for="item in items.values"
                  :value="item.id"
                  :disabled="form.county === items.name ? false : true"
              >
                {{ item.name }}
              </a-select-option>
            </a-select-opt-group>
          </a-select>
        </a-form-model-item>

        <a-form-model-item label="影像服务" prop="path_id" v-else>
          <a-select v-model:value="form.path_id" placeholder="请选择影像服务">
            <a-select-opt-group v-for="items in resListsObj.imagesList">
              <span slot="label" style="font-size: 16px; color: #42b4f2">
                <i
                    class="iconfont icon-groai-base"
                    style="margin-right: 8px"
                />{{ items.name }}
              </span>
              <a-select-option
                  v-for="item in items.values"
                  :value="item.id"
                  :disabled="form.county === items.name ? false : true"
              >
                {{ item.name }}
              </a-select-option>
            </a-select-opt-group>
          </a-select>
        </a-form-model-item>
        <a-form-model-item label="检测结果" prop="data_path_id" >
          <a-select v-model:value="form.data_path_id" placeholder="请选择业务数据服务" >
            <a-select-opt-group v-for="items in resListsObj.businessList">
              <span slot="label" style="font-size: 16px; color: #42b4f2">
                <i
                    class="iconfont icon-groai-base"
                    style="margin-right: 8px"
                />{{ items.name }}
              </span>
              <a-select-option
                  v-for="item in items.values"
                  :value="item.id"
                  :disabled="form.county === items.name ? false : true"
              >
                {{ item.name }}
              </a-select-option>
            </a-select-opt-group>
          </a-select>
        </a-form-model-item>
        <a-form-model-item :label="remarkLabel">
          <a-input v-model:value="form.otherText" type="textarea"/>
        </a-form-model-item>

        <a-form-model-item :wrapper-col="{ span: 14, offset: 4 }">
          <a-button type="primary" :loading="loading" @click="onSubmit">注册</a-button>
          <a-button style="margin-left: 10px" @click="resetForm">重置</a-button>
        </a-form-model-item>
      </a-form-model>
    </div>
  </div>
</template>

<script>
/**
 * @author: Zhang Siyu
 * @date: 2022-04-07
 * @Description: 任务配置
 */

import {postRegisterTask, getAllTaskResources,getRegionInfoListApi} from '@/api/commonApi';

export default {
  name: 'taskConfig',
  data() {
    return {
      remarkLabel: '备\xa0\xa0\xa0\xa0\xa0\xa0\xa0注',
      // 页面高度
      formBoxHeight: 'height:500px',
      // 注册服务类型
      activeKey: '地类变化',
      // 表单内容及验证规则
      configUrls: config.resCenterUrls,
      // 资源列表
      resListsObj: {},
      ywsj: [],
      region: {},
      detectionResult: {},
      labelCol: {span: 4},
      wrapperCol: {span: 14},
      form: {
        name: '',
        county: undefined,
        prev_id: undefined,
        next_id: undefined,
        path_id: undefined,
        data_path_id: undefined,
        // ywsj_id: undefined,
        otherText: ''
      },
      rules: {
        name: [
          {
            required: true,
            message: '请输入小于10个字符的服务名称！',
            trigger: 'blur'
          }
        ],
        prev_id: [
          {required: true, message: '请选择一个影像！', trigger: 'change'}
        ],
        next_id: [
          {required: true, message: '请选择一个影像！', trigger: 'change'}
        ],
        path_id: [
          {required: true, message: '请选择一个影像！', trigger: 'change'}
        ],
        data_path_id: [
          {required: true, message: '请选择一个影像！', trigger: 'change'}
        ],
        county: [
          {
            required: true,
            message: '请先选择行政区，再选择影像服务！',
            trigger: 'change'
          }
        ]
      },
      loading: false,
      filterCountyData: [],
      countyList: [],
    };
  },
  methods: {
    async initData() {
      let res = await getAllTaskResources();
      if (res.code === 0) {
        this.resListsObj = res.data;
      } else {
        this.$message.warning('数据返回失败，无法正常使用该功能！', 3);
      }
    },
      //获取区域的级联数据
      async getRegionOptions() {
          const res = await getRegionInfoListApi();
          this.countyList = res.data;
      },
    // 行政区筛选
    filterCounty(value) {
      if (value == '') {
        this.$message.warning('行政区检索条件不能为空！', 3);
        this.filterCountyData = [];
      } else {
        let reg = new RegExp(value);
        let arr = [];
        for (let i = 0; i < this.countyList.length; i++) {
          if (reg.test(this.countyList[i].value)) {
            arr.push(this.countyList[i]);
          }
        }
        this.filterCountyData = arr;
      }
    },
    // 表单提交及检验
    onSubmit() {
      this.$refs.ruleForm.validate((valid) => {
        if (valid) {
          this.resRegister();
        } else {
          this.$message.warning('请检查表单项是否合法！', 3);
        }
      });
    },
    // 重置表单事件
    resetForm() {
      this.$refs.ruleForm.resetFields();
    },
    // 资源注册事件
    async resRegister() {
      // 判断前后时影像
      if (
          this.activeKey == '地类变化' &&
          this.form.prev_id === this.form.next_id
      ) {
        this.$message.warning('前后景影像不能相同！', 3);
        return false;
      } else {
        this.loading = true;
        // let temIds = JSON.parse(JSON.stringify(this.form.ywsj_id))
        let params = {
          name: this.form.name,
          taskType: this.activeKey,
          dataPathId: this.form.data_path_id,
          // ywsjid: temIds.join(','),
          username: localStorage.getItem('username'),
          county:this.form.county
        };
        if (this.activeKey == '地类变化') {
          params.prevId = this.form.prev_id
          params.nextId = this.form.next_id
        } else {
          params.pathId = this.form.path_id
        }
        const res = await postRegisterTask(params);
        if (res.code !== 0) {
            this.loading = false;
          return this.$message.warning(res.msg, 3);

        }
        this.loading = false;
        this.$message({
          type: 'success',
          message: res.msg,
          duration: 1000,
          onClose: () => {
            this.$router.push('/resource-center/task-management/task-directory');
          }
        });
      }
    },
    selectRegion(value) {
      this.detectionResult.change_detection_list = this.resListsObj.changeDetectionList.filter((item) => {
        return item.county.includes(value);
      });
      this.detectionResult.image_segmentation_list = this.resListsObj.imageSegmentationList.filter((item) => {
        return item.county.includes(value);
      });
    }
  },
  mounted() {
    this.initData();
    this.getRegionOptions();
  }
};
</script>

<style scoped>
.layout-title {
  background: #fff;
  padding: 0;
}

.layout-content {
  margin: 15px;
  background-color: #ffffff;
}

.form-box-title {
  margin-top: 5px;
  padding: 20px;
}

.form-box-content {
  padding-top: 20px;
}

::v-deep(.ant-tabs-nav .ant-tabs-tab-active) {
  background-color: #42b4f2;
  color: #fff;
}
</style>
