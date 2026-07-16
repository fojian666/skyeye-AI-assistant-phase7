<template>
    <div class="se-container">
        <div class="main-content">
            <div class="left-content">
                <div @click="dialogTableVisible = true" class="left-content-top">
                    <div class="upload-btn-item">
                        <i class="el-icon-upload" style="font-size: 45px"></i>
                        <div>点此上传文件并开始解译</div>
                    </div>
                </div>
                <div class="left-content-middle">
                    <el-form>
                        <el-form-item>
                            <el-input type="text" placeholder="请输入视频名称" v-model="searchName">
                                <template slot="append">
                                    <el-button icon="el-icon-search" size="medium" @click="searchdata"></el-button>
                                </template>
                            </el-input>
                        </el-form-item>
                    </el-form>
                </div>
                <div class="left-content-bottom">
                    <div style="height: 20%" v-for="(item, index) in taskList" :key="index">
                        <cards :data="item" @open-task-details="openTaskDetails" @remove="removeCard(index)" />
                    </div>
                </div>
                <el-pagination
                    small
                    background
                    layout="prev, pager, next, total"
                    :page-size="pageSize"
                    :total="totalTaskCount"
                    :current-page.sync="currentPage"
                    @current-change="handleTaskPageChange"
                    style="position: fixed">
                </el-pagination>
            </div>

            <div class="right-content">
                <ve-details v-show="showDetails" :oddata="selectedCardData" :key="detailsKey" @openTaskDetails="openTaskDetails"></ve-details>
                <div v-show="mapVisible" id="map"></div>
            </div>
        </div>

        <el-dialog title="上传数据" :visible.sync="dialogTableVisible" width="30%" append-to-body :close-on-click-modal="false">
            <div style="width: 100%; height: 39vh; padding-top: 10px">
                <el-form class="form_class">
                    <el-form-item label="视角选择:" label-width="100px">
                        <el-radio-group v-model="checkedview">
                            <el-radio v-for="view in views" :label="view" :key="view"></el-radio>
                        </el-radio-group>
                    </el-form-item>
                    <el-form-item label="上传方式:" label-width="100px">
                        <el-radio-group v-model="uploadmethod">
                            <el-radio label="local">本地上传</el-radio>
                            <el-radio label="server">服务器上传</el-radio>
                        </el-radio-group>
                    </el-form-item>

                    <el-form-item label="本地上传:" label-width="100px" v-if="uploadmethod === 'local'">
                        <el-input type="text" placeholder="支持本地上传视频文件" v-model="filePath">
                            <template slot="append">
                                <el-button icon="el-icon-folder-opened" size="medium" @click="checkFile"></el-button>
                                <input type="file" id="fileinput" style="display: none" accept="video/mp4" @change="handleFolderSelection" />
                            </template>
                        </el-input>
                    </el-form-item>
                    <el-form-item v-else label="服务器上传:" label-width="100px">
                        <el-select v-model="selectedFile" placeholder="请选择" @change="handleFileSelection" style="width: 100%">
                            <el-option v-for="item in serverPathList" :key="item" :label="item" :value="item"> </el-option>
                        </el-select>
                    </el-form-item>
                    <el-form-item label="操作人员:" label-width="100px">
                        <el-input v-model="username" :disabled="true"></el-input>
                    </el-form-item>
                    <div class="btn-uploading">
                        <el-button style="margin-right: 20px" type="primary" size="medium" @click="sumfolder"
                            >解译<i class="el-icon-upload el-icon--right"></i
                        ></el-button>
                        <el-button style="margin-left: 20px" size="medium" @click="reupload">重置</el-button>
                    </div>
                </el-form>
            </div>

            <el-dialog width="30%" :visible.sync="uploading" append-to-body>
                <el-progress :text-inside="true" :stroke-width="18" :percentage="upProgress" status="success" style="margin-top: 10px"> </el-progress>
            </el-dialog>
        </el-dialog>
    </div>
</template>

<script>
import Cards from './Cards';
import VeDetails from './details';
import axios from 'axios';
import { TiledMapLayer } from '@supermap/iclient-leaflet';
import { getFileFolder, getTaskDataListApi, getMapInfoApi } from '@/api/commonApi';

