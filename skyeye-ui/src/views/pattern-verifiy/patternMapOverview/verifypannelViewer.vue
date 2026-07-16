<template>
    <div style="height: 100%">
        <div
            id="panoramaContainer"
            style="position: relative"
            :style="{ height: isThumbnailCollapsed ? '100%' : '80%' }"
            @mousemove="mouseMoveFunction"
            @mouseleave="MouseLeaveFunction">
            <div class="pannellum-layer" v-if="afterLoadPannellum"></div>
            <canvas id="overlay" ref="canvas"></canvas>
            <div class="show-yaw">
                <div class="gongju_left">{{ formattedShotTime }}</div>
            </div>
            <div class="gt-toolbar-right">
                <div class="gt-alarms-list" title="返回" @click="goBack">
                    <img src="@/assets/images/back.png" />
                </div>
                <div v-if="isAutoRotating" class="gt-alarms-list" title="暂停自动播放" @click="autoPlay">
                    <img src="@/assets/images/stop.png" />
                </div>
                <div v-else class="gt-alarms-list" title="自动播放" @click="autoPlay">
                    <img src="@/assets/images/play.png" />
                </div>
                <div class="gt-alarms-list" @click="handleResetViewYaw" title="一键归位">
                    <img src="@/assets/images/guiwei.png" />
                </div>
            </div>
            <div class="toolbar">
                <div @click="handleMeasure('measureDistance')" :class="{ baractive: activeToolBarType === 'measureDistance' }">
                    <span class="icon iconfont icon-icon-line-graph icon-toolbar"></span><span>测距</span>
                </div>
                <span style="color: #cccccc">|</span>
                <div @click="handleMeasure('measureArea')" :class="{ baractive: activeToolBarType === 'measureArea' }">
                    <span class="icon iconfont icon-duobianxing icon-toolbar"></span><span>测面积</span>
                </div>
                <span style="color: #cccccc">|</span>
                <div @click="handleClear"><span class="icon iconfont icon-qingchu icon-toolbar"></span><span>清除</span></div>
            </div>
            <div class="select-gd">
                <el-collapse>
                    <el-collapse-item title="业务图层" name="allLayers">
                        <div v-for="(item, index) in allLayers" :key="item.id" class="gd-item">
                            <el-checkbox v-model="item.check">{{ item.name }}</el-checkbox>
                        </div>
                    </el-collapse-item>
                </el-collapse>
            </div>
        </div>
        <div class="thumbnail-footer" :class="{ collapsed: isThumbnailCollapsed }">
            <div class="thumbnail-content" v-if="!isThumbnailCollapsed">
                <div class="rfoot">
                    <el-button @click="prevImages" circle icon="el-icon-arrow-left" class="rleftbtn"></el-button>
                    <div class="thumbnail-container">
                        <div class="dimg" v-for="(image, index) in taskList" :key="index" @click="handleClickDiv(image)">
                            <img :src="url" :class="{ active: currentTask.batchName === image.batchName }" />
                            <span>{{ image.batchName }}</span>
                        </div>
                    </div>
                    <el-button @click="nextImages" class="rrightbtn" circle icon="el-icon-arrow-right"></el-button>
                </div>
            </div>
        </div>
        <div @click="toggleThumbnail" class="toggle-button" :class="{ collapsed: isThumbnailCollapsed }">
            <i :class="isThumbnailCollapsed ? 'el-icon-arrow-up' : 'el-icon-arrow-down'"></i>
        </div>
    </div>
</template>

<script>
import screenfull from 'screenfull';
import { getPanoramaImageApi, calculatePanoramaApi, getBufferLayerApi, getPointBufferLayerApi } from '@/api/commonApi';
import { calculateTotalArea, calculateTotalDistance, imageToLatLon } from '@/utils/utils';
import { isPointInView, sphericalToScreen, updateZoomButtonsState } from '@/utils/panoramaTools';

