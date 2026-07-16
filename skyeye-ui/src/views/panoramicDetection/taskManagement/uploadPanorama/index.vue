<template>
    <div class="gt-container se-container" :class="themeClass">
        <!-- 上传数据   -->
        <div class="left-content">
            <div class="dbox">
                <el-button type="text" size="mini" class="back-btn" @click="handleGoBackPage"
                    ><i class="el-icon el-icon-back"></i>
                    返回
                </el-button>
            </div>
            <div class="left-form">
                <div class="upload-item">
                    <div class="big">上传数据</div>
                    <div class="small">(上传前请检查图片质量)</div>
                </div>
                <div class="check-box">
                    <el-form ref="addForm" :model="addForm" :rules="rules" class="check-box">
                        <!-- 所属街道 -->
                        <el-form-item label="所属街道" prop="street" class="street">
                            <el-input v-model="addForm.street" disabled />
                        </el-form-item>

                        <!-- 批次名称 -->
                        <el-form-item label="批次名称" prop="batchName" class="street">
                            <el-input v-model="addForm.batchName" disabled />
                        </el-form-item>
                        <el-form-item label="批次ID" prop="batchId" class="street">
                            <el-input v-model="addForm.batchId" disabled />
                        </el-form-item>

                        <!-- 全景数量 -->
                        <el-form-item label="全景数量" class="street">
                            <el-input v-model="selectPanoramaCount" style="width: 220px" disabled></el-input>
                        </el-form-item>

                        <!-- 文件类型 -->
                        <el-form-item label="文件类型" class="street file-type">
                            <el-radio v-model="addForm.fileType" label="1">全景</el-radio>
                        </el-form-item>

                        <!-- 文件上传 -->
                        <el-form-item label="文件上传" prop="file" class="street file-upload">
                            <el-upload
                                ref="upload"
                                class="upload-demo"
                                :action="fileUploadUrl"
                                :headers="headers"
                                accept=".zip"
                                :limit="1"
                                :file-list="fileList"
                                :on-success="getUploadFile"
                                :on-remove="handleRemoveFile"
                                :on-progress="handleUploadProgress">
                                <el-button size="mini" type="primary">点击上传</el-button>
                            </el-upload>
                        </el-form-item>

                        <!-- 操作用户 -->
                        <el-form-item label="操作用户" class="street upload-people">
                            <el-input v-model="addForm.uploadPeople" disabled placeholder="请输入姓名"></el-input>
                        </el-form-item>

                        <!-- 按钮 -->
                        <el-form-item class="button-group">
                            <el-button type="primary" size="mini" @click="start_detection">开始检测</el-button>
                            <el-button type="info" size="mini" @click="resetForm">重置</el-button>
                        </el-form-item>
                    </el-form>
                </div>
            </div>
        </div>
        <div class="border"></div>
        <div class="right-content">
            <div class="right-content-header">
                <span class="icon iconfont icon-tupianshangchuanguanli"></span>
                <span class="title">固定批次全景上传管理</span>
            </div>
            <div class="right-content-body">
                <div class="t-query">
                    <div class="t-query-item">
                        <span class="idemonstration">批次名称：</span>
                        <el-input v-model="batchName" placeholder="请输入批次名称" />
                    </div>
                    <div class="t-query-item">
                        <el-button type="primary" size="mini" @click="query()">查询</el-button>
                        <el-button type="info" size="mini" @click="reset()">重置</el-button>
                        <el-button type="danger" size="mini" @click="del()">删除</el-button>
                    </div>
                </div>
                <div class="ttable">
                    <el-table :data="tableDataList" border @selection-change="handleSelectionChange" max-height="100%" height="100%">
                        <el-table-column type="selection" width="50" align="center"></el-table-column>
                        <el-table-column type="index" label="序号" width="60"></el-table-column>
                        <el-table-column prop="batch_name" label="批次名称" align="center"></el-table-column>
                        <el-table-column prop="street" label="所属街道" align="center"></el-table-column>
                        <el-table-column prop="count" label="上传全景数量" align="center" width="120"></el-table-column>
                        <el-table-column prop="clue_count" label="疑似线索数(个)" align="center" width="150"></el-table-column>
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
                        <el-table-column label="操作" width="150px" align="center">
                            <template slot-scope="scope">
                                <ul class="action-list">
                                    <li
                                        class="action-item1"
                                        @click="handleDownload(scope.row)"
                                        v-if="scope.row.status === 2 || scope.row.status === 0">
                                        <span :style="{ color: getStatusColor(scope.row.result) }"> 检测结果 </span>
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
    getDownloadAnalysisInfoApi,
    getBatchInfoByIdApi,
    getUploadBatchData,
    getUploadProgress,
    postPanoramaDetectionApi
} from '@/api/commonApi';

