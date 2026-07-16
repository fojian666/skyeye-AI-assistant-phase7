<template>
    <div id="panoramaContainerl" style="position: relative">
        <div class="pannellum-layer" v-if="afterLoadPannellum"></div>
        <canvas id="overlay" ref="canvas"></canvas>
        <div class="show_jiaodu">
            <div class="gongju_left">{{ formattedShotTime }}</div>
        </div>
        <!--        <div class="select-gd">-->
        <!--            <el-collapse >-->
        <!--                <el-collapse-item title="业务图层" name="allLayers">-->
        <!--                    <div v-for="(item, index) in allLayers" :key="item.id" class="gd-item">-->
        <!--                        <el-checkbox v-model="item.check">{{ item.name }}</el-checkbox>-->
        <!--                    </div>-->
        <!--                </el-collapse-item>-->
        <!--            </el-collapse>-->
        <!--        </div>-->
    </div>
</template>

<script>
import screenfull from 'screenfull';
import { getBufferLayerApi, getOneQuanjingPointClueInfoApi, getPointBufferLayerApi } from '@/api/commonApi';
import { isPointInView, sphericalToScreen, updateZoomButtonsState } from '@/utils/panoramaTools';

export default {
    name: 'verifypannelViewRight',
    //接收父组件传递的数据
    props: {
        currentObjRight: Object,
        angleParams: Object,
        currentLeftObj: Object,
        allLayersCheck: Array,
        yaw: Number,
        pitch: Number,
        relativeYaw: Number
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
            listData: [],
            currentPitch: localStorage.getItem('initPitch'),
            currentYaw: this.normalizeYaw(localStorage.getItem('initYaw')),
            currentHfov: localStorage.getItem('initHfov'),
            editFlag: false,
            ctx: null,
            canvas: null, //画布
            circleRadius: window.config.circleRadius, //外圈数值
            innerCircleRadius: window.config.innerCircleRadius, //内圈数值
            allLayers: [],
            isAutoRotating: false
        };
    },
    beforeDestroy() {
        if (this.viewer) {
            this.viewer.destroy(); // 调用Pannellum的销毁方法，清理资源
        }
    },
    methods: {
        normalizeYaw(yaw) {
            yaw = Number(yaw); // 转为数字
            // 归一化到 -180~180 范围
            while (yaw > 180) yaw -= 360;
            while (yaw < -180) yaw += 360;
            return yaw;
        },
        async fetchData(image_id) {
            if (image_id) {
                const listres = await getOneQuanjingPointClueInfoApi(image_id);
                if (listres.code === 0) {
                    this.width = listres.data.image_width;
                    this.height = listres.data.image_height;
                    this.listData = listres.data.clue_list;
                    this.listData.forEach((item) => {
                        // 将像素坐标转换为弧度
                        var yawRad = (item.center_x / this.width) * 2 * Math.PI - Math.PI;
                        var pitchRad = Math.PI / 2 - (item.center_y / this.height) * Math.PI;
                        // 将弧度转换为角度
                        var yaw = (yawRad * 180) / Math.PI;
                        var pitch = (pitchRad * 180) / Math.PI;
                        if (item.status != 1) {
                            // 添加热点到viewer
                            this.viewer.addHotSpot({
                                id: item.clue_id,
                                pitch: pitch,
                                yaw: yaw,
                                text: item.label,
                                type: 'info',
                                cssClass: 'custom-hotspot'
                            });
                        }
                    });
                } else {
                    this.$message.error(listres.msg);
                }
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
        //根据全景图路径切换全景图
        async handleViewerChange() {
            if (this.currentObjRight) {
                // 全景图对象
                if (this.currentObjRight.imageId) {
                    this.currentPitch = this.angleParams.pitch;
                    this.currentYaw = this.angleParams.yaw;
                    this.currenthfov = this.angleParams.hfov;
                    this.yawDegree = this.currentObjRight.yawDegree;
                    this.viewer = pannellum.viewer('panoramaContainerl', {
                        type: 'multires',
                        sceneFadeDuration: 1000,
                        autoLoad: true,
                        hfov: this.currentHfov, // 初始的水平视场角
                        minHfov: 0, // 最小水平视场角
                        pitch: this.currentPitch,
                        yaw: -this.yawDegree,
                        maxHfov: 120, // 最大水平视场角
                        multiRes: {
                            basePath: '/panoramaUrl/static/layers/' + this.currentObjRight.batchId + '/' + this.currentObjRight.imageId,
                            path: '/%l/%s%y_%x',
                            fallbackPath: '/fallback/%s',
                            extension: 'png',
                            tileResolution: this.currentObjRight.tileResolution ? this.currentObjRight.tileResolution : 512,
                            maxLevel: this.currentObjRight.maxLevel ? this.currentObjRight.maxLevel : 5,
                            cubeResolution: this.currentObjRight.cubeResolution ? this.currentObjRight.cubeResolution : 4576
                        },
                        // "compass": true,// 添加指南针
                        // 其他全景图配置...
                        draggable: false,
                        autoRotate: 0,
                        autoRotateInactivityDelay: 0
                    });

                    // 设置初始的正北方向
                    // this.viewer.on('mousedown', this.handleMouseDown);
                    // 场景加载完成时添加图层选择节点
                    this.viewer.on('load', () => {
                        this.afterLoadPannellum = true;
                    });
                    this.viewer.setYaw(this.currentYaw);
                    this.viewer.setPitch(this.currentPitch);
                    this.viewer.setHfov(this.currenthfov);
                    this.viewer.on('rendercanvas', (event) => {
                        this.currentYaw = this.viewer.getYaw();
                        updateZoomButtonsState(this.viewer, 0, 120);
                        this.canvasDrawPolygon();
                    });
                    this.canvas = this.$refs.canvas;
                    this.canvas.width = this.viewer.getContainer().clientWidth;
                    this.canvas.height = this.viewer.getContainer().clientHeight;
                    this.ctx = this.canvas.getContext('2d');
                }
                // 监听窗口大小改变，screenfull.isFullscreen的值为是否全屏，若是则true，反之false
                window.onresize = () => {
                    this.isScreenFull = screenfull.isFullscreen;
                    if (this.canvas) {
                        this.canvas.width = this.viewer.getContainer().clientWidth;
                        this.canvas.height = this.viewer.getContainer().clientHeight;
                    }
                };
                this.fetchData(this.currentObjRight.imageId);
            }
        },
        startRotate(rotationSpeed, angleRadio, pitch, hfov) {
            if (angleRadio === '') {
                this.viewer.setHfov(this.currentHfov);
                this.viewer.startAutoRotate(-rotationSpeed, this.currentPitch);
            } else {
                this.viewer.setHfov(hfov);
                this.viewer.startAutoRotate(-rotationSpeed, pitch);
            }
            this.isAutoRotating = true;
        },
        stopRotate() {
            this.viewer.stopAutoRotate();
            this.isAutoRotating = false;
        },
        //canvas绘制多边形
        canvasDrawPolygon() {
            if (this.ctx) {
                this.ctx.clearRect(0, 0, this.ctx.canvas.width, this.ctx.canvas.height);
                this.allLayers.forEach((child) => {
                    if (child.check) {
                        this.drawGdPolygons();
                    }
                });
                this.drawBuffer();
                this.drawInnerCircleBuffer();
                this.drawPointCircleLocation();
            }
        },
        differenceValue() {
            const leftYaw = this.currentLeftObj.yawDegree;
            const rightYaw = this.currentObjRight.yawDegree;
            const chazhi = Math.abs(leftYaw - rightYaw);
            if (leftYaw > rightYaw) {
                return chazhi;
            } else {
                return -chazhi;
            }
        },
        //绘制700m缓冲区
        drawBuffer() {
            this.ctx.beginPath();
            this.ctx.strokeStyle = 'yellow';
            this.ctx.lineWidth = 3;
            const bufferPoints = [];
            const bufferPitch = Math.atan(120 / (this.circleRadius * Math.cos((Math.abs(0) * Math.PI) / 180))) * (180 / Math.PI);
            for (let i = -90; i <= 90; i++) {
                const point = sphericalToScreen(this.viewer, -bufferPitch, this.currentYaw + i, this.canvas);
                bufferPoints.push(point);
            }
            this.ctx.moveTo(bufferPoints[0][0], bufferPoints[0][1]);
            for (let i = 1; i < bufferPoints.length; i++) {
                this.ctx.lineTo(bufferPoints[i][0], bufferPoints[i][1]);
            }
            this.ctx.stroke();
        },
        drawInnerCircleBuffer() {
            this.ctx.beginPath();
            this.ctx.strokeStyle = 'yellow';
            this.ctx.lineWidth = 3;
            const bufferPoints = [];
            this.bufferPitch = Math.atan(112 / (this.innerCircleRadius * Math.cos((Math.abs(0) * Math.PI) / 180))) * (180 / Math.PI);
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
        drawPointCircleLocation() {
            if (this.currentPitch < 0) {
                this.ctx.beginPath();
                this.ctx.strokeStyle = 'yellow';
                this.ctx.lineWidth = 3;
                const bufferPoints = [];
                const bufferPitch = Math.atan(112 / (this.pointCircleRadius * Math.cos((Math.abs(0) * Math.PI) / 180))) * (180 / Math.PI);
                for (let i = -180; i <= 180; i++) {
                    const point = sphericalToScreen(this.viewer, -bufferPitch, this.currentYaw + i, this.canvas);
                    bufferPoints.push(point);
                }
                this.ctx.moveTo(bufferPoints[0][0], bufferPoints[0][1]);
                for (let i = 1; i < bufferPoints.length; i++) {
                    this.ctx.lineTo(bufferPoints[i][0], bufferPoints[i][1]);
                }
                this.ctx.stroke();
            }
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
                panorama_image_id: this.currentObjRight.imageId,
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
        }
    },
    async mounted() {
        this.getBufferGD();
        this.handleViewerChange();
    },
    computed: {
        formattedShotTime() {
            const timeMatch = this.currentObjRight?.imageName?.match(/(\d{4})(\d{2})(\d{2})\d{6}/);
            return timeMatch ? `${timeMatch[1]}-${timeMatch[2]}-${timeMatch[3]}` : '未知日期';
        }
    },
    created() {},
    watch: {
        angleParams: {
            handler(newVal) {
                if (this.viewer && newVal && !this.isAutoRotating) {
                    this.viewer.setYaw(newVal.yaw + this.differenceValue());
                    this.viewer.setPitch(newVal.pitch);
                    this.viewer.setHfov(newVal.hfov);
                    this.currentYaw = newVal.yaw + this.differenceValue();
                    this.currentPitch = newVal.pitch;
                    this.currenthfov = newVal.hfov;
                }
            }
        },
        allLayersCheck: {
            handler(newVal) {
                newVal.forEach((item) => {
                    let targetLayer = this.allLayers.find((layer) => layer.name === item.name);
                    if (targetLayer) {
                        targetLayer.check = item.check;
                    }
                });
                this.drawGdPolygons();
            },
            deep: true,
            immediate: true
        }
    }
};
</script>

<style scoped>
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
    background-color: rgba(0, 0, 0, 0.1); /* 半透明背景 */
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
    bottom: 20px;
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
    border: 1px solid #fff;
}

::v-deep .leaflet-control-attribution {
    display: none !important;
}

.ctrllayers {
    position: absolute;
    left: 300px;
    bottom: 225px; /* 距离底部10px */
    z-index: 9999999;
    width: 90px;
    height: 70px;
    display: flex; /* 使用flex布局 */
    flex-direction: column; /* 子元素按列排列 */
    background: #fff;
    border-radius: 5px;
    box-shadow: 0 0 5px rgba(0, 0, 0, 0.2);
}

.ctrllayers label {
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

.show_jiaodu {
    width: 100%;
    height: 30px;
    z-index: 9999999;
    position: absolute;
    display: flex; /* 使用flex布局 */
    justify-content: space-between;
    color: black;
}

.gongju_left {
    width: 30%;
    height: 100%;
    overflow-wrap: break-word; /* 允许在单词内换行 */
    word-break: break-word; /* 允许在单词内换行 */
    justify-content: left; /* 水平居中 */
    margin-left: 10px;
    font-size: 20px;
}

.gongju_main {
    width: 30%;
    height: 100%;
    justify-content: space-between;
}

.gongju_right {
    width: 30%;
    height: 100%;
}

.gongju_main,
.gongju_left,
.gongju_right {
    display: flex; /* 启用 flexbox */
    align-items: center; /* 垂直居中 */
    overflow-wrap: break-word; /* 允许在单词内换行 */
    font-size: 20px;
}

#overlay {
    z-index: 1000;
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none; /* 确保不会干扰Pannellum的交互 */
}

::v-deep div.pnlm-tooltip span {
    visibility: visible;
    width: 100px;
    background-color: rgba(0, 0, 0, 0);
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
</style>