export default {
    name: 'VideoIndex',
    data() {
        return {
            currentPage: 1, //当前页码
            pageSize: 4, //每页显示的数量
            totalTaskCount: 0,
            taskList: [], //展示数据
            delete_card_count: 0, //当前已删除的card数量
            dialogTableVisible: false,
            filePath: '', //文件名称
            uploading: false,
            uploadSuccess: null, // 文件夹上传状态标识
            searchName: '',
            currentObj: {},
            mapVisible: true,
            checkedview: '斜视',
            views: ['正视', '斜视'],
            uploadmethod: 'server', // 上传方式
            username: '',
            showDetails: false,
            selectedCardData: { pictures: [] },
            detailsKey: '',
            pannellumDialogVisible: false,
            uniquekey: 1,
            upProgress: 0,
            serverPathList: [], // 服务器文件列表
            selectedFile: '', // 选择的文件
            mapService: '',
            center: '',
            task_type: '视频检测'
        };
    },
    computed: {},
    watch: {},
    components: {
        Cards,
        VeDetails
    },
    async mounted() {
        let res = await getFileFolder();
        if (res.code === 0) {
            this.serverPathList = res.data;
        } else {
            this.serverPathList = [];
        }
        this.username = window.localStorage.getItem('username');
        if (!this.username) {
            this.$router.push('/login');
        }

        const res1 = await getMapInfoApi();
        if (res1.code === 0) {
            this.mapService = res1.data.map_service;
            this.center = res1.data.center;
            this.initMap();
            this.fetchData();
        }
    },
    methods: {
        initMap() {
            this.map = L.map('map').setView(this.center, 14);
            // 添加天地图瓦片图层
            const tdtLayer = L.tileLayer(
                'http://t0.tianditu.gov.cn/img_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=img&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&tk=d40cf3cbefc882d9a93de1dab6a5a48c'
            ).addTo(this.map);
        },
        openTaskDetails(taskData) {
            this.selectedCardData = taskData;
            this.showDetails = true;
            this.mapVisible = false;
            this.detailsKey = taskData.task_id;
        },
        checkFile() {
            document.querySelector('#fileinput').click();
        },
        handleFolderSelection(event) {
            const selectedFolder = event.target.files[0];
            if (selectedFolder) {
                this.filePath = selectedFolder.name; // 更新文件夹路径
                this.uploadSuccess = null; // 重置上传状态
            }
        },
        async sumfolder() {
            try {
                this.uploading = true;
                //拿到元素节点
                let twos = document.getElementById('fileinput');
                //读取dom节点图片
                const fileObj = twos.files[0];

                if (fileObj) {
                    let formData = new FormData();
                    formData.append('files', fileObj);
                    // 传递 任务名、文件夹路径到后端
                    formData.append('filePath', this.filePath);
                    formData.append('upload_way', this.uploadmethod);
                    formData.append('server_path', this.selectedFile);
                    formData.append('view_angle', this.checkedview);
                    let own = this;
                    const { data: res } = await axios.post('/common/video_task', formData, {
                        headers: { 'content-type': 'application/x-www-form-urlencoded' },
                        onUploadProgress: (progressEvent) => {
                            // 计算上传进度并更新你的进度条
                            own.upProgress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
                        }
                    });
                    // 设置文件夹名称和上传成功状态
                    this.uploading = null;
                    this.uploadSuccess = true;
                    this.dialogTableVisible = false;
                    await this.fetchData();
                    this.$message({
                        message: '解译成功！',
                        type: 'success'
                    });
                } else {
                    this.$message({
                        message: '请填写数据信息',
                        type: 'warning'
                    });
                }
            } catch (error) {
                console.error('Error uploading folder:', error);
                this.uploading = null;
                this.uploadSuccess = false;
                this.$message.error('解译失败，请重试。');
            }
        },
        reupload() {
            this.filePath = '';
        },

        handleTaskPageChange(newPage) {
            this.currentPage = newPage;
            this.fetchData();
        },
        //删除卡片
        removeCard(index) {
            var del_index = (this.currentPage - 1) * this.pageSize + index;
            this.taskList.splice(del_index, 1);
        },
        handleFileSelection(file) {
            this.selectedFile = file;
        },
        async fetchData() {
            const params = {
                page: this.currentPage,
                limit: this.pageSize,
                task_type: this.task_type
            };
            const res = await getTaskDataListApi(params);
            if (res.code === 0) {
                this.taskList = res.data;
                this.totalTaskCount = res.count;
                // 清空地图上的所有标记
                this.clearMap();
                // 遍历数据，在地图上添加标记
                this.taskList.forEach((taskData) => {
                    const lat = taskData.latitude;
                    const lon = taskData.longitude;

                    // 创建标记并添加到地图上
                    this.addMarker(lat, lon, taskData);
                });
            } else {
                console.error('Invalid data format:', res.data);
            }
        },
        addMarker(lat, lon, taskData) {
            // 创建标记并添加到地图上
            const customIcon = L.icon({
                iconUrl: '../../static/video_mark_model.png',
                iconSize: [32, 40],
                iconAnchor: [16, 32],
                popupAnchor: [0, -32]
            });
            const Pcontent = taskData.task_name;
            const marker = L.marker([lat, lon], { icon: customIcon }).addTo(this.map);
            marker.bindPopup(Pcontent);
        },
        clearMap() {
            // 清除地图上的所有标记
            if (this.map) {
                this.map.eachLayer((layer) => {
                    if (layer instanceof L.Marker) {
                        this.map.removeLayer(layer);
                    }
                });
            }
        },
        async searchdata() {
            // 触发搜索操作，根据名称筛选数据
            if (this.searchName) {
                const params = {
                    name: this.searchName,
                    page: this.currentPage,
                    limit: this.pageSize
                };
                const res = await getTaskDataListApi(params);
                // 检查返回数据是否存在并且包含 data 属性
                if (res.code === 0) {
                    this.taskList = res.data;
                    this.totalTaskCount = res.count;
                } else {
                    console.error('Invalid data format:', res.data);
                }
            } else {
                // 如果搜索名称为空，使用全部数据
                this.fetchData(); // 调用原先的 fetchData 方法获取全部数据
            }
        }
    },

    created() {
        document.body.style.overflow = 'hidden';
    }
};
</script>