export default {
    name: 'mainDetection',
    components: {},
    data() {
        return {
            activeRow: {}, //查看某一行表格数据
            intervalId: null, //定时器
            uploadProgress: 50, //上传进度
            uploadFileName: '', //上传的压缩包名称
            batchName: '',
            selectPanoramaCount: 0,
            batchNumbersOptions: [],
            fileType: '1',
            fileList: [],
            currentPage: 1,
            pageSize: 10,
            total: 0,
            selectedItems: [], //选中的记录
            tableDataList: [],
            headers: { Authorization: 'Bearer ' + sessionStorage.getItem('token') || 'unknown' },
            loading: null,
            currentBatchId: '',
            // 表单绑定对象
            addForm: {
                street: '', // 所属街道
                batchName: '', // 批次
                batchId: '',
                fileType: '1',
                file: '', // 上传文件
                uploadPeople: localStorage.getItem('username')
            },
            // 校验规则
            rules: {
                file: [{ required: true, message: '请上传zip文件', trigger: 'change' }]
            }
        };
    },
    methods: {
        getStatus(percentage) {
            //设置进度条状态
            return percentage === 100 ? 'success' : null;
        },
        //设置任务状态颜色
        getStatusColor(result) {
            switch (result) {
                case 1:
                    return '#409eff';
                default:
                    return 'gray';
            }
        },
        //获取进度百分比
        async getProgress() {
            const res = await getUploadProgress();
            if (res.data.length === 0) return;
            this.tableDataList.forEach((item) => {
                const filterData = res.data.filter((it) => it.upload_batch_id === item.id);
                if (filterData.length !== 0) {
                    item.percent = Math.floor(filterData[0].percent * 100);
                    item.result = filterData[0].result;
                }
            });
            //根据进度设置定时器
            const hasPercent = this.tableDataList.some((item) => item.percent < 100);
            if (!hasPercent && this.intervalId) {
                clearInterval(this.intervalId);
                this.intervalId = null;
            } else if (hasPercent && !this.intervalId) {
                this.intervalId = setInterval(this.getProgress, 10000); //10S请求一次
            }
        },
        // 重置表单
        resetForm() {
            this.$refs.addForm.resetFields();
            this.fileList = [];
        },
        //获取上传表格数据
        async getTableData() {
            const para = {
                pageSize: this.pageSize,
                pageIndex: this.currentPage,
                gridId: '',
                batchId: this.currentBatchId,
                pointType: 0
            };
            const res = await getUploadBatchData(para);
            if (res.code !== 0) {
                this.$message.error(res.msg);
                return;
            }
            this.tableDataList = res.data;
            this.total = res.count;
            await this.getProgress();
            this.activeRow = {};
        },
        getUploadFile(response, file, fileList) {
            if (response.code === 0) {
                this.uploadFileName = response.unzip_path;
                this.$message.success(response.msg);
            } else {
                this.$refs.upload.handleRemove(file);
                this.$message.error(response.msg);
            }
            if (this.loading) {
                this.loading.close();
                this.loading = null;
            }
        },
        handleRemoveFile(file, fileList) {
            //移除文件时更新上传文件名称为空
            this.uploadFileName = '';
            if (this.loading) {
                this.loading.close();
                this.loading = null;
            }
        },

        handleUploadProgress(event) {
            // 创建新的loading
            this.loading = this.$loading({
                text: '正在上传文件中，请稍后...',
                background: 'rgba(0, 0, 0, 0.6)',
                lock: true,
                spinner: 'el-icon-loading'
            });
            return true; // 允许上传继续
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
            if (this.uploadFileName) {
                const params = {
                    fileName: this.uploadFileName,
                    batchId: this.addForm.batchId,
                    street: this.addForm.street,
                    operator: this.addForm.uploadPeople
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
                this.currentPage = 1;
                await this.getTableData();
            } else {
                this.$message.error('输入表单存在空值，请确认输入的参数');
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
            //重置筛选参数（与 mainDetection/index.vue 一致）
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
        //获取批次信息
        async getBatchInfoById() {
            const res = await getBatchInfoByIdApi(this.currentBatchId);
            if (res.code === 0) {
                if (res.data.length === 0) {
                    this.$message.warning('当前批次没有数据');
                    this.handleGoBackPage();
                    return;
                }
                const dataDic = res.data;
                this.addForm.street = dataDic.street;
                this.addForm.batchId = dataDic.pk_id;
                this.addForm.batchName = dataDic.batch_name;
                this.batchNumbersOptions = dataDic.batch_list;
                this.selectPanoramaCount = dataDic.remaining_count;
            }
        },
        handleGoBackPage() {
            // 1. 找到当前路由在路由配置中的记录
            this.$route.meta.clueId = null;
            this.$router.go(-1);
        }
    },
    async mounted() {
        this.currentBatchId = this.$route.query.batch_id;
        this.getTableData();
        if (this.currentBatchId === undefined || this.currentBatchId === '') {
            this.$message.warning('请选择批次进行上传');
        }
        this.getBatchInfoById();
    },
    beforeDestroy() {
        // 组件销毁前清除定时器
        if (this.intervalId) {
            clearInterval(this.intervalId);
        }
    },
    computed: {
        themeClass() {
            return 'theme-' + (this.$store.state.theme || 'light');
        },
        fileUploadUrl() {
            return '/api/panorama/files_upload';
        }
    },
    created() {},
    watch: {
        selectStreet(newValue, oldValue) {
            if (newValue !== '') {
                this.fileList = [];
                this.uploadFileName = '';
            }
        }
    }
};
</script>

<style scoped lang="scss">
/* 布局由本页控制，颜色交给 public/theme 全局主题 + theme-light/theme-dark 补充 */
.gt-container {
    padding: 10px;
    height: 100%;
    position: relative;
    display: flex;
    box-sizing: border-box;
}

.left-content {
    width: 320px;
    height: 100%;
    border-radius: 2px;
    box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.1);
}

.right-content {
    width: calc(100% - 340px);
    height: 100%;
    flex-direction: column;
    border-radius: 2px;
    box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.1);
}

.border {
    width: 10px;
    height: 100%;
    flex-shrink: 0;
}

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

.t-query {
    display: flex;
    flex-direction: row;
    align-items: center;
    justify-content: left;
    margin-left: 10px;
    flex-wrap: nowrap; /* 禁止子元素换行 */
    gap: 10px; /* 给子元素之间添加一些间隔 */
    margin-top: 10px;
}

.t-query-item {
    white-space: nowrap; /* 防止内容换行 */
    padding-right: 20px;
}

.idemonstration {
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
.button-group {
    text-align: center;
}
.ttable {
    margin-left: 10px;
    margin-right: 10px;
    margin-top: 10px;
    height: calc(100% - 100px);
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
    color: #409eff; /* 设置文字颜色为蓝色 */
    padding: 5px; /* 添加一些内边距 */
}

.action-item1 {
    cursor: pointer;
    padding: 5px;
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
    height: 40px;
    width: 320px;
    display: flex;
    align-items: center;
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

.img {
    width: 300px;
    height: 220px;
    background-color: pink;
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

.left-content-header,
.right-content-header {
    padding: 0 16px;
    font-weight: 700;
    font-size: 16px;
    height: 40px;
    line-height: 40px;
}

.left-content-body {
    padding-top: 20px;
}

.right-content-body {
    padding: 20px 10px 10px 10px;
    height: calc(100% - 40px);
}

.red-xing {
    color: red;
    margin-right: 1px;
}

.task-region-select .el-cascader-menu__wrap {
    height: 304px !important;
}

.task-region-select .el-cascader-node {
    padding: 0 0 0 10px;
}

.task-region-select .el-cascader-menu:last-child .el-cascader-node {
    padding-right: 0px;
}

.task-region-select .el-cascader-menu {
    min-width: 140px;
}

.title {
    font-weight: 700;
    font-size: 16px;
}

.back-btn {
    float: right;
    font-size: 18px;
    font-weight: bold;
}

::v-deep .el-form-item__label {
    min-width: 80px !important;
    white-space: nowrap !important;
    text-align: right;
}

/* 亮色主题 */
.theme-light {
    .border {
        border-right: 1px solid #dcdfe6;
    }

    .dbox {
        border-bottom: 1px solid #dcdfe6;
    }

    .upload-item .big,
    .upload-item .small {
        color: #303133;
    }

    .action-item1 {
        color: #909399;
    }

    .action-item1:hover {
        color: #409eff;
    }

    .back-btn {
        color: #606266;
    }

    .back-btn i:hover {
        color: #409eff;
    }

    ::v-deep .el-form-item__label {
        color: #606266 !important;
    }

    ::v-deep .el-input.is-disabled .el-input__inner {
        color: #909399 !important;
        background-color: #f5f7fa !important;
        border-color: #e4e7ed !important;
    }
}

/* 暗色主题 */
.theme-dark {
    .border {
        border-right: 1px solid #0a579e;
    }

    .dbox {
        border-bottom: 1px solid rgba(255, 255, 255, 0.2);
    }

    .upload-item .big,
    .upload-item .small {
        color: #fff;
    }

    .action-item1 {
        color: #ccc;
    }

    .action-item1:hover {
        color: #fff;
    }

    .back-btn {
        color: #cbd5e0;
    }

    .back-btn i:hover {
        color: #fff;
    }

    ::v-deep .el-input.is-disabled .el-input__inner {
        color: rgba(217, 217, 217, 0.74) !important;
        background-color: rgba(191, 191, 191, 0.1) !important;
        border: rgba(191, 191, 191, 0.1) 1px solid !important;
    }

    ::v-deep .el-form-item__label {
        color: #fff !important;
    }
}
</style>