export default {
    name: 'verifypannelViewer',
    //接收父组件传递的数据
    props: {
        pointId: String,
        currentPointObj: Object,
        currentAzimuth: Number,
        polygonItem: Object
    },
    data() {
        return {
            url: require('@/assets/images/test.png'),
            // 图层显示
            afterLoadPannellum: false,
            yawDegree: 0,
            // 全景对象
            viewer: null,
            currentHfov: 0,
            //是否全屏
            isScreenFull: false,
            pixel_x: 0,
            pixel_y: 0,
            pitch: 0,
            yaw: 0,
            currentYaw: 0,
            currentPitch: 0,
            imageName: '',
            pointName: '',
            currentTask: {},
            isAutoRotating: false,
            ctx: null,
            canvas: null, //全景图画布
            showMap: false,
            taskList: [],
            relativeYaw: 0,
            hotSpotId: -1,
            polygons: null,
            circleRadius: window.config.circleRadius,
            activeToolBarType: '',
            measureDistancePoints: [],
            measureAreaPoints: [],
            isMeasureDistance: false,
            isMeasureArea: false,
            minHfov: 10,
            maxHfov: 120,
            allLayers: [],
            isThumbnailCollapsed: false,
            currentIndex: null //当前索引
        };
    },
    beforeDestroy() {
        if (this.viewer) {
            this.viewer.destroy(); // 调用Pannellum的销毁方法，清理资源
        }
    },
    methods: {
        goBack() {
            this.$router.push('/pattern-verifiy/task_management');
        },
        //监听鼠标移入
        mouseMoveFunction(event) {
            if (this.viewer) {
                var coords = this.viewer.mouseEventToCoords(event);
                const lat_lon = imageToLatLon(
                    this.currentTask.latitude,
                    this.currentTask.longitude,
                    this.currentTask.height,
                    coords[1],
                    coords[0],
                    this.currentTask.yawDegree
                );
                var customIcon = L.icon({
                    iconUrl: '../../static/guangbiao.png',
                    iconSize: [32, 32] // 图标的尺寸
                    // 可选的其他图标样式选项
                });
                const r = this.isPointInBuffer(coords[1], coords[0]);
                if (r) {
                    this.currentLocationMarker = L.marker(lat_lon, {
                        icon: customIcon,
                        className: 'custom-cursor'
                    });
                } else {
                    // 创建一个完全透明的自定义图标
                    const emptyIcon = L.divIcon({
                        className: 'empty-marker',
                        html: '', // 空内容
                        iconSize: [0, 0] // 零尺寸
                    });

                    this.currentLocationMarker = L.marker(lat_lon, {
                        icon: emptyIcon,
                        interactive: true // 保持可交互性
                    });
                }
                this.$emit('panorama-mousemove', { currentLocationMarker: this.currentLocationMarker });
            }
        },
        //鼠标离开全景图事件
        MouseLeaveFunction(event) {
            // 创建一个完全透明的自定义图标
            const emptyIcon = L.divIcon({
                className: 'empty-marker',
                html: '', // 空内容
                iconSize: [0, 0] // 零尺寸
            });
            this.currentLocationMarker = L.marker([0, 0], {
                icon: emptyIcon,
                interactive: true // 保持可交互性
            });
            this.$emit('panorama-mousemove', { currentLocationMarker: this.currentLocationMarker });
        },
        isPointInBuffer(targetYaw, targetPitch) {
            // 将目标yaw/pitch转换为屏幕坐标
            const targetPoint = sphericalToScreen(this.viewer, targetPitch, targetYaw, this.canvas);

            // 使用Canvas的isPointInPath方法判断点是否在路径内
            this.ctx.beginPath();

            // 重新构建缓冲区路径
            const bufferPoints = [];
            this.bufferPitch = Math.atan(112 / (this.circleRadius * Math.cos((Math.abs(0) * Math.PI) / 180))) * (180 / Math.PI);

            for (let i = -90; i <= 90; i++) {
                const point = sphericalToScreen(this.viewer, -this.bufferPitch, this.currentYaw + i, this.canvas);
                bufferPoints.push(point);
            }

            this.ctx.moveTo(bufferPoints[0][0], bufferPoints[0][1]);
            for (let i = 1; i < bufferPoints.length; i++) {
                this.ctx.lineTo(bufferPoints[i][0], bufferPoints[i][1]);
            }

            // 闭合路径以确保isPointInPath正确工作
            this.ctx.closePath();

            // 判断目标点是否在路径内
            return this.ctx.isPointInPath(targetPoint[0], targetPoint[1]);
        },
        prevImages() {
            // const container = this.$el.querySelector('.thumbnail-container');
            // container.scrollBy({
            //     left: -100, // 调整此值以匹配你的需求
            //     behavior: 'smooth'
            // });
            if (this.currentIndex > 0) {
                this.currentIndex--;
                this.handleClickDiv(this.taskList[this.currentIndex]);
            }
        },
        nextImages() {
            // const container = this.$el.querySelector('.thumbnail-container');
            // container.scrollBy({
            //     left: 100, // 调整此值以匹配你的需求
            //     behavior: 'smooth'
            // });
            if (this.currentIndex < this.taskList.length - 1) {
                this.currentIndex++;
                this.handleClickDiv(this.taskList[this.currentIndex]);
            }
        },
        async handleClickDiv(image) {
            this.isAutoRotating = false;
            // 根据需要处理点击事件
            this.currentTask = image;
            this.yawDegree = image.yawDegree;
            this.imageName = image.imageName;
            // 显示全景图
            this.showPanorama();
        },

        autoPlay() {
            this.currentHfov = this.viewer.getHfov(); // 当前水平视场角
            if (this.isAutoRotating) {
                // 如果已经在自动旋转，禁用自动旋转
                this.viewer.stopAutoRotate();
                this.isAutoRotating = false;
            } else {
                // 否则，启用自动旋转
                this.viewer.setHfov(this.currentHfov);
                this.viewer.startAutoRotate(-5, this.currentPitch);
                this.isAutoRotating = true;
            }
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
        drawClue(points, name, color) {
            const screenPoints = [];
            const isInViews = [];
            points.forEach((coord) => {
                //将全景图坐标pitch，yaw转为屏幕坐标
                const point = sphericalToScreen(this.viewer, coord[0], coord[1], this.canvas);
                screenPoints.push(point);
                const isInView = isPointInView(this.viewer, coord[0], coord[1], this.canvas);
                isInViews.push(isInView);
            });
            if (isInViews.indexOf(true) === -1) return; //所有点均不在视角范围内，不绘制多边形
            if (screenPoints.length === 0) return;

            if (screenPoints.length === 0) return;
            this.ctx.beginPath();
            this.ctx.strokeStyle = 'red';
            this.ctx.lineWidth = 3;

            // 绘制多边形
            this.ctx.fillStyle = 'transparent';
            this.ctx.moveTo(screenPoints[0][0], screenPoints[0][1]);
            for (let i = 1; i < screenPoints.length; i++) {
                this.ctx.lineTo(screenPoints[i][0], screenPoints[i][1]);
            }
            this.ctx.closePath(); // 闭合路径以形成多边形
            this.ctx.stroke(); // 描边
            this.ctx.fill(); //填充多边形
            this.ctx.font = '16px Arial';
            this.ctx.fillStyle = 'transparent';
            const center = this.getPolygonCenterXY(screenPoints);
            this.ctx.fillText(name, center[0] - 60, center[1]);
        },
        //获取多边形的中心坐标
        getPolygonCenterXY(polygon) {
            let sumX = 0;
            let sumY = 0;
            polygon.forEach((point) => {
                sumX += point[0];
                sumY += point[1];
            });
            return [sumX / polygon.length, sumY / polygon.length];
        },
        //根据全景图路径切换全景图
        async showPanorama() {
            if (this.hotSpotId !== -1) {
                this.viewer.removeHotSpot(this.hotSpotId);
            }
            this.relativeYaw = this.cacuRelativeYaw(this.currentAzimuth);
            this.destroyExistingWebGLContext();
            await this.handleViewLoad();
            this.getPartern();
        },
        async getPointPanoramaImage() {
            const data = {
                pointId: this.pointId
            };
            const res = await getPanoramaImageApi(data);
            if (res.code === 0) {
                this.taskList = res.data;
                if (this.taskList.length > 0) {
                    this.currentTask = this.taskList[0];
                }
                // 全景图对象
                if (this.currentTask.imageId) {
                    this.imageName = this.currentTask.imageName;
                    this.pointName = this.currentPointObj.pointName;
                    this.relativeYaw = this.cacuRelativeYaw(this.currentAzimuth);
                    this.yawDegree = this.currentTask.yawDegree;
                    //加载全景图
                    await this.handleViewLoad();
                    this.getPartern();
                }
            } else {
                this.$message.error(res.msg);
            }
        },

        //绘制700m缓冲区
        drawBuffer() {
            this.ctx.beginPath();
            this.ctx.strokeStyle = 'yellow';
            this.ctx.lineWidth = 3;
            const bufferPoints = [];
            this.bufferPitch = Math.atan(112 / (this.circleRadius * Math.cos((Math.abs(0) * Math.PI) / 180))) * (180 / Math.PI);
            for (let i = -90; i <= 90; i++) {
                const point = sphericalToScreen(this.viewer, -this.bufferPitch, this.currentYaw + i, this.canvas);
                bufferPoints.push(point);
            }
            this.ctx.moveTo(bufferPoints[0][0], bufferPoints[0][1]);
            for (let i = 1; i < bufferPoints.length; i++) {
                this.ctx.lineTo(bufferPoints[i][0], bufferPoints[i][1]);
            }
            this.ctx.stroke();
        },
        //绘制所有多边形
        drawPolygons() {
            if (this.ctx) {
                this.ctx.clearRect(0, 0, this.ctx.canvas.width, this.ctx.canvas.height);
                this.drawBuffer();
            }
        },
        cacuRelativeYaw(Azimuth) {
            var yawDegree = this.currentTask.yawDegree || 0; // 假设point1有yawDegree属性
            var relativeYaw = (Azimuth - yawDegree + 360) % 360; // 确保yaw角度在0-
            if (relativeYaw > 360) {
                relativeYaw = relativeYaw - 360;
            }
            return relativeYaw;
        },
        //获取图斑
        async getPartern() {
            if (this.polygonItem.id) {
                const para = {
                    polygonDataId: this.polygonItem.id,
                    imageId: this.currentTask.imageId
                };
                const res = await calculatePanoramaApi(para);
                if (res.code === 0) {
                    const hotSpot = {
                        id: this.polygonItem.id,
                        pitch: res.data.pitch,
                        yaw: res.data.yaw,
                        type: 'info',
                        cssClass: 'custom-hotspot'
                    };
                    this.viewer.addHotSpot(hotSpot);
                    this.polygons = res.data.points.slice();
                    // this.drawClue(this.polygons,  this.polygonItem.id, 'red');
                    this.hotSpotId = this.polygonItem.id;
                } else {
                    this.$message.error(res.msg);
                }
            }
        },
        handleResetViewYaw() {
            this.viewer.setYaw(this.relativeYaw);
            this.viewer.setPitch(0);
            this.viewer.setHfov(100);
            this.$emit('resetMap');
        },
        handleMouseDown(event) {
            if (this.isAutoRotating) {
                this.viewer.stopAutoRotate();
                this.isAutoRotating = false;
            }
            var coords = this.viewer.mouseEventToCoords(event);
            if (this.isMeasureDistance) {
                if (event.button === 2) {
                    //表示右击结束面绘制
                    this.isMeasureDistance = false;
                    return;
                }
                this.measureDistancePoints.push(coords);
                this.drawMeasureLine();
            } else if (this.isMeasureArea) {
                if (event.button === 2) {
                    //表示右击结束面绘制
                    this.isMeasureArea = false;
                    return;
                }
                this.measureAreaPoints.push(coords);
                this.drawMeasureArea();
            }
        },
        async handleViewLoad() {
            this.viewer = pannellum.viewer('panoramaContainer', {
                type: 'multires',
                sceneFadeDuration: 1000,
                autoLoad: true,
                hfov: 100, // 初始的水平视场角
                minHfov: this.minHfov, // 最小水平视场角
                yaw: this.relativeYaw,
                pitch: 0,
                maxHfov: this.maxHfov, // 最大水平视场角
                multiRes: {
                    basePath: '/panoramaUrl/static/layers/' + this.currentTask.batchId + '/' + this.currentTask.imageId,
                    path: '/%l/%s%y_%x',
                    fallbackPath: '/fallback/%s',
                    extension: 'png',
                    tileResolution: this.currentTask.tileResolution ? this.currentTask.tileResolution : 512,
                    maxLevel: this.currentTask.maxLevel ? this.currentTask.maxLevel : 5,
                    cubeResolution: this.currentTask.cubeResolution ? this.currentTask.cubeResolution : 4576
                },
                autoRotate: 0,
                autoRotateInactivityDelay: 0
            });

            this.viewer.on('mousedown', this.handleMouseDown);
            // 场景加载完成时添加图层选择节点
            this.viewer.on('load', () => {
                this.afterLoadPannellum = true;
            });
            this.canvas = this.$refs.canvas;
            this.canvas.width = this.viewer.getContainer().clientWidth;
            this.canvas.height = this.viewer.getContainer().clientHeight;
            this.ctx = this.canvas.getContext('2d');
            //全程监听yaw的值,等待加载完成
            this.viewer.on('animatefinished', (event) => {
                if (this.ctx) {
                    this.allLayers.forEach((child) => {
                        if (child.check) {
                            this.drawGdPolygons();
                        }
                    });
                }
                this.$emit('updateSectorYaw', {
                    currentYaw: this.currentYaw,
                    originYaw: this.yawDegree,
                    currentPitch: this.currentPitch,
                    currentHfov: this.currentHfov
                });
            });
            this.viewer.on('rendercanvas', (event) => {
                this.currentYaw = this.viewer.getYaw();
                this.currentPitch = this.viewer.getPitch();
                this.currentHfov = this.viewer.getHfov();
                this.drawPolygons(); // 绘制多边形
                this.drawMeasureLine();
                this.drawMeasureArea();

                // if(this.polygons) {
                //     this.drawClue(this.polygons, '用地', 'red');
                // }
                if (this.currentHfov !== 100 && this.currentHfov !== 0 && this.isAutoRotating) {
                    this.viewer.setHfov(this.currentHfov);
                }
                updateZoomButtonsState(this.viewer, this.minHfov, this.maxHfov);
            });
            // 监听窗口大小改变，screenfull.isFullscreen的值为是否全屏，若是则true，反之false
            window.onresize = () => {
                this.isScreenFull = screenfull.isFullscreen;
                if (this.canvas) {
                    this.canvas.width = this.viewer.getContainer().clientWidth;
                    this.canvas.height = this.viewer.getContainer().clientHeight;
                }
            };
        },
        handleMeasure(type) {
            this.activeToolBarType = type;
            this.drawPolygonFlag = false;
            this.editFlag = false;
            this.drawRectPolygonFlag = false;
            if (this.activeToolBarType == 'measureDistance') {
                this.isMeasureDistance = true;
            } else if (this.activeToolBarType == 'measureArea') {
                this.isMeasureArea = true;
            }
        },
        judgePoints(points) {
            const screenPoints = [];
            const isInViews = [];
            points.forEach((coord) => {
                //将全景图坐标pitch，yaw转为屏幕坐标
                const point = sphericalToScreen(this.viewer, coord[0], coord[1], this.canvas);
                screenPoints.push(point);
                const isInView = isPointInView(this.viewer, coord[0], coord[1], this.canvas);
                isInViews.push(isInView);
            });
            if (isInViews.indexOf(true) === -1) return []; //所有点均不在视角范围内，不绘制多边形
            if (screenPoints.length === 0) return [];
            return screenPoints;
        },
        drawMeasureLine() {
            const color = ['red', 'rgba(190, 0, 0, 0.3)'];
            this.drawLine(this.measureDistancePoints, color);
        },
        drawLine(points, color) {
            const screenPoints = this.judgePoints(points);
            // 没有点或只有1个点，不绘制线（可保留点绘制）
            if (screenPoints.length < 2) {
                if (screenPoints.length === 1) {
                    // 绘制单个点
                    const [x, y] = screenPoints[0];
                    this.ctx.beginPath();
                    this.ctx.arc(x, y, 3, 0, Math.PI * 2);
                    this.ctx.fillStyle = 'red';
                    this.ctx.fill();
                }
                return;
            }
            // 点大于等于2个时，绘制折线（连接所有连续点）
            this.ctx.beginPath();
            this.ctx.strokeStyle = color[0]; // 线的颜色
            this.ctx.lineWidth = 3; // 线的宽度
            // 从第一个点开始，依次连接所有后续点
            this.ctx.moveTo(screenPoints[0][0], screenPoints[0][1]); // 起点
            for (let i = 1; i < screenPoints.length; i++) {
                this.ctx.lineTo(screenPoints[i][0], screenPoints[i][1]); // 连接到第i个点
            }
            this.ctx.stroke(); // 绘制线条
            if (!this.isMeasureDistance) {
                const points = [];
                for (let i = 0; i < this.measureDistancePoints.length; i++) {
                    const coor = this.measureDistancePoints[i];
                    const drawPoint = imageToLatLon(
                        this.currentTask.latitude,
                        this.currentTask.longitude,
                        this.currentTask.height,
                        coor[1],
                        coor[0],
                        this.currentTask.yawDegree
                    );
                    points.push(L.latLng(drawPoint[0], drawPoint[1]));
                }
                const MEASURERESULT = calculateTotalDistance(points);
                this.ctx.font = '16px Arial';
                this.ctx.fillStyle = 'white';
                this.ctx.fillText(
                    `${MEASURERESULT.toFixed(2)}米`,
                    screenPoints[screenPoints.length - 1][0] + 1,
                    screenPoints[screenPoints.length - 1][1] + 1
                );
            }
        },
        drawMeasureArea() {
            const color = ['red', 'rgba(190, 0, 0, 0.3)'];
            const screenPoints = [];
            const isInViews = [];
            this.measureAreaPoints.forEach((coord) => {
                //将全景图坐标pitch，yaw转为屏幕坐标
                const point = sphericalToScreen(this.viewer, coord[0], coord[1], this.canvas);
                screenPoints.push(point);
                const isInView = isPointInView(this.viewer, coord[0], coord[1], this.canvas);
                isInViews.push(isInView);
            });
            if (isInViews.indexOf(true) === -1) return; //所有点均不在视角范围内，不绘制多边形
            if (screenPoints.length === 0) return;
            this.ctx.beginPath();
            this.ctx.strokeStyle = color[0];
            this.ctx.lineWidth = 3;
            if (screenPoints.length === 1) {
                // 绘制点
                const [x, y] = screenPoints[0];
                this.ctx.arc(x, y, 3, 0, Math.PI * 2); // 小圆表示点
                this.ctx.fillStyle = 'red';
                this.ctx.fill();
            } else if (screenPoints.length === 2) {
                // 绘制线段
                this.ctx.moveTo(screenPoints[0][0], screenPoints[0][1]);
                this.ctx.lineTo(screenPoints[1][0], screenPoints[1][1]);
                this.ctx.stroke();
            } else {
                // 绘制多边形
                this.ctx.fillStyle = color[1];
                this.ctx.moveTo(screenPoints[0][0], screenPoints[0][1]);
                for (let i = 1; i < screenPoints.length; i++) {
                    this.ctx.lineTo(screenPoints[i][0], screenPoints[i][1]);
                }
                this.ctx.closePath(); // 闭合路径以形成多边形
                this.ctx.stroke(); // 描边
                this.ctx.fill(); //填充多边形
            }
            if (!this.isMeasureArea) {
                const points = [];
                for (let i = 0; i < this.measureAreaPoints.length; i++) {
                    const coor = this.measureAreaPoints[i];
                    const drawPoint = imageToLatLon(
                        this.currentTask.latitude,
                        this.currentTask.longitude,
                        this.currentTask.height,
                        coor[1],
                        coor[0],
                        this.currentTask.yawDegree
                    );
                    points.push(L.latLng(drawPoint[0], drawPoint[1]));
                }
                const MEASURERESULT = calculateTotalArea(points);
                this.ctx.font = '16px Arial';
                this.ctx.fillStyle = 'white';
                const center = this.getPolygonCenterXY(screenPoints);
                this.ctx.fillText(`${MEASURERESULT.toFixed(2)}平方米`, center[0] - 60, center[1]);
            }
        },
        handleClear() {
            this.measureDistancePoints = [];
            this.measureAreaPoints = [];
            this.activeToolBarType = '';
        },
        async drawGdPolygons() {
            for (let i = 0; i < this.allLayers.length; i++) {
                const child = this.allLayers[i];
                if (child.check) {
                    // 1. 若正在请求，等待后跳过
                    if (child.isLoading) {
                        await new Promise((resolve) => {
                            const timer = setInterval(() => {
                                if (!child.isLoading) {
                                    clearInterval(timer);
                                    resolve();
                                }
                            }, 100);
                        });
                        continue;
                    }
                    if (!child.gdPolygons) {
                        child.isLoading = true; // 2. 标记为请求中
                        try {
                            const res = await this.getLayerBuffer(child);
                            child.gdPolygons = res.points; // 3. 赋值后清除标记
                        } catch (error) {
                            console.error('请求失败：', error);
                        } finally {
                            child.isLoading = false;
                        }
                    }
                    child.gdPolygons.forEach((item) => {
                        const color = child.color;
                        const points = item.points;
                        const screenPoints = [];
                        const isInViews = [];
                        points.forEach((coord) => {
                            //将全景图坐标pitch，yaw转为屏幕坐标
                            const point = sphericalToScreen(this.viewer, coord[0], coord[1], this.canvas);
                            screenPoints.push(point);
                            const isInView = isPointInView(this.viewer, coord[0], coord[1], this.canvas);
                            isInViews.push(isInView);
                        });
                        if (isInViews.indexOf(true) === -1) return; //所有点均不在视角范围内，不绘制多边形
                        if (screenPoints.length === 0) return;
                        this.ctx.beginPath();
                        this.ctx.strokeStyle = color;
                        this.ctx.lineWidth = 2;
                        // 绘制多边形
                        this.ctx.fillStyle = 'transparent';
                        this.ctx.moveTo(screenPoints[0][0], screenPoints[0][1]);
                        for (let i = 1; i < screenPoints.length; i++) {
                            this.ctx.lineTo(screenPoints[i][0], screenPoints[i][1]);
                        }
                        this.ctx.closePath(); // 闭合路径以形成多边形
                        this.ctx.stroke(); // 描边
                        this.ctx.fill(); //填充多边形
                        this.ctx.font = '16px Arial';
                        this.ctx.fillStyle = 'blue';
                    });
                }
            }
        },
        //获取全部需叠加在全景图层
        async getBufferGD() {
            let layerRes = await getBufferLayerApi();
            if (layerRes.code === 0) {
                let tempLayers = layerRes.data;
                for (let i = 0; i < tempLayers.length; i++) {
                    let child = tempLayers[i];
                    child.check = false;
                    child.color = window.config.colorList[i] || '#09c9ea';
                }
                this.allLayers = tempLayers;
            } else {
                this.$message.error(layerRes.msg);
            }
        },
        getLayerBuffer(param) {
            let op = {
                panorama_image_id: this.currentTask.imageId,
                resource_id: param.id
            };
            return getPointBufferLayerApi(op)
                .then((res) => {
                    if (res.code === 0) {
                        const gdPolygons = res.data.map((item) => ({ points: item }));
                        return { points: gdPolygons, id: param.id }; // 直接 return 结果
                    } else {
                        return { points: [], id: param.id }; // 错误时也 return 结果
                    }
                })
                .catch((error) => {
                    // 捕获异常，返回兜底结果
                    return { points: [], id: param.id };
                });
        },
        toggleThumbnail() {
            this.isThumbnailCollapsed = !this.isThumbnailCollapsed;
        }
    },
    async mounted() {
        if (this.pointId !== -1) {
            this.getBufferGD();
            this.getPointPanoramaImage();
        }
    },
    computed: {
        formattedShotTime() {
            const timeMatch = this.currentTask?.imageName?.match(/(\d{4})(\d{2})(\d{2})\d{6}/);
            return timeMatch ? `${timeMatch[1]}-${timeMatch[2]}-${timeMatch[3]}` : '未知日期';
        }
    },
    watch: {
        currentTask: {
            handler() {}
        }
    }
};
</script>

<style scoped>
@import '@/css/pannellum.css';

#overlay {
    z-index: 1000;
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none; /* 确保不会干扰Pannellum的交互 */
}
::v-deep .transparent-dialog .el-dialog__headerbtn .el-icon-close:hover {
    background-color: transparent;
}

