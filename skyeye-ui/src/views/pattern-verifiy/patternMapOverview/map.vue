<template>
  <div className="gtp-container">
    <div id="mapContainer" style="height: 100%;" ref="mapContainer"></div>
    <div class="tree-container" ref="ctrllayer">
      <!-- 控制按钮 -->
      <div class="show-control">
        <div @click="handleExpandAll" class="button-expand" v-if="isShowTree"><i class="iconfont icon-sys-minus-square"
                                                                                 style="font-size: 16px"></i>服务目录
        </div>
        <div @click="handleCollapseAll" class="button-expand" v-else><i class="iconfont icon-shouqizhankai"
                                                                        style="font-size: 16px"></i>服务目录
        </div>
      </div>
      <el-tree
        :data="businessData"
        :show-checkbox="true"
        :default-expand-all="true"
        @check-change="loadOrDeleteMap"
        ref="tree"
        node-key="label"
        :highlight-current="false"
        :render-content="renderContent">

      </el-tree>
    </div>
    <div
      class="detect-list"
      v-show="dialogTableVisible">
      <div class="title">
        <!-- 新增收起/展开按钮 -->
        <el-tooltip class="item" effect="dark" content="添加至地图" placement="top">
          <el-button icon="iconfont icon-xiangjiaofenxi" circle @click="addToMap">
          </el-button>
        </el-tooltip>
        <el-tooltip class="item" effect="dark" content="全屏" placement="top">
          <el-button icon=" iconfont icon-quantu1" circle @click="toggleFullScreen"></el-button>
        </el-tooltip>
        <span style="padding:0 10px">拍摄时间：{{ currentTopViewImageTime }}</span>
        <el-tooltip class="item" effect="dark" content="关闭" placement="top"
                    style="position:absolute;right:8px">
          <el-button icon="el-icon-close" circle @click="closeDetectDialog"></el-button>
        </el-tooltip>
      </div>
      <!-- 可收起的内容区域 -->
      <div class="collapsible-content">
        <div class="gt-query">
          <img ref="image" :src="currentImagePath" style="width:100%;height:100%"/>
        </div>
        <div class="block">
          <el-slider
            @input="handleInput"
            v-model="value"
            show-input>
          </el-slider>
        </div>
      </div>
    </div>
    <div v-if="isFullScreen" class="fullscreen-container" ref="fullscreenContainer">
      <img :src="currentImagePath" class="fullscreen-image">
      <button @click="closeFullScreen" class="close-fullscreen-btn">×</button>
    </div>
  </div>
</template>

<script>
import {FeatureService, GetFeaturesBySQLParameters, ImageTileLayer, TiledMapLayer} from "@supermap/iclient-leaflet";
import {
  getSmallMapApi,
  getPanoramaPointByCountryApi,
  getTopViewDataApi,
  getOneMapApi,
  getFrameAreaByPointIdApi
} from "@/api/commonApi";
import 'leaflet.markercluster'; // 引入插件
import 'leaflet.markercluster/dist/MarkerCluster.Default.css'

import 'leaflet-rotate';
import axios from "axios";
import L from "leaflet";

