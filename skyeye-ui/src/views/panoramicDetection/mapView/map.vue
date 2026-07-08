<template>
  <div class="gtp-container">
    <div id="mapContainer" style="height: 100%" @click="drawPointActive" @dblclick="measureActive"></div>
    <div class="image" v-show="activeClueImage">
      <div class="gt-header">
        <el-descriptions title="线索详情" style="padding-left: 6px"></el-descriptions>
        <div @click="closeImage" style="color:black; "><i class="el-icon-close"></i></div>
      </div>
      <el-descriptions class="margin-top" :column="2" border>
        <el-descriptions-item>
          <template slot="label">
            <i class="el-icon-location-outline"></i>
            所属区域
          </template>
          {{ activeItem.region }}
        </el-descriptions-item>
        <el-descriptions-item>
          <template slot="label">
            <i class="el-icon-document"></i>
            线索名称
          </template>
          {{ activeItem.clue_name }}
        </el-descriptions-item>
      </el-descriptions>
      <div class="gt-image">
        <img :src="activeClueImage" alt=""/>
      </div>
    </div>
    <div class="toolbar" :style="targetDivStyle">
      <div>
        <el-dropdown trigger="click">
          <div><span class="icon iconfont icon-layer"></span> 图层</div>
          <el-dropdown-menu slot="dropdown">
            <el-checkbox v-model="checkboxPanorama">全景点</el-checkbox>
            <el-checkbox v-model="checkboxBuffer">覆盖范围</el-checkbox>
            <el-checkbox v-model="checkboxGengdi">耕地图层</el-checkbox>
          </el-dropdown-menu>
        </el-dropdown>
      </div>
      <span>|</span>
      <div @click="drawPoint" :class="{ active: activeToolBarIndex === 2 }">
        <span class="icon iconfont icon-position"></span><span>查经纬度</span>
      </div>
      <span>|</span>
      <div @click="measureLength" :class="{ active: activeToolBarIndex === 3 }">
        <span class="icon iconfont icon-icon-line-graph"></span><span>测距</span>
      </div>
      <span>|</span>
      <div @click="startDrawPolygon" :class="{ active: activeToolBarIndex === 4 }">
        <span class="icon iconfont icon-duobianxing"></span><span>测面积</span>
      </div>
      <span>|</span>
      <div @click="clearDraw"><span class="icon iconfont icon-qingchu"></span><span>清除</span></div>
    </div>
    <div class="detectlist" v-if="drawer">
      <div class="title">
        <span>当前点位：{{ currentClickPointName }}</span>
        <el-tooltip class="item" effect="dark" content="多期对比" placement="top">
          <el-button icon="el-icon-position" circle @click="openMulti"></el-button>
        </el-tooltip>
        <el-tooltip class="item" effect="dark" content="关闭" placement="top">
          <el-button icon="el-icon-close" circle @click="closeDrawer"></el-button>
        </el-tooltip>
      </div>
      <el-table :data="listData">
        <el-table-column type="index" label="序号"></el-table-column>
        <el-table-column property="batchName" label="批次名称"></el-table-column>
        <el-table-column property="operation" label="操作">
          <template slot-scope="scope">
            <el-button type="text" size="small" @click="handleSingleView(scope.row)">本期</el-button>
            <el-button type="text" size="small" @click="hanldeViewMultiLeft(scope.row)"
                       :disabled="leftObj === scope.row"
            >前景
            </el-button>
            <el-button type="text" size="small" @click="hanldeViewMultiRight(scope.row)"
                       :disabled="rightObj === scope.row"
            >后景
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
    <div class="view-multi-comparision" v-if="isShowMultiDiv">
      <viewMultiComparision
        @closeMultiDiv="handlecloseMultiDiv"
        :rightObj="rightObj"
        :key="uniquekey"
        :leftObj="leftObj"></viewMultiComparision>
    </div>
    <div class="view-single" v-if="isShowSingleDiv">
      <viewSingle :singleObj="singleObj" @closeDiv="closeDiv"></viewSingle>
    </div>
  </div>
</template>

