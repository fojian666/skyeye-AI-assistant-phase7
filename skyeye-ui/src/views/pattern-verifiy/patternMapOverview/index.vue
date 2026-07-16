<template>
    <div class="se-container" v-if="isShow">
        <div class="left-content-show">
            <div class="search-container">
                <div class="search-container-item">
                    <el-input v-model="formInfo.bsm" placeholder="请输入编码" clearable style="margin-bottom: 5px; margin-right: 5px"></el-input>
                    <el-input v-model="formInfo.name" placeholder="请输入地类名称" clearable style="margin-bottom: 5px"></el-input>
                </div>
                <div class="search-container-item">
                    <el-select v-model="formInfo.polygonDataStatus" placeholder="请选择" clearable>
                        <el-option v-for="item in polygonStatus" :key="item.value" :label="item.label" :value="item.value"> </el-option>
                    </el-select>
                    <el-button type="primary" style="margin-top: 5px" @click="getClue">搜索</el-button>
                    <el-button type="info" style="margin-top: 5px" @click="reset">重置</el-button>
                </div>
            </div>
            <div class="cards-containers">
                <div
                    v-for="(item, index) in patternList"
                    :key="index"
                    :class="{ 'is-active': index === activeCardIndex }"
                    @click="setActiveCard(index, item)"
                    class="card">
                    <cards-component :data="item" :key="uniqueCardKey"></cards-component>
                </div>
            </div>
            <div class="page-show">
                <el-pagination
                    small
                    background
                    @current-change="handleCurrentChange"
                    :current-page="formInfo.page"
                    :page-sizes="[5]"
                    :page-size="formInfo.limit"
                    layout="prev, pager, next, total"
                    :total="dataCount"
                    style="position: fixed; bottom: 0px">
                </el-pagination>
            </div>
        </div>
        <div class="border"></div>
        <div class="right-content-show">
            <map-component
                :activeItem="activeItem"
                ref="mapComponent"
                class="map-show"
                :currentLocationMarker="currentLocationMarker"
                @handleReceivePointId="handleReceivePointId">
            </map-component>
            <verifypannelViewer
                class="panoramanic-show"
                :pointId="currentPointID"
                :currentPointObj="currentPointObj"
                :currentAzimuth="currentAzimuth"
                :polygonItem="polygonItem"
                :key="uniqueKey"
                @panorama-mousemove="handlePanoramaMove"
                @updateSectorYaw="updateSectorYaw"
                @resetMap="resetMap">
            </verifypannelViewer>
        </div>
    </div>
    <div class="se-container" v-else style="font-size: 1.5rem; font-weight: bold; padding: 30px">请先至任务管理页面查看任务数据</div>
</template>

<script>
import CardsComponent from './Cards.vue';
import MapComponent from './map.vue';
import verifypannelViewer from './verifypannelViewer.vue';
import { getPatternDataByTaskIdApi } from '@/api/commonApi';
import dictValue from '@/views/resource-center/system-management/dataDict/DictValue';