export default {
  name: "MapComponent",
  props: {
    activeItem: {
      type: Object,
      required: true
    },
    currentLocationMarker: {
      type: Object,
      default: null
    }
  },

  data() {
    return {
      map: null,
      baseMapService: window.config.baseMapService,
      baseMapServiceType: window.config.baseMapServiceType,
      baseMaxNativeZoom: window.config.baseMaxNativeZoom,
      center:window.config.center,
      layerRandList: [],
      isShowTree: true,
      pointLocationList: [],//全景点坐标
      drawCircles: [],//在地图上加载的所有全景点集合
      drawMarkers: [],//在地图上加载的所有marker集合
      marker: null,//线索标记
      clusterLayer: null,//聚合图层组
      allClueList: [],//所有线索集合，10000
      position: {
        top: 140, // 初始 top 值
        left: 850, // 初始 left 值
      },
      isDragging: false,
      startX: 0,
      startY: 0,
      dialogVideoVisible: false,
      currentPolygonLayer: null,
      markers: [],
      currentMarker: null,
      currentAzimuth: 0,
      currentActivateCenter: 0,
      businessData: [
        {label: '基础地理数据', children: []},
        {label: '资源调查数据', children: []},
        {label: '低空业务数据', children: []}
      ], //业务数据列表
      currentLeafNodes: [],
      panoramaPointLayer: L.layerGroup(), //全景点位图层
      bufferLayer: L.layerGroup(), //缓冲区图层
      topViewList: [],
      nestList: [], //机巢点列表
      nestLayer: L.layerGroup(), //机巢点图层
      neatBufferLayer: L.layerGroup(), //机巢缓冲区图层
      topViewLayer: L.layerGroup(), //俯视图图层
      isClickCompass: true, //是否点击了指北针
      changeYaw: 0,
      circleRadius: window.config.circleRadius,
      projectCity: window.config.projectCity,
      polygonToPointId: -1,  //当前图斑对应的点位id
      topViewMarker: [],
      dialogTableVisible: false,
      overlay: null,
      value: 70,
      isFullScreen: false,
      currentImagePath: '',
      currentTopViewImageTime: '',
      currentImageBounds: [],
      maxZoom: window.config.maxZoom,
    };
  },
  watch: {
    activeItem(newVal, oldVal) {
      if (this.currentPolygonLayer) {
        this.map.removeLayer(this.currentPolygonLayer)
      }
      const currentPolygon = L.polygon(newVal.polygon, {
        color: '#56f501',
        fillColor: '#30f',
        fillOpacity: 0
      }).addTo(this.map)
      this.currentPolygonLayer = currentPolygon;
      const center = currentPolygon.getBounds().getCenter();
      // 将地图视角移动到多边形的中心位置
      this.map.setView(center, 13);

      //寻找对应的marker
      this.markers.forEach(mData => {
        if (mData.sector) {
          this.map.removeLayer(mData.sector);  // 移除扇形
        }
        mData.circle.setStyle({
          color: 'orange',
          fillColor: 'orange',
          opacity: 0.4,
          fillOpacity: 0.4,         // 填充透明度
          weight: 2               // 边框宽度
        });
      });

      const markerObj = this.markers.find(marker => marker.id === newVal.point_location_id);
      this.currentActivateCenter = [markerObj.lat, markerObj.lon]
      this.drawSector(markerObj.lat, markerObj.lon, markerObj, markerObj.circle)
      const itemObj = this.pointLocationList.find(item => item.pointId === markerObj.id)
      this.$emit('handleReceivePointId',
        {
          'point_id': markerObj.id,
          'point_obj': itemObj,
          'azimuth': this.currentAzimuth,
          'polygon_item': this.activeItem,
        })
      this.polygonToPointId = markerObj.id
      this.getTopViewData({time: ''})
    },
    currentLocationMarker(newVal, oldVal) {
      if (oldVal) {
        this.map.removeLayer(oldVal.currentLocationMarker)
      }
      if (newVal) {
        this.map.addLayer(newVal.currentLocationMarker);
      }
    }

  },
  computed: {},

  methods: {
    // 一键展开所有节点
    handleExpandAll() {
      this.isShowTree = false;
    },
    // 一键收起所有节点
    handleCollapseAll() {
      this.isShowTree = true;
    },
    async initMap() {
      let resolutions = [
        1.40625,
        0.703125,
        0.3515625,
        0.17578125,
        0.087890625,
        0.0439453125,
        0.02197265625,
        0.010986328125,
        0.0054931640625,
        0.00274658203125,
        0.001373291015625,
        0.0006866455078125,
        0.00034332275390625,
        0.000171661376953125,
        0.0000858306884765625,
        0.00004291534423828125,
        0.000021457672119140625,
        0.000010728836059570312,
        0.000005364418029785156
      ];
      let myCrs = null;
        if (this.projectCity === 'nanjing') {
            myCrs = L.CRS.EPSG3857;
        }else if(this.projectCity === 'jiangyin'){
            const resolutions = [];
            let res = 78183.89453125001;
            for (let i = 0; i < 20; i++) {
                resolutions.push(res);
                res /= 2;
            }
            proj4.defs("EPSG:4528","+proj=tmerc +lat_0=0 +lon_0=120 +k=1 +x_0=40500000 +y_0=0 +ellps=GRS80 +units=m +no_defs +type=crs");
            myCrs = new L.Proj.CRS("EPSG:4528", {
                resolutions: resolutions,
            })
        } else {
            myCrs = L.Proj.CRS('EPSG:4326', {
                bounds: L.bounds([-180, -90], [180, 90]),
                origin: [-180, 90],
                resolutions: resolutions
            });
        }

      this.map = L.map('mapContainer', {
        crs: myCrs,
        zoom: 13, //缩放级别
        zoomControl: false, //缩放组件
        attributionControl: false, //去掉右下角logo
        rotate: true,
        rotateControl: {
          closeOnZeroBearing: false,
          position: 'topright',
        },
        compassBearing: true,
        touchRotate: true
      });
      if (this.baseMapService) {
        if (this.baseMapServiceType === '1') {
          this.baseMapLayer = new TiledMapLayer(this.baseMapService, {
            maxZoom: this.maxZoom, // 允许地图缩放到 22 级
            maxNativeZoom: this.baseMaxNativeZoom, // 瓦片服务实际支持的最高级别
            reuseTiles: false, // 关键参数：禁止复用旧瓦片
            updateWhenIdle: false, // 拖动时也更新瓦片
            updateWhenZooming: false, // 缩放时也更新
            keepBuffer: 1000, // 仅保留1屏缓冲
            updateInterval: 0,
            tileSize: 256,
            fadeAnimation: false,  // 禁用淡入动画
            zoomAnimation: false,  // 禁用缩放动画（可选）
            preferCanvas: true,    // 使用Canvas渲染，性能更好
            noWrap: true // 禁止瓦片重复
          });
        } else if (this.baseMapServiceType === '2') {
          this.baseMapLayer = L.tileLayer(`${this.baseMapService}/tile/{z}/{y}/{x}`, {
            maxZoom: this.maxZoom, // 允许地图缩放到 22 级
            maxNativeZoom: this.baseMaxNativeZoom, // 瓦片服务实际支持的最高级别
            minZoom: this.minZoom,
            pane: 'tilePane',
            updateWhenIdle: false, // 拖动时也更新瓦片
            updateWhenZooming: false, // 缩放时也更新
            keepBuffer: 3, // 仅保留1屏缓冲
            updateInterval: 200,
            zoomOffset: 0,
            noWrap: true // 禁止瓦片重复
          });
        } else {
          this.baseMapLayer = L.tileLayer(this.baseMapService, {
            maxZoom: this.maxZoom,       // 允许地图缩放到 22 级
            maxNativeZoom: 16, // 瓦片服务实际支持的最高级别
            reuseTiles: false,  // 关键参数：禁止复用旧瓦片
            updateWhenIdle: true,
            updateInterval: 200,
            keepBuffer: 1,      // 仅保留1屏缓冲
            noWrap: true        // 禁止瓦片重复
          }).addTo(this.map)
        }
        this.baseMapLayer.addTo(this.map);
        this.baseMapLayer.bringToBack();
        this.map.setView(this.center,16)
        this.layerRandList.unshift({
          name: '底图',
          layer: this.baseMapLayer,
          shapeOption: {
            opacity: 1, //透明度
            brightness: 1, //亮度
            contrast: 1, //对比度
            saturation: 1 //饱和度
          },
          show: true,
          expanded: false,
          source_type: '底图'
        });

      }
      // 为按钮添加点击事件,默认事件不生效
      if (document.getElementsByClassName('leaflet-control-rotate-toggle')) {
        var elements = document.getElementsByClassName('leaflet-control-rotate-toggle');
        var that = this;
        for (var i = 0; i < elements.length; i++) {
          elements[i].onclick = (e) => {
            // that.rotateMap(0);
            e.stopPropagation();
            this.isClickCompass = !this.isClickCompass
            if (this.isClickCompass) {
              // 第一次点击：启用跟随模式
              this.map.setBearing(this.changeYaw);
            } else {
              // 第二次点击：重置到正北
              that.rotateMap(0);
            }
          };
        }
      }
    },

    initPanoramaPointLayer() {
      try {
        this.panoramaPointLayer.clearLayers();
        this.pointLocationList.forEach((item) => {
          const circle = L.circle([item.latitude, item.longitude], 80, {
            color: 'orange',
            fillColor: 'orange',
            fillOpacity: 0.5,
            weight: 2
          }).addTo(this.panoramaPointLayer)
          const lat = item.latitude;
          const lon = item.longitude;
          const markerData = {
            id: item.pointId,
            circle,
            sector: null,
            lat,
            lon,
          };
          this.markers.push(markerData);
          // 添加点击事件
          circle.on('click', () => {
            this.markers.forEach(mData => {
              if (mData.sector) {
                this.map.removeLayer(mData.sector);  // 移除扇形
              }
              mData.circle.setStyle({
                color: 'orange',
                fillColor: 'orange',
                fillOpacity: 0.5,         // 填充透明度
                weight: 2               // 边框宽度
              });
            });

            // 绘制当前标记的扇形
            this.drawSector(lat, lon, markerData, circle)
            this.$emit('handleReceivePointId',
              {
                'point_id': item.pointId,
                'point_obj': item,
                'azimuth': this.currentAzimuth,
                'polygon_item': this.activeItem
              })
          });
        });
        if (this.pointLocationList.length > 0) {
          const firstMarker = this.markers[0];
          this.drawSector(firstMarker.lat, firstMarker.lon, firstMarker, firstMarker.circle)
          this.$emit('handleReceivePointId',
            {
              'point_id': this.pointLocationList[0].pointId,
              'point_obj': this.pointLocationList[0],
              'azimuth': this.currentAzimuth,
              'polygon_item': this.activeItem
            })
        }
        return this.panoramaPointLayer;
      } catch (error) {
        return L.layerGroup(); // 返回空图层避免中断
      }
    },

    async getPanoramaPoint() {
      //获取全景点坐标
      const res = await getPanoramaPointByCountryApi({});
      if (res.code !== 0) {
        this.$message.error(res.msg)
        return
      }
      this.pointLocationList = res.data;
    },

    //获取700m缓冲区数据图层
    getBufferData() {
      this.bufferLayer.clearLayers();
      this.pointLocationList.forEach((item) => {
        // 绘制圆圈范围
        const radiusNew = this.circleRadius;
        const startAngleNew = 0;
        const endAngleNew = 360;
        const numberOfPointsNew = 360;
        const latlngsNew = [];
        const angleStep = (endAngleNew - startAngleNew) / numberOfPointsNew;
        for (let i = 0; i <= numberOfPointsNew; i++) {
          const angle = ((startAngleNew + i * angleStep) * Math.PI) / 180; // 转换为弧度
          const pointLat = item.latitude + (radiusNew / 111320) * Math.cos(angle); // 111320是大约的米/纬度度转换系数
          const pointLon = item.longitude + (radiusNew / 111320) * Math.sin(angle);

          latlngsNew.push([pointLat, pointLon]);
        }
        const circle = L.polygon(latlngsNew, {
          color: 'yellow',
          fillColor: 'red',
          fillOpacity: 0,
          weight: 1
        }).addTo(this.bufferLayer);
      });
      return this.bufferLayer;
    },


    // 计算从中心点到边界点的角度
    calculateAngle(lat1, lon1, lat2, lon2) {
      const radLat1 = this.toRadians(lat1);
      const radLon1 = this.toRadians(lon1);
      const radLat2 = this.toRadians(lat2);
      const radLon2 = this.toRadians(lon2);
      const y = Math.sin(radLon2 - radLon1) * Math.cos(radLat2);
      const x = Math.cos(radLat1) * Math.sin(radLat2) -
        Math.sin(radLat1) * Math.cos(radLat2) * Math.cos(radLon2 - radLon1);
      const brng = Math.atan2(y, x) * (180 / Math.PI);
      return (brng + 360) % 360;
    },
    // 将角度转换为弧度
    toRadians(degrees) {
      return degrees * Math.PI / 180;
    },
    //计算图斑中心点坐标
    calculateSimpleCentroid(coords) {
      let sumX = 0;
      let sumY = 0;
      let numPoints = coords.length;
      for (let i = 0; i < numPoints; i++) {
        sumX += coords[i][0];
        sumY += coords[i][1];
      }
      return [sumX / numPoints, sumY / numPoints];
    },
    drawSector(lat, lon, markerData, marker) {
      // 绘制当前标记的扇形
      const radius = this.circleRadius;
      const startAngle = -30;
      const endAngle = 30;
      const numberOfPoints = 50;
      if (this.activeItem.polygon) {
        let centroid = this.calculateSimpleCentroid(this.activeItem.polygon)
        // 计算从原中心点到图斑中心点的连线与正北方向的夹角
        const angle = this.calculateAngle(lat, lon, centroid[0], centroid[1]);
        // 确定起始角度和结束角度
        const startAngle = angle - 30;
        const endAngle = angle + 30;
        this.currentAzimuth = angle;
      }

      const latlngs = this.getSectorCoordinates(lat, lon, radius, startAngle, endAngle, numberOfPoints);
      latlngs.push([lat, lon]);
      const sector = L.polygon(latlngs, {
        color: 'blue',
        fillColor: 'transparent',
        fillOpacity: 0
      }).addTo(this.map);
      // 设置当前点击的标记图标为红色
      marker.setStyle({
        color: 'blue',
        fillColor: 'blue',
        fillOpacity: 0.3,         // 填充透明度
        weight: 1               // 边框宽度
      });
      this.currentMarker = {marker, sector, lat, lon};
      // 更新当前标记的扇形数据
      markerData.sector = sector;
    },
    //绘制扇形
    getSectorCoordinates(lat, lon, radius, startAngle, endAngle, numberOfPoints) {
      const latlngs = [];
      const angleStep = (endAngle - startAngle) / numberOfPoints;
      for (let i = 0; i <= numberOfPoints; i++) {
        const angle = (startAngle + i * angleStep) * Math.PI / 180; // 转换为弧度
        const pointLat = lat + (radius / 111320) * Math.cos(angle); // 111320是大约的米/纬度度转换系数
        //const pointLon = lon + (radius / (111320 * Math.cos(lat * Math.PI / 180))) * Math.sin(angle);
        const pointLon = lon + (radius / 111320) * Math.sin(angle);
        latlngs.push([pointLat, pointLon]);
      }
      return latlngs;
    },
    //更新扇形
    updateSector(yaw, originyawDegree) {
      if (!this.currentMarker) return;
      // 旋转底图
      this.changeYaw = 0 - yaw - originyawDegree;
      const {marker, sector, lat, lon} = this.currentMarker;
      if (this.changeYaw && this.isClickCompass) {
        this.map.setView([lat, lon])
        this.map.setBearing(this.changeYaw);
      }

      const radius = this.circleRadius;
      const startAngle = yaw + originyawDegree - 30;
      const endAngle = yaw + originyawDegree + 30;
      const numberOfPoints = 50;
      // 更新扇形坐标
      let latlngs = this.getSectorCoordinates(lat, lon, radius, startAngle, endAngle, numberOfPoints);
      latlngs.push([lat, lon]);
      // 更新地图上的扇形
      sector.setLatLngs(latlngs);
      sector.addTo(this.map)
    },
    // 旋转底图
    rotateMap(yaw) {
      if (!yaw) {
        yaw = 0;
      }
      this.map.setBearing(yaw);
    },
    updateMap() {
      this.map.setView(this.currentActivateCenter, 14);
    },
    get_business_data() {
      getSmallMapApi().then((res) => {
        if (res.code === 0) {
          this.businessData = res.data;
          res.data.forEach((item) => {
            if (item.label === '低空业务数据') {
              const nestList = item.children.find((i) => i.data_type === 'nest_location');
              if (nestList) {
                this.nestList = nestList.data ? nestList.data : [];
              }
            }
          });
          //设置初始选中的地图服务
          this.$nextTick(() => {
            const lowAltitudeData = this.businessData.find((item) => item.label === '低空业务数据');
            const panorama = lowAltitudeData.children.find((item) => item.data_type === 'panorama');
            const panoramaCoverage = lowAltitudeData.children.find((item) => item.data_type === 'panorama_coverage');
            this.$refs.tree.setCheckedNodes([panorama, panoramaCoverage]);
          });
        } else {
          this.$message.error('获取业务数据失败');
        }
      });
    },
    loadOrDeleteMap() {
      const nodes = this.$refs.tree.getCheckedNodes();
      // 叶节点
      const leafNodes = nodes.filter((node) => !node.children || node.children.length === 0);
      // 新增叶节点
      if (leafNodes.length > this.currentLeafNodes.length) {
        const addLeafNodes = leafNodes.filter((node) => !this.currentLeafNodes.some((currentNode) => currentNode.label === node.label));
        this.addLayers(addLeafNodes);
      } else if (leafNodes.length < this.currentLeafNodes.length) {
        // 删除叶节点
        const deleteLeafNodes = this.currentLeafNodes.filter((node) => !leafNodes.some((currentNode) => currentNode.label === node.label));
        this.removeLayers(deleteLeafNodes);
      }
    },
    //设置树子节点样式
    renderContent(h, {node}) {
      // 获取子节点数量
      return (
        <span class="custom-tree-node" style="display:flex;align-items:center">
                    {node.isLeaf
                      ? [
                        <span
                          key="label"
                          title={node.label}
                          style="font-weight:700;font-size:14px;color:#000000a6;display:inline-block;width:120px;text-overflow:ellipsis;overflow:hidden;white-space:nowrap;">
                                  {node.label}
                              </span>
                      ]
                      : [
                        <span key="label" style="font-weight:bold;font-size:14px;color:#000000a6;">
                                  {node.label}
                              </span>
                      ]}
                </span>
      );
    },
    //添加地图图层
    async addLayers(addLeafNodes) {
      addLeafNodes.forEach(async (node) => {
        let layer;
        if (node.source_type === '业务矢量数据服务' && node.datasets_name) {
          layer = await this.getVectorData(node); //矢量服务
        } else if (node.data_type && node.data_type === 'panorama') {
          layer = this.initPanoramaPointLayer(); //全景点位
        } else if (node.data_type && node.data_type === 'panorama_coverage') {
          layer = this.getBufferData(); //全景覆盖范围
        } else if (node.data_type && node.data_type === 'nest_location') {
          layer = this.getNestData(node); //机巢点位
        } else if (node.data_type && node.data_type === 'nest_coverage') {
          layer = this.getNestBufferData(node); //机巢覆盖范围
        } else if (node.data_type && node.data_type === 'top_view') {
          layer = this.getTopViewLayerData(); //俯视图范围
        } else {
          if (node.label !== '航片') {
            if (node.gis_service_type === '1') {
              //iserver服务
              layer = new TiledMapLayer(node.service, {
                maxZoom: this.maxZoom,       // 允许地图缩放到 22 级
                maxNativeZoom: this.maxZoom, // 瓦片服务实际支持的最高级别
                reuseTiles: false,  // 关键参数：禁止复用旧瓦片
                updateWhenIdle: true,
                updateInterval: 200,
                keepBuffer: 1,      // 仅保留1屏缓冲
                noWrap: true        // 禁止瓦片重复
              });
            } else if (node.gis_service_type === '2') {
            } else if (node.gis_service_type === '3') {
              //天地图服务
              // 矩阵集id, 决定了在每一级该去请求哪一个identifier对应的切片，如果只有个别几级需要处理minZoom， maxZoom
              let identifier = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]
              let matrixIds = [];
              for (var i = 0; i < identifier.length; i++) {
                matrixIds.push({
                  identifier: identifier[i]
                })
              }
              layer = new L.supermap.WMTSLayer(node.service, {
                layer: "img",
                style: "default",
                tilematrixSet: "c",
                format: "tiles",
                matrixIds: matrixIds,
                maxZoom: identifier.length - 1,
              }).addTo(this.map)
              this.map.setView(this.center, 13)
            } else {
              //geoserver服务
              layer = L.tileLayer.wms(node.service, {
                layers: `${node.datasource_name}:${node.datasets_name}`, // 图层名称
                format: 'image/png',
                transparent: true,
                attribution: "Your Attribution"
              })
            }
          } else {
            layer = await this.getAerialPhotoLayer(node)
          }
        }
        this.map.addLayer(layer);
        // if (node.data_type && node.data_type === '地图服务' && node.service) {
        //     layer.bringToBack(); //地图服务图层置底
        // }
        if (node.center && node.source_type === '影像服务') {
          this.map.setView(JSON.parse(node.center));
        }
        node.layer = layer;
      });
      this.currentLeafNodes = this.currentLeafNodes.concat(addLeafNodes);
    },
    //删除地图图层
    removeLayers(deleteLeafNodes) {
      deleteLeafNodes.forEach((node) => {
        this.map.removeLayer(node.layer);
        if (node.data_type === 'panorama') {
          this.markers.forEach((mData) => {
            if (mData.sector) {
              this.map.removeLayer(mData.sector); // 移除扇形
            }
          });
        }
        // 新增：移除关联的影像图层和事件监听
        if (node.layer._zoomHandler) {
          this.map.off('zoomend', node.layer._zoomHandler); // 移除事件监听
        }
        if (node.layer._imageLayers) { // 假设将imageLayers挂载到layerGroup上
          Object.values(node.layer._imageLayers).forEach(layer => {
            this.map.removeLayer(layer);
          });
        }
      });

      this.currentLeafNodes = this.currentLeafNodes.filter((node) => !deleteLeafNodes.some((currentNode) => currentNode.label === node.label));
    },
    getFeaturesBySQLAsync(featureService, params) {
      return new Promise((resolve, reject) => {
        featureService.getFeaturesBySQL(params, (serviceResult) => {
          if (serviceResult && serviceResult.result) {
            resolve(serviceResult.result);
          } else {
            reject(new Error('No features found or invalid response'));
          }
        });
      });
    },
    //获取地图服务矢量数据图层
    async getVectorData(node) {
      if (node.gis_service_type === '1') {
        try {
          //获取网格数据多边形坐标
          var sqlParam = new GetFeaturesBySQLParameters({
            queryParameter: {
              name: `${node.datasets_name}@${node.datasource_name}`,
              attributeFilter: '1=1'
            },
            datasetNames: [`${node.datasource_name}:${node.datasets_name}`]
          });
          const vectorData = [];
          const featureService = await new FeatureService(node.service);
          const serviceResult = await this.getFeaturesBySQLAsync(featureService, sqlParam);
          serviceResult.features.features.forEach((item) => {
            vectorData.push(item);
          });
          if (vectorData.length > 0) {
            const geojsonFeature = {
              type: 'FeatureCollection',
              features: vectorData
            };
            return L.geoJSON(geojsonFeature, {
              style: {
                color: 'red',
                weight: 2,
                opacity: 1,
                fillColor: '#ffeb3b',
                fillOpacity: 0
              }
            });
          }
        } catch (error) {
          this.$message.error('加载矢量数据错误！');
        }
      } else {
        var urlString = node.service + "/" + node.datasource_name + "/ows";
        var param = {
          service: 'WFS',
          transparent: '50%',
          version: '1.1.0',
          request: 'GetFeature',
          typeName: node.datasets_name,
          outputFormat: 'application/json',
          maxFeatures: 20000,
          srsName: "EPSG:4326"
        };
        var u = urlString + L.Util.getParamString(param, urlString);
        // 关键：用await等待axios请求完成，确保数据返回后再继续
        const response = await axios.get(u);

        // 基于返回数据创建图层
        const layer = L.geoJson(response.data, {
          style: {
            color: "red",
            fillOpacity: 0
          }
        });
        return layer;
      }
    },
    async getAerialPhotoLayer(node) {
      // 创建图层组
      const layerGroup = await this.createAggregateMarker(node);
      // 存储影像图层引用
      const imageLayers = {};
      // 记录当前是否已放大到显示影像的级别
      let isShowingImagery = false;
      // 将imageLayers挂载到layerGroup上便于后续清理
      layerGroup._imageLayers = imageLayers;
      // 监听地图缩放事件
      const zoomHandler = () => {
        const zoom = this.map.getZoom();
        console.log('当前缩放级别：', zoom);
        // 当放大到指定级别(如14级)时显示影像
        if (zoom >= 14) {
          if (!isShowingImagery) {
            layerGroup.eachLayer(marker => {
              const bbox = marker._bbox;
              const bboxBounds = L.latLngBounds(
                L.latLng(bbox[1], bbox[0]), // 西南角 (minY, minX)
                L.latLng(bbox[3], bbox[2])  // 东北角 (maxY, maxX)
              );
              // if (this.map.getBounds().contains(marker._imageCenter)) {
              if (this.map.getBounds().intersects(bboxBounds)) {
                if (marker._imageService && !imageLayers[marker._imageService + `+${marker._timeName}`]) {  //区分开来
                  const imageLayer = new ImageTileLayer(marker._imageService, {
                    collectionId: marker._tiffServiceCollection,
                    names: [marker._timeName],
                    maxZoom: 24  //设置最大级别
                  })
                  // 存储图层引用
                  imageLayers[marker._imageService + `+${marker._timeName}`] = imageLayer;
                  // 将影像图层添加到地图
                  this.map.addLayer(imageLayer);
                }
              }
            });
            isShowingImagery = true;
          }
        } else {
          // 当缩小到指定级别以下时移除影像图层
          if (isShowingImagery) {
            Object.values(imageLayers).forEach(layer => {
              this.map.removeLayer(layer);
            });
            // 清空对象
            for (const key in imageLayers) {
              delete imageLayers[key];
            }
            isShowingImagery = false;
          }
        }
      };

      // 添加事件监听
      this.map.on('zoomend', zoomHandler);
      // 存储zoomHandler以便后续可以移除
      layerGroup._zoomHandler = zoomHandler;
      // 点击标记时显示对应影像
      layerGroup.on('click', (e) => {
        if (e.layer._imageService) {
          // 放大到显示影像的级别但不改变中心点
          this.map.setZoom(14);
          this.map.flyTo(e.layer._imageCenter)
        }
      });
      return layerGroup;
    },
    // 创建聚合标记
    async createAggregateMarker(node) {
      const layerGroup = L.markerClusterGroup({
        disableClusteringAtZoom: 14, // 在16级停止聚合
        spiderfyOnMaxZoom: false,    // 禁用最后一级的蜘蛛展开
        showCoverageOnHover: false,   // 禁用悬停显示覆盖区域
        singleMarkerMode: true,
        // 自定义图标创建函数，使单个点也显示为聚合样式
        iconCreateFunction: function (cluster) {
          const count = cluster.getChildCount();
          // 即使是单个标记，也强制使用聚合样式
          return L.divIcon({
            html: '<div><span>' + count + '个</span></div>',
            className: 'marker-cluster marker-cluster-' +
              (count < 10 ? 'small' : count < 100 ? 'medium' : 'large'),
            iconSize: new L.Point(40, 40) // 确保尺寸正确
          });
        }
      });
      // 为每个航片添加标记
      // node.list.forEach((item) => {
      for (const item of node.list) {
        if (item.tiffCenter !== "") {
          const center = item.tiffCenter.split(',').map(item => parseFloat(item));
          const defaultIconBlue = L.icon({
            iconUrl: require('@/assets/images/marker-icon-blue.png'),
            iconSize: [25, 40], // 图标大小
            iconAnchor: [12.5, 40], // 图标锚点（中心点）
            popupAnchor: [-3, -40] // 弹出窗偏移量
          });
          const marker = L.marker(center, {icon: defaultIconBlue});
          // 存储影像服务URL到标记上
          marker._imageService = window.config.iserverAdress;
          marker._imageCenter = center;
          marker._tiffServiceCollection = item.tiffServiceCollection;
          marker._timeName = item.timeName;
          const bbox = await this.cacuBounds(item.tiffId, item.tiffServiceCollection)
          marker._bbox = bbox;
          layerGroup.addLayer(marker);
        }
      }
      ;
      return layerGroup;
    },
    //计算航片边界
    async cacuBounds(tiffId, tiffServiceCollection) {
      if (tiffId == '' || tiffServiceCollection == '') {
        this.$message.error('航片数据不全，无法计算边界，导致无法显示影像')
      }
      try {
        const res = await this.axios.get(
          `${window.config.iserverAdress}collections/${tiffServiceCollection}/items/${tiffId}.json`,
          {withCredentials: false}
        );
        const bbox = res.data.properties['proj:bbox'];
        return bbox;
      } catch (err) {
        console.error(err);
        return null; // 或者抛出错误 throw err;
      }
    },
    async getTopViewData(para) {
      const res = await getTopViewDataApi(para);
      if (res.code === 0) {
        this.topViewList = res.data;
      }
      const params1 = {
        pointId: this.polygonToPointId
      }
      const res1 = await getFrameAreaByPointIdApi(params1);
      if (res1.code && res1.code === 0) {
        this.no_detection_area_list = res1.data.no_detection_area_list
      }
    },
    getTopViewLayerData() {
      //换成红色图标
      const customIcon = L.icon({
        iconUrl: require('@/assets/images/topBlue.png'), // 替换为红色图标的路径
        iconSize: [32, 32],
        iconAnchor: [16, 32],
        popupAnchor: [0, -32]
      });
      const redIcon = L.icon({
        iconUrl: require('@/assets/images/topRed.png'), // 替换为红色图标的路径
        iconSize: [32, 32],
        iconAnchor: [16, 32],
        popupAnchor: [0, -32]
      });
      const data = [];
      this.topViewList.map(item => {
        const bounds = JSON.parse(item.bounds)
        data.push(
          {
            'path': '/panoramaUrl' + item.path,
            'imageBounds': bounds
          }
        )
        const marker = L.marker(bounds[0], {icon: customIcon})
        const markerData = {
          marker,
          customIcon: customIcon,
          redIcon: redIcon
        };
        this.topViewMarker.push(markerData)
        this.topViewLayer.addLayer(marker)
        marker.on('click', () => {
          this.dialogTableVisible = true;
          this.currentImagePath = '/panoramaUrl' + item.path;
          this.currentImageBounds = bounds;
          this.currentTopViewImageTime = item.collect_time;
          this.topViewMarker.forEach((mData) => {
            mData.marker.setIcon(mData.customIcon); // 重置图标为默认
          });
          marker.setIcon(redIcon); // 设置为红色图标
          this.map.setView(bounds[0], 16)
        });
      })
      return this.topViewLayer

    },
    //获取机巢数据图层
    getNestData(node) {
      const nestIcon = L.icon({
        iconUrl: require('@/assets/images/nest.png'),
        iconSize: [40, 40], // 图标大小
        iconAnchor: [20, 20], // 图标锚点（中心点）
        popupAnchor: [-3, -40] // 弹出窗偏移量
      });
      this.nestList.forEach((item) => {
        const marker = L.marker([item.latitude, item.longitude], {icon: nestIcon, nest_id: item.id});
        // 拼接多个信息为 HTML 字符串
        const popupContent = `
                    <div>
                        <strong>名称：</strong>${item.name}<br>
                        <strong>飞机型号：</strong>${item.plane_model}<br>
                        <strong>机巢SN：</strong>${item.nest_sn}<br>
                        <strong>飞机SN：</strong>${item.plane_sn}<br>
                        <strong>经纬度：</strong>${item.latitude},${item.longitude}<br>
                        <strong>位置：</strong>${item.location}
                    </div>
                `;
        marker.bindPopup(popupContent);
        this.nestLayer.addLayer(marker);
      });
      return this.nestLayer;
    },
    //获取机巢5000m缓冲区数据图层
    getNestBufferData(node) {
      this.neatBufferLayer.clearLayers();
      this.nestList.forEach((item) => {
        L.circle([item.latitude, item.longitude], 5000, {
          color: 'red',
          fillColor: 'transport',
          fillOpacity: 0,
          opacity: 1,
          weight: 1
        }).addTo(this.neatBufferLayer);
      });

      return this.neatBufferLayer;
    },
    //获取地图服务数据，构造树节点
    getOneMap(para) {
      getOneMapApi(para).then((res) => {
        if (res.code === 0) {
          this.businessData.forEach((item) => {
            if (item.label === '基础地理数据') {
              item.children = res.data['基础地理数据'].children;
            } else if (item.label === '资源调查数据') {
              item.children = res.data['资源调查数据'].children;
            } else if (item.label === '低空业务数据') {
              // item.children = res.data['低空业务数据'].children;
              const alllowShow = ['panorama', 'panorama_coverage', 'temp_panorama', 'temp_panorama_coverage', '航片', 'top_view']
              res.data['低空业务数据'].children.forEach((i) => {
                if (alllowShow.indexOf(i.data_type) != -1 || alllowShow.indexOf(i.label) != -1) {
                  item.children.push(i)
                }
              })
              item.children.push(
                {
                  "service": "",
                  "center": "",
                  "data_type": "frame_area",
                  "county": "320100",
                  "orderIndex": 10,
                  "datasource_name": "",
                  "datasets_name": "",
                  "label": "不检测区域"
                },
              )
            }
          });
          const targetIndex = this.businessData[0].children.findIndex(item => item.source_type === '影像服务');
          if (targetIndex !== -1) {
            // 从原位置移除
            const targetTask = this.businessData[0].children.splice(targetIndex, 1)[0];
            // 添加到首位
            this.businessData[0].children.unshift(targetTask);
          }
          //设置初始选中的地图服务
          this.$nextTick(() => {
            if (this.businessData[0].children.length > 0) {
              if (para.time === '') {
                const defaultDisplayDataList = []
                const panorama = this.businessData[2].children.find((item) => item.data_type === 'panorama');
                const panoramaCoverage = this.businessData[2].children.find((item) => item.data_type === 'panorama_coverage');
                const aerialPhoto = this.businessData[2].children.find((item) => item.label === '航片');
                defaultDisplayDataList.push(panorama, panoramaCoverage, aerialPhoto)
                this.businessData.forEach((i) => {
                  i.children.forEach((item) => {
                    if (item.isShow && item.isShow == 1) {
                      defaultDisplayDataList.push(item)
                    }
                  })
                })
                this.$refs.tree.setCheckedNodes(defaultDisplayDataList);
              } else {
                this.$refs.tree.setCheckedNodes(this.selectNodes);
              }
            }
          });
        } else {
          message.error('获取地图服务数据失败！');
        }
      });
    },

    closeDetectDialog() {
      this.dialogTableVisible = false;
      if (this.overlay) {
        this.map.removeLayer(this.overlay);
      }
      this.topViewMarker.forEach((mData) => {
        mData.marker.setIcon(mData.customIcon); // 重置图标为默认
      });
    },
    addToMap() {
      if (this.overlay) {
        this.map.removeLayer(this.overlay);
      }
      this.overlay = L.imageOverlay(this.currentImagePath, this.currentImageBounds, {
        opacity: 0.5,       // 透明度（0-1）
        interactive: true   // 允许交互（如点击事件）
      }).addTo(this.map);
    },
    handleInput(val) {
      const value = val / 100;
      if (this.overlay) {
        this.overlay.setOpacity(value);
      }
    },
    toggleFullScreen() {
      this.isFullScreen = true
      this.$nextTick(() => {
        const elem = this.$refs.fullscreenContainer
        if (elem.requestFullscreen) {
          elem.requestFullscreen()
        } else if (elem.webkitRequestFullscreen) { /* Safari */
          elem.webkitRequestFullscreen()
        } else if (elem.msRequestFullscreen) { /* IE11 */
          elem.msRequestFullscreen()
        }
      })
    },
    closeFullScreen() {
      if (document.exitFullscreen) {
        document.exitFullscreen()
      } else if (document.webkitExitFullscreen) { /* Safari */
        document.webkitExitFullscreen()
      } else if (document.msExitFullscreen) { /* IE11 */
        document.msExitFullscreen()
      }
      this.isFullScreen = false

    },
  },
  async created() {

  },
  async mounted() {
    await this.getPanoramaPoint()
    await this.initMap();
    await this.getTopViewData({time: ''});
    await this.getOneMap({time: ''});

    this.$on('panorama-mousemove', (data) => {
      this.map.addLayer(data);
    });
  },

};
</script>