<style lang="scss" scoped>
.se-container {
    display: flex;
    height: 100%;
}

.business-sidebar {
    width: 90px;
}

.business-sidebar .el-menu-item {
    display: flex;
    align-items: center;
}

.el-menu-item .menu-text {
    padding: 10px 14px 6px 14px;
    font-size: 18px;
    font-weight: bold;
}

.main-content {
    display: flex;
    flex: 1;
    width: 100%;
}

.left-content {
    width: 320px;
    height: 100%;
}
.left-content-top {
    margin: 10px;
    width: 300px;
    border: 2px dashed gray;
    border-radius: 5px;
}
.left-content-middle {
    width: 300px;
    height: 32px;
    margin: 0 10px;
    text-align: start;
}

.left-content-bottom {
    width: 300px;
    height: calc(100% - 188px);
    margin: 10px;
}
.right-content {
    flex: 1;
}

.form_class {
    margin-right: 30px;
}

.input-item {
    margin: 20px;
}

.btn-uploading {
    margin-top: 30px;
    text-align: center;
}

.txt-uploading {
    margin: 20px;
}

.el-pagination {
    bottom: 10px;
}

.upload-btn-item {
    text-align: center;
    cursor: pointer;
}

.el-menu-item {
    height: 140px !important;
    float: left;
    width: 100%;
    text-align: center;
    color: #fff;
    cursor: pointer;
    overflow: hidden;
    line-height: 24px !important;
    box-sizing: border-box;
    padding: 8px !important;
    margin: 0 !important;
    white-space: normal !important;
}

.leftmenu-title {
    background: rgba(23, 125, 228, 0.2);
    border-radius: 10px;
    overflow: hidden;
    transition: border-radius 0.3s ease;
    position: relative;
    width: 100%;
    height: 100%;
    box-sizing: border-box;
    padding-top: 20%;
}

.el-menu-item:focus,
.el-menu-item:hover {
    background-color: white !important;
}

.el-menu-item.is-active > div {
    background: #42b4f2 !important;
}

#map {
    height: 100%;
    width: 100%;
    background-color: #ffffff;
}

.custom-icon {
    font-size: 26px;
    color: #42b4f2;
}
</style>