<script>
import {TiledMapLayer, GetFeaturesBySQLParameters, FeatureService} from '@supermap/iclient-leaflet';
import '@supermap/iclient-leaflet';
import {
  getPanoramaImageApi,
  getMapInfoApi,
  getPanoramaPointByCountryApi,
} from '@/api/commonApi';
import 'leaflet.markercluster'; // 引入插件
import 'leaflet.markercluster/dist/MarkerCluster.Default.css';
import {drawPoint, measureDistance, measureArea, clearGraphical} from '@/utils/utils';
import {load4528BaseMap, createGeoCrs, createGeoBaseLayer} from '@/utils/map4528Loader';
import viewMultiComparision from '@/views/panoramicDetection/mapView/clueToMultiComparision/viewMultiComparision.vue';
import viewSingle from '@/views/panoramicDetection/mapView/singlePeriodView/viewSingle.vue';
import codeNode from 'three/addons/nodes/code/CodeNode';
import L from "leaflet";

export default {
  name: 'MapComponent',
  components: {viewMultiComparision, viewSingle},
  props: {
    activePanoramaPoint: {
      type: String,
      required: true
    },
    activeClueImage: {
      type: String,
      required: true
    },
    activeMarker: {
      type: Number,
      required: true
    },
    activeItem: {
      type: Object,
      required: true
    },
    clueList: {
      type: Array,
      required: true
    }
  },

  data() {
    return {

      targetDivPosition: {x: 0}, // 初始 X 轴位置
      checkboxBuffer: false,
      bufferLayer: L.layerGroup(),
      checkboxPanorama: false,
      circleLayer: L.layerGroup(), //全景点图层组
      checkboxGengdi: false,
      domLayer: null,
      activeToolBarIndex: 0,
      mapService: '',
      datasetsName: '',
      dataSourceName: '',
      gisServiceType: '',

      gridService: '',
      gengdiService: '',
      gridDatasourceName: '',
      gridDatasetsName: '',
      panoramaPoint: [], //全景点坐标
      gridGeometry: [], //网格多边形
      drawCircles: [], //在地图上加载的所有全景点集合
      drawMarkers: [], //在地图上加载的所有marker集合
      marker: null, //线索标记
      clusterLayer: L.markerClusterGroup(), //聚合图层组
      allClueList: [], //所有线索集合，10000
      gridDataSources: [], //所有的网格数据源
      drawer: false,
      listData: [],
      isShowMultiDiv: false,
      multiInfo: null,
      rightObj: null,
      leftObj: null,
      uniquekey: 1,
      geoJsonLayer: null,
      currentClickPointName: '',
      isShowSingleDiv: false,
      singleObj: null,
      mapBounds: [],
      isClueViewPage: true,
      circleRadius: window.config.circleRadius,
      maxZoom: window.config.maxZoom,
      center: window.config.center,
      zoom:window.config.zoom,//初始层级
      baseMapService: window.config.baseMapService,
      baseMapServiceType: window.config.baseMapServiceType,
      baseMaxNativeZoom: window.config.baseMaxNativeZoom,
      baseMapUse4528: window.config.baseMapUse4528 === true,
      baseMap4528Epsg: window.config.baseMap4528Epsg || 'EPSG:4528',
      baseMap4528Proj: window.config.baseMap4528Proj || '+proj=tmerc +lat_0=0 +lon_0=120 +k=1 +x_0=40500000 +y_0=0 +ellps=GRS80 +units=m +no_defs',
      projectCity: window.config.projectCity,
      layerRandList: [],
      map: null,

    };
  },
  watch: {
    gridGeometry() {
      if (this.gridGeometry.length > 0) {
        const geojsonFeature = {
          type: 'FeatureCollection',
          features: this.gridGeometry
        };
        this.geoJsonLayer = L.geoJSON(geojsonFeature, {
          style: {
            color: 'red',
            weight: 2,
            opacity: 1,
            fillColor: '#ffeb3b',
            fillOpacity: 0
          }
        }).addTo(this.map);
      }
    },
    allClueList() {
      // 先移除旧 clusterLayer 的事件
      if (this.allClueList.length > 0) {
        this.clusterLayer.clearLayers();
        const defaultIconBlue = L.icon({
          iconUrl: require('@/assets/images/marker-icon-blue.png'),
          iconSize: [25, 40], // 图标大小
          iconAnchor: [12.5, 40], // 图标锚点（中心点）
          popupAnchor: [-3, -40] // 弹出窗偏移量
        });
        this.allClueList.forEach((item, index) => {
          const marker = L.marker([item.latitude, item.longitude], {icon: defaultIconBlue});
          marker.bindPopup(item.clue_name);
          // marker.on('click', (e) => {
          //     //this.$emit('marker', item);
          //     marker.openPopup();
          // });
          this.clusterLayer.addLayer(marker);
          this.drawMarkers.push({clue_id: item.clue_id, marker: marker});
        });
      }
    },
    activePanoramaPoint(newValue, oldValue) {
      //根据选中的全景点位跳转到该点,修改样式，还原旧点样式
      if (newValue) {
        const newPoint = this.panoramaPoint.filter((item) => item.pointId === newValue)[0];
        this.map.setView([newPoint.latitude, newPoint.longitude], 15);
        const newCircle = this.drawCircles.filter((item) => item.pointId === newValue)[0].circle;
        newCircle.setStyle({color: 'red', fillColor: 'red', fillOpacity: 1, weight: 2});
        newCircle.setRadius(150);
      } else {
        // this.map.setView(this.center,12);//没有激活的全景点初始化地图视图
      }
      if (oldValue) {
        //还原样式
        const oldCircle = this.drawCircles.filter((item) => item.pointId === oldValue)[0].circle;
        oldCircle.setStyle({color: 'orange', fillColor: 'orange', fillOpacity: 1, weight: 2});
        oldCircle.setRadius(80);
      }
    },
    activeMarker(newValue, oldValue) {
      //根据选中的线索添加marker
      const defaultIconRed = L.icon({
        iconUrl: require('@/assets/images/marker-icon-red.png'),
        iconSize: [25, 40], // 图标大小
        iconAnchor: [12.5, 40], // 图标锚点（中心点）
        popupAnchor: [-3, -40] // 弹出窗偏移量
      });
      const defaultIconBlue = L.icon({
        iconUrl: require('@/assets/images/marker-icon-blue.png'),
        iconSize: [25, 40], // 图标大小
        iconAnchor: [12.5, 40], // 图标锚点（中心点）
        popupAnchor: [-3, -40] // 弹出窗偏移量
      });

      if (newValue) {
        const newMarker = this.drawMarkers.filter((item) => item.clue_id === newValue)[0].marker;
        newMarker.setIcon(defaultIconRed);
        newMarker.setZIndexOffset(10); //覆盖其他标记
        this.map.flyTo(newMarker.getLatLng(), 16);
      }
      if (oldValue && oldValue !== -1) {
        //还原样式
        const oldMarker = this.drawMarkers.filter((item) => item.clue_id === oldValue)[0].marker;
        oldMarker.setIcon(defaultIconBlue);
        oldMarker.setZIndexOffset(1);
      }
      this.clusterLayer.refreshClusters();
    },
    checkboxPanorama() {
      if (this.checkboxPanorama) {
        this.map.addLayer(this.circleLayer);
      } else {
        this.map.removeLayer(this.circleLayer);
      }
    },
    checkboxBuffer() {
      if (this.checkboxBuffer) {
        this.map.addLayer(this.bufferLayer);
        this.bufferLayer.eachLayer(function (layer) {
          layer.bringToBack();
        });
      } else {
        this.map.removeLayer(this.bufferLayer);
      }
    },
    checkboxGengdi() {
      if (this.checkboxGengdi) {
        this.map.addLayer(this.gengdiLayer);
      } else {
        this.map.removeLayer(this.gengdiLayer);
      }
    }
  },
  computed: {
    targetDivStyle() {
      return {
        transform: `translateX(${this.targetDivPosition.x}px)`
      };
    }
  },

  methods: {
    drawPointActive() {
      //点击事件取消选中
      if (this.activeToolBarIndex === 2) {
        this.activeToolBarIndex = 0;
      }
    },
    closeImage() {
      this.$emit('updateActiveClueImage', '');
    },
    measureActive() {
      //双击事件取消选中
      if (this.activeToolBarIndex > 2) {
        this.activeToolBarIndex = 0;
      }
    },
    // 画点，显示经纬度
    drawPoint() {
      this.map.off('mousedown');
      this.map.off('mousemove');
      this.map.off('dblclick');
      this.activeToolBarIndex = 2;
      drawPoint(this.map);
    },
    //画线，测量距离
    measureLength() {
      this.map.off('mousedown');
      this.map.off('mousemove');
      this.map.off('dblclick');
      this.activeToolBarIndex = 3;
      measureDistance(this.map);
    },
    // 画面，测量面积
    startDrawPolygon() {
      this.map.off('mousedown');
      this.map.off('mousemove');
      this.map.off('dblclick');
      this.activeToolBarIndex = 4;
      measureArea(this.map);
    },
    clearDraw() {
      this.activeToolBarIndex = 0;
      clearGraphical(this.map);
    },
    async initMap() {
      if (this.map) {
        this.map.remove();
        this.map = null;
      }
      try {
        if (this.baseMapUse4528 && this.baseMapService) {
          await this.init4528Map();
        } else {
          this.initGeoMap();
        }
      } catch (err) {
        console.error('[底图] 初始化失败', err);
        this.$message.error('底图加载失败：' + (err.message || '请检查服务地址与 tileInfo'));
      }
    },
    async init4528Map() {
      const {crs, layer, maxZoom, minZoom, fitBounds, initialZoom} = await load4528BaseMap(
        this.baseMapService,
        this.baseMapServiceType,
        {
          epsgCode: this.baseMap4528Epsg,
          projDef: this.baseMap4528Proj,
          initialZoom: this.zoom
        }
      );
      this.map = L.map('mapContainer', {
        crs,
        zoomControl: false,
        attributionControl: false,
        preferCanvas: true,
        maxZoom,
        minZoom
      });
      this.baseMapLayer = layer;
      this.baseMapLayer.addTo(this.map);
      this.baseMapLayer.bringToBack();
      if (fitBounds && fitBounds.isValid()) {
        this.map.fitBounds(fitBounds);
      } else {
        this.map.setView(this.center, initialZoom);
      }
      this.addBaseLayerToList('底图(4528)');
      this.$nextTick(() => this.map && this.map.invalidateSize());
      this.finishMapSetup();
    },
    initGeoMap() {
      const myCrs = createGeoCrs(this.projectCity);
      this.map = L.map('mapContainer', {
        crs: myCrs,
        center: this.center,
        zoom: this.zoom,
        zoomControl: false,
        attributionControl: false,
        preferCanvas: true,
        maxZoom: this.maxZoom
      });
      if (this.baseMapService) {
        this.baseMapLayer = createGeoBaseLayer(this.baseMapService, this.baseMapServiceType, {
          maxZoom: this.maxZoom,
          maxNativeZoom: this.baseMaxNativeZoom,
          minZoom: this.minZoom
        });
        if (this.baseMapLayer) {
          this.baseMapLayer.addTo(this.map);
          this.baseMapLayer.bringToBack();
          this.addBaseLayerToList('底图');
        }
      }
      this.finishMapSetup();
    },
    addBaseLayerToList(name) {
      this.layerRandList.unshift({
        name,
        layer: this.baseMapLayer,
        shapeOption: {opacity: 1, brightness: 1, contrast: 1, saturation: 1},
        show: true,
        expanded: false,
        source_type: '底图'
      });
    },
    finishMapSetup() {
      if (!this.map) return;
      //加载geoserver地图（4528 底图验证阶段跳过 4326 业务瓦片，避免 CRS 不一致）
      try {
        if (!this.baseMapUse4528) {
          if (this.gisServiceType === '1') {
          var layer = new TiledMapLayer(this.mapService, {
            maxZoom: this.maxZoom,       // 允许地图缩放到 22 级
            maxNativeZoom: this.maxZoom, // 瓦片服务实际支持的最高级别
            reuseTiles: false,  // 关键参数：禁止复用旧瓦片
            updateWhenIdle: true,
            updateInterval: 200,
            keepBuffer: 1,      // 仅保留1屏缓冲
            noWrap: true        // 禁止瓦片重复
          }).addTo(this.map);
        } else if (this.gisServiceType === '2') {
          var layer = L.tileLayer(`${this.mapService}/tile/{z}/{y}/{x}`, {
            maxZoom: this.maxZoom,
            minZoom: this.minZoom,
            pane: 'tilePane',
            updateWhenIdle: false, // 拖动时也更新瓦片
            updateWhenZooming: false, // 缩放时也更新
            keepBuffer: 3, // 仅保留1屏缓冲
            updateInterval: 200,
            noWrap: true // 禁止瓦片重复
          }).addTo(this.map);
        } else if (this.gisServiceType === '3') {
          //天地图服务
          // 矩阵集id, 决定了在每一级该去请求哪一个identifier对应的切片，如果只有个别几级需要处理minZoom， maxZoom
          let identifier = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]
          let matrixIds = [];
          for (var i = 0; i < identifier.length; i++) {
            matrixIds.push({
              identifier: identifier[i]
            })
          }
          var layer = new L.supermap.WMTSLayer(this.mapService, {
            layer: "img",
            style: "default",
            tilematrixSet: "c",
            format: "tiles",
            matrixIds: matrixIds,
            maxZoom: identifier.length - 1,
          }).addTo(this.map)
          this.map.setView(this.center, 13)
        } else if(this.gisServiceType === '4') {
          var layer = L.tileLayer.wms(this.mapService, {
            layers: `${this.dataSourceName}:${this.datasetsName}`, // 图层名称
            format: 'image/png',
            transparent: true,
            attribution: "Your Attribution"
          }).addTo(this.map);
        }
        }
        this.clusterLayer.addTo(this.map);
      } catch (error) {
        this.$message.error(error);
      }

      //this.gengdiLayer = new TiledMapLayer(this.gengdiService);
      // 存储所有数字标签的数组
      const numberLabels = [];
      //加载全景点
      this.panoramaPoint.forEach((item) => {
        const bufferCircle = L.circle([item.latitude, item.longitude], this.circleRadius, {
          color: 'yellow',
          fillColor: 'red',
          fillOpacity: 0,
          weight: 1
        }).addTo(this.bufferLayer);
        const circle = L.circle([item.latitude, item.longitude], 80, {
          color: 'orange',
          fillColor: 'orange',
          fillOpacity: 1,
          weight: 2
        }).addTo(this.circleLayer);
        // 定义数字标签
        const numberLabel = L.marker([item.latitude, item.longitude], {
          icon: L.divIcon({
            className: 'circle-number', // 自定义样式类名
            html: `<div style="
                           border-radius: 50%;
                           width: 40px;
                           height: 40px;
                           line-height: 40px;
                           text-align: center;
                           font-size: 30px;

                           position: relative;
                           color: #fff;">${item.panoramaImageCount}</div>`, // 替换为你的数字
            iconSize: [40, 40] // 设置图标大小
          }),
          opacity: 0 // 默认隐藏
        }).addTo(this.circleLayer);
        // 将数字标签添加到数组中
        numberLabels.push(numberLabel);
        // 为每个 circle 添加 popupp
        // 添加点击事件
        circle.on('click', () => {
          // 1. 重置所有圆圈的样式（取消之前的高亮）
          this.circleLayer.eachLayer(layer => {
            if (layer instanceof L.Circle) {
              layer.setStyle({
                color: 'orange',    // 默认边框颜色
                fillColor: 'orange' // 默认填充颜色
              });
            }
          });

          // 2. 将当前点击的圆圈设为红圈（高亮）
          circle.setStyle({
            color: 'red',       // 边框改为红色
            fillColor: 'red',   // 填充改为红色
            weight: 3           // 可选：加粗边框
          });
          // 触发工具栏位置变化
          if (!this.drawer) {
            this.targetDivPosition.x -= 360; // 向左移动 200px
          }
          //请求该全景点对应的多期图片
          this.getMultiInfo(item.pointId, item.pointName);
        });
        // 绑定鼠标悬停事件
        circle.on('mouseover', (e) => {
          // 绑定并打开弹窗
          circle
            .bindPopup(
              '点位名称:' +
              item.pointName +
              '<br>' +
              '批次数量:' +
              item.panoramaImageCount +
              '<br>' +
              '最近拍摄时间:' +
              item.latestTime +
              '<br>' +
              '飞行员信息:' +
              item.gridOperator
            )
            .openPopup();
        });
        this.drawCircles.push({pointId: item.pointId, circle: circle}); //添加circle对象
      });
      //监听影像缩放层级，控制批次显隐
      this.map.on('zoomend', (e) => {
        const currentZoom = this.map.getZoom();
        if (currentZoom >= 14) {
          numberLabels.forEach((label) => {
            label.setOpacity(1);
          });
        } else {
          numberLabels.forEach((label) => {
            label.setOpacity(0);
          });
        }
      });
    },
    async getPanoramaPoint() {
      //获取全景点坐标
      const res = await getPanoramaPointByCountryApi({});
      if (res.code !== 0) {
        this.$message.error(res.msg);
        return;
      }
      this.panoramaPoint = res.data;
    },

    async getGridGeometry() {
      try {
        //获取网格数据多边形坐标
        var sqlParam = new GetFeaturesBySQLParameters({
          queryParameter: {
            name: `${this.gridDatasetsName}@${this.gridDatasourceName}`,
            attributeFilter: '1=1'
          },
          datasetNames: [`${this.gridDatasourceName}:${this.gridDatasetsName}`]
        });
        const that = this;
        await new FeatureService(this.gridService).getFeaturesBySQL(sqlParam, async function (results) {
          if (results.result !== undefined && results.result.features) {
            results.result.features.features.forEach((item) => {
              that.gridGeometry.push(item);
            });
          }
        });
      } catch (error) {
        this.$message.error('加载网格数据多边形错误：', error);
      }
    },

    async getMultiInfo(point_id, point_name) {
      const data = {
        pointId: point_id
      }
      const multiObjres = await getPanoramaImageApi(data);
      var batchImageCount = 0;
      if (multiObjres.code === 0) {
        this.listData = multiObjres.data;
        this.currentClickPointName = point_name;
        batchImageCount = this.listData.length;
      } else {
        this.$message.error(multiObjres.msg);
      }
      this.drawer = true;
    },
    openMulti() {
      if (this.listData.length <= 1) {
        this.$message.warning('当前该全景点没有多期图片，暂不可进行多期对比查看!!!!');
      } else {
        this.leftObj = this.listData[0];
        this.rightObj = this.listData[1];
        this.isShowMultiDiv = true;
      }
    },
    closeDrawer() {
      if (this.drawer) {
        this.targetDivPosition.x += 360; // 向左移动 200px
      }
      this.drawer = false;
      this.rightObj = null;
      this.leftObj = null;
      this.isShowMultiDiv = false;
      this.isShowSingleDiv = false;
    },
    handlecloseMultiDiv() {
      this.isShowMultiDiv = false;
      this.rightObj = null;
      this.leftObj = null;
    },
    hanldeViewMultiRight(row) {
      if (this.isShowMultiDiv) {
        if (this.leftObj !== row) {
          if (this.rightObj != row) {
            this.rightObj = row;
            this.uniquekey += 1;
          }
        } else {
          this.$message.warning('左右两期图片不能相同，请重新选择！！！！');
        }
      } else {
        this.$message.warning('请先点击右上角多期对比，在进行查看！！！！');
      }
    },
    hanldeViewMultiLeft(row) {
      if (this.isShowMultiDiv) {
        if (this.rightObj !== row) {
          if (this.leftObj != row) {
            this.leftObj = row;
            this.uniquekey += 1;
          }
        } else {
          this.$message.warning('左右两期图片不能相同，请重新选择！！！！');
        }
      } else {
        this.$message.warning('请先点击右上角多期对比，在进行查看！！！！');
      }
    },
    handleSingleView(row) {
      this.singleObj = row;
      this.isShowSingleDiv = true;
    },
    closeDiv() {
      this.isShowSingleDiv = false;
    },
    async updateCluesList(data) {
      this.allClueList = data;
    },
    async getMapUrl() {
      if (this.mapService != '') {
        const url = this.mapService + '.json'
        await this.axios.get(
          url,
          {withCredentials: false}
        )
          .then((res) => {
            const leftBottom = res.data.bounds.leftBottom;
            const rightTop = res.data.bounds.rightTop;
            this.mapBounds = [[leftBottom.y, leftBottom.x], [rightTop.y, rightTop.x]]
          })
          .catch((err) => {
            console.error(err);
          })
      }
    }
  },
  async mounted() {
    this.allClueList = this.clueList;
    const res = await getMapInfoApi();
    if (res.code === 0) {
      this.mapService = res.data.map_service;
      this.datasetsName = res.data.datasets_name;
      this.dataSourceName = res.data.datasource_name;
      this.gisServiceType = res.data.gis_service_type;
      this.gengdiService = res.data.gengdi_service;

      await this.getPanoramaPoint();
      await this.initMap();

    }
  }
};
</script>

