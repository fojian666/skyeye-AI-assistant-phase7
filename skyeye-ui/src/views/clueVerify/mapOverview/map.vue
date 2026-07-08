<template>
    <div class="gtp-container">
        <div id="mapContainer" style="height: 100%" @click="drawPointActive" @dblclick="measureActive"></div>

        <div class="toolbar" :style="targetDivStyle">
            <div @click="drawPoint" :class="{'active': activeToolBarIndex===2}"><span
                    class="icon iconfont icon-position"></span><span>查经纬度</span></div>
            <span style="color: #cccccc">|</span>
            <div @click="measureLength" :class="{'active': activeToolBarIndex===3}"><span
                    class="icon iconfont icon-icon-line-graph"></span><span>测距</span></div>
            <span style="color: #cccccc">|</span>
            <div @click="startDrawPolygon" :class="{'active': activeToolBarIndex===4}"><span
                    class="icon iconfont icon-duobianxing"></span><span>测面积</span></div>
            <span style="color: #cccccc">|</span>
            <div @click="clearDraw"><span class="icon iconfont icon-qingchu"></span><span>清除</span></div>
        </div>
        <div class="video"
             :style="{display: dialogVideoVisible ? 'block' : 'none'}"
             @mousedown="startDrag" v-show="dialogVideoVisible">
            <div class="video-title">
                <span>视频编号：3203456666</span>
                <el-tooltip class="item" effect="dark" content="关闭" placement="top">
                    <el-button icon="el-icon-close" style="border: none;background: none" @click="closeDetectdialog"></el-button>
                </el-tooltip>
            </div>
            <video
                    class="myVideo"
                    controls
            >
                <source src='/static/video/road.mp4' type="video/mp4">
                您的浏览器不支持视频标签。
            </video>
        </div>

    </div>
</template>

