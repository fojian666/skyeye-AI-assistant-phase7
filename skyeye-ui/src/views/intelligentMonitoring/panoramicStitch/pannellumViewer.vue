<template>
    <div id="panoramaContainer" style="position: relative">
        <div class="pannellum-layer" v-if="afterLoadPannellum"></div>
        <div class="map-container" v-show="showMap">
            <div class="map-container-header">
                <div><i class="el-icon-map-location" style="margin-right: 6px"></i>地图展示</div>
                <div><i class="el-icon-arrow-left" @click="toggle_map"></i></div>
            </div>
            <div id="map" class="map-container-body"></div>
        </div>
        <div class="arrow-right" v-show="!showMap" title="展开地图"><i class="el-icon-arrow-right" @click="toggle_map"></i></div>
        <div class="gt-toolbar-right">
            <div class="gt-alarms-list" title="拖拽">
                <img src="@/assets/images/toggle.png" />
            </div>
            <div class="gt-alarms-list" title="检测列表" @click="fetchList">
                <img src="@/assets/images/list.png" />
            </div>
            <div class="gt-alarms-list" title="提交复核">
                <img src="@/assets/images/save.png" />
            </div>
            <div class="gt-alarms-list" @click="openDialog" title="添加目标">
                <img src="@/assets/images/add.png" />
            </div>
            <div class="gt-alarms-list" @click="dialogVisible = true" title="简介">
                <img src="@/assets/images/jj.png" />
            </div>
        </div>
        <el-dialog
            title="检测列表"
            :visible.sync="dialogTableVisible"
            center
            class="gt-od-list-data"
            :close-on-click-modal="false"
            :modal="false"
            :append-to-body="true">
            <el-table :data="listData">
                <el-table-column property="id" label="id" width="50"></el-table-column>
                <el-table-column property="label" label="标签" width="100"></el-table-column>
                <el-table-column property="operation" label="操作">
                    <template slot-scope="scope">
                        <el-button type="text" size="small" @click="handleView(scope.row.id)">查看</el-button>
                        <el-button type="text" size="small" @click="handleDelete(scope.row.id)">删除</el-button>
                    </template>
                </el-table-column>
            </el-table>
        </el-dialog>

        <el-dialog :title="currentTitle" :visible.sync="dialogVisible" :modal="false" class="transparent-dialog">
            <div>这是采用大疆无人机在龙潭街道拍摄的全景图</div>
            <div>{{ currentObj.task_name }}</div>
        </el-dialog>

        <el-dialog
            title="添加目标点"
            :visible.sync="labelVisible"
            :modal="false"
            class="label-dialog"
            :close-on-click-modal="false"
            @close="handleClose">
            <el-form class="form_class">
                <el-form-item label="点位像素x:" style="display: flex">
                    <el-input v-model="pixel_x"> </el-input>
                </el-form-item>
                <el-form-item label="点位像素y:" style="display: flex">
                    <el-input v-model="pixel_y"></el-input>
                </el-form-item>
                <el-form-item label="目标类型:" style="display: flex">
                    <el-select v-model="currentClass" placeholder="请选择">
                        <el-option v-for="item in classList" :key="item" :label="item" :value="item"> </el-option>
                    </el-select>
                </el-form-item>

                <div class="btn-uploading">
                    <el-button style="margin-right: 20px" type="primary" size="medium" @click="addOdLabel">添加 </el-button>
                    <el-button style="margin-left: 20px" size="medium" @click="handleClose">取消</el-button>
                </div>
            </el-form>
        </el-dialog>
    </div>
</template>

<script>
//import pannellum from 'pannellum';
// import '../../../js/pannellum'
// import '../../../js/libpannellum'
import screenfull from 'screenfull';
import { TiledMapLayer } from '@supermap/iclient-leaflet';
import {
    getShapeApi,
    postLabelDataApi,
    getTaskDataListApi,
    deleteAlarmsByIdApi,
    getAlarmsByIdApi,
    getAlarmsListApi,
    getMapInfoApi
} from '@/api/commonApi';

