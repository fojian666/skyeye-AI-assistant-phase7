<template>
    <div class="box">
        <div class="left">
            <!--      <div class="title"><span>{{ subTitle }}</span></div>-->
            <div class="form">
                <div class="sub-title">
                    <i class="iconfont icon-baogaoguanli"></i>
                    <span style="margin-left: 8px">全景点参数设置</span>
                </div>
                <el-form
                    :model="ruleForm"
                    status-icon
                    :rules="rules"
                    ref="ruleForm"
                    label-width="100px"
                    class="demo-ruleForm"
                    :inline-message="false">
                    <el-form-item label="全景点名称" prop="panoramicPointSetName" class="form-item-vertical">
                        <el-input
                            v-model.number="ruleForm.panoramicPointSetName"
                            autocomplete="off"
                            clearable
                            class="custom-elinput-height"></el-input>
                    </el-form-item>
                    <el-form-item label="缓冲区半径" prop="radius" class="form-item-vertical">
                        <el-input v-model.number="ruleForm.radius" autocomplete="off" clearable class="custom-elinput-height"></el-input>
                    </el-form-item>
                    <el-form-item label="区域选择" prop="uploadMethod" class="form-item-vertical">
                        <el-select
                            v-model="ruleForm.uploadMethod"
                            placeholder="请选择检测区域方式"
                            @change="handleSelectChange"
                            class="custom-elinput-height">
                            <el-option v-for="item in uploadMethodOption" :key="item.value" :label="item.label" :value="item.value"></el-option>
                        </el-select>
                    </el-form-item>
                    <el-form-item label="检测区域矢量" prop="detectAreaShpName" class="form-item-vertical" v-if="ruleForm.uploadMethod == '1'">
                        <el-input
                            type="text"
                            v-model="ruleForm.detectAreaShpName"
                            autocomplete="off"
                            class="upload-input custom-elinput-height"></el-input>
                        <el-button
                            class="custom-button"
                            type="primary"
                            icon="el-icon-plus"
                            size="medium"
                            circle
                            @click="handleDetectionShp"></el-button>
                    </el-form-item>
                    <el-form-item class="search-button">
                        <el-button class="right-button" type="info" size="mini" @click="resetForm('ruleForm')">重置任务 </el-button>
                        <el-button class="right-button begin-btn" type="primary" size="mini" @click="submitForm('ruleForm')">全景点设计 </el-button>
                    </el-form-item>
                </el-form>
            </div>

            <div class="plan-infos">
                <div class="sub-title">
                    <i class="iconfont icon-geoai-list"></i>
                    <span style="margin-left: 8px">全景点列表</span>
                </div>
                <div class="plantable">
                    <el-table :data="tableData" style="width: 100%" row-key="id" border>
                        <el-table-column type="index" width="50" label="序"></el-table-column>
                        <el-table-column label="全景点集合">
                            <template #default="{ row }">
                                {{ row.file && row.file.fileName ? row.file.fileName : row.name }}
                            </template>
                        </el-table-column>
                        <el-table-column label="操作">
                            <template slot-scope="scope">
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
                                    <li class="action-item red" @click="handleDelete(scope.$index, scope.row)">
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
            <map-container ref="mapRef" :tableData="tableData" @finishDraw="finishDraw" />
            <!--            <div class="mapcontainer" id="map"></div>-->
        </div>

        <el-dialog title="上传文件" :visible.sync="dialogVisible" width="20%" :modal="false">
            <el-upload
                style="width: 100%"
                class="upload-demo"
                drag
                action=""
                accept=".zip,.rar"
                ref="upload"
                v-loading="isLoading"
                :on-change="handleChange"
                :on-progress="handleProgress"
                :auto-upload="false"
                :element-loading-text="percent"
                element-loading-spinner="el-icon-loading"
                element-loading-background="rgba(241, 245, 250, 0.5)"
                :file-list="fileList">
                <i class="el-icon-upload"></i>
                <div class="el-upload__text">将文件拖到此处，或<em>点击上传</em></div>
                <div class="el-upload__tip" slot="tip">只能上传压缩文件.zip,.rar，大小不超过500MB</div>
            </el-upload>
            <div class="btn">
                <el-button @click="dialogVisible = false">取 消</el-button>
                <el-button type="primary" @click="uploadConfirm">确 定</el-button>
            </div>
        </el-dialog>
    </div>
</template>

