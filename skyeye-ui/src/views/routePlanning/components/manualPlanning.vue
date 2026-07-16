<template>
    <div class="box">
        <div class="left">
            <!--      <div class="title"><span>{{ subTitle }}</span></div>-->
            <div class="form">
                <div class="sub-title">
                    <i class="iconfont icon-baogaoguanli"></i>
                    <span style="margin-left: 8px">人工选点航线参数设置</span>
                </div>
                <el-form :model="ruleForm" status-icon :rules="rules" ref="ruleForm" label-width="100px" class="demo-ruleForm">
                    <el-form-item label="区域选择" prop="region" class="form-item-vertical input-width">
                        <el-cascader
                            v-if="selectShow"
                            :options="regionOptions"
                            v-model="ruleForm.region"
                            @change="handleRegionChange"
                            clearable
                            :change-on-select="true"></el-cascader>
                    </el-form-item>
                    <el-form-item label="航线名称" prop="planname" class="form-item-vertical input-width">
                        <el-input
                            v-model.number="ruleForm.planname"
                            autocomplete="off"
                            clearable
                            placeholder="请输入航线名称"
                            class="custom-elinput-height input-width"></el-input>
                    </el-form-item>
                    <el-form-item label="相机型号" prop="cameraSize" class="form-item-vertical input-width">
                        <el-select v-model="ruleForm.cameraSize" placeholder="请选择相机型号" class="custom-elinput-height">
                            <el-option v-for="item in uavoptions" :key="item.value" :label="item.label" :value="item.value"></el-option>
                        </el-select>
                    </el-form-item>
                    <el-form-item label="飞行高度" prop="uavflightHeight" class="form-item-vertical input-width">
                        <el-input
                            v-model.number="ruleForm.uavflightHeight"
                            autocomplete="off"
                            clearable
                            placeholder="请输入飞行高度"
                            class="custom-elinput-height"></el-input>
                    </el-form-item>
                    <el-form-item label="飞行坐标记录" prop="pointLists">
                        <div class="pointlists-box">
                            <div v-for="(point, index) in ruleForm.pointLists" :key="index" class="point">
                                <i class="el-icon-location-information"></i>航点<span style="color: red">{{ index }} </span>：{{
                                    point.lat.toFixed(4)
                                }}, {{ point.lon.toFixed(4) }}
                            </div>
                        </div>
                    </el-form-item>
                    <el-form-item class="search-button">
                        <el-button type="primary" class="right-button" size="mini" @click="handleAddmarker">选点 </el-button>
                        <el-button type="info" class="right-button" size="mini" @click="resetForm('ruleForm')">重置 </el-button>
                        <el-button type="primary" class="right-button" size="mini" @click="submitForm('ruleForm')"> 航线设计 </el-button>
                    </el-form-item>
                </el-form>
            </div>
            <div class="plan-infos">
                <div class="sub-title">
                    <i class="iconfont icon-geoai-list"></i>
                    <span style="margin-left: 8px">航线列表</span>
                </div>
                <div class="plantable">
                    <el-table :data="tableData" style="width: 100%" row-key="id" border>
                        <el-table-column type="index" width="50" label="序"></el-table-column>
                        <el-table-column label="航线名称" prop="name"></el-table-column>
                        <el-table-column label="操作">
                            <template v-slot="scope">
                                <ul class="action-list">
                                    <li class="action-item blue" @click="handleViewPlan(scope.row)">
                                        <i v-if="!scope.row.isViewing" class="iconfont icon-geoai-look" />
                                        <i v-else class="iconfont icon-yanjing-bi-01" />
                                    </li>
                                    <li class="action-item">|</li>
                                    <li class="action-item orange" @click="handleDownload(scope.$index, scope.row)">
                                        <i class="iconfont icon-24px" />
                                    </li>
                                    <li class="action-item">|</li>
                                    <li class="action-item red" @click="handelDeletePlan(scope.$index, scope.row)">
                                        <i class="iconfont icon-shanchu" />
                                    </li>
                                </ul>
                            </template>
                        </el-table-column>
                    </el-table>
                </div>
            </div>
            <div class="page-left">
                <el-pagination
                    small
                    background
                    @current-change="handleCurrentChange"
                    :current-page="tablePage.page"
                    :page-sizes="[5]"
                    :pager-count="5"
                    :page-size="tablePage.limit"
                    layout="prev, pager, next, total"
                    :total="tablePage.dataCount"
                    style="position: fixed; bottom: 10px">
                </el-pagination>
            </div>
        </div>
        <div class="right">
            <map-container ref="mapRef" :table-data="tableData" />
        </div>
    </div>