#hotspot-buttons {
    display: none;
    position: absolute;
    z-index: 100;
    background-color: rgba(0, 0, 0, 0.6);
}

#hotspot-buttons button {
    margin: 5px;
    padding: 5px 10px;
    cursor: pointer;
    border: none;
    background: none;
    color: white;
}

#hotspot-buttons button :hover {
    color: #2db6f4;
}

.detectlist,
.undetected-region-list {
    margin-top: 10vh;
    background-color: rgba(0, 0, 0, 0.4);
    box-shadow: none;
    z-index: 9999999;
    color: #fff;
    position: absolute;
    right: 50px;
    width: 300px;
    height: 500px;
    overflow: hidden;
    padding: 10px;
    display: flex;
    flex-direction: column;
}

.detectlist .title,
.undetected-region-list .title {
    display: flex;
    text-align: center;
    border-bottom: 1px solid #fff;
    padding-bottom: 10px;
}

.detectlist .title span,
.undetected-region-list .title span {
    text-align: center;
    font-weight: 700;
    width: 98%;
}

::v-deep .el-button--small.is-circle {
    padding: 4px;
}

::v-deep .el-table::before {
    left: 0;
    bottom: 0;
    width: 100%;
    height: 0px;
}

::v-deep .transparent-dialog {
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
    width: 360px;
}

