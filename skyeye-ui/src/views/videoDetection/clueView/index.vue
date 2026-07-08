<template>
	<div class="se-container">
		<div class="content">
			<div class="content-header">
				<div>
					<span class="icon iconfont icon-xinzengtianjia"></span>
					<span class="title">视频解译结果</span>
				</div>
				<div>
					<a class="" @click="goBack">返回</a>
				</div>
			</div>
			<div class="filter">
				<div class="filter-header">
					<span>已选择条件:</span>
					<div class="filter-header-right">
						<p style="margin-right: 16px">已筛选出<span style="color: red">{{ dataCount }}</span>条数据</p>
						<!--                        <el-button size="medium" style="padding: 4px 8px" type="text">-->
						<!--                            <i v-if="showFilter" class="iconfont icon-shouqi"></i>-->
						<!--                            <i v-else class="iconfont icon-zhankai"></i>-->
						<!--                            <span>展开筛选条件</span>-->
						<!--                        </el-button>-->
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
															:class="{active: item === filterInfo.clueName}"
															@click="categoryFilter(item)"
												>{{ item }}</span>
					</div>
				</div>
			</div>
			<div class="content-body">
				<div class="content-card" v-for="(item, index) in clueList" :key="index">
					<div  style="width: 100%">
						<img  @click="showCardDetail(item)" style="width: 100%;height: 200px;" :src="'/panoramaUrl'+item.filePath"/>
						<!-- 右上角状态标签 -->
						<div class="status-badge" :class="getStatusClass(item.status)">
							{{ getStatusText(item.status) }}
						</div>
						<p class="clue-name text" style="font-weight: bold;font-size: 16px">{{ item.clueName }}</p>
						<p class="time text">拍摄时间：{{ item.createDate }}</p>
						<div class="check-status text">
							<span>审核状态：</span>
							<span>{{ checkStatus[item.status + 1].name }}</span>
						</div>
						<div class="btn-judge">
							<el-button size="mini" type="primary" @click="changeStatus(item.id,2)" :disabled="item.status === 1 || item.status === 2">有效</el-button>
							<el-button size="mini" type="danger" @click="changeStatus(item.id,1)" :disabled="item.status === 1 || item.status === 2">无效</el-button>
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
								:current-page="filterInfo.pageIndex"
								:page-sizes="[12,24,48,100]"
								:page-size="filterInfo.pageSize"
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
							 :src="'/panoramaUrl'+cardDetailInfo.filePath"/>
					<p class="clue-name text" style="font-weight: bold;font-size: 15px">{{ cardDetailInfo.clueName }}</p>
					<p class="region text">所属区域：{{ cardDetailInfo.address }}</p>
					<p class="time text">拍摄时间：{{ cardDetailInfo.createDate }}</p>
					<p class="text">线索编号：{{ cardDetailInfo.id }}</p>
					<p class="text">方框位置：{{ cardDetailInfo.position }}</p>
					<p class="text">所属区县：{{ cardDetailInfo.county }}</p>
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
				<img style="width: 100%;height:600px;object-fit: contain" :src="'/panoramaUrl'+cardDetailInfo.filePath"/>
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
		</div>
	</div>
</template>