</template>

<script>
import {
    deleteKmzfileApi,
    getDownloadRouteFileApi,
    getRouteListApi,
    getRegionTreeByUser,
    getUavInfoApi,
    saveRoutePlanApi,
    viewPlanApi
} from '@/api/commonApi';
import L from 'leaflet';
import { normalizeLatLngList } from '@/utils/utils';
import MapContainer from '@/components/routeMap.vue';

export default {
    name: 'manualPlanning',
    components: { MapContainer },
    data() {
        return {
            regionOptions: [],
            ruleForm: {
                cameraSize: '',
                region: [],
                uavflightHeight: '',
                pointLists: [],
                planname: ''
            },
            dialogVisible: false,
            rules: {
                cameraSize: [{ required: true, message: '请选择相机型号' }],
                region: [{ required: true, message: '请选择规划区域' }],
                uavflightHeight: [{ type: 'number', required: true, message: '请输入飞行高度，须为数字' }],
                planname: [{ required: true, message: '请输入航线名称' }]
            },
            isLoading: false,
            tag: '',
            zipfile: '',
            addMarkerType: '0', //0表示起点，1表示终点
            currentStartPoint: null,
            currentEndPoint: null,
            tableData: [],
            pointOperation: '',
            lines: {},
            tablePage: {
                page: 1,
                limit: 5,
                dataCount: 0
            },
            uavoptions: [],
            subTitle: '',
            selectShow: true,
            isRunning: false,
            line: null,
            clickRowId: ''
        };
    },
    watch: {
        '$store.state.currentMenuList': function (newValue, oldValue) {
            this.findSubTitle(newValue);
        },
        'ruleForm.region': {
            handler(newVal) {
                const map = this.getMap();
                if (!map) return;
                if (!Array.isArray(newVal) || newVal.length === 0) return;
                if (!Array.isArray(this.regionOptions) || this.regionOptions.length === 0) return;
                if (this.selectShow) {
                    const findLocation = (items) => {
                        for (const item of items) {
                            if (item.value === newVal[newVal.length - 1]) {
                                return item;
                            }
                            if (item.children && item.children.length > 0) {
                                const found = findLocation(item.children);
                                if (found) return found;
                            }
                        }
                        return null;
                    };
                    const matchedItem = findLocation(this.regionOptions);
                    if (matchedItem && matchedItem.latitude && matchedItem.longitude) {
                        map.flyTo([matchedItem.latitude, matchedItem.longitude], 12);
                    } else {
                        console.warn('未找到匹配的经纬度数据', newVal);
                    }
                } else {
                    this.regionOptions.forEach((item) => {
                        if (item.value === newVal) {
                            map.flyTo([item.latitude, item.longitude], 12);
                        }
                    });
                }
            },
            immediate: false,
            deep: false
        }
    },
    methods: {
        getMap() {
            return this.$refs.mapRef ? this.$refs.mapRef.getMapInstance() : null;
        },
        waitForMapReady() {
            return new Promise((resolve) => {
                const check = () => {
                    const map = this.getMap();
                    if (map) {
                        resolve(map);
                        return;
                    }
                    setTimeout(check, 100);
                };
                check();
            });
        },
        clearManualPointLayers() {
            const map = this.getMap();
            if (!map) return;
            map.off('click', this.mapClick);
            if (this.lines) {
                map.removeLayer(this.lines);
                this.lines = null;
            }
            (this.ruleForm.pointLists || []).forEach((point) => {
                if (point.marker) {
                    map.removeLayer(point.marker);
                }
            });
        },
        // 地图点击，添加航点
        async mapClick(e) {
            const map = this.getMap();
            if (!map) return;
            const defaultIconviolet = L.icon({
                iconUrl: require('@/assets/images/marker-icon-blue.png'),
                iconSize: [25, 40],
                iconAnchor: [12.5, 40],
                popupAnchor: [-3, -40]
            });
            const lat = e.latlng.lat;
            const lon = e.latlng.lng;
            let id_num = 0;
            if (this.pointOperation == 'add') {
                const marker = L.marker([lat, lon], { icon: defaultIconviolet, draggable: true });
                marker.addTo(map);
                this.currentStartPoint = marker;
                this.ruleForm.pointLists.push({ id: id_num++, marker: marker, lat: lat, lon: lon });
                if (this.lines) {
                    map.removeLayer(this.lines);
                }
                this.lines = L.polyline(this.ruleForm.pointLists.map((point) => [point.lat, point.lon])).addTo(map);
                marker.dragging.enable();
                marker.on('dragend', (ev) => {
                    const newLatLng = marker.getLatLng();
                    const newLat = newLatLng.lat;
                    const newLon = newLatLng.lng;
                    this.ruleForm.pointLists.forEach((point) => {
                        if (point.marker === ev.target) {
                            point.lat = newLat;
                            point.lon = newLon;
                        }
                    });
                    map.removeLayer(this.lines);
                    this.lines = L.polyline(this.ruleForm.pointLists.map((point) => [point.lat, point.lon])).addTo(map);
                });
            }
        },
        // 添加航点
        async handleAddmarker() {
            const map = await this.waitForMapReady();
            if (!map) {
                this.$message.error('地图尚未加载完成，请稍后再试');
                return;
            }
            this.pointOperation = 'add';
            map.on('click', this.mapClick);
        },
        // 表单提交
        async submitForm(formName) {
            this.$refs[formName].validate((valid) => {
                if (valid) {
                    const map = this.getMap();
                    if (map) {
                        map.off('click', this.mapClick);
                    }
                    this.savePlan();
                } else {
                    console.log('error submit!!');
                    return false;
                }
            });
        },
        //保存航线
        async savePlan() {
            const fly_points = [];
            if (this.ruleForm.pointLists.length < 2) {
                this.$message.error('请至少添加两个航点');
                return;
            } else {
                this.ruleForm.pointLists.forEach((point) => {
                    fly_points.push([point.lon, point.lat]);
                });
            }
            const para = {
                routeType: '人工选点',
                region: [this.ruleForm.region],
                name: this.ruleForm.planname,
                cameraSize: this.ruleForm.cameraSize,
                height: this.ruleForm.uavflightHeight,
                points: fly_points
            };
            const res = await saveRoutePlanApi(para);
            if (res.code == 0) {
                this.$message.success(res.msg);
                this.handelGetKmzFile();
            }
        },
        // 重置表单
        resetForm(formName) {
            this.$refs[formName].resetFields();
            this.clearManualPointLayers();
            this.stopAnimation();
            this.tableData.forEach((item) => {
                this.$set(item, 'isViewing', false);
            });
        },

        //允许点位拖动，此时地图的点击事件失效
        handleEditPoint() {
            // this.pointOperation = 'drag'
            // this.map.off('click', this.mapClick);
        },
        //获取kmz文件
        async handelGetKmzFile(pageIndex) {
            if (!pageIndex) {
                pageIndex = this.tablePage.page;
            } else {
                this.tablePage.page = pageIndex;
            }
            const para = {
                pageIndex: pageIndex,
                pageSize: this.tablePage.limit,
                routeType: '人工选点',
                orderType: 1,
                orderField: 'createDate'
            };
            const res = await getRouteListApi(para);
            if (res.code === 0) {
                this.tableData = res.data;
                this.tablePage.dataCount = res.total;
            } else {
                this.$message.error(res.msg);
            }
        },
        resetPlan() {
            this.isRunning = false;
            this.stopAnimation(); // 确保停止动画并清理
        },
        async handleViewPlan(row) {
            const map = await this.waitForMapReady();
            if (!map) {
                this.$message.error('地图尚未加载完成');
                return;
            }
            if (this.isRunning) {
                this.resetPlan();
            }
            if (this.clickRowId != row.id) {
                this.tableData.forEach((item) => {
                    if (item != row) {
                        this.$set(item, 'isViewing', false);
                    }
                });
            }
            this.clickRowId = row.id;
            this.resetPlan();
            if (this.line) {
                map.removeLayer(this.line);
                this.line = null;
            }
            if (this.animationMarkers) {
                map.removeLayer(this.animationMarkers);
                this.animationMarkers = null;
            }
            this.$set(row, 'isViewing', !row.isViewing);
            if (!row.isViewing) {
                this.resetPlan();
                return;
            } else {
                this.line = null;
                this.animationMarkers = null;
                const res = await viewPlanApi(row.fileId, 'kmz');
                if (res.code == 0) {
                    this.addLatLngsAnimation(res.data);
                } else {
                    this.$message.error(res.msg);
                }
            }
        },
        //下载kmz文件
        async handleDownload(index, row) {
            const file_id = row.fileId;
            const file_name = row.file !== null && row.file !== undefined ? row.file.fileName : row.name;
            try {
                const response = await getDownloadRouteFileApi(file_id);
                // 创建一个临时的a标签来模拟下载
                const url = window.URL.createObjectURL(new Blob([response]));
                const link = document.createElement('a');
                link.href = url;
                link.setAttribute('download', file_name + '.kmz'); // 假设文件路径的最后一部分是文件名
                document.body.appendChild(link);
                link.click();
                // 清理
                window.URL.revokeObjectURL(url);
                document.body.removeChild(link);
            } catch (error) {
                if (error.response && error.response.status === 404) {
                    this.$message.error('文件未找到');
                } else {
                    this.$message.error('下载文件时发生错误');
                }
            }
        },
        addLatLngsAnimation(latlngs) {
            const map = this.getMap();
            if (!map) return;
            latlngs = normalizeLatLngList(latlngs);
            if (this.isRunning) {
                this.$message.warning('航线绘制中，请等待当前动画完成！');
                return;
            }
            this.currentAnimationInterval = null;
            if (this.line == null) {
                this.line = L.polyline([], { color: 'red' }).addTo(map);
                this.animationMarkers = L.layerGroup().addTo(map);
            } else {
                this.line.setLatLngs([]);
                this.animationMarkers.clearLayers();
            }
            let index = 0;
            const totalPoints = latlngs.length;
            if (latlngs.length > 0) {
                map.setView(latlngs[0], 13);
            }
            this.currentAnimationInterval = setInterval(() => {
                this.isRunning = true;
                if (index >= totalPoints) {
                    clearInterval(this.currentAnimationInterval);
                    this.isRunning = false;
                    return;
                }
                const currentLatLng = latlngs[index];
                const currentPath = this.line.getLatLngs();
                currentPath.push(currentLatLng);
                this.line.setLatLngs(currentPath);
                const marker = L.circleMarker(currentLatLng, { color: 'yellow', fillColor: 'yellow', radius: 4 });
                if (index === totalPoints - 1) {
                    marker.bindPopup('终点');
                }
                this.animationMarkers.addLayer(marker);
                if (index % 10 === 0) {
                    map.panTo(currentLatLng, { animate: true, duration: 0.5 });
                }
                index++;
            }, 200);
            this.animationData = {
                interval: this.currentAnimationInterval,
                totalPoints: totalPoints
            };
        },
        stopAnimation() {
            if (this.currentAnimationInterval) {
                clearInterval(this.currentAnimationInterval);
                this.currentAnimationInterval = null;
            }
            const map = this.getMap();
            if (this.line && map) {
                map.removeLayer(this.line);
                this.line = null;
            }
            if (this.animationMarkers && map) {
                map.removeLayer(this.animationMarkers);
                this.animationMarkers = null;
            }
            this.isRunning = false;
        },
        //删除kmz文件
        handelDeletePlan(index, row) {
            this.$confirm('此操作将永久删除该文件, 是否继续?', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            })
                .then(async () => {
                    this.stopAnimation();
                    if (this.line !== null) {
                        this.line.setLatLngs([]); // 清空已有航线
                        this.animationMarkers.clearLayers(); // 清除标记
                    }
                    const params = {
                        route_id: row.fileId
                    };
                    const res = await deleteKmzfileApi(params);
                    if (res.code === 0) {
                        this.$message.success('删除成功');
                        this.handelGetKmzFile(1);
                    } else {
                        this.$message.error(res.msg);
                    }
                })
                .catch(() => {
                    this.$message.info('已取消删除');
                });
        },
        //处理表格页码的转变
        handleCurrentChange(val) {
            // 改变页码
            this.tablePage.page = val;
            this.handelGetKmzFile();
        },
        async handleGetUavInfo() {
            const res = await getUavInfoApi();
            if (res.code === '0' || res.code === 0) {
                this.uavoptions = res.data;
            }
        },
        findSubTitle(newValue) {
            const filteredItems = newValue.filter((item) => item.url === this.$route.path);
            this.subTitle = filteredItems.length > 0 ? filteredItems[0].name : null;
        },
        async getRegionoptions() {
            const res = await getRegionTreeByUser();
            if (res.code === 0 && Array.isArray(res.data)) {
                this.regionOptions = res.data;
                this.selectShow = this.regionOptions.some((item) => Array.isArray(item.children) && item.children.length > 0);
            } else {
                this.regionOptions = [];
                this.$message.error((res && res.msg) || '获取区域数据失败');
            }
        },
        async loadPageData() {
            await this.handelGetKmzFile();
        },
        handleRegionChange(value) {}
    },
    mounted() {
        this.loadPageData();
    },
    created() {
        this.handleGetUavInfo();
        this.getRegionoptions();
    },
    computed: {}
};
</script>

