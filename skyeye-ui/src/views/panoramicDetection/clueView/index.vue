<template>
  <div class="se-container">
    <div class="content">
      <div class="content-header">
        <div>
          <span class="icon iconfont icon-xinzengtianjia"></span>
          <span class="title">线索总览</span>
        </div>
        <div>
          <el-button type="primary" @click="showExportDialog">导出线索</el-button>
        </div>
      </div>
      <div class="filter">
        <div class="filter-header">
          <span>已选择条件:</span>
          <div class="filter-header-right">
            <p style="margin-right: 16px">已筛选出<span style="color: red">{{ dataCount }}</span>条数据</p>
          </div>
        </div>
        <div class="filter-content">
          <span class="filter-title">审核状态:</span>
          <div class="status-list">
                        <span v-for="(item, index) in checkStatus" :key="index"
                              :class="{active: item.value === filterInfo.status}"
                              @click="checkFilter(item)"
                        >{{ item.name }}</span>
          </div>
        </div>
        <div class="filter-content">
          <span class="filter-title">线索类别:</span>
          <div class="status-list">
                        <span v-for="(item, index) in clueCategory" :key="index"
                              :class="{active: item === filterInfo.keyword}"
                              @click="categoryFilter(item)"
                        >{{ item }}</span>
          </div>
        </div>
      </div>
      <div class="content-body">
        <div class="content-card" v-for="(item, index) in clueList" :key="index">
          <div @click="showCardDetail(item)" style="width: 100%">
            <img style="width: 100%;height: 200px;" :src="item.image_path"/>
            <p class="clue-name text" style="font-weight: bold;font-size: 15px">{{ item.label }}</p>
            <p class="region text">所属区域：{{ item.address }}</p>
            <p class="time text">拍摄时间：{{ item.create_time }}</p>
            <div class="check-status text">
              <span>审核状态：</span>
              <span>{{ checkStatus[item.status + 1].name }}</span>
            </div>
          </div>
        </div>

      </div>
      <div class="page">
        <!--分页设置-->
        <el-pagination
          background
          small
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
          :current-page="filterInfo.page"
          :page-sizes="[12,24,48,100]"
          :page-size="filterInfo.limit"
          layout="total, sizes, prev, pager, next, jumper"
          :total="dataCount"
        >
        </el-pagination>
      </div>
      <el-dialog
        :visible.sync="cardDetailVisible"
        width="20%"
        class="card-detail"
        :close-on-click-modal="false"
        :show-close="false"
      >
        <template slot="title">
          <div class="card-detail-title" style="display: flex;align-items: center;justify-content: space-between">
            <div style="display: inline-block">
              <span class="iconfont icon-xinzengtianjia" style="margin-right: 5px"></span>
              <span class="title">线索详情</span>
            </div>
            <span class="el-icon-close" @click="cardDetailVisible = false"></span>
          </div>
        </template>
        <div class="card-detail-content">
          <img @click="imgVisible = true" style="width: 100%;height: 200px;object-fit: contain"
               :src="cardDetailInfo.image_path"/>
          <p class="clue-name text" style="font-weight: bold;font-size: 15px">{{ cardDetailInfo.label }}</p>
          <p class="region text">所属区域：{{ cardDetailInfo.address }}</p>
          <p class="time text">拍摄时间：{{ cardDetailInfo.create_time }}</p>
          <p class="text">批次编号：{{ cardDetailInfo.batch_id }}</p>
          <p class="text">任务编号：{{ cardDetailInfo.task_id }}</p>
          <p class="text">经度：{{ cardDetailInfo.longitude }}</p>
          <p class="text">纬度：{{ cardDetailInfo.latitude }}</p>
          <div class="check-status text">
            <span>审核状态：</span>
            <span>{{ checkStatus[cardDetailInfo.status + 1].name }}</span>
          </div>
          <div class="card-detail-btn">
            <el-button type="primary" @click="mapVisible = true">查看</el-button>
            <el-button @click="cardDetailVisible = false">取消</el-button>
          </div>
        </div>
      </el-dialog>
      <el-dialog
        class="img-dialog"
        :visible.sync="imgVisible"
        width="60%"
        :show-close="false"
      >
        <template slot="title">
          <div class="card-detail-title" style="display: flex;align-items: center;justify-content: space-between">
            <div style="display: inline-block">
              <span class="iconfont icon-xinzengtianjia" style="margin-right: 5px"></span>
              <span class="title">图片预览</span>
            </div>
            <span class="el-icon-close" @click="imgVisible = false"></span>
          </div>
        </template>
        <img style="width: 100%;height:600px;object-fit: contain" :src="cardDetailInfo.image_path"/>
      </el-dialog>
      <el-dialog
        class="map-dialog"
        :visible.sync="mapVisible"
        width="60%"
        :show-close="false"
        :close-on-click-modal="false"
      >
        <template slot="title">
          <div class="card-detail-title" style="display: flex;align-items: center;justify-content: space-between">
            <div style="display: inline-block">
              <span class="iconfont icon-xinzengtianjia" style="margin-right: 5px"></span>
              <span class="title">地图预览</span>
            </div>
            <span class="el-icon-close" @click="mapVisible = false"></span>
          </div>
        </template>
        <div id="mapContainer" style="width: 100%;height: 600px"></div>
      </el-dialog>
      <el-dialog
        class="export-dialog"
        :visible.sync="isShowExportDialog"
        width="60%"
        @close="resetForm"
        title="线索导出筛选"
      >
        <el-form  size="medium" :model="exportForm" ref="form"class="export-form">
          <el-form-item label="线索状态" prop="clueStatus"  class="custom-input" label-width="100px">
            <el-select v-model="exportForm.clueStatus"  clearable placeholder="请选择线索状态"
                       :change-on-select="true">
              <el-option v-for="item in checkStatus" :key="item.value" :label="item.name"
                         :value="item.value">

              </el-option>
            </el-select>
          </el-form-item>
          <el-form-item label="线索标签" prop="clueType"  class="custom-input" label-width="100px">
            <el-select v-model="exportForm.clueType"  clearable placeholder="请选择线索标签"
                       :change-on-select="true">
              <el-option v-for="item in clueCategory" :key="item" :label="item"
                         :value="item">

              </el-option>
            </el-select>
          </el-form-item>
          <el-form-item class="button-container">
            <el-button class="right-button" type="primary" size="mini" @click="handleExport" :loading="exportLoading">导出 </el-button>
            <el-button class="right-button" type="info" size="mini" @click="closeDialog">关闭</el-button>
          </el-form-item>
        </el-form>
      </el-dialog>
    </div>
  </div>
