<template>
  <div style="height: 100%">
    <div id="mapContainer" class="map-box"></div>

    <div id="toolbar">
      <a-menu mode="vertical">
        <a-menu-item title="首页" class="menu-class">
          <router-link to="/">
            <a-icon type="home" class="iconfont"/>
          </router-link>
        </a-menu-item>
        <a-menu-item :class="isPredict ? 'disableClick' : ''" class="menu-class" :title="isPredictText">
          <a-dropdown>
            <a class="ant-dropdown-link" @click="drawRectangle">
              <i class="iconfont icon-geoai-draw"></i>
            </a>
            <a-menu slot="overlay" style="min-width: 8rem">
              <a-menu-item @click="drawRectangle">绘制预测区域</a-menu-item>
              <a-menu-item @click="editDrawRectangle">编辑已绘区域</a-menu-item>
              <a-menu-item @click="dragDrawRectangle">拖拽移动</a-menu-item>
              <a-menu-item @click="deleteDrawRectangle">删除区域</a-menu-item>
            </a-menu>
          </a-dropdown>
        </a-menu-item>

        <a-menu-item title="地图放大" class="menu-class" @click="mapZoomIn">
          <a>
            <a-icon type="plus" class="iconfont"/>
          </a>
        </a-menu-item>

        <a-menu-item title="地图缩小" class="menu-class" @click="mapZoomOut">
          <a>
            <a-icon type="minus" class="iconfont"/>
          </a>
        </a-menu-item>

        <a-menu-item title="地图重置" class="menu-class" @click="mapZoomResize">
          <a>
            <a-icon type="redo" class="iconfont"/>
          </a>
        </a-menu-item>

      </a-menu>
    </div>
  </div>
</template>

<script>
    import 'leaflet.pm';
    import 'leaflet.pm/dist/leaflet.pm.css';
    import '@/utils/MovingMarker';
    import {TiledMapLayer, spatialAnalystService} from "@supermap/iclient-leaflet";
    import {getExperienceData} from "@/api/commonApi";