::v-deep .el-dialog__body {
    height: 200px;
    overflow: auto;
}

::v-deep .el-table,
::v-deep.el-table tr,
::v-deep .el-table th,
::v-deep.el-table th.el-table__cell {
    background-color: rgba(0, 0, 0, 0.1); /* 半透明背景 */
    box-shadow: none; /* 可选，移除阴影 */
    z-index: 999;
    color: #fff;
    overflow: auto;
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
    top: 300px;
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
    text-align: left;
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
    background-color: rgba(0, 0, 0, 0);
}

::v-deep .map-container {
    position: absolute;
    bottom: 0; /* 距离底部10px */
    left: 0; /* 距离左侧10px */
    width: 300px;
    height: 300px;
    z-index: 9999999;
    border: 1px solid #fff;
    display: flex;
    flex-direction: column;
}

::v-deep .map-containerlarge {
    position: absolute;
    bottom: 0; /* 距离底部10px */
    left: 0; /* 距离左侧10px */
    width: 30%; /* 设定宽度 */
    height: calc(100% - 60px);
    z-index: 9999999;
    border: 1px solid #fff;
    display: flex;
    flex-direction: column;
}

::v-deep .leaflet-control-attribution {
    display: none !important;
}

.gt-reback {
    position: absolute;
    right: 10px;
    top: 100px;
    width: 40px;
    z-index: 800;
    border: white;
    margin-bottom: -10px;
    width: 70px;
    height: 30px;
    text-align: center;
    display: flex;
    justify-content: center;
    align-items: center;
    font-size: 1rem;
    cursor: pointer; /* 添加手型指针 */
    background-color: white;
}

