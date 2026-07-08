<template>
    <div style="width: 100%; height: 100%; display: flex">
        <div class="small-map-container" ref="smallMapContainer" v-if="showSmallMap">
            <small-map
                    class="small-map"
                    ref="smallMap"
                    :gengdi-service="gengdiService"
                    :map-service="mapService"
                    :task-list="panoramaList"
                    :currentYaw="currentAzimuth"
                    :current-task="currentPointObj"
                    :currentLocationMarker1="currentLocationMarker"
                    @clickMarker="handleMarkerClick">
            </small-map>
        </div>
        <div style="width: 50%; height: 100%" v-if="currentPointObj.pointId">
            <panorama-viewer
                    class="panoramanic-show"
                    :pointId="currentPointObj.pointId"
                    :currentPointObj="currentPointObj"
                    :key="uniqueKey"
                    @imageSwitch="updatePanoramaList"
                    @updateSectorYaw="updateSectorYaw"
                    @panorama-mousemove="handlePanoramaMove"
                    @resetMap="resetMap"
                    @skipMulti="skipMulti"
            >
            </panorama-viewer>
        </div>
    </div>
</template>

<script>
    import { getMapInfoApi, getAllPanoramaImageByBatchIdApi } from '@/api/commonApi';
    import smallMap from '@/components/smallMap/index.vue';
    import panoramaViewer from '@/components/panoramaViewer';

    export default {
        name: 'singlePannelView',
        components: { panoramaViewer, smallMap },
        //接收父组件传递的数据
        props: {
            currentObj: Object
        },
        data() {
            return {
                uniqueKey: 0,
                currentPointObj: {}, //当前全景点，接收父组件传递的数据
                currentAzimuth: 0, //正北方位角
                showSmallMap: false, //是否显示小地图
                yawDegree: 0,
                mapService: null, //地图服务
                gengdiService: '', //耕地服务
                panoramaList: [], //根据批次获取所有全景点对应的全景图
                currentLocationMarker:null,
            };
        },
        beforeDestroy() {
            if (this.viewer) {
                this.viewer.destroy(); // 调用Pannellum的销毁方法，清理资源
            }
        },

        methods: {
            handlePanoramaMove(data) {
                this.currentLocationMarker = data;
            },
            updateSectorYaw(dicValue) {
                if (this.showSmallMap) {
                    this.$nextTick(() => {
                        this.currentAzimuth = dicValue.yaw;
                    });
                }

            },
            resetMap() {
                this.$refs.smallMap.resetMapZoom();
            },
            //处理marker的点击事件
            async handleMarkerClick(task) {
                //重新请求线索接口
                this.currentPointObj = task;
                this.uniqueKey += 1;
                this.$emit('markerclick', '-1');
            },
            // 根据批次id获取该批次下所有的全景点影像数据
            async getPanoramaByBatch(batchId) {
                const paraAll = {
                  batchId: batchId
                };
                const panorama_response = await getAllPanoramaImageByBatchIdApi(paraAll);
                if (panorama_response.code === 0) {
                    this.panoramaList = panorama_response.data.cards; //是为了画地图里面所有全景点的marker需要
                } else {
                    this.$message.error(panorama_response.msg);
                }
            },
            async updatePanoramaList(currentImage) {
                await this.getPanoramaByBatch(currentImage.batchId);
                this.$nextTick(() => {
                    currentImage.point_id = this.currentPointObj.pointId;
                    this.currentPointObj = currentImage;
                });
            },
            skipMulti(){
                this.$emit('skipMulti');
            }
        },
        async mounted() {
            this.currentPointObj = this.currentObj;
            await this.getPanoramaByBatch(this.currentPointObj.batchId);
            const res = await getMapInfoApi();
            if (res.code === 0) {
                this.mapService = res.map_service;
                this.gengdiService = res.gengdi_service;
                this.showSmallMap = true;
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

    ::v-deep .el-form-item--small .el-form-item__content,
    .el-form-item--small .el-form-item__label {
        line-height: 32px;
        width: 205px;
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

    .small-map-container {
    //position: absolute;
    //bottom: 0; /* 距离底部10px */
    //left: 0; /* 距离左侧10px */
    //width: 240px;
    //height: 200px;
    //z-index: 9999999;
    //border: 1px solid #fff;
    //display: flex;
    //flex-direction: column;
        width: 50%;
        height: 100%;
    }
    .small-map {
        width: 100%;
        height: 100%;
    }

    .panoramanic-show {
        width: 100%;
        height: 100%;
        display: flex;
        flex-direction: column;
    }
</style>