export default {
    name: 'pannellumViewer',
    //接收父组件传递的数据
    props: {
        currentObj: Object,
        taskList: {
            type: Array,
            required: true
        }
    },
    data() {
        return {
            // 图层显示
            afterLoadPannellum: false,
            yawDegree: 0,
            // 全景对象
            viewer: undefined,
            //是否全屏
            isScreenFull: false,
            currentScene: '',
            lastIndex: 1,
            dialogVisible: false,
            currentTitle: '全景图简介',
            labelVisible: false,
            editFlag: false,
            pixel_x: 0,
            pixel_y: 0,
            pitch: 0,
            yaw: 0,
            lastHighView: {
                id: 0,
                yaw: 0,
                pitch: 0,
                label: ''
            },
            currentClass: '',
            classList: [
                '大巴',
                '堆土',
                '脚手架',
                '翻土机',
                '翻斗车',
                '钢筋',
                '水泥地坪',
                '挖掘机',
                '堆砖',
                '火焰',
                '推土车',
                '彩钢瓦',
                '搅拌机',
                '物料提升机',
                '起重机',
                '小轿车',
                '围挡',
                '压路车',
                '打桩机',
                '在建砖房',
                '运输车',
                '树',
                '搅拌车',
                '烟雾',
                '防尘网',
                '板房棚房',
                '塔吊',
                '水泥管',
                '工程管',
                '工程车辆'
            ],
            currentIndex: 1,
            dialogTableVisible: false,
            listData: [],
            currentMarker: null,
            markers: [],
            marker: null,
            totalTaskList: [],
            baseUrl: process.env.VUE_APP_API_URL,
            mapService: '',
            center: '',
            redIcon: null,
            showMap: true,
            circleRadius: window.config.circleRadius
        };
    },
    beforeDestroy() {
        if (this.viewer) {
            this.viewer.destroy(); // 调用Pannellum的销毁方法，清理资源
        }
        //window.removeEventListener('resize', this.adjustPanoramaSize);
    },
    methods: {
        //初始化天地图
        initMap() {
            this.map = L.map('map').setView([this.currentObj.latitude, this.currentObj.longitude], 14);
            // 添加天地图瓦片图层
            const tdtLayer = L.tileLayer(
                'http://t0.tianditu.gov.cn/img_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=img&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&tk=d40cf3cbefc882d9a93de1dab6a5a48c'
            ).addTo(this.map);
        },
        toggle_map() {
            if (this.showMap) {
                this.showMap = false;
            } else {
                this.showMap = true;
            }
        },
        openDialog() {
            this.editFlag = true;
        },
        handleMouseDown(event) {
            if (this.editFlag) {
                var coords = this.viewer.mouseEventToCoords(event);
                this.drawMarker(coords);
                // 将 pitch 和 yaw 转换为 x 和 y 像素坐标
                var imageWidth = this.width; // 假设全景图宽度为 4000 像素
                var imageHeight = this.height; // 假设全景图高度为 2000 像素
                this.pixel_x = (((coords[1] * Math.PI) / 180 + Math.PI) / (2 * Math.PI)) * imageWidth;
                this.pixel_y = ((Math.PI / 2 - (coords[0] * Math.PI) / 180) / Math.PI) * imageHeight;
                this.labelVisible = true;
            }
        },
        handleClose() {
            this.viewer.removeHotSpot(this.currentIndex);
            this.editFlag = false;
            this.labelVisible = false;
        },
        removeAllHotspots() {
            // 获取所有热点
            this.listData.forEach((item) => {
                this.viewer.removeHotSpot(item.id);
            });
        },

        //在地图上添加点
        addMarker() {
            this.totalTaskList.forEach((task) => {
                const lat = task.latitude;
                const lon = task.longitude;
                const taskPath = task.task_path; // 假设任务数据中包含 task_path
                const panoramaUrl = `/panoramaUrl/static/layers/${taskPath}`; // 构造全景图 URL
                // 创建自定义图标
                const customIcon = L.icon({
                    iconUrl: '../../static/video_mark_model.png',
                    iconSize: [20, 30],
                    iconAnchor: [16, 32],
                    popupAnchor: [0, -32]
                });
                //换成红色图标
                this.redIcon = L.icon({
                    iconUrl: '../../static/marker-icon-red.png', // 替换为红色图标的路径
                    iconSize: [20, 30],
                    iconAnchor: [16, 32],
                    popupAnchor: [0, -32]
                });
                const marker = L.marker([lat, lon], { icon: customIcon }).addTo(this.map);
                // 初始不创建扇形，点击时再绘制
                const markerData = { marker, sector: null, lat, lon, customIcon, redIcon: this.redIcon };
                // 绘制圆形范围
                L.circle([lat, lon], {
                    color: 'red', // 圆圈边框颜色
                    fillColor: 'red', // 圆圈填充颜色
                    fillOpacity: 0, // 圆圈透明度
                    radius: this.circleRadius, // 半径（以米为单位）
                    weight: 1
                }).addTo(this.map);
                this.markers.push(markerData);
                // 检查是否初始化时要显示这个任务的全景图和扇形
                if (this.currentObj.task_id === task.task_id) {
                    // 重置所有标记为默认状态
                    this.markers.forEach((mData) => {
                        if (mData.sector) {
                            this.map.removeLayer(mData.sector); // 移除扇形
                        }
                        mData.marker.setIcon(mData.customIcon); // 重置图标为默认
                    });
                    // 绘制当前标记的扇形
                    this.drawSector(lat, lon, markerData, marker);
                }

                marker.on('click', () => {
                    // 重置所有标记为默认状态
                    this.markers.forEach((mData) => {
                        if (mData.sector) {
                            this.map.removeLayer(mData.sector); // 移除扇形
                        }
                        mData.marker.setIcon(mData.customIcon); // 重置图标为默认
                    });
                    this.removeAllHotspots();
                    this.yawDegree = task.yaw_degree;
                    // 显示全景图
                    this.showPanorama(panoramaUrl, task.yaw_degree);
                    this.fetchData(task.task_id);
                    this.drawSector(lat, lon, markerData, marker);
                });
            });
        },
        drawSector(lat, lon, markerData, marker) {
            // 绘制当前标记的扇形
            const radius = this.circleRadius;
            const startAngle = -30;
            const endAngle = 30;
            const numberOfPoints = 50;

            const latlngs = this.getSectorCoordinates(lat, lon, radius, startAngle, endAngle, numberOfPoints);
            latlngs.push([lat, lon]);

            const sector = L.polygon(latlngs, {
                color: 'blue',
                fillColor: '#30f',
                fillOpacity: 0.2
            }); //.addTo(this.map);

            // 设置当前点击的标记图标为红色
            marker.setIcon(this.redIcon);
            this.currentMarker = { marker, sector, lat, lon };
            // 更新当前标记的扇形数据
            markerData.sector = sector;
        },
        //绘制扇形
        getSectorCoordinates(lat, lon, radius, startAngle, endAngle, numberOfPoints) {
            const latlngs = [];
            const angleStep = (endAngle - startAngle) / numberOfPoints;
            for (let i = 0; i <= numberOfPoints; i++) {
                const angle = ((startAngle + i * angleStep) * Math.PI) / 180; // 转换为弧度
                const pointLat = lat + (radius / 111320) * Math.cos(angle); // 111320是大约的米/纬度度转换系数
                const pointLon = lon + (radius / (111320 * Math.cos((lat * Math.PI) / 180))) * Math.sin(angle);
                latlngs.push([pointLat, pointLon]);
            }
            return latlngs;
        },
        //更新扇形
        updateSector(yaw) {
            if (!this.currentMarker) return;
            const { marker, sector, lat, lon } = this.currentMarker;
            const radius = this.circleRadius;
            const startAngle = yaw + this.yawDegree - 30;
            const endAngle = yaw + this.yawDegree + 30;
            const numberOfPoints = 50;
            // 更新扇形坐标
            let latlngs = this.getSectorCoordinates(lat, lon, radius, startAngle, endAngle, numberOfPoints);
            latlngs.push([lat, lon]);
            // 更新地图上的扇形
            sector.setLatLngs(latlngs);
            sector.addTo(this.map);
        },
        //保存目标点
        async addOdLabel() {
            const params = {
                pixel_x: this.pixel_x,
                pixel_y: this.pixel_y,
                task_id: this.currentObj.task_id,
                class: this.currentClass
            };
            const res = await postLabelDataApi(params);
            if (res.code === 0) {
                this.$message.success('添加成功！');
                this.lastIndex = this.currentIndex;
                this.viewer.removeHotSpot(this.currentIndex);
                this.viewer.addHotSpot({
                    id: this.currentIndex,
                    pitch: this.pitch,
                    yaw: this.yaw,
                    text: this.currentClass,
                    type: 'info',
                    cssClass: 'custom-hotspot'
                });
                this.currentIndex = this.lastIndex + 1;
            } else {
                this.$message.error('添加失败，请查看后台日志！');
            }
            this.editFlag = false;
            this.labelVisible = false;
            this.pixel_y = 0;
            this.pixel_y = 0;
        },
        handleMouseUp(event) {
            // console.log('鼠标抬起时的处理逻辑')
            // 鼠标抬起时的处理逻辑
        },
        handleMouseMove(event) {
            // console.log('鼠标移动时的处理逻辑')
            // 鼠标移动时的处理逻辑
        },
        drawMarker(coords) {
            this.pitch = coords[0];
            this.yaw = coords[1];
            this.viewer.addHotSpot({
                id: this.currentIndex,
                pitch: this.pitch,
                yaw: this.yaw,
                text: this.currentClass,
                type: 'info',
                cssClass: 'custom-hotspot'
            });
        },
        /*
         * 获取全景任务信息
         * @param {task_id} task_id - 任务的ID
         */
        async fetchData(task_id) {
            if (task_id) {
                const res = await getShapeApi(task_id);
                if (res.code === 0) {
                    this.width = res.data.width;
                    this.height = res.data.height;
                }
                const listres = await getAlarmsListApi(task_id);
                if (listres.code === 0) {
                    this.listData = listres.data;
                    this.listData.forEach((item) => {
                        // 将像素坐标转换为弧度
                        var yawRad = (item.center_x / this.width) * 2 * Math.PI - Math.PI;
                        var pitchRad = Math.PI / 2 - (item.center_y / this.height) * Math.PI;
                        // 将弧度转换为角度
                        var yaw = (yawRad * 180) / Math.PI;
                        var pitch = (pitchRad * 180) / Math.PI;
                        this.viewer.addHotSpot({
                            id: item.id,
                            pitch: pitch,
                            yaw: yaw,
                            text: item.id + ' ' + item.label,
                            type: 'info',
                            cssClass: 'custom-hotspot'
                        });
                    });
                }
            }
        },
        async fetchList() {
            this.dialogTableVisible = true;
        },
        destroyExistingWebGLContext() {
            const canvases = document.querySelectorAll('canvas');
            canvases.forEach((canvas) => {
                const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
                if (gl && gl.getExtension('WEBGL_lose_context')) {
                    gl.getExtension('WEBGL_lose_context').loseContext();
                }
            });
        },
        async handleView(id) {
            const res = await getAlarmsByIdApi(id);
            if (res.code === 0) {
                const result = res.data;
                var yawRad = (result.center_x / this.width) * 2 * Math.PI - Math.PI;
                var pitchRad = Math.PI / 2 - (result.center_y / this.height) * Math.PI;
                // 将弧度转换为角度
                var yaw = (yawRad * 180) / Math.PI;
                var pitch = (pitchRad * 180) / Math.PI;
                this.viewer.setHfov(20);
                const customIcon = L.icon({
                    iconUrl: require('@/assets/images/marker-icon-violet.png'),
                    iconSize: [20, 30],
                    iconAnchor: [16, 32],
                    popupAnchor: [0, -32]
                });
                if (this.marker) {
                    this.map.removeLayer(this.marker);
                }

                this.marker = L.marker([result.latitude, result.longitude], { icon: customIcon }).addTo(this.map);
                if (this.lastHighView.id !== 0) {
                    this.viewer.lookAt(pitch, yaw);

                    this.viewer.removeHotSpot(id);
                    this.viewer.removeHotSpot(this.lastHighView.id);
                    this.viewer.addHotSpot({
                        id: id,
                        pitch: pitch,
                        yaw: yaw,
                        text: result.id + ' ' + result.label,
                        type: 'info',
                        cssClass: 'custom-hotspot2'
                    });
                    this.viewer.addHotSpot({
                        id: this.lastHighView.id,
                        pitch: this.lastHighView.pitch,
                        yaw: this.lastHighView.yaw,
                        text: this.lastHighView.id + ' ' + this.lastHighView.label,
                        type: 'info',
                        cssClass: 'custom-hotspot'
                    });
                } else {
                    this.viewer.lookAt(pitch, yaw);
                    this.viewer.removeHotSpot(id);
                    this.viewer.addHotSpot({
                        id: id,
                        pitch: pitch,
                        yaw: yaw,
                        text: result.id + ' ' + result.label,
                        type: 'info',
                        cssClass: 'custom-hotspot2'
                    });
                }
                this.lastHighView = {
                    id: id,
                    pitch: pitch,
                    yaw: yaw,
                    label: result.label
                };
            }
        },
        async handleDelete(id) {
            const params = {
                id: id
            };
            this.currentIndex = id;
            this.$confirm('此操作将永久删除该目标物, 是否继续?', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            })
                .then(async () => {
                    const res = await deleteAlarmsByIdApi(params);
                    if (res.code === 0) {
                        this.$message.success('图斑删除成功！');
                        this.viewer.removeHotSpot(this.currentIndex);
                        this.listData = this.listData.filter((item) => item.id !== id);
                    } else {
                        this.$message.error(res.msg);
                    }
                })
                .catch(() => {
                    this.$message({
                        type: 'info',
                        message: '已取消删除'
                    });
                });
        },
        //根据全景图路径切换全景图
        showPanorama(panoramaUrl, yaw_degree) {
            this.destroyExistingWebGLContext();
            this.viewer = pannellum.viewer('panoramaContainer', {
                type: 'multires',
                sceneFadeDuration: 1000,
                autoLoad: true,
                hfov: 100, // 初始的水平视场角
                minHfov: 10, // 最小水平视场角
                maxHfov: 120, // 最大水平视场角
                yaw: -yaw_degree,
                // "pitch":0,
                //"northOffset": 0,
                compass: true,
                multiRes: {
                    basePath: panoramaUrl,
                    path: '/%l/%s%y_%x',
                    fallbackPath: '/fallback/%s',
                    extension: 'png',
                    tileResolution: 512,
                    maxLevel: 5,
                    cubeResolution: 4576
                },
                autoRotate: -10
                // 其他全景图配置...
            });
            //全程监听yaw的值
            // this.viewer.on('animatefinished', (event) => {
            //     this.updateSector(event.yaw)
            // })
            //全程监听yaw的值
            this.viewer.on('rendercanvas', (event) => {
                const yaw = this.viewer.getYaw();
                const pitch = this.viewer.getPitch();
                // if(parseInt(event.yaw)-parseInt(this.yawDegree)!==0){
                this.updateSector(yaw);
            });
        },
        async fetchAllTask(project_id) {
            const params = {
                project_id: project_id,
                query: '',
                page: 1,
                limit: 100
            };
            const res = await getTaskDataListApi(params);
            if (res.code === 0) {
                this.totalTaskList = res.data;
                this.addMarker();
            }
        }
    },
    async mounted() {
        // 全景图对象
        if (this.currentObj.task_id) {
            this.yawDegree = this.currentObj.yaw_degree;
            this.viewer = pannellum.viewer('panoramaContainer', {
                default: {
                    type: 'multires',
                    sceneFadeDuration: 1000,
                    autoLoad: true,
                    hfov: 100, // 初始的水平视场角
                    minHfov: 10, // 最小水平视场角
                    yaw: -this.yawDegree,
                    // "pitch":0,
                    maxHfov: 120, // 最大水平视场角
                    multiRes: {
                        basePath: '/panoramaUrl/static/layers/' + this.currentObj.task_path,
                        path: '/%l/%s%y_%x',
                        fallbackPath: '/fallback/%s',
                        extension: 'png',
                        tileResolution: 512,
                        maxLevel: 5,
                        cubeResolution: 4576
                    },
                    autoRotate: -10
                },
                // 其他全景图配置...
                scenes: {
                    first: {
                        title: 'scene1',
                        type: 'multires',
                        hfov: 110,
                        pitch: -3,
                        yaw: 117,
                        multiRes: {
                            basePath: '/panoramaUrl/static/layers/' + this.currentObj.task_path,
                            path: '/%l/%s%y_%x',
                            fallbackPath: '/fallback/%s',
                            extension: 'png',
                            tileResolution: 512,
                            maxLevel: 5,
                            cubeResolution: 4576
                        },
                        hotSpots: [
                            {
                                pitch: -3.1,
                                yaw: -99,
                                type: 'scene',
                                sceneId: '3'
                            }
                        ]
                    }
                }
            });

            // 设置初始的正北方向
            this.viewer.on('mousedown', this.handleMouseDown);
            // 场景加载完成时添加图层选择节点
            this.viewer.on('load', () => {
                this.afterLoadPannellum = true;
            });
            //全程监听yaw的值
            // this.viewer.on('animatefinished', (event) => {
            //     this.updateSector(event.yaw)
            // })
            //全程监听yaw的值
            this.viewer.on('rendercanvas', (event) => {
                const yaw = this.viewer.getYaw();
                const pitch = this.viewer.getPitch();
                // if(parseInt(event.yaw)-parseInt(this.yawDegree)!==0){
                this.updateSector(yaw);
            });
        }
        // 监听窗口大小改变，screenfull.isFullscreen的值为是否全屏，若是则true，反之false
        window.onresize = () => {
            this.isScreenFull = screenfull.isFullscreen;
        };
        const res = await getMapInfoApi();
        if (res.code === 0) {
            this.mapService = res.data.map_service;
            this.center = res.data.center;
            this.initMap();
            this.fetchData(this.currentObj.task_id);
            this.fetchAllTask(this.currentObj.project_id);
        }
    },
    computed: {},
    watch: {
        // 使用watch来观察parentValue的变化
        currentObj: {
            handler() {
                //this.fetchData(this.currentObj.task_id);
            },
            deep: true // 开启深度监听
        }
    }
};
</script>