.ctrllayers,
.ctrllayerlarge {
    position: absolute;
    display: flex; /* 使用flex布局 */
    flex-direction: column; /* 子元素按列排列 */
    background: #fff;
    border-radius: 5px;
    box-shadow: 0 0 5px rgba(0, 0, 0, 0.2);
}

.ctrllayers {
    left: 210px;
    bottom: 200px;
    z-index: 9999999;
    width: 90px;
    height: 70px;
}

.ctrllayerlarge {
    left: 26%;
    top: 92px;
    bottom: 0px; /* 距离底部10px */
    z-index: 9999999;
    width: 90px;
    height: 70px;
}

.ctrllayers label {
    display: flex;
    align-items: center; /* 垂直居中对齐子元素 */
    padding: 5px; /* 移除默认的外边距 */
}

.ctrllayerlarge label {
    display: flex;
    align-items: center; /* 垂直居中对齐子元素 */
    padding: 5px; /* 移除默认的外边距 */
}

.layer-checkbox {
    margin-right: 8px;
}

::v-deep .el-collapse-item__content {
    font-size: 13px;
    color: #303133;
    line-height: 1.769230769230769;
    margin-left: 5px;
    padding-bottom: 0px;
}

::v-deep .el-collapse-item__header {
    display: flex;
    align-items: center;
    height: 36px;
    line-height: 36px;
    background-color: #fff;
    color: #303133;
    cursor: pointer;
    border-bottom: 1px solid #ebeef5;
    font-size: 13px;
    font-weight: 500;
    transition: border-bottom-color 0.3s;
    outline: 0;
    margin-left: 10px;
}