<style lang="scss" scoped>
.gtp-container {
  height: 100%;
  width: 100%;
  position: relative;
}

#mapContainer {
  background-color: white; //地图背景颜色
}

.image {
  position: absolute;
  width: 400px;
  height: 350px;
  right: 0;
  bottom: 0;
  z-index: 1000;
  overflow: auto;
  display: flex;
  flex-direction: column;
  padding: 6px;
  background-color: #fff;
}

img {
  width: 100%;
  height: 100%;
  object-fit: fill;
  border: 2px solid #cccccc;
}

.toolbar {
  width: 500px;
  height: 35px;
  position: absolute;
  top: 20px;
  right: 20px;
  border: 1px solid #cccccc;
  border-radius: 5px;
  z-index: 999;
  font-weight: bold;
  line-height: 35px;
  background-color: white;
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  padding: 0 20px;
  color: #606266;
}

.toolbar div {
  cursor: pointer;
}

.toolbar div:hover {
  color: #42b4f2;
}

.el-checkbox {
  margin: 0 10px;
}

.icon {
  margin: 0 6px;
  font-size: 18px;
}

::v-deep .el-drawer.ltr,
.el-drawer.rtl {
  top: 4rem;
  bottom: 0;
}

.detectlist {
  top: 0px;
  background-color: white;
  box-shadow: none;
  z-index: 9999999;
  color: black;
  position: absolute;
  right: 0;
  width: 360px;
  height: 100%;
  overflow-y: auto;
  padding: 10px;
  display: flex;
  flex-direction: column;
  border-left: 1px solid #cccccc;
}

.detectlist .title {
  display: flex;
  text-align: center;
  border-bottom: 1px solid #fff;
  padding-bottom: 10px;
  font-size: 1rem;
}

.detectlist .title span {
  text-align: left;
  font-weight: 700;
  width: 98%;
}

.multicard {
  height: 90%;
  width: 98%;
  background-color: red;
  margin: auto;
}

.view-multi-comparision,
.view-single {
  top: 120px;
  background-color: white;
  box-shadow: none;
  z-index: 9999999;
  color: black;
  position: absolute;
  right: 377px;
  width: 75%;
  height: 80%;
  overflow-y: auto;
  padding: 10px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.show {
  display: flex;
  flex-direction: column;
  padding: 4px;
}

.gt-header {
  display: flex;
  padding-left: 6px;
  height: 32px;
  line-height: 32px;
}

.gt-image {
  height: 240px;
}

::v-deep .el-button.is-disabled {
  color: #C0C4CC !important;
}

::v-deep .iclient-leaflet-logo {
  display: none !important;
}
</style>