<style scoped lang="scss">
@import '@/css/pannellum.css';

::v-deep .transparent-dialog .el-dialog__headerbtn .el-icon-close:hover {
    background-color: transparent;
}

::v-deep .transparent-dialog .el-dialog {
    background-color: rgba(0, 0, 0, 0.6); /* 半透明背景 */
    box-shadow: none; /* 可选，移除阴影 */
    z-index: 999;
    color: #fff;
}

::v-deep .el-dialog {
    background-color: rgba(0, 0, 0, 0.4); /* 半透明背景 */
    box-shadow: none; /* 可选，移除阴影 */
    z-index: 999;
    color: #fff;
    position: absolute;
    right: 50px;
    width: 300px;
}

::v-deep .el-dialog__body {
    height: 500px;
    overflow-y: auto;
}

::v-deep .el-table,
::v-deep.el-table tr,
::v-deep .el-table th,
::v-deep.el-table th.el-table__cell {
    background-color: rgba(0, 0, 0, 0); /* 半透明背景 */
    box-shadow: none; /* 可选，移除阴影 */
    z-index: 999;
    color: #fff;
}

::v-deep .el-table__body tr:hover > td {
    background-color: rgba(0, 0, 0, 0.6) !important;
}

::v-deep .el-dialog__header,
::v-deep .el-dialog__header {
    text-align: center;
    font-weight: 700;
    border-bottom: 1px solid #fff;
}