.show-yaw {
    width: 100%;
    height: 30px;
    z-index: 9999999;
    position: absolute;
    display: flex;
    justify-content: center; /* 只需要声明一次 */
    align-items: center;
    font-size: 0.9rem;
    color: black;
    line-height: 30px; /* 设置行高与容器高度一致 */
}

.gongju_left {
    width: 95%;
    height: 100%;
    overflow: hidden;
    overflow-wrap: break-word; /* 允许在单词内换行 */
    word-break: break-word; /* 允许在单词内换行 */
    padding-left: 2px;
    margin-left: 10px;
    font-size: 20px;
}

.gongju_main {
    width: 30%;
    height: 100%;
    justify-content: space-between;
    text-align: center; /* 确保文本在水平方向上居中 */
}

.gongju_right {
    width: 30%;
    height: 100%;
    text-align: right;
}

::v-deep .highlight-row {
    background-color: #6f6a6a !important; /* 你选择的颜色 */
}

::v-deep .el-form-item--small .el-form-item__content,
.el-form-item--small .el-form-item__label {
    line-height: 32px;
    width: 205px;
}

.btn-uploading {
    text-align: center;
}

.rectangle {
    position: absolute;
    border: 2px solid red;
    background-color: #2a7be8;
    z-index: 9999999;
}