</template>

<script>

import {
  getClueOverviewApi,
  getEnumOptionApi,
  getMapInfoApi,
  getSceneData
} from "@/api/commonApi";
import {TiledMapLayer} from "@supermap/iclient-leaflet";

export default {
  name: 'clueViewIndex',
  data() {
    return {
      exportLoading:false,
      center: '',
      mapService: '',
      farmlandService: '',
      map: null,
      isShowExportDialog: false,
      exportForm:{
        clueStatus:'',
        clueType:'',
      },
      cardDetailInfo: {
        image_path: '',
        label: '',
        address: '',
        create_time: '',
        status: '',
        latitude: '',
        longitude: '',
        batch_id: '',
        task_id: '',
        panorama_image_lat: '',
        panorama_image_lon: '',
      },//线索详情数据
      baseUrl: process.env.VUE_APP_API_URL,//请求地址
      cardDetailVisible: false,//线索详情
      imgVisible: false,//图片详情
      mapVisible: false,//地图详情
      dataCount: 0,
      filterInfo: {
        limit: 12,
        page: 1,
        status: '',
        keyword: '不限',
      }, //筛选参数
      showFilter: false,
      checkStatus: [{name: '不限', value: ''}, {name: '待审批', value: 0}, {
        name: '已审批，无效',
        value: 1
      }, {name: '已审批，待核实', value: 2},
        {name: '已打点', value: 3}, {name: '已核实，确认', value: 4}, {name: '已核实，误检', value: 5}],//审核状态
      clueCategory: [],//线索类型
      clueList: [],//线索列表
      circleRadius: window.config.circleRadius
    };
  },
  watch: {
    // 地图显示隐藏时初始化地图
    mapVisible(val) {
      if (val) {
        this.$nextTick(() => {
          this.initMap();
        })
      } else {
        if (this.map)
          this.map.remove();
        this.map = null;
      }
    }

  },
  methods: {
    resetForm(){
      this.$refs.form.resetFields(); // 重置表单验证状态和字段值
    },
    closeDialog(){
      this.isShowExportDialog = false;
    },
    //导出线索信息，图片+点位shp
    async handleExport() {

      try {
        const response = await fetch('/api/panorama/clue/export_clue_data', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(this.exportForm)
        });

        if (response.ok) {
          this.exportLoading = false;
          // 创建下载链接
          const blob = await response.blob();
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `clue_export_${new Date().getTime()}.zip`;
          document.body.appendChild(a);
          a.click();
          window.URL.revokeObjectURL(url);
          document.body.removeChild(a);

          // 或者如果后端返回的是文件流，可以直接触发下载
        } else {
          const errorData = await response.json();
          alert(`导出失败: ${errorData.message}`);
        }
      } catch (error) {
        console.error('导出失败:', error);
        alert('导出失败，请稍后重试');
      }
      this.isShowExportDialog = false;
    },
    showExportDialog(){
      this.isShowExportDialog = true;
    },
    getMapInfo() {
      getMapInfoApi().then(res => {
        this.center = res.data.center;
        this.mapService = res.data.map_service;
        this.farmlandService = res.data.gengdi_service;
      })
    },
    //初始化地图
    initMap() {
      this.map = L.map('mapContainer',
        {
          crs: L.CRS.EPSG4326,
          center: this.center,//中心坐标
          zoom: 12,//缩放级别
          zoomControl: false, //缩放组件
          attributionControl: false, //去掉右下角logo
          preferCanvas: true,
          maxZoom: 18
        });
      try {
        const layer = new TiledMapLayer(this.mapService);
        layer.addTo(this.map);
        new TiledMapLayer(this.farmlandService).addTo(this.map);
      } catch (error) {
        this.$message.error(error)
      }
      const defaultIconBlue = L.icon({
        iconUrl: require('@/assets/images/marker-icon-blue.png'),
        iconSize: [20, 30], // 图标大小
        iconAnchor: [12.5, 40], // 图标锚点（中心点）
        popupAnchor: [-3, -40] // 弹出窗偏移量
      })
      // 添加标记点
      L.marker([this.cardDetailInfo.latitude, this.cardDetailInfo.longitude], {icon: defaultIconBlue}).addTo(this.map)
      // 添加全景700米缓冲区
      L.circle([this.cardDetailInfo.panorama_image_lat, this.cardDetailInfo.panorama_image_lon], this.circleRadius, {
        color: 'red',
        fillColor: 'red',
        fillOpacity: 0,
        weight: 1
      }).addTo(this.map);
      // 添加全景点
      L.circle([this.cardDetailInfo.panorama_image_lat, this.cardDetailInfo.panorama_image_lon], 80, {
        color: 'orange',
        fillColor: 'orange',
        fillOpacity: 1,
        weight: 2
      }).addTo(this.map);
      // 设置地图中心点
      this.map.setView([this.cardDetailInfo.latitude, this.cardDetailInfo.longitude], 12);
    },
    // 显示卡片详情
    showCardDetail(item) {
      this.cardDetailVisible = true
      this.cardDetailInfo = item
    },
    // 筛选审核状态
    checkFilter(item) {
      this.filterInfo.status = item.value;
      this.filterInfo.page = 1
      this.getClueList();
    },
    categoryFilter(item) {
      this.filterInfo.keyword = item;
      this.filterInfo.page = 1
      this.getClueList();
    },
    handleSizeChange(val) {
      // 改变每页展示的数据
      this.filterInfo.limit = val;
      this.filterInfo.page = 1
      this.getClueList();
    },
    handleCurrentChange(val) {
      // 改变页码
      this.filterInfo.page = val;
      this.getClueList();
    },
    getClueList() {
      const params = {...this.filterInfo}
      if (params.keyword === '不限') {
        params.keyword = ''
      }

      getClueOverviewApi(params).then(res => {
        if (res.code === 0) {
          this.dataCount = res.count
          this.clueList = res.data
        }
      })
    },
    getClueCategory() {
      getSceneData({keyword: '', limit: 1, page: 1}).then(res => {
        if (res.code === 0) {
          // 获取线索类别
          this.clueCategory = res.labels
          if (!this.clueCategory.includes('不限')) {
            this.clueCategory.unshift('不限')
          }
        }
      })
    },
    async getClueNameList() {
      const classNameListResponse = await getEnumOptionApi('Class_Name')
      if (classNameListResponse.code === 0) {
        classNameListResponse.data.Class_Name.map(item => {
          this.clueCategory.push(item.name)
        })
        if (!this.clueCategory.includes('不限')) {
          this.clueCategory.unshift('不限')
        }
      }
    }
  },
  created() {
    this.getClueNameList();
    //this.getClueCategory()
    this.getClueList()
    this.getMapInfo()
  },
  computed: {},
};
</script>