export default {
    name: 'MapOverView',
    data() {
        return {
            baseUrl: process.env.VUE_APP_API_URL, //请求地址
            statusList: [
                { value: '1', name: '待核实' },
                { value: '0', name: '已核实' }
            ], //获取的业务状态列表
            activeCardIndex: null, //激活的卡片
            activeItem: {},
            dataCount: 0, //数据总数
            currentLocationMarker: null,
            formInfo: {
                status: '',
                page: 1,
                limit: 5,
                task_id: '',
                polygonDataStatus: '',
                name: '',
                bsm: ''
            }, //筛选表单参数
            taskNumList: [],
            patternList: [],
            isShow: false,
            currentPointID: null,
            uniqueKey: 0,
            currentPointObj: {},
            currentAzimuth: 0,
            uniqueCardKey: 0,
            polygonItem: {},
            polygonStatus: [
                {
                    label: '未占用',
                    value: 1
                },
                {
                    label: '占用',
                    value: 2
                },
                {
                    label: '未判读',
                    value: 0
                }
            ]
        };
    },
    components: {
        CardsComponent,
        MapComponent,
        verifypannelViewer
    },
    watch: {
        'formInfo.polygonDataStatus': {
            handler(val) {
                this.getClue();
            }
        },
        'formInfo.name': {
            handler(val) {
                this.getClue();
            }
        },
        'formInfo.bsm': {
            handler(val) {
                this.getClue();
            }
        }
    },
    methods: {
        handlePanoramaMove(data) {
            this.currentLocationMarker = data;
        },
        handleCurrentChange(val) {
            // 改变页码
            this.formInfo.page = val;
            this.activeCardIndex = null;
            this.getClue();
        },
        setActiveCard(index, item) {
            //设置激活的线索卡片
            this.activeCardIndex = index;
            this.activeItem = item;
        },

        async getClue() {
            const para = {
                taskId: this.formInfo.task_id,
                page: this.formInfo.page,
                limit: this.formInfo.limit,
                polygonDataStatus: this.formInfo.polygonDataStatus,
                name: this.formInfo.name,
                bsm: this.formInfo.bsm
            };
            const res = await getPatternDataByTaskIdApi(para);
            if (res.code === 0) {
                this.patternList = res.data;
                this.dataCount = res.count;
                this.uniqueCardKey += 1;
            } else {
                this.$message.error(res.msg);
            }
        },
        handleReceivePointId(value) {
            this.currentPointID = value.point_id;
            this.currentPointObj = value.point_obj;
            this.currentAzimuth = value.azimuth; //方位角
            this.polygonItem = value.polygon_item;
            this.uniqueKey += 1;
        },
        updateSectorYaw(dicValue) {
            this.$refs.mapComponent.updateSector(dicValue.currentYaw, dicValue.originYaw, dicValue.currentPitch, dictValue.currentHfov);
        },
        resetMap() {
            this.$refs.mapComponent.updateMap();
        },
        reset() {
            this.formInfo.bsm = '';
            this.formInfo.name = '';
            this.formInfo.polygonDataStatus = '';
            this.getClue();
        }
    },
    mounted() {
        this.formInfo.task_id = this.$route.query.id;
        if (this.formInfo.task_id) {
            this.isShow = true;
            this.getClue();
        } else {
            this.formInfo.task_id = '';
            this.isShow = false;
        }
    },
    async created() {},
    computed: {}
};
</script>

<style lang="scss" scoped>
.panorama div:last-of-type,
.closed div:last-of-type,
.check div:last-of-type {
    //字体设置
    width: 60px;
    height: 20px;
    line-height: 20px;
    text-align: center;
    font-size: 12px;
}
.panorama div:first-of-type,
.closed div:first-of-type,
.check div:first-of-type {
    //符号设置
    width: 60px;
    height: 60px;
    display: flex;
    justify-content: center;
    align-items: center;
    border-radius: 50%;
    color: white;
    font-size: 20px;
    font-weight: bold;
}
.left-content-show {
    width: 320px;
    height: calc(100% - 20px);
    position: relative;
    margin: 10px 0 10px 10px;
}

.right-content-show {
    width: calc(100% - 340px); //计算剩余宽度
    height: 100%;
    display: flex;
    flex-direction: row;
}
.border {
    width: 10px;
    margin-right: 10px;
    height: 100%;
    border-right: 1px solid #cccccc; //边框设置
}

.page-show {
    position: absolute;
    left: 0;
    bottom: 0;
}
.el-form-item {
    margin-bottom: 5px;
}
.cards-container {
    height: 90%;
    overflow: auto;
}
::v-deep .is-active .el-card {
    border: 2px solid #42b4f2;
}

.el-pager li,
.el-pagination__editor,
.el-pagination .btn-prev,
.el-pagination .btn-next {
    margin: 0 1px !important;
}
::v-deep .el-form-item .el-range-separator {
    width: 10%;
}
.map-show {
    width: 50%;
    position: relative;
}
.panoramanic-show {
    width: 50%;
    height: 100%;
    display: flex;
    flex-direction: column;
}
.search-container {
    display: flex;
    height: 70px;
}
.cards-containers {
    height: calc(100% - 70px);
}

.card {
    height: calc(100% / 5 - 10px);
    margin-top: 5px;
}

::v-deep .el-input__inner {
    width: 155px;
    color: white;
}
:deep(.el-input__clear) {
    right: 5px !important; /* 默认在输入框内右侧 */
    margin-left: 0 !important;
}
</style>