.draw-canvas {
    position: absolute;
    top: 0;
    left: 0;
}

::v-deep .el-input__inner {
    width: 90px;
}

::v-deep .el-input {
    display: inline-block;
}

.gt-query {
    display: flex;
    flex-direction: row;
    padding-bottom: 10px;
    justify-content: space-between;
    padding-top: 10px;
    border-bottom: 1px solid #fff;
}

::v-deep .el-table__body,
.el-table__footer,
.el-table__header {
    table-layout: fixed;
    border-collapse: separate;
    width: 300px !important;
}

::v-deep .el-table__header {
    table-layout: fixed;
    border-collapse: separate;
    width: 300px !important;
}

.tablenum {
    width: 30px;
    border-radius: 50%;
    background-color: #2db6f4;
    display: flex;
    align-items: center;
    justify-content: center;
}

.model {
    width: 25px;
    height: 40px;
    background-size: 100% 100%;
    position: absolute;
    transform: translate(-50%, -50%);
    z-index: 999;
}

.map-container-header {
    height: 32px;
    line-height: 32px;
    color: #666;
    font-size: 16px;
    display: flex;
}

.map-container-header div:first-child {
    width: 96%;
    background-color: white;
}

.map-container-header div:last-child {
    flex: 1;
    background-color: white;
}