<style lang="scss" scoped>

.content {
  width: 100%; //剩余宽度
  height: 100%;
  flex-direction: column;
  border-radius: 2px;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.5);
}

.icon {
  font-size: 24px;
  color: #42b4f2;
  padding-right: 5px;
}

.content-header {
  display: flex;
  justify-content: space-between;
  padding: 0 16px;
  font-weight: 700;
  font-size: 16px;
  height: 40px;
  line-height: 40px;
}

.filter-header {
  background-color: rgba(173, 216, 230, 0.3); /* 浅蓝色背景 */
  display: flex;
  justify-content: space-between;
  align-items: center;
  border: 1px solid #0a579e;
  margin: 0 16px;
  padding-left: 16px;
  height: 36px;
}

.filter-header-right {
  display: flex;
  align-items: center;
  margin-right: 10px;
}

.icon-zhankai, .icon.shouqi {
  font-size: 12px;
}

.filter-content {
  border-bottom: 1px solid #0a579e;
  border-left: 1px solid #0a579e;
  border-right: 1px solid #0a579e;
  margin: 0 16px;
  padding: 8px 16px;
  display: flex;
  align-items: center;
}

.filter-title {
  background-color: #606266;
  color: white;
  font-weight: 700;
  margin-right: 10px;
  padding: 0 10px;
  height: 22px;
}