<script>
import { deleteKmzfileApi, getDownloadRouteFileApi, getRouteListApi, savePanoramicPointPlanApi, upLoadShpApi } from '@/api/commonApi';
import MapContainer from '@/components/routeMap.vue';

export default {
    name: 'algorithmPlanning',
    components: { MapContainer },
    data() {
        return {
            ruleForm: {
                panoramicPointSetName: '',
                uploadMethod: '1',
                planArea: [],
                radius: 700,
                detectAreaShpName: '',
                shpFileId: ''
            },
            dialogVisible: false,
            rules: {
                panoramicPointSetName: [{ required: true, message: '请输入全景规划名称', trigger: 'blur' }]
            },
            tableData: [],
            tablePage: {
                page: 1,
                limit: 5,
                dataCount: 0
            },
            isLoading: false,
            percent: '0%',
            totalFiles: 0,
            fileList: [],
            isShowToolBar: false, //是否显示右侧标绘菜单
            uploadMethodOption: [
                { value: '0', label: '人工绘制' },
                { value: '1', label: '矢量上传' }
            ],
            drawnItems: new L.FeatureGroup(), // 存储所有绘制的多边形
            currentFileId: '',
            subTitle: '',
            isShowLook: true,
            mapBounds: []
        };
    },
    watch: {
        fileList(newValue) {
            if (this.totalFiles) this.percent = ((1 - newValue.length / this.totalFiles) * 100).toFixed(0).toString() + '%';
            else this.percent = '0%';
        },
        '$store.state.currentMenuList': function (newValue, oldValue) {
            this.findSubTitle(newValue);
        }
    },
    methods: {
        //结束绘制
        finishDraw(items) {
            this.drawnItems = items;
        },
        //提交表单
        submitForm(formName) {
            this.$refs.mapRef.closeMapClick();
            this.$refs[formName].validate((valid) => {
                if (valid) {
                    this.$refs.mapRef.closeMapClick();
                    this.savePlan();
                } else {
                    return false;
                }
            });
        },
        //保存航线
        async savePlan() {
            // 遍历 drawnItems 中的每个图层
            this.drawnItems.eachLayer((layer) => {
                if (layer instanceof L.Polygon) {
                    // 获取多边形的坐标
                    const latLngs = layer.getLatLngs()[0]; // 获取第一个层级的坐标
                    const coordinates = latLngs.map((latLng) => [latLng.lng, latLng.lat]); // 转换为 [lon, lat] 格式
                    // 将“列表”对象添加到 planArea 中
                    this.ruleForm.planArea.push(coordinates);
                }
            });
            const para = {
                planType: '全景规划',
                planName: this.ruleForm.panoramicPointSetName,
                radius: this.ruleForm.radius,
                planArea: this.ruleForm.planArea,
                shpName: this.ruleForm.detectAreaShpName,
                planAreaUploadTag: this.ruleForm.uploadMethod,
                shpFileId: this.ruleForm.shpFileId
            };
            if (this.ruleForm.uploadMethod === '0') {
                if (this.ruleForm.planArea.length === 0) {
                    this.$message.error('请绘制规划区域');
                    return;
                }
            }

            const loading = this.$loading({
                lock: true,
                text: '正在规划中',
                spinner: 'el-icon-loading',
                background: 'rgba(0, 0, 0, 0.7)'
            });
            const res = await savePanoramicPointPlanApi(para);
            if (res.code === 0) {
                this.fileList = [];
                this.currentFileId = res.data.file_id;
                loading.close();
                let id_num = 0;
                res.data.forEach((item) => {
                    this.$refs.mapRef.updateView(item, id_num);
                });
                this.handelGetZipFile();
            } else {
                loading.close();
                this.$message.error(res.msg);
            }
        },
        //重置表单
        resetForm(formName) {
            this.$refs[formName].resetFields();
            this.ruleForm.detectAreaShpName = '';
            this.activeToolBarIndex = 0;
            this.drawnItems.clearLayers();
            this.tableData.forEach((item) => {
                this.$set(item, 'isViewing', false);
            });
        },
        //获取kmz文件列表
        async handelGetZipFile(pageIndex) {
            if (!pageIndex) {
                pageIndex = this.tablePage.page;
            } else {
                this.tablePage.page = pageIndex;
            }
            const para = {
                pageIndex: pageIndex,
                pageSize: this.tablePage.limit,
                routeType: '全景规划',
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
        async handleViewPlan(row) {
            this.$refs.mapRef.handleViewPlan(row);
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
                link.setAttribute('download', file_name + '.zip'); // 假设文件路径的最后一部分是文件名
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
        //删除kmz文件
        async handleDelete(index, row) {
            this.$confirm('此操作将永久删除该文件, 是否继续?', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            })
                .then(async () => {
                    const params = {
                        route_id: row.fileId
                    };
                    const res = await deleteKmzfileApi(params);
                    if (res.code === 0) {
                        this.$message.success('删除成功');
                        this.handelGetZipFile(1);
                    } else {
                        this.$message.error(res.msg);
                    }
                })
                .catch(() => {
                    this.$message.info('已取消删除');
                });
        },
        //处理当前页码的转换
        handleCurrentChange(val) {
            // 改变页码
            this.tablePage.page = val;
            this.handelGetZipFile();
        },
        handleDetectionShp() {
            this.dialogVisible = true;
        },
        //上传文件
        async uploadConfirm() {
            // this.$refs.upload.submit()
            // 创建一个空的FormData对象:
            const formData = new FormData();
            this.isLoading = true;
            this.totalFiles = this.fileList.length;
            formData.append('files', this.zipfile.raw);
            const res = await upLoadShpApi(formData);
            if (res.code === 0) {
                this.$message.success('检测区域矢量上传成功');
                this.ruleForm.detectAreaShpName = this.zipfile.name;
                const polygonLists = res.data;
                this.ruleForm.shpFileId = res.data.shpFileId;
                polygonLists.forEach((polygon) => {
                    // 创建多边形并添加到地图
                    this.$refs.mapRef.addPolygon(polygon, { color: '#49fb18' });
                });
            } else {
                this.$message.error('检测区域矢量上传失败');
            }
            this.isLoading = false;
            this.dialogVisible = false;
            this.tag = '';
            this.zipfile = '';
        },
        //处理上传文件的转换
        handleChange(file, fileList) {
            if (file.size / 1024 / 1024 / 1024 > 1) {
                fileList.pop(file);
                this.$message.warning(`${file.name}文件超出1GB，不支持上传`);
                return;
            }
            this.zipfile = file;
        },
        handleProgress(event, file, fileList) {},
        //监听选择框值的变化
        handleSelectChange(value) {
            if (value === '0') {
                this.$refs.mapRef.isShowToolBar = true;
            } else {
                this.$refs.mapRef.isShowToolBar = false;
            }
            return value;
        },

        findSubTitle(newValue) {
            const filteredItems = newValue.filter((item) => item.url === this.$route.path);
            this.subTitle = filteredItems.length > 0 ? filteredItems[0].name : null;
        }
    },
    async mounted() {
        this.handelGetZipFile();
    },
    created() {},
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

.demo-ruleForm {
    padding-top: 7px;
}

::v-deep .el-form-item--small .el-form-item__content,
.el-form-item--small {
    line-height: 10px;
}

::v-deep .el-form-item__content {
    margin-left: 0 !important;
    width: calc(100% - 100px);
}

::v-deep .el-form-item--small.el-form-item {
    margin-top: 5px;
}

::v-deep .el-cascader {
    position: relative;
    font-size: 14px;
    line-height: 40px;
}

::v-deep .el-table .cell {
    line-height: 20px !important;
}

.pointlists-box {
    height: 100px;
    width: 100%;
    border: black dashed 1px;
    margin-top: 10px;
    overflow-y: auto;
}

.active {
    color: #42b4f2;
}

.point-tools-bar {
    height: 100px;
    position: absolute;
    width: 15px;
    bottom: 10px;
    left: 490px;
    border: 1px solid #cccccc;
    border-radius: 5px;
    z-index: 999;
    font-weight: bold;
    line-height: 35px;
    background-color: white;
    display: flex;
    flex-direction: column;
    padding: 0 20px;
}

::v-deep .point-tools-bar div {
    height: 40px;
    cursor: pointer;
    text-align: center;
    display: flex;
    justify-content: center;
    align-items: center;
}

::v-deep .point-tools-bar .gt-alarms-list img {
    width: 20px;
    height: 20px;
}

::v-deep .el-pagination__total {
    margin-left: 10px;
}

.upload-demo ::v-deep(.el-upload),
.upload-demo ::v-deep(.el-upload .el-upload-dragger) {
    width: 100% !important;
}

.upload-input {
    width: calc(100% - 54px);
}

.mapcontainer {
    background-color: white;
}
::v-deep .iclient-leaflet-logo {
    display: none !important;
}
</style>