.map-container-body {
    width: 100%;
    flex: 1;
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

.hotspot-image {
    width: 50px; /* 热点图片的宽度 */
    height: 50px; /* 热点图片的高度 */
    border-radius: 50%; /* 如果需要，可以设置圆形 */
    cursor: pointer; /* 鼠标悬停时的指针样式 */
}
.rfoot {
    display: flex;
    align-items: center;
    width: calc(100% - 20px);
    margin: 20px 10px;
    overflow: hidden;
}
.rleftbtn {
    border: 1px solid black;
    color: black;
    margin-left: 5px;
}
.rleftbtn:hover {
    background-color: #1da2ff;
}
.rrightbtn {
    border: 1px solid black;
    color: black;

    margin-right: 0px;
}
.rrightbtn:hover {
    background-color: #1da2ff;
}

.thumbnail-container {
    white-space: nowrap;
    overflow-x: auto;
    height: auto;
    margin: 0 10px;
}
.dimg {
    width: 120px; /* 固定宽度 */
    height: 120px;
    display: inline-block;
    margin-right: 10px;
}
/* 针对小屏幕优化 */
@media (max-width: 600px) {
    .dimg {
        width: 120px; /* 更窄的屏幕使用更小的图片宽度 */
    }
}
.dimg span {
    display: block;
    text-align: center;
}
.dimg img {
    width: 90%; /* 缩略图的宽度 */
    height: 90%;
    margin: 0 5px;
    cursor: pointer;
    border: 2px solid transparent;
}

.dimg img.active {
    border: 5px solid #1da2ff;
}
#panoramaContainer {
    position: relative;
    height: 80%;
    background-color: white;
}
.toolbar {
    width: 25%;
    height: 35px;
    position: absolute;
    top: 10px;
    right: 20px;
    border-radius: 5px;
    z-index: 999;
    font-weight: bold;
    line-height: 35px;
    background-color: rgb(218 213 213 / 38%);
    display: flex;
    flex-direction: row;
    justify-content: space-between;
    padding: 0 20px;
    color: black;
}
.toolbar div {
    cursor: pointer;
}
.toolbar div:hover {
    color: #1890ff;
}
.baractive {
    color: #1890ff;
}
.select-gd {
    z-index: 9999999;
    position: absolute;
    font-size: 0.9rem;
    color: black;
    line-height: 32px;
    top: 40px;
    left: 10px;
    height: 32px;
}
::v-deep .el-collapse-item__header {
    display: flex;
    align-items: center;
    height: 32px;
    line-height: 32px;
    color: #303133;
    cursor: pointer;
    font-size: 0.9rem;
    font-weight: 500;
    transition: border-bottom-color 0.3s;
    outline: 0;
    border-bottom: none;
    background-color: rgb(218 213 213 / 38%);
    margin-left: 0px;
    padding: 0 10px;
}
::v-deep .el-collapse {
    border-top: none;
    border-bottom: none;
}
::v-deep .el-collapse-item__wrap {
    border-bottom: none;
    background-color: rgb(218 213 213 / 38%);
    padding: 10px;
}
.thumbnail-footer {
    position: relative;
    height: 20%;
    background-color: #f2f0f0;
    overflow: hidden;
}
.thumbnail-footer.collapsed {
    height: 0; /* 折叠后的高度 */
}
.toggle-button {
    position: absolute;
    left: 80%;
    transform: translateX(-50%);
    width: 60px;
    height: 20px;
    background-color: #ddd;
    border-radius: 0 0 5px 5px;
    display: flex;
    justify-content: center;
    align-items: center;
    cursor: pointer;
    z-index: 1000;
}

.toggle-button:not(.collapsed) {
    bottom: calc(20% - 20px);
}

.toggle-button.collapsed {
    bottom: 0;
}

.toggle-button:hover {
    background-color: #ccc;
}
.toggle-button i {
    font-size: 12px;
    color: #666;
}
.thumbnail-content {
    height: 100%;
}
</style>