.status-list {
  width: calc(100% - 100px);
  display: flex;
  align-items: center;
  flex-flow: wrap;

  span {
    margin-right: 10px;
    padding: 0 10px;
    border-radius: 2px;
  }

  span:hover {
    cursor: pointer;
    background-color: #dcdcdc;
  }

}

.content-body {
  width: 100%;
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 4px 6px;
  padding: 4px 16px;
  overflow: auto;
  height: calc(100% - 240px);
}

.content-card {
  width: 100%;
  position: relative;
  float: left;
  cursor: pointer;
  overflow: hidden;
  padding-bottom: 8px;

  .text {
    padding: 0 8px;
    white-space: nowrap;
  }
}

.content-card:hover {
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.8);
  border-color: #1890ff;

}

.card-detail-content {
  margin: 8px 12px;

  .text {
    padding: 2px 8px;
    white-space: nowrap;
  }

  .card-detail-btn {
    width: 100%;
    border-top: 1px solid #dcdcdc;
    padding: 12px 0;
    text-align: center;
    position: absolute;
    bottom: 0;
  }
}

.card-detail ::v-deep(.el-dialog) {
  height: 75%;
  float: right;
}
.export-form{
  padding:20px
}
::v-deep(.el-dialog__header) {
  padding: 8px;
  background-color: #42b4f2;
  color: white;
}

::v-deep(.el-dialog__body) {
  padding: 0;
}
::v-deep .el-dialog__headerbtn{
  top: 10px!important;
}
</style>