::v-deep .el-dialog__title,
::v-deep .el-dialog__title {
    color: #fff;
    font-size: 16px;
}

::v-deep .gt-od-list-data .el-dialog__body {
    padding: 10px; /* 根据需要调整内边距 */
    color: #fff;
}

::v-deep .label-dialog .el-dialog {
    position: absolute;
    bottom: 4%;
    width: 400px;
    left: 50%;
    margin-left: -200px;
    background-color: rgba(0, 0, 0, 0.6); /* 半透明背景 */
    box-shadow: none; /* 可选，移除阴影 */
    z-index: 999;
    color: #fff;
}

::v-deep .gt-toolbar-right {
    position: absolute;
    right: 10px;
    top: 340px;
    width: 40px;
    z-index: 99999;
    background-color: rgba(0, 0, 0, 0.5);
    border-radius: 10px;
    margin-bottom: -10px;
}

::v-deep .gt-toolbar-right div {
    width: 40px;
    height: 40px;
    cursor: pointer;
    text-align: center;
    display: flex;
    justify-content: center;
    align-items: center;
}

::v-deep .gt-toolbar-right .gt-alarms-list img {
    width: 24px;
    height: 24px;
}

::v-deep .transparent-dialog .el-dialog__header,
.label-dialog .el-dialog__header {
    text-align: center;
    font-weight: 700;
    border-bottom: 1px solid #fff;
}