<style>
div#mapContainer .leaflet-control-container .leaflet-left {
  display: none !important;
}
</style>

<style lang="scss" scoped>
.gtp-container {
  height: 100%;
  width: 100%;
  position: relative;
  overflow: hidden;
}

#mapContainer {
  background-color: white; //地图背景颜色
}

.image {
  position: absolute;
  width: 400px;
  height: 400px;
  right: 0;
  bottom: 0;
  z-index: 1000;
  overflow: auto;
  display: flex;
  flex-direction: column;
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
}

.toolbar div {
  cursor: pointer;
}

.toolbar div:hover {
  color: #177de4;
}

.active {
  color: #177de4;
}

.el-checkbox {
  margin: 0 10px;
}

.icon {
  margin: 0 6px;
  font-size: 18px
}

::v-deep .el-drawer.ltr, .el-drawer.rtl {
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
  width: 98%
}

.multicard {
  height: 90%;
  width: 98%;
  background-color: red;
  margin: auto;
}

.view-multi-comparision, .view-single {
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
}

.gt-info {
  width: 100%;
  background-color: #e8e8e8
}

.video {
  position: absolute;
  background-color: #f5f5f5e3;
  user-select: none;
  cursor: move;
  z-index: 99999;
  height: 25%;
  width: 25%;
  right: 10px;
  top: 100px;
}