<style lang="scss" scoped>
.box {
    @import '@/assets/css/table/route-planning';
}

.box {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: row;
}

::v-deep .el-form-item__label {
    font-size: 14px;
    width: 100px !important;
    color: #fff !important;
}

.form-item-vertical {
    display: flex;
    flex-direction: row;
    text-align: left !important;
}

.form-item-vertical1 {
    display: flex;
    flex-direction: column;
    text-align: left !important;
}

::v-deep .el-form-item__content {
    margin-left: 0 !important;
    width: 100%;
}

::v-deep .input-width .el-form-item__content {
    width: calc(100% - 100px);
}

::v-deep .el-form-item--small.el-form-item {
    margin-top: 5px;
}

::v-deep .el-cascader {
    position: relative;
    font-size: 14px;
    line-height: 40px;
    width: 100%;
}

.reset {
    background: gray;
    border-block: none;
}

.btn {
    margin-top: 10px;
    text-align: center;
}

.pointlists-box {
    height: 100px;
    width: 100%;
    border: #3e74b3 dashed 1px;
    margin-top: 10px;
    overflow-y: auto;
}

.point {
    padding-left: 10px;
    color: white;
}

.delete-btn {
    background: red;
    border-block: none;
}

.plan-infos {
    flex: 1;
    width: 100%;
    margin-left: 10px;
    margin-bottom: 50px;
    display: flex;
    flex-direction: column;
    overflow-y: auto;
}

