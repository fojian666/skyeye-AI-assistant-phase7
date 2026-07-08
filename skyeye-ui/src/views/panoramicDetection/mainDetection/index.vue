<template>
    <div class="se-container">
        <!-- 上传数据   -->
        <div class="se-left-content">
            <div class="dbox">
                <div class="down">
                    <div @click="downloadUrl">全景点KML文件下载</div>
                </div>
            </div>
            <div class="left-form">
                <div class="upload-item">
                    <div class="big">上传数据</div>
                    <div class="small">(上传前请检查图片质量)</div>
                </div>
                <div class="check-box">
                    <div class="street">
                        <span>所属街道：</span>
                        <el-select v-model="selectStreet" style="width: 220px">
                            <el-option v-for="item in selectStreetOptions" :key="item.value" :label="item.value" :value="item.value"></el-option>
                        </el-select>
                    </div>
                    <div class="number">
                        <span>批次编号：</span>
                        <el-select v-model="selectNumber" style="width: 220px">
                            <el-option v-for="number in batchNumbersOptions" :key="number.batch_id" :label="number.batch_id" :value="number.batch_id"></el-option>
                        </el-select>
                    </div>
                    <div class="street">
                        <span>批次名称：</span>
                        <el-input v-model="selectBatchName" style="width: 220px" disabled></el-input>
                    </div>
                    <div class="street">
                        <span>全景数量：</span>
                        <el-input v-model="selectPanoramaCount" style="width: 220px" disabled></el-input>
                    </div>
                    <div class="file-type">
                        <span>文件类型：</span>
                        <el-radio v-model="fileType" label="1">全景</el-radio>
                    </div>
                    <div class="file-upload">
                        <span>文件上传：</span>
                        <el-upload
                            ref="upload"
                            class="upload-demo"
                            :data="batchselect"
                            :action="fileUploadUrl"
                            :headers="headers"
                            accept=".zip"
                            :limit="1"
                            :file-list="fileList"
                            :on-success="getUploadFile"
                            :on-remove="handelRemoveFile">
                            <el-button size="mini" type="primary">点击上传</el-button>
                        </el-upload>
                    </div>
                    <div class="upload-people">
                        <span style="width: 70px">操作用户：</span>
                        <el-input v-model="uploadPeople" disabled placeholder="请输入姓名"></el-input>
                    </div>
                    <div class="upload-button">
                        <el-button type="primary" size="mini" @click="start_detection">开始检测</el-button>
                        <el-button type="info" size="mini" @click="resetForm">重置</el-button>
                    </div>
                    <div class="img">
                        <map-component :activeRow="activeRow"></map-component>
                    </div>
                </div>
            </div>

            <!-- 上传管理 -->
        </div>
        <div class="se-right-content">
            <div class="right-content-header">
                <span class="icon iconfont icon-tupianshangchuanguanli"></span>
                <span class="title">固定批次全景上传管理</span>
            </div>
            <div class="right-content-body">
                <div class="se-filter-form">
                    <div class="se-filter-form-item">
                        <span class="se-filter-form-label">批次编号：</span>
                        <el-select v-model="batchselect" placeholder="请选择" style="max-width: 200px" clearable>
                            <el-option v-for="item in batchOptions" :key="item" :label="item" :value="item"></el-option>
                        </el-select>
                    </div>
                    <div class="se-filter-form-item">
                        <span class="se-filter-form-label">网格编号：</span>
                        <el-select v-model="gridselect" placeholder="请选择" style="max-width: 150px" clearable>
                            <el-option v-for="item in gridOptions" :key="item" :label="item" :value="item"></el-option>
                        </el-select>
                    </div>
                    <div class="se-filter-form-item">
                        <el-button type="primary" size="mini" @click="query()">查询</el-button>
                        <el-button type="info" size="mini" @click="reset()">重置</el-button>
                        <el-button type="danger" size="mini" @click="del()">删除</el-button>
                    </div>
                </div>

                <div class="ttable">
                    <el-table :data="projects" border @selection-change="handleSelectionChange" max-height="100%" height="100%">
                        <el-table-column type="selection" width="50" align="center"></el-table-column>