::v-deep .transparent-dialog .el-dialog__title,
.label-dialog .el-dialog__title {
    color: #fff;
    font-size: 16px;
}

::v-deep .transparent-dialog .el-dialog__body {
    padding: 10px; /* 根据需要调整内边距 */
    color: #fff;
}

::v-deep .label-dialog .el-form-item__label {
    color: #fff;
    width: 80px;
}

::v-deep .pannellum-layer {
    z-index: 9999;
    position: fixed;
    right: 3%;
    top: 3%;
}

::v-deep .el-radio .el-radio__input .el-radio__inner {
    border-radius: 2px;
}

::v-deep .custom-hotspot {
    width: 25px;
    height: 40px;
    background-image: url('@/assets/images/marker-icon-blue.png');
    background-size: 100% 100%;
    position: absolute;
    transform: translate(-50%, -50%);
    z-index: 999;
}

::v-deep .custom-hotspot2 {
    width: 25px;
    height: 40px;
    background-image: url('@/assets/images/marker-icon-red.png');
    background-size: 100% 100%;
    position: absolute;
    transform: translate(-50%, -50%);
    z-index: 999;
}

::v-deep .el-radio .el-radio__input.is-checked .el-radio__inner::after {
    box-sizing: content-box;
    content: '';
    transition: transform 0.15s ease-in 0.05s;
    transform-origin: center;
    transform: rotate(-45deg) scaleY(1);
    width: 6px;
    height: 3px;
    border: 2px solid white;
    border-top: transparent;
    border-right: transparent;
    text-align: center;
    display: block;
    position: absolute;
    top: 18%;
    left: 18%;
    vertical-align: middle;
    border-radius: 0;
    background: none;
}