.video-title {
  display: flex;
  text-align: center;
  border-bottom: 1px solid #fff;
  align-items: center;
  padding: 4px;
}

.video-title span {
  text-align: left;
  width: 98%;

}

.myVideo {
  padding: 0 4px;
  width: 100%;
  height: calc(100% - 50px);
}

.tree-container {
  left: 0px;
  bottom: 10px;
  z-index: 9999999;
  width: 160px;
  height: auto;
  position: absolute;
  display: flex; /* 使用flex布局 */
  flex-direction: column; /* 子元素按列排列 */
  background: #fff;
  border-radius: 5px;
  overflow-y: auto;
}

.tree-container label {
  display: flex;
  align-items: center; /* 垂直居中对齐子元素 */
  padding: 5px; /* 移除默认的外边距 */
  font-size: 12px;
}

.tree-container {
  background-color: rgba(255, 255, 255, 0.4);
}

.tree-container ::v-deep(.el-checkbox) {
  position: absolute;
  right: 0;
}

.tree-container ::v-deep(.el-tree) {
  background-color: rgba(255, 255, 255, 0);
}

.tree-container ::v-deep(.is-leaf) {
  display: none;
}

.tree-container ::v-deep(.el-tree-node) {
  padding: 4px 0;
}

.tree-container ::v-deep(.el-tree-node__content):hover,
.tree-container ::v-deep(.el-tree-node.is-current > .el-tree-node__content) {
  background-color: rgba(255, 255, 255, 0.3) !important;
}

.tree-container ::v-deep(.el-tree-node__expand-icon) {
  color: black;
}

.tree-container ::v-deep(.el-tree-node__children) {
  padding-top: 2px;
}

/*
::v-deep .leaflet-control-rotate-toggle {
  background-color: #fff !important;
}


::v-deep .leaflet-control-rotate-toggle:hover {
  background-color: #b3d4fc !important;
}
*/
.detect-list {
  background-color: rgba(0, 0, 0, 0.4);
  box-shadow: none;
  z-index: 999;
  color: #fff;
  position: absolute;
  width: 330px;
  height: auto;
  overflow-y: auto;
  padding: 10px;
  display: flex;
  flex-direction: column;
  min-height: 40px;
  cursor: grab;
  right: 10px;
  top: 80px;
}

::v-deep .el-button--small.is-circle {
  padding: 5px;
}

::v-deep .button-expand {
  color: rgba(0, 0, 0, 0.65);
  font-weight: bold;
  font-size: 15px !important;
  cursor: pointer;
}

::v-deep .button-expand i {
  font-size: 18px !important;
  padding-right: 6px;
  font-weight: bold;
}

.show-control {
  padding: 4px;
  background-color: rgba(255, 255, 255, 0.4);
}
</style>