<!--                        <el-table-column prop="id" label="上传编号" width="80" align="center"></el-table-column>-->
                        <el-table-column type="index" label="序号"></el-table-column>
                        <el-table-column prop="batch_id" label="批次编号" align="center"></el-table-column>
                        <el-table-column prop="grid_id" label="网格编号" align="center"></el-table-column>
                        <el-table-column prop="count" label="上传全景数量" align="center" width="100"></el-table-column>
                        <el-table-column prop="clue_count" label="待核实线索数(个)" align="center" width="150"></el-table-column>
                        <el-table-column prop="grid_operator" label="网格员" align="center" width="120"></el-table-column>
                        <el-table-column prop="create_time" label="上传日期" align="center"></el-table-column>
                        <el-table-column prop="percent" label="检测进度" align="center">
                            <template slot-scope="scope">
                                <el-progress
                                    :percentage="scope.row.percent"
                                    :status="getStatus(scope.row.percent)"
                                    style="text-align: left"></el-progress>
                            </template>
                        </el-table-column>
                        <el-table-column label="操作" width="100px" align="center">
                            <template slot-scope="scope">
                                <ul class="action-list">
                                    <li class="action-item"
                                        @click="handleView(scope.row)">
                                        查看
                                    </li>

                                    <!-- 当 status 为其他值时显示另一个按钮（例如"编辑"） -->
                                    <li class="action-item1"
                                        @click="handleDownload(scope.row)"
                                        v-if="scope.row.status === 0">
                                        信息反馈
                                    </li>
                                </ul>
                            </template>
                        </el-table-column>
                    </el-table>
                </div>
                    <el-pagination
                        background
                        small
                        layout="total, sizes,  prev, pager, next, jumper"
                        v-model="currentPage"
                        class="pagination"
                        :total="total"
                        :page-size="pageSize"
                        @size-change="handleSizeChange"
                        @current-change="handleCurrentChange">
                    </el-pagination>
            </div>
        </div>
    </div>
</template>

<script>
import {
    deleteUploadByIdApi,
    getDownloadPanoramaPointApi,
    getMainDetectionApi,
    getUploadBatchData,
    getUploadProgress,
    postPanoramaDetectionApi,
    getDownloadAnalysisInfoApi
} from '@/api/commonApi';
import MapComponent from './map.vue';