<script>

    import {TiledMapLayer, GetFeaturesBySQLParameters, FeatureService,} from "@supermap/iclient-leaflet";
    import {
        getMapInfoApi,
        verifyClueByTaskIDApi
    } from "@/api/commonApi";
    import 'leaflet.markercluster'; // 引入插件
    import 'leaflet.markercluster/dist/MarkerCluster.Default.css'
    import {
        drawPoint,
        measureDistance,
        measureArea,
        clearGraphical
    } from '@/utils/utils';

    export default {
        name: "MapComponent",
        props: {
            activeMarker: {
                type: Number,
                required: true
            },
            activeItem:{
                type:Object,
                required: true
            },
        },

        data() {
            return {
                targetDivPosition: {
                    x: 0 // 初始 X 轴位置
                },
                checkboxPanorama: false,
                activeToolBarIndex: 0,
                mapService: '',
                center: '',
                crs: L.CRS.EPSG4326,
                gridService: '',
                panoramaPoint: [],//全景点坐标
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
                dialogVideoVisible:false
            };
        },
        watch: {
            allClueList() {
                if (this.clusterLayer){
                    this.map.removeLayer(this.clusterLayer)
                    this.drawMarkers=[]
                }
                //点聚合
                this.clusterLayer = L.layerGroup()
                const defaultIconBlue = L.icon({
                    iconUrl: require('@/assets/images/marker-icon-blue.png'),
                    iconSize: [25, 40], // 图标大小
                    iconAnchor: [12.5, 40], // 图标锚点（中心点）
                    popupAnchor: [-3, -40] // 弹出窗偏移量
                })
                this.allClueList.forEach((item, index) => {
                    const marker = L.marker([item.latitude, item.longitude], {icon: defaultIconBlue})
                    marker.bindPopup(item.address)
                    marker.on('click', (e) => {
                        marker.openPopup()
                    })
                    this.clusterLayer.addLayer(marker)
                    this.drawMarkers.push({'clue_id': item.clue_id, 'marker': marker,"latitude":item.latitude,"longitude":item.longitude})

                })
                this.map.addLayer(this.clusterLayer)
                if (this.drawMarkers.length > 0){
                    this.map.flyTo([this.drawMarkers[0].latitude, this.drawMarkers[0].longitude], 12)
                }
            },
            activeMarker(newValue, oldValue) {
                this.dialogVideoVisible = true
                //根据选中的线索添加marker
                const defaultIconRed = L.icon({
                    iconUrl: require('@/assets/images/marker-icon-red.png'),
                    iconSize: [25, 40], // 图标大小
                    iconAnchor: [12.5, 40], // 图标锚点（中心点）
                    popupAnchor: [-3, -40] // 弹出窗偏移量
                })
                const defaultIconBlue = L.icon({
                    iconUrl: require('@/assets/images/marker-icon-blue.png'),
                    iconSize: [25, 40], // 图标大小
                    iconAnchor: [12.5, 40], // 图标锚点（中心点）
                    popupAnchor: [-3, -40] // 弹出窗偏移量
                })

                if (newValue) {
                    const newMarker_obj = this.drawMarkers.filter(item => item.clue_id === newValue)[0]
                    const newMarker = newMarker_obj.marker
                    newMarker.setIcon(defaultIconRed)
                    newMarker.setZIndexOffset(10) //覆盖其他标记
                    this.map.setView([newMarker_obj.latitude, newMarker_obj.longitude], 15)
                }
                if (oldValue) {
                    //还原样式
                    const oldMarker = this.drawMarkers.filter(item => item.clue_id === oldValue)[0].marker
                    oldMarker.setIcon(defaultIconBlue)
                    oldMarker.setZIndexOffset(1)
                }
                // this.clusterLayer.refreshClusters()
            },

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
                    this.activeToolBarIndex = 0
                }
            },
            measureActive() {
                //双击事件取消选中
                if (this.activeToolBarIndex > 2) {
                    this.activeToolBarIndex = 0
                }
            },
            // 画点，显示经纬度
            drawPoint() {
                this.map.off("mousedown");
                this.map.off("mousemove");
                this.map.off("dblclick");
                this.activeToolBarIndex = 2
                drawPoint(this.map);
            },
            //画线，测量距离
            measureLength() {
                this.map.off("mousedown");
                this.map.off("mousemove");
                this.map.off("dblclick");
                this.activeToolBarIndex = 3
                measureDistance(this.map);
            },
            // 画面，测量面积
            startDrawPolygon() {
                this.map.off("mousedown");
                this.map.off("mousemove");
                this.map.off("dblclick");
                this.activeToolBarIndex = 4
                measureArea(this.map);
            },
            clearDraw() {
                this.activeToolBarIndex = 0
                clearGraphical(this.map);
            },
            initMap() {
                //初始化地图
                if (process.env.NODE_ENV === "production"){
                    this.map = L.map('mapContainer',
                        {
                            crs: this.crs,
                            center: this.center,//中心坐标
                            zoom: 12,//缩放级别
                            zoomControl: false, //缩放组件
                            attributionControl: false, //去掉右下角logo
                            preferCanvas: true,
                        });
                    //加载全景点
                    const layer = new TiledMapLayer(this.mapService);
                    layer.addTo(this.map);
                    this.clusterLayer.addTo(this.map)
                }else{
                    this.map = L.map('mapContainer').setView(this.center, 14);
                    // 添加天地图瓦片图层
                    const tdtLayer = L.tileLayer('http://t0.tianditu.gov.cn/img_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=img&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&tk=d40cf3cbefc882d9a93de1dab6a5a48c').addTo(this.map);
                    this.clusterLayer.addTo(this.map)
                }

            },

            async getAllClue(taskid) {
                const para = {task_id: taskid}
                const res = await verifyClueByTaskIDApi(para)
                if (res.code !== 0) {
                    this.$message.error(res.msg)
                    return
                }else{
                    this.allClueList = res.data
                }
            },
            handelUpdateClues(taskid){
                this.getAllClue(taskid)
            },
            startDrag(event) {
                this.isDragging = true;
                this.startX = event.clientX - this.position.left;
                this.startY = event.clientY - this.position.top;
                document.addEventListener('mousemove', this.dragging);
                document.addEventListener('mouseup', this.endDrag);
            },
            dragging(event) {
                if (this.isDragging) {
                    const dx = event.clientX - this.startX;
                    const dy = event.clientY - this.startY;
                    this.position.left = dx;
                    this.position.top = dy;
                }
            },
            endDrag() {
                this.isDragging = false;
                document.removeEventListener('mousemove', this.dragging);
                document.removeEventListener('mouseup', this.endDrag);
            },
            closeDetectdialog(){
                this.dialogVideoVisible = false
            }
        },
        async created() {

        },
        async mounted() {
            const res = await getMapInfoApi();
            if (res.code === 0) {
                this.mapService = res.data.map_service;
                this.center = res.data.center;
                let taskid = this.$route.query.task_id;
                if (taskid){
                }else{
                    taskid = ''
                }
                await this.getAllClue(taskid)
                this.initMap();
            }

        },


    };
</script>

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
    color: #42b4f2;
  }

  .active {
    color: #42b4f2;
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

  .show{
    display: flex;
    flex-direction: column;
  }
  .gt-info{
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
    right:10px;
    top:100px;
  }
  .video-title{
    display: flex;
    text-align: center;
    border-bottom: 1px solid #fff;
    align-items: center;
    padding:4px;
  }
  .video-title span{
    text-align: left;
    width: 98%;

  }
  .myVideo{
    padding: 0 4px;
    width: 100%;
    height: calc(100% - 50px);
  }
</style>