<script>
  import {getVideoClueByIdApi, getMapInfoApi, updateVideoClueStatusByIdApi, getSceneData} from "@/api/commonApi";
  import {TiledMapLayer} from "@supermap/iclient-leaflet";
  export default {
    name: 'clueViewIndex',
    data() {
      return {
        center: '',
        taskId: null,
        mapService: '',
        farmlandService: '',
        map: null,
        cardDetailInfo: {
          image_path: '',
          label: '',
          address: '',
          create_time: '',
          status: '',
          latitude: '',
          longitude: '',
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
          pageSize: 12,
          pageIndex: 1,
          status: null,
          clueName: '不限',
        }, //筛选参数
        showFilter: false,
        checkStatus: [{name: '不限', value: ''}, {name: '待审批', value: 0}, {
          name: '已审批,无效', value: 1
        }, {name: '已审批,有效', value: 2}],//审核状态
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
      // 获取状态文本
      getStatusText(status) {
        const statusMap = {
          1: '已审批，无效',
          2: '已审批，有效'
        };
        return statusMap[status] || '';
      },

      // 获取状态样式类
      getStatusClass(status) {
        const classMap = {
          1: 'status-invalid',  // 已审批无效
          2: 'status-valid'     // 已审批有效
        };
        return classMap[status] || '';
      },
			//返回
      goBack(){
        this.$router.go(-1);
			},
			// 视频线索判读
      async changeStatus(clue_id,status){
        const params = {
          id:clue_id,
					status:status
				}
				const res = await updateVideoClueStatusByIdApi(params);
        if(res.code === 0){
          this.$message.success("判读成功！");
          this.getClueList();
				}else{
          this.$message.error("判读失败！");
				}
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
              zoomSnap: 0.25,
              zoomControl: false, //缩放组件
              attributionControl: false, //去掉右下角logo
              preferCanvas: true,
              maxZoom: 18
            });
        try {
          const layer = new TiledMapLayer(this.mapService, {
            maxZoom: 22,       // 允许地图缩放到 22 级
            maxNativeZoom: 22, // 瓦片服务实际支持的最高级别
            reuseTiles: false,  // 关键参数：禁止复用旧瓦片
            updateWhenIdle: true,
            updateInterval: 200,
            keepBuffer: 1,      // 仅保留1屏缓冲
            noWrap: true        // 禁止瓦片重复
          });
          layer.addTo(this.map);
          new TiledMapLayer(this.farmlandService, {
            maxZoom: 22,       // 允许地图缩放到 22 级
            maxNativeZoom: 22, // 瓦片服务实际支持的最高级别
            reuseTiles: false,  // 关键参数：禁止复用旧瓦片
            updateWhenIdle: true,
            updateInterval: 200,
            keepBuffer: 1,      // 仅保留1屏缓冲
            noWrap: true        // 禁止瓦片重复
          }).addTo(this.map);
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
        this.filterInfo.pageIndex = 1
        this.getClueList();
      },
      categoryFilter(item) {
        this.filterInfo.clueName = item;
        this.filterInfo.pageIndex = 1
        this.getClueList();
      },
      handleSizeChange(val) {
        // 改变每页展示的数据
        this.filterInfo.pageSize = val;
        this.filterInfo.pageIndex = 1
        this.getClueList();
      },
      handleCurrentChange(val) {
        // 改变页码
        this.filterInfo.pageIndex = val;
        this.getClueList();
      },
      async getClueList() {
        const params = {...this.filterInfo}
        if (params.clueName === '不限') {
          params.clueName = ''
        }
        const res = await getVideoClueByIdApi(this.taskId, params)
        if (res.code === 0) {
          this.dataCount = res.total;
          this.clueList = res.data
        }

      },
      getClueCategory() {
        getSceneData({clueName: '', pageSize: 1, pageIndex: 1}).then(res => {
          if (res.code === 0) {
            // 获取线索类别
            this.clueCategory = res.labels
            if (!this.clueCategory.includes('不限')) {
              this.clueCategory.unshift('不限')
            }
          }
        })
      }
    },
    created() {

      const pathArray = window.location.pathname.split('/').filter(Boolean);
      this.taskId = pathArray[2];


    },
    mounted() {
      this.getClueCategory();
      this.getClueList()
      this.getMapInfo();
    },
    computed: {},
  };
</script>

<style lang="scss" scoped>
  .se-container {
    padding: 10px;
    height: 100%;
    position: relative;
    background-color: #081738;
    color: #fff;
  }

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
    border-top: 1px solid #dcdcdc;
    color: #000;
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

    span.active {
      color: #42b4f2;
    }
  }

  .content-body {
    width: 100%;
    height: calc(100% - 220px);
    padding: 0 16px;
    overflow: auto;
  }

  .content-card {
    width: calc(16% - 16px);
    border: 1px solid #0a579e;
    position: relative;
    float: left;
    margin: 16px 16px 0 0;
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

  ::v-deep(.el-dialog__header) {
    padding: 8px;
    background-color: #42b4f2;
    color: white;
  }

  ::v-deep(.el-dialog__body) {
    padding: 0;
  }

  .title {
    color: white;
  }
	.btn-judge{
		padding:4px;
		text-align: center;
		justify-content: center;
		display: flex;
	}
  /* 状态标签样式 */
  .status-badge {
    position: absolute;
    top: 4px;
    right: 4px;
    padding: 4px 12px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: bold;
    color: white;
    z-index: 10;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  }

  /* 有效状态 - 绿色 */
  .status-valid {
    background-color: #67c23a;
    border: 1px solid #5daf34;
  }

  /* 无效状态 - 红色 */
  .status-invalid {
    background-color: #f56c6c;
    border: 1px solid #e25c5c;
  }

  /* 如果需要更多状态，可以继续添加 */
  .status-pending {
    background-color: #909399;  /* 灰色 - 待审批 */
    border: 1px solid #82848a;
  }

  /* 如果图片容器已经有边框或圆角，可以调整位置 */
  .content-card {
    position: relative;
    overflow: hidden;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }

  /* 如果图片有圆角，让状态标签适应 */
  .content-card img {
    border-radius: 8px 8px 0 0;
  }

  /* 确保其他元素不会重叠 */
  .content-card > div {
    position: relative;
  }
  /* 添加动画效果 */
  .status-badge {
    /* 原有样式... */
    opacity: 0.9;
    transition: all 0.3s ease;
  }

  .status-badge:hover {
    opacity: 1;
    transform: scale(1.05);
  }

  /* 如果状态改变时想要有动画 */
  .status-badge.fade-in {
    animation: fadeIn 0.5s ease;
  }

  @keyframes fadeIn {
    from {
      opacity: 0;
      transform: translateY(-10px);
    }
    to {
      opacity: 0.9;
      transform: translateY(0);
    }
  }
</style>