::v-deep .gt-img-desc {
    width: 100%;
    text-overflow: clip;
    overflow: hidden;
    height: 20px;
    line-height: 20px;
    white-space: nowrap;
    text-align: center;
    font-size: 10px;
    color: #fff;
    text-shadow: 3px 3px 3px #000;
}

::v-deep div.pnlm-tooltip span {
    visibility: visible;
    width: 100px;
}

::v-deep .map-container {
    position: absolute;
    bottom: 0; /* 距离底部10px */
    left: 0; /* 距离左侧10px */
    width: 400px; /* 设定宽度 */
    height: 300px; /* 设定高度 */
    z-index: 9999999;
    border: 1px solid #909090;
    background-color: #fff;
}

::v-deep .leaflet-control-attribution {
    display: none !important;
}
.map-container-header {
    height: 32px;
    line-height: 32px;
    padding: 0 6px;
    color: #666;
    font-size: 16px;
    display: flex;
}
.map-container-header div:first-child {
    width: 96%;
}
.map-container-header div:last-child {
    flex: 1;
}
.map-container-body {
    width: 100%;
    height: 268px;
}
.map-container-header .el-icon-arrow-left {
    cursor: pointer;
}
.arrow-right {
    position: absolute;
    bottom: 100px;
    left: 4px;
    width: 26px;
    height: 26px;
    z-index: 9999;
    border: 1px solid #999;
    background-color: #fff;
    border-radius: 3px;
}
.arrow-right i {
    width: 26px;
    height: 26px;
    font-size: 14px;
    color: black;
    font-weight: bold;
    text-align: center;
    display: flex;
    justify-content: center;
    align-items: center;
}
</style>