::v-deep .el-table .cell {
    line-height: 20px !important;
}

.bottom-title {
    height: 30px;
    margin-top: 5px;
    background: linear-gradient(45deg, #42b4f2, transparent);
    display: flex;
    align-items: center;
    font-weight: bold;
    margin-bottom: 5px;
}

.toolsbar {
    height: 100px;
    position: absolute;
    width: 20px;
    bottom: 10px;
    left: 490px;
    border: 1px solid #cccccc;
    opacity: 0.5;
    border-radius: 5px;
    z-index: 999;
    font-weight: bold;
    line-height: 35px;
    background-color: white;
    display: flex;
    flex-direction: column;
    padding: 0 20px;
    color: #231815;
}

::v-deep .toolsbar div {
    height: 40px;
    cursor: pointer;
    text-align: center;
    display: flex;
    justify-content: center;
    align-items: center;
}

::v-deep .toolsbar .gt-alarms-list img {
    width: 20px;
    height: 20px;
}

::v-deep .el-pagination__total {
    margin-left: 10px;
}

.right {
    flex: 1;
    height: 100%;
    min-height: 0;
}

.right ::v-deep .se-container {
    width: 100%;
    height: 100%;
}

.demo-ruleForm {
    padding-top: 7px;
}

::v-deep .iclient-leaflet-logo {
    display: none !important;
}
</style>