export default {
  name: 'imageSegmentation',
  data() {
    return {
      // 配置信息
      standardConfig: {
      },
        baseUrl:process.env.VUE_APP_API_URL,
      // 当前状态
      currentLayer: {},
      currentSelect: {
        model: {
          key: '',
          value: '模型选择'
        },
        layer: {
          id: 0,
          value: '图层信息'
        }
      },
      // 地图信息
      map: {},
      mapLayer: {},
      // 预测信息：isPredict是否预测中
      isPredict: false,
      isPredictText: '预测区域',
      // 绘制图形信息
      rectanglePolygon: {},
      rectangleLayer: {},
      // 添加开始检测图标及图层
      markerAction: L.icon({
        iconUrl: require('@/assets/maker/marker-action.png'),
        iconSize: [100, 100]
      }),
      makerLayer: {},
      // 预测结果图层
      hasPredictLayer: false,
      predictLayer: {}
    };
  },
  props: [],
  methods: {
    initMap() {

      this.map = L.map('mapContainer', {
        crs: L.CRS.EPSG4326,
        center: this.currentLayer.center,
        maxZoom: 18,
        minZoom: 10,
        zoom: 14,
        zoomControl: false
      })

      this.mapLayer = new TiledMapLayer(this.currentLayer.url, {noWrap: true})
          .addTo(this.map);
      // 添加放大缩小控件
      this.map.addControl(L.control.zoom({position: 'topright'}));
      // 构建绘图工具
      this.initDrawTool();
    },
    initDrawTool() {
      // 初始化绘制工具
      this.map.pm.setLang('zh');
      this.map.pm.addControls({
        position: 'topleft',
        drawPolygon: false, // 绘制多边形
        drawMarker: false, //绘制标记点
        drawCircleMarker: false, //绘制圆形标记
        drawPolyline: false, //绘制线条
        drawRectangle: true, //绘制矩形
        drawCircle: false, //绘制圆圈
        editMode: true, //编辑多边形
        dragMode: true, //拖动多边形
        cutPolygon: false, // 添加一个按钮以删除多边形里面的部分内容
        removalMode: true // 清除多边形
      });
      // 监听创建图形
      this.map.on('pm:create', e => {
        // 记录当前绘制的图形
        this.rectanglePolygon = L.rectangle([
          e.layer._bounds._northEast,
          e.layer._bounds._southWest
        ]);
        this.rectangleLayer = e.layer;
        this.addMarkerCenterPoint(e.layer.getCenter());
      });
    },
    selectedModel(item) {
      this.currentSelect.model.value = item.name;
      this.currentSelect.model.key = item.datasets_name;
      // 删除预测图层
      if (this.hasPredictLayer) {
        this.hasPredictLayer = false;
        this.map.removeLayer(this.predictLayer);
        this.predictLayer = {};
        // 添加预测按钮
        this.makerLayer = L.marker(this.rectangleLayer.getCenter(), {
          icon: this.markerAction
        }).addTo(this.map).on('click', e => {
          this.map.setView(e.latlng);
          this.inference();
        });
      }
    },
    drawRectangle() {
      // 删除已有图形
      this.deleteDrawRectangle();
      // 激活绘制多边形功能
      this.rectangleLayer = this.map.pm.enableDraw('Rectangle', {
        snappable: true,
        snapDistance: 20,
        allowSelfIntersection: false,
        getGeomanDrawLayers: true
      });
      //设置全局的pathOptions样式
      this.map.pm.setPathOptions({
        fillOpacity: 0
      });
    },
    editDrawRectangle() {
      let self = this;
      // 监听编辑
      this.rectangleLayer.on('pm:edit', function (e) {
        // 记录当前绘制的图形
        self.rectanglePolygon = L.rectangle([
          e.target._bounds._northEast,
          e.target._bounds._southWest
        ]);
        self.addMarkerCenterPoint(e.target.getCenter());
      });
      this.map.pm.disableGlobalDragMode();
      this.map.pm.toggleGlobalEditMode();
    },
    dragDrawRectangle() {
      let self = this;
      // 监听拖拽
      this.rectangleLayer.on('pm:dragend', function (e) {
        self.rectanglePolygon = L.rectangle([
          e.target._bounds._northEast,
          e.target._bounds._southWest
        ]);
        self.addMarkerCenterPoint(e.target.getCenter());
      });
      this.map.pm.disableGlobalEditMode();
      this.map.pm.toggleGlobalDragMode();
    },
    deleteDrawRectangle() {
      this.map.removeLayer(this.makerLayer);
      this.makerLayer = {};
      this.map.removeLayer(this.rectangleLayer);
      this.rectangleLayer = {};
      // 删除预测图层
      if (this.hasPredictLayer) {
        this.hasPredictLayer = false;
        this.map.removeLayer(this.predictLayer);
        this.predictLayer = {};
      }
    },
    addMarkerCenterPoint(centerPoint) {
      //加载marker点到地图中并绑定点击事件
      this.map.removeLayer(this.makerLayer);
      this.makerLayer = L.marker(centerPoint, {icon: this.markerAction})
          .addTo(this.map)
          .on('click', e => {
            this.map.setView(e.latlng);
            this.inference();
          });
    },
    inference() {
      this.map.pm.disableGlobalDragMode();
      this.map.pm.disableGlobalEditMode();
      if (this.currentSelect.model.key == '') {
        return this.$message.warning('请选择模型后，再尝试监测！', 3);
      }
      // 移除中心图标
      this.map.removeLayer(this.predictLayer);
      this.predictLayer = {};
      // 修改预测样式
      this.isPredict = true;
      this.isPredictText = '预测中…';
      this.map.removeLayer(this.makerLayer);
      this.makerLayer = {};
      //  构建矩阵点位数组
      let latlngArray = [];
      this.rectangleLayer._latlngs[0].forEach(thisLoc => {
        latlngArray.push([thisLoc.lat, thisLoc.lng]);
      });
      latlngArray.push(latlngArray[0]);
      //  设置矩形框等待动画
      let dynamicMarkerOutLayer = new L.featureGroup([]);
      let dynamicMarkerOut = L.Marker.movingMarker(
          latlngArray,
          [1000, 1500, 1000, 1500],
          {autostart: true, loop: true}
      );
      let iconOut = L.icon({
        iconUrl: require('@/assets/maker/marker-point.png'),
        iconSize: [30, 30]
      });
      dynamicMarkerOut.setIcon(iconOut).addTo(dynamicMarkerOutLayer);
      dynamicMarkerOutLayer.addTo(this.map);
      // 开始预测
      let overlayAnalystService = spatialAnalystService(
          this.currentLayer.analyticalUrl
      );
      let datasetOverlayAnalystParameters = new SuperMap.DatasetOverlayAnalystParameters(
          {
            sourceDataset: this.currentSelect.model.key, //叠加分析中源数据集的名称,'forest@PREDICT_vector ','water@PREDICT_vector ','building@PREDICT_vector '
            tolerance: 0, //容限
            operateRegions: [this.rectanglePolygon], //操作区域。仅对该区域内的对象进行分析
            operation: SuperMap.OverlayOperationType.CLIP //叠加操作枚举值CLIP。
          }
      );
      // 防止this失效
      let than = this;
      overlayAnalystService.overlayAnalysis(
          datasetOverlayAnalystParameters,
          function (serviceResult) {
            than.isPredict = false;
            than.isPredictText = '预测区域';
            // 清除等待标记
            dynamicMarkerOutLayer.clearLayers();

            // 空间查询
            if (
                serviceResult.type == 'processCompleted' &&
                typeof serviceResult.result.recordset != 'undefined'
            ) {
              than.predictLayer = L.geoJSON(
                  serviceResult.result.recordset.features.features,
                  {
                    style: function (feature) {
                      than.hasPredictLayer = true;
                      //针对查询到的不同的值上色,耕地2：黄色；水系3：蓝色；林地4：绿色；建设用地5：红色，农房6：橙色
                      switch (feature.properties.SmUserID) {
                        case '0':
                          return {color: 'red', fillOpacity: 0};
                        case '1':
                          return {color: 'red', fillOpacity: 0};
                        case '2':
                          return {color: 'yellow', fillOpacity: 0};
                        case '3':
                          return {color: 'red', fillOpacity: 0};
                        case '4':
                          return {color: 'green', fillOpacity: 0};
                        case '5':
                          return {color: 'red', fillOpacity: 0};
                        case '6':
                          return {color: 'orange', fillOpacity: 0};
                        default:
                          return {Color: 'red', fillOpacity: 0};
                      }
                    }
                  }
              ).addTo(than.map);
            } else {
              than.$message.error('监测失败！', 3);
              than.deleteDrawRectangle();
              console.error(serviceResult);
            }
          }
      );
    },
    mapZoomIn() {
      this.map.zoomIn()
    },
    mapZoomOut() {
      this.map.zoomOut()
    },
    mapZoomResize() {
      this.map.setZoom(14)
    }
  },
  async created() {
      const res = await getExperienceData();
      if (res.code === 0) {
        this.currentLayer = {
            "id": 1,
            "name": res.data.name,
            "url": res.data.is_map_url,
            "center": [32.275163,120.187654],
            "crs": 4326,
            "analyticalUrl": res.data.spatial_analysis_url,
            "models": res.data.models
          }

        // 设置默认选中模型
        this.currentSelect.model.key = this.currentLayer.models[0].datasets_name
        this.currentSelect.model.value = this.currentLayer.models[0].name
        this.initMap();
      } else {
        this.$message.error('数据请求失败！', 3);
      }

  },
};
</script>

<style scoped lang="scss">
.map-box {
  /*height: calc(100% - 4rem);*/
  height: 100%;
}

/*  隐藏右下角logo*/
::v-deep .leaflet-bottom {
  display: none;
}

/*  放大缩小控件位置*/
::v-deep #mapContainer .leaflet-control-container .leaflet-control-zoom.leaflet-bar.leaflet-control {
  display: none;
}

/*  工具条样式*/
#toolbar {
  position: absolute;
  bottom: 14rem;
  right: 1rem;
  height: 4rem;
  width: 30px;
  max-width: 80%;
  z-index: 999;
}

#toolbar .menu-class {
  padding: 0;
  height: 30px;
  text-align: center;
  border-bottom: 1px solid #e8e8e8;
}

#toolbar .menu-class > a {
  line-height: 30px;
}

#toolbar .iconfont {
  font-size: 16px;
  margin: 0 auto;
}

/*  隐藏绘面工具条*/
::v-deep .leaflet-pm-toolbar {
  display: none;
}

/*  禁止点击事件*/
.disableClick {
  pointer-events: none;
}
</style>