export default {
    name: 'mainDetection',
    components: { MapComponent },
    data() {
        return {
            activeRow: {}, //查看某一行表格数据
            intervalId: null, //定时器
            uploadProgress: 50, //上传进度
            uploadFileName: '', //上传的压缩包名称
            baseUrl: process.env.VUE_APP_API_URL,
            kml_path: '',
            selectStreet: '',
            selectNumber: '',
            batchNumbersOptions: [],
            fileType: '1',
            fileList: [],
            uploadPeople: localStorage.getItem('username'),
            batchselect: '', // 选择的批次
            gridselect: '', // 选择的网格
            currentPage: 1,
            time_interval: 0,
            pageSize: 10,
            total: 0,
            selectedItems: [], //选中的记录
            projects: [],
            headers: { Authorization: 'Bearer ' + sessionStorage.getItem('token') || 'unknown' },
            gridRelatedOptions: [],
            selectStreetOptions:[],
            currentStreetOptions: [],
            currentBatch:{
                "count": 0,
                "batch_id": "",
                "batch_name": ""
            }
        };
    },
    component: {
        MapComponent
    },
    methods: {
        getStatus(percentage) {
            //设置进度条状态
            return percentage === 100 ? 'success' : null;
        },
        async getProgress() {
            //获取进度百分比
            const res = await getUploadProgress();
            if (res.data.length === 0) return;
            this.projects.forEach((item) => {
                const filterData = res.data.filter((it) => it.upload_batch_id === item.id);
                if (filterData.length !== 0) {
                    item.percent = Math.floor(filterData[0].percent * 100);
                }
                // item.percent = Math.floor(res.data.filter((it) => it.upload_batch_id === item.id)[0].percent * 100);
            });
            //根据进度设置定时器
            const hasPercent = this.projects.some((item) => item.percent < 100);
            if (!hasPercent && this.intervalId) {
                clearInterval(this.intervalId);
                this.intervalId = null;
            } else if (hasPercent && !this.intervalId) {
                this.intervalId = setInterval(this.getProgress, 10000); //10S请求一次
            }
        },
        async getTableData() {
            //获取上传表格数据
            const para = {
                pageSize: this.pageSize,
                pageIndex: this.currentPage,
                gridId: this.gridselect,
                batchId: this.batchselect,
                batchType:0
            };
            const res = await getUploadBatchData(para);
            if (res.code !== 0) {
                this.$message.error(res.msg);
                return;
            }
            this.projects = res.data;
            this.total = res.count;
            await this.getProgress();
            this.activeRow = {};
        },
        // getUploadFile(res, file, fileList) {
        //     //上传成功后获取上传的文件名称
        //     this.uploadFileName = file.name;
        // },
        getUploadFile(response, file, fileList) {
            if (response.code === 0) {
                this.uploadFileName =response.unzip_path;
                this.$message.success(response.msg);
            } else {
                this.$refs.upload.handleRemove(file);
                this.$message.error(response.msg);
            }
        },
        handelRemoveFile(file, fileList) {
            //移除文件时更新上传文件名称为空
            this.uploadFileName = '';
        },
        handleSizeChange(val) {
            // 改变每页展示的数据
            this.pageSize = val;
            this.currentPage = 1;
            this.getTableData();
        },
        handleCurrentChange(val) {
            // 改变页码
            this.currentPage = val;
            this.getTableData();
        },
        async start_detection() {
            //检测
            if (this.uploadFileName && this.selectStreet && this.selectNumber) {
                const params = {
                    fileName: this.uploadFileName,
                    batchId: this.selectNumber,
                    street: this.selectStreet,
                    operator: this.uploadPeople
                };
                const element = document.querySelector('.tmain');
                const loading = this.$loading({
                    target: element,
                    text: '正在进行全景检测，请稍后。。。',
                    background: 'rgba(0, 0, 0, 0.6)',
                    lock: true
                });
                try {
                    const res = await postPanoramaDetectionApi(params);
                    if (res.code === 0) {
                        this.$message.success(res.msg);
                    } else {
                        this.$message.error(res.msg);
                    }
                } catch (error) {
                    console.log(error);
                }
                loading.close();
                this.resetForm();
                this.currentPage = 1;
                await this.getTableData();
            } else {
                this.$message.error('输入表单存在空值，请确认输入的参数');
            }
        },
        resetForm() {
            if(this.$route.query.batch_id !== undefined){
                // this.$message.warning("当前批次下无法重置表单，请清除路由批次名称即可获取全部批次状况!!!")
                const query = { ...this.$route.query }
                delete query.batch_id
                this.currentBatch.batch_name = ''
                this.currentBatch.count = 0
                this.selectNumber = '';
                this.fileList = [];
                this.uploadFileName = '';
                this.selectStreet = ''
                this.$router.replace({ query }).then(() => {
                    // 可选：路由更新后重新加载数据
                    this.handleGetInitMessage()
                })
            }else{
                //重置检测表单
                this.selectNumber = '';
                this.fileList = [];
                this.uploadFileName = '';
                this.selectStreet = ''
            }

        },
        async downloadUrl() {
            //全景点kml下载
            if (this.kml_path !== '' && this.kml_path != null) {
                try {
                    const response = await getDownloadPanoramaPointApi(this.kml_path);
                    // 创建一个临时的a标签来模拟下载
                    const url = window.URL.createObjectURL(new Blob([response]));
                    const link = document.createElement('a');
                    link.href = url;
                    link.setAttribute('download', this.grid_name + '.kml'); // 假设文件路径的最后一部分是文件名    
                    document.body.appendChild(link); 
                    link.click();

                    // 清理
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(link);
                } catch (error) {
                    console.log(error);
                    if (error.response && error.response.status === 404) {
                        this.$message.error('文件未找到');
                    } else {
                        this.$message.error('下载文件时发生错误');
                    }
                }
            } else {
                this.$message.warning('当前用户没有绑定网格！请先绑定后再下载');
            }
        },
        handleSelectionChange(val) {
            //获取选中的表格记录
            this.selectedItems = val.map((item) => item.id); // 选中的记录
        },
        del() {
            //删除表格数据
            if (this.selectedItems.length === 0) {
                this.$message.warning('请选择要删除的项');
                return;
            }
            const params = { ids: this.selectedItems };
            this.$confirm('确认删除选中的项吗？', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            })
                .then(async () => {
                    const res = await deleteUploadByIdApi(params);
                    if (res.code === 0) {
                        this.$message.success('数据删除成功！');
                        this.currentPage = 1;
                        await this.getTableData();
                    } else {
                        this.$message.error(res.msg);
                    }
                })
                .catch(() => {
                    this.$message({ type: 'info', message: '已取消删除' });
                });
        },
        reset() {
            //重置筛选参数
            this.batchselect = '';
            this.gridselect = '';
            this.currentPage = 1;
            this.getTableData();
        },
        query() {
            //筛选数据
            this.currentPage = 1;
            this.getTableData();
        },
        handleView(row) {
            this.activeRow = row;
        },
        //下载信息反馈
        async handleDownload(row) {
            const pk_id = row.id;
            try {
                const response = await getDownloadAnalysisInfoApi(pk_id);
                // 创建一个临时的a标签来模拟下载
                const url = window.URL.createObjectURL(new Blob([response]));
                const link = document.createElement('a');
                link.href = url;
                link.setAttribute('download', pk_id + '.txt'); // 假设文件路径的最后一部分是文件名
                document.body.appendChild(link);
                link.click();

                // 清理
                window.URL.revokeObjectURL(url);
                document.body.removeChild(link);
            } catch (error) {
                console.log(error);
                if (error.response && error.response.status === 404) {
                    this.$message.error('文件未找到');
                } else {
                    this.$message.error('下载文件时发生错误');
                }
            }
        },
        async handleGetInitMessage(){
            const res = await getMainDetectionApi();
            if (res.code === 0) {
                this.gridRelatedOptions = res.data
                if (this.selectNumber != '' && this.selectNumber != undefined){ //说明点击待办跳转过来的
                    this.gridRelatedOptions.forEach((item)=>{
                        item.batch_list.forEach((batch)=>{
                            if (batch.batch_id == this.selectNumber){
                                this.selectStreet = item.street
                                this.currentBatch = batch
                            }
                        })
                    })
                }else {
                    this.gridRelatedOptions.forEach((item)=>{
                        this.selectStreetOptions.push({value:item.street,label:item.street})
                    })
                }
            } else {
                //this.$message.warning(res.msg);
            }
        }
    },
    async mounted() {
        this.selectNumber = this.$route.query.batch_id;
        this.handleGetInitMessage();
    },
    beforeDestroy() {
        // 组件销毁前清除定时器
        if (this.intervalId) {
            clearInterval(this.intervalId);
        }
    },
    computed: {
        fileUploadUrl() {
            return '/api/panorama/files_upload';
        },
        batchOptions() {
            return [...new Set(this.projects.map((item) => item.batch_id))]; //获取批次编号集合
        },
        gridOptions() {
            return [...new Set(this.projects.map((item) => item.grid_id).filter((id) => id !== null && id !== undefined && id !== ''))]; //获取网格编号集合
        },
        selectBatchName() {
            if (this.selectNumber && this.$route.query.batch_id == undefined) {
                let batch_obj = this.batchNumbersOptions.filter((item) => item.batch_id === this.selectNumber);
                if (batch_obj) {
                    return this.batchNumbersOptions.filter((item) => item.batch_id === this.selectNumber)[0].batch_name;
                } else {
                    return '请选择批次名称';
                }
            }else{
                return this.currentBatch.batch_name;
            }
        },
        selectPanoramaCount() {
            if (this.selectNumber && this.$route.query.batch_id == undefined) {
                let batch_obj = this.batchNumbersOptions.filter((item) => item.batch_id === this.selectNumber)[0];
                if (batch_obj) {
                    return this.batchNumbersOptions.filter((item) => item.batch_id === this.selectNumber)[0].count;
                } else {
                    return '全景点数据';
                }
            }else{
                return this.currentBatch.count;
            }
        },

    },
    created() {
        this.getTableData();
    },
    watch:{
        selectStreet(newValue, oldValue) {
            if (newValue != '') {
                this.selectNumber = '';
                this.fileList = [];
                this.uploadFileName = '';
                this.currentStreetOptions = this.gridRelatedOptions.filter((item) => item.street === newValue);
                this.kml_path = this.currentStreetOptions[0].kml_path;
                this.grid_name = this.currentStreetOptions[0].grid_name;
                if(this.selectStreet != '' && this.$route.query.batch_id == undefined){
                    let batch_obj = this.currentStreetOptions.filter((item) => item.street === this.selectStreet)[0];
                    if (batch_obj) {
                        const NumbersOptions = [];
                        batch_obj.batch_list.forEach((item) => {
                            NumbersOptions.push({batch_id: item.batch_id,count: item.count, batch_name: item.batch_name});
                        })
                        this.batchNumbersOptions = NumbersOptions;
                    }
                }else{
                    this.selectNumber = this.$route.query.batch_id;
                }
            }
        }
    }
};
</script>

