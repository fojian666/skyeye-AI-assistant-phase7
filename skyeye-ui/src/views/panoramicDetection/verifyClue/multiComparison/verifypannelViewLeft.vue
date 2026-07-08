<template>
    <div id="panoramaContainer" style="position: relative">
        <div class="pannellum-layer" v-if="afterLoadPannellum"></div>
        <canvas id="overlay" ref="canvas"></canvas>
        <div class="show_jiaodu">
            <div class="gongju_left">{{formattedShotTime}}</div>
        </div>
        <div class="select-gd">
            <el-collapse >
              <el-collapse-item title="业务图层" name="allLayers">
                <div v-for="(item, index) in allLayers" :key="item.id" class="gd-item">
                  <el-checkbox v-model="item.check" @change="handleGdChange">{{ item.name }}</el-checkbox>
                </div>
              </el-collapse-item>
            </el-collapse>
        </div>
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
    import screenfull from 'screenfull';
    import {
      getBufferLayerApi, getEnumOptionApi,
      getOneQuanjingPointClueInfoApi,
      getPointBufferLayerApi,
      postClueInfoApi
    } from '@/api/commonApi';
    import {sphericalToScreen, isPointInView, updateZoomButtonsState} from "@/utils/panoramaTools";
    export default {
        name: 'verifypannelViewLeft',
        //接收父组件传递的数据
        props: {
            currentObj: Object,
            isAddCluePoint: Boolean,
            yaw:Number,
            pitch:Number,
            relativeYaw:Number,
        },
        data() {
            return {
              currentNewCluePitch:null,
              currentNewClueYaw:null,
                currentViewPoint:null,
                // 图层显示
                afterLoadPannellum: false,
                yawDegree: 0,
                // 全景对象
                viewer: undefined,
                //是否全屏
                isScreenFull: false,
                pixel_x: 0,
                pixel_y: 0,
                listData: [],
                currentPitch: localStorage.getItem("initPitch"),
                currentYaw:  this.normalizeYaw(localStorage.getItem("initYaw")),
                currentHfov: localStorage.getItem('initHfov'),
                editFlag: false,
                currentClass: '',
                labelVisible: false,
                currentIndex: 1,
                classList: [],
                ctx: null,
                canvas: null, //全景图画布
                circleRadius: window.config.circleRadius,
                innerCircleRadius:window.config.innerCircleRadius,
                minHfov: 10,
                maxHfov: 100,
                allLayers:[],
                isAutoRotate:false,
                isSendUpdateRightAngleParams:true,
              lastHighLightClueObj:null,
                customIcon: L.icon({
                    iconUrl: '../../../static/marker-icon-red.png',
                    iconSize: [32, 32],
                    iconAnchor: [16, 32],
                    popupAnchor: [0, -32]
                }),
            };
        },
        beforeDestroy() {
            if (this.viewer) {
                this.viewer.destroy(); // 调用Pannellum的销毁方法，清理资源
            }
        },
        methods: {
          //业务图层选择变化监听
          handleGdChange() {
            this.drawGdPolygons();
          },
          //获取标签列表
          async getClueNameList() {
            const classNameListResponse = await getEnumOptionApi('Class_Name');
            if (classNameListResponse.code === 0) {
              classNameListResponse.data.Class_Name.map(item => {
                this.classList.push(item.name)
              })
            }
          },
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
                            item.yaw = yaw;
                            item.pitch = pitch;
                            if (item.status !== 1) {
                                this.viewer.addHotSpot({
                                    id: item.clue_id,
                                    pitch: pitch,
                                    yaw: yaw,
                                    text:  item.label,
                                    type: 'info',
                                    cssClass: 'custom-hotspot',
                                    clickHandlerFunc: (event) => {
                                        this.clickHandlerFunc(event, item);
                                    }
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
            getCurrentAngleParm() {
                const yaw = this.viewer.getYaw();
                const pitch = this.viewer.getPitch();
                const hfov = this.viewer.getHfov();
                this.currentPitch = pitch;
                this.currentYaw = yaw;
                this.currentHfov = hfov;
            },
            handleViewerChange() {
                this.currentHfov = 100;
                // 全景图对象
                this.currentYaw = this.yawDegree;
                if (this.currentObj.imageId) {
                    this.yawDegree = this.currentObj.yawDegree;
                    this.viewer = pannellum.viewer('panoramaContainer', {
                        type: 'multires',
                        sceneFadeDuration: 1000,
                        autoLoad: true,
                        hfov: this.currentHfov, // 初始的水平视场角
                        minHfov: this.minHfov, // 最小水平视场角
                        yaw: 0,
                        pitch:this.relativeYaw?0:this.currentPitch,
                        maxHfov: this.maxHfov, // 最大水平视场角
                        multiRes: {
                            basePath: '/panoramaUrl/static/layers/'  + this.currentObj.batchId + '/' + this.currentObj.imageId,
                            path: '/%l/%s%y_%x',
                            fallbackPath: '/fallback/%s',
                            extension: 'png',
                            tileResolution: this.currentObj.tileResolution? this.currentObj.tileResolution : 512,
                            maxLevel: this.currentObj.maxLevel ? this.currentObj.maxLevel:5,
                            cubeResolution: this.currentObj.cubeResolution?this.currentObj.cubeResolution : 4576
                        },
                        // "compass": true,// 添加指南针
                        // 其他全景图配置...
                        autoRotate: 0,
                        autoRotateInactivityDelay: 0
                    });

                    // 设置初始的正北方向
                    this.viewer.on('mousedown', this.handleMouseDown);
                    // 场景加载完成时添加图层选择节点
                    this.viewer.on('load', () => {
                        this.afterLoadPannellum = true;

                    });
                    //全程监听yaw的值,等待加载完成
                    this.viewer.on('animatefinished', (event) => {
                        if (this.isSendUpdateRightAngleParams && !this.isAutoRotate) {
                            this.$emit('angleParam', {
                                yaw: this.currentYaw,
                                pitch: this.currentPitch,
                                hfov: this.currentHfov
                            });
                        }
                    });
                    this.viewer.on('rendercanvas', (event) => {
                        //获取当前的角度值
                        this.getCurrentAngleParm();
                        updateZoomButtonsState(this.viewer, this.minHfov,this.maxHfov)
                        this.canvasDrawPolygon();
                    });
                    this.canvas = this.$refs.canvas;
                    this.canvas.width = this.viewer.getContainer().clientWidth;
                    this.canvas.height = this.viewer.getContainer().clientHeight;
                    this.ctx = this.canvas.getContext('2d');
                }
                this.handleResize = () => {
                    this.isScreenFull = screenfull.isFullscreen;
                    if (this.canvas) {
                        this.canvas.width = this.viewer.getContainer().clientWidth;
                        this.canvas.height = this.viewer.getContainer().clientHeight;
                        // 可选：重新绘制canvas内容（如之前的线条、多边形）
                        this.canvasDrawPolygon();
                    }
                };
                this.editFlag = this.isAddCluePoint;
                this.fetchData(this.currentObj.imageId);
                window.addEventListener('resize', this.handleResize);

            },
            //canvas绘制多边形
            canvasDrawPolygon(){
                if (this.ctx) {
                    this.ctx.clearRect(0, 0, this.ctx.canvas.width, this.ctx.canvas.height);
                    this.allLayers.forEach((child)=>{
                        if(child.check){
                            this.drawGdPolygons()
                        }
                    })
                    this.drawBuffer();
                    this.drawInnerCircleBuffer();
                    //this.drawPointCircleLocation()

                }
            },
            handleMouseDown(event) {
                this.$emit('clickView');
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
                this.$emit('closeAddCluePoint', { value: false });
            },
            drawMarker(coords) {
                this.currentNewCluePitch = coords[0];
                this.currentNewClueYaw = coords[1];
                this.viewer.addHotSpot({
                    id: this.currentIndex,
                    pitch: this.pitch,
                    yaw: this.yaw,
                    text: this.currentClass,
                    type: 'info',
                    cssClass: 'custom-hotspot'
                });
            },
            //处理线索的点击事件，可处理线索状态，也可点击全景点跳转：tag为0表明是线索点点击事件，为1表明是全景点点击事件
            clickHandlerFunc(event, item) {
                this.currentViewPoint = L.marker([item.latitude,item.longitude],
                    {   icon: this.customIcon,
                        clueId: item.clue_id,
                        clueName: item.label,
                        imageId:this.currentObj.imageId,
                        pointName: this.currentObj.pointName,
                        pointId: this.currentObj.pointId,
                        clueStatus: item.status,
                      draggable: true, //支持拖拽
                    }
                )
              this.viewer.removeHotSpot(item.clue_id)
              if(this.lastHighLightClueObj){
                this.viewer.removeHotSpot(this.lastHighLightClueObj.clue_id);
                this.viewer.addHotSpot({
                  id: this.lastHighLightClueObj.clue_id,
                  pitch: this.lastHighLightClueObj.pitch,
                  yaw: this.lastHighLightClueObj.yaw,
                  text: this.lastHighLightClueObj.label,
                  type: 'info',
                  cssClass: 'custom-hotspot',
                  clickHandlerFunc: (event) => {
                    this.clickHandlerFunc(event, this.lastHighLightClueObj);
                  }
                });
              }
              this.viewer.addHotSpot({
                id: item.clue_id,
                pitch: item.pitch,
                yaw: item.yaw,
                text: item.label,
                type: 'info',
                cssClass: 'custom-hotspot2',
                clickHandlerFunc: (event) => {
                  this.clickHandlerFunc(event, item);
                }
              });
                this.lastHighLightClueObj = {
                  clue_id: item.clue_id,
                  pitch: item.pitch,
                  yaw: item.yaw,
                  text: item.label,
                  status:item.status,
                }
              this.$emit('showClueInMap',this.currentViewPoint);
            },

            //保存目标点
            async addOdLabel() {
                if (this.currentClass === '') {
                    this.$message.warning('请选择标签类别！');
                    return;
                }
                const params = {
                    pixelX: this.pixel_x,
                    pixelY: this.pixel_y,
                    panoramaImageId: this.currentObj.imageId,
                    className: this.currentClass,
                    yaw: this.currentNewClueYaw,
                    pitch: this.currentNewCluePitch
                };
                const res = await postClueInfoApi(params);
                if (res.code === 0) {
                    this.$message.success('添加成功！');
                    this.lastIndex = this.currentIndex;
                    this.viewer.removeHotSpot(this.currentIndex);
                    this.viewer.addHotSpot({
                        id: this.currentIndex,
                        pitch: this.currentNewCluePitch,
                        yaw: this.currentNewClueYaw,
                        text: this.currentClass,
                        type: 'info',
                        cssClass: 'custom-hotspot2',
                        clickHandlerFunc: (event) => {
                            this.clickHandlerFunc(event, res.data);
                        }
                    });
                    this.currentIndex = this.lastIndex + 1;
                } else {
                    this.$message.error('添加失败，请查看后台日志！', res.msg);
                }
                this.editFlag = false;
                this.labelVisible = false;
                this.pixel_y = 0;
                this.pixel_y = 0;
                this.fetchData(this.currentObj.imageId);
                this.$emit('closeAddCluePoint', { value: false });
            },
            startRotate(rotationSpeed,angleRadio,pitch,hfov) {
                if(angleRadio === "") {
                    this.viewer.setHfov(this.currentHfov);
                    this.viewer.startAutoRotate(-rotationSpeed, this.currentPitch);
                }else{
                    this.viewer.setHfov(hfov);
                    this.viewer.startAutoRotate(-rotationSpeed, pitch);
                }
                this.isAutoRotate = true;
            },
            stopRotate() {
                this.viewer.stopAutoRotate();
                this.isAutoRotate = false;
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
            //绘制300米内圈
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
            async drawGdPolygons() {
                for (let i = 0; i < this.allLayers.length; i++) {
                    const child = this.allLayers[i]
                    if (child.check) {
                        // 1. 若正在请求，等待后跳过
                        if (child.isLoading) {
                            await new Promise(resolve => {
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
                                console.error("请求失败：", error);
                            } finally {
                                child.isLoading = false;
                            }
                        }
                        child.gdPolygons.forEach((item) => {
                            const color = child.color;
                            const points = item.points
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
            async getBufferGD(){
                let layerRes = await getBufferLayerApi()
                if(layerRes.code === 0){
                    let tempLayers = layerRes.data;
                    for(let i = 0; i < tempLayers.length;i++){
                        let child = tempLayers[i]
                        child.check = false;
                        child.color= window.config.colorList[i] || '#09c9ea'
                    }
                    this.allLayers = tempLayers;
                }else{
                    this.$message.error(layerRes.msg);
                }
            },
            getLayerBuffer( param ){
                let op = {
                    panorama_image_id: this.currentObj.imageId,
                    resource_id: param.id
                }
                return getPointBufferLayerApi(op).then((res) => {
                    if (res.code === 0) {
                        const gdPolygons = res.data.map((item) => ({ points: item }));
                        return { points: gdPolygons, id: param.id }; // 直接 return 结果
                    } else {
                        return { points: [], id: param.id }; // 错误时也 return 结果
                    }
                }).catch((error) => {
                    // 捕获异常，返回兜底结果
                    return { points: [], id: param.id };
                });
            },
        },
        async mounted() {
            await this.getClueNameList();
            await this.getBufferGD()
            this.handleViewerChange();
            this.currentYaw=this.initYaw;
            this.currentPitch=this.initPitch;
            this.currentHfov=this.initHfov
        },
        computed: {
            formattedShotTime() {
                const timeMatch = this.currentObj?.imageName?.match(/(\d{4})(\d{2})(\d{2})\d{6}/)
                return timeMatch ? `${timeMatch[1]}-${timeMatch[2]}-${timeMatch[3]}` : '未知日期'
            }
        },
        watch: {
            isAddCluePoint: {
                handler(newVal) {
                    this.editFlag = newVal;
                }
            },
            allLayers: {
                handler(newVal) {
                    const allLayersList = [];
                    newVal.forEach((item) => {
                        allLayersList.push({'name': item.name, 'check': item.check});
                    })
                    this.$emit('updateAllLayersCheck', allLayersList);
                },
                deep: true
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
        height: 300px;
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

    ::v-deep .el-dialog__header {
        text-align: center;
        font-weight: 700;
        border-bottom: 1px solid #fff;
    }

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
        top:10px;
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

    }
    ::v-deep .el-form-item--small .el-form-item__content,
    .el-form-item--small .el-form-item__label {
        line-height: 32px;
        width: 205px;
    }
    .btn-uploading {
        text-align: center;
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
    .select-gd{
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
        transition: border-bottom-color .3s;
        outline: 0;
        border-bottom:none;
        background-color: rgb(218 213 213 / 38%);
        margin-left: 0px;
        padding:0 10px
    }
    ::v-deep .el-collapse {
        border-top: none;
        border-bottom: none;
    }
    ::v-deep .el-collapse-item__wrap {
        border-bottom: none;
        background-color: rgb(218 213 213 / 38%);
        padding:10px
    }
</style>