<style scoped lang="scss">

.left-form {
    padding: 10px;
}

.demonstration {
    width: 27%;
}

.el-color-picker__icon,
.el-input,
.el-textarea {
    display: inline-block;
    width: 220px;
}

.page {
    position: absolute; //绝对定位
    right: 20px;
    bottom: 20px;
}

.el-cascader-menu {
    min-width: 100px;
    box-sizing: border-box;
    color: #606266;
    border-right: solid 1px #e4e7ed;
}

.se-filter-form {
    display: flex;
    flex-direction: row;
    align-items: center;
    justify-content: left;
    margin-left: 10px;
    flex-wrap: nowrap; /* 禁止子元素换行 */
    gap: 10px; /* 给子元素之间添加一些间隔 */
    margin-top: 10px;
}

.se-filter-form-item {
    white-space: nowrap; /* 防止内容换行 */
    padding-right: 20px;
}

.se-filter-form-label {
    width: 30px;
}

.el-button {
    margin-right: 2px; /* 给按钮之间添加一些间隔 */
}

/* 确保这些样式只在 .tright 类下生效 */
.tright .el-cascader,
.tright .el-select,
.tright .el-input {
    width: 100%; /* 设置宽度为100% */
}

.ttable {
    margin-left: 10px;
    margin-right: 10px;
    margin-top: 10px;
    height: calc(100% - 100px);
  background: #00092d !important;
}

.action-list {
    list-style: none; /* 移除列表前的默认项目符号 */
    padding: 0; /* 移除默认的内边距 */
    margin: 0; /* 移除默认的外边距 */
    display: flex;
    justify-content: center;
}

.action-item {
    cursor: pointer; /* 鼠标悬停时显示指针样式 */
    color: #409EFF; /* 设置文字颜色为蓝色 */
    padding: 5px; /* 添加一些内边距 */
}

.action-item:hover {
    color: white;
}
.action-item1 {
  cursor: pointer; /* 鼠标悬停时显示指针样式 */
  color: #ccc; /* 设置文字颜色为蓝色 */
  padding: 5px; /* 添加一些内边距 */
}

.action-item1:hover {
  color: white;
}
.down {
    width: 200px;
    height: 40px;
    background-color: #108ee9;
    margin: 0 auto;
    text-align: center;
    line-height: 40px;
    color: #ccedfa;
    cursor: pointer;
}

.dbox {
    height: 80px;
    width: 320px;
    border-bottom: 1px solid #b4b2b2;
    padding-top: 25px;
}

.upload-item {
    display: flex;
    align-items: flex-end; /* 子盒子在底部对齐 */
    padding: 10px 0;
}

.upload-item .big {
    font-weight: bold;
    font-size: 18px;
}

.upload-item .small {
    font-weight: bold;
    font-size: 12px;
}

.street {
    display: flex;
    align-items: center;
    margin-bottom: 20px;
}

.check-box span {
    text-align: right; //表单文本居右对齐
}

.check-box .number {
    margin-bottom: 20px;
}

.check-box .file-type {
    margin-bottom: 20px;
}

.check-box .file-upload {
    display: flex;
    margin-bottom: 20px;
}

.check-box .upload-people {
    display: flex;
    align-items: center;
    margin-bottom: 20px;
}

.check-box .upload-button {
    margin-bottom: 40px;
    text-align: center;
}

.img {
    width: 300px;
    height: 220px;
    margin: 0 auto;
    text-align: center;
    line-height: 220px;
}

.upload-demo {
    max-width: 220px; //设置最大宽度防止上传文件时样式混乱
}

.icon {
    font-size: 24px;
    color: #42b4f2;
    padding-right: 5px;
}

.left-content-body {
    padding-top: 20px;
}

.right-content-body {
    padding: 20px 10px 10px 10px;
    height: calc(100% - 40px);
}
</style>
