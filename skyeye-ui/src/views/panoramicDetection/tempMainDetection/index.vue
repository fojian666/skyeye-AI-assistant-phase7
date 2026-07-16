<template>
    <div class="se-container">
        <!-- 上传数据   -->
        <div class="se-left-content">
            <div class="left-content-header">
                <span class="icon iconfont icon-xinzengtianjia"></span>
                <span class="title"><span>临时上传批次</span></span>
            </div>
            <div class="left-form">
                <div class="upload-item">
                    <div class="big">上传数据</div>
                    <div class="small">(上传前请检查图片质量)</div>
                </div>
                <div class="check-box">
                    <div class="number">
                        <span>批次编号：</span>
                        <el-input v-model="tempForm.batchId" style="width: 220px" disabled></el-input>
                    </div>
                    <div class="street">
                        <span>批次名称：</span>
                        <el-input v-model="tempForm.batchName" style="width: 220px" disabled></el-input>
                    </div>

                    <div class="file-upload">
                        <span>文件上传：</span>
                        <el-upload
                            class="upload-demo"
                            :action="fileUploadUrl"
                            :headers="headers"
                            accept=".zip"
                            :limit="1"
                            :file-list="fileList"
                            :on-success="getUploadFile"
                            :on-remove="handelRemoveFile">
                            <el-button size="small" type="primary">点击上传</el-button>
                        </el-upload>
                    </div>
                    <div class="upload-people">
                        <span>操作用户：</span>
                        <el-input v-model="uploadPeople" disabled placeholder="请输入姓名"></el-input>
                    </div>
                    <div class="street">
                        <span>资源选择：</span>
                        <el-select v-model="tempForm.resourceIdList" placeholder="请选择" style="width: 220px" multiple clearable>
                            <el-option v-for="item in resourceOptions" :key="item.id" :label="item.name" :value="item.id"> </el-option>
                        </el-select>
                    </div>

                    <div class="upload-button">
                        <el-button type="primary" @click="start_detection">开始检测</el-button>
                    </div>
                </div>
            </div>

            <!-- 上传管理 -->
        </div>
        <div class="se-right-content">
            <div class="right-content-header">
                <span class="icon iconfont icon-tupianshangchuanguanli"></span>
                <span class="title">临时批次全景上传管理</span>
            </div>
            <div class="right-content-body">
                <div class="se-filter-form">
                    <div class="se-filter-form-item">
                        <span class="se-filter-form-label">批次编号：</span>
                        <el-select v-model="batchSelect" placeholder="请选择" style="max-width: 200px" clearable>
                            <el-option v-for="item in batchOptions" :key="item" :label="item" :value="item"></el-option>
                        </el-select>
                    </div>
                    <div class="se-filter-form-item">
                        <span class="se-filter-form-label">网格编号：</span>
                        <el-select v-model="gridSelect" placeholder="请选择" style="max-width: 150px" clearable>
                            <el-option v-for="item in gridOptions" :key="item" :label="item" :value="item"></el-option>
                        </el-select>
                    </div>
                    <div class="se-filter-form-item">
                        <el-button type="primary" size="mini" @click="query()">查询</el-button>
                        <el-button type="info" size="mini" @click="reset()">重置</el-button>
                        <el-button type="danger" size="mini" @click="del()">删除</el-button>
                    </div>
                </div>

                <div class="se-data-table">
                    <el-table :data="projects" border @selection-change="handleSelectionChange" max-height="100%" height="100%">
                        <el-table-column type="selection" width="50" align="center"></el-table-column>
                        <el-table-column type="index" label="编号" width="80" align="center"></el-table-column>
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
                                    <li class="action-item" @click="handleView(scope.row)">查看</li>
                                    <li class="action-item1" @click="handleDownload(scope.row)" v-if="scope.row.status === 0">信息反馈</li>
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
    getAutoCreateBatchApi,
    getDownloadAnalysisInfoApi,
    getResourceListsApi,
    getUploadBatchData,
    getUploadProgress,
    tempAddUploadBatchApi
} from '@/api/commonApi';

export default {
    name: 'tempMainDetection',
    data() {
        return {
            activeRow: {}, //查看某一行表格数据
            intervalId: null, //定时器
            uploadProgress: 50, //上传进度
            uploadFileName: '', //上传的压缩包名称
            fileList: [],
            resourceOptions: [],
            uploadPeople: localStorage.getItem('username'),
            batchSelect: '', // 选择的批次
            gridSelect: '', // 选择的网格
            currentPage: 1,
            pageSize: 10,
            total: 0,
            selectedItems: [], //选中的记录
            projects: [],
            unzipPath: null,
            headers: { Authorization: 'Bearer ' + sessionStorage.getItem('token') || 'unknown' },
            tempForm: {
                batchId: '',
                batchName: '',
                resourceIdList: []
            }
        };
    },
    methods: {
        //处理跳转
        handleView(row) {
            // const uploadedCount= row.count
            // if (uploadedCount === 0) {
            //     this.$message.warning("该批次没有上传的线索,当前无法查看")
            // } else {
            //     const id = row.batch_id;
            //     this.$router.push({name: 'verifyClue', query: {id}})
            // }
            this.activeRow = true;
        },
        getStatus(percentage) {
            //设置进度条状态
            return percentage === 100 ? 'success' : null;
        },
        //获取资源数据
        async getResourceOptions() {
            let county = localStorage.getItem('county');
            let params = {
                county: county,
                serviceType: '资源调查数据',
                sourceType: '业务矢量数据服务'
            };
            const res = await getResourceListsApi(params);
            this.resourceOptions = res.data;
        },
        async getProgress() {
            //获取进度百分比
            const res = await getUploadProgress();
            this.projects.forEach((item) => {
                item.percent = Math.floor(res.data.filter((it) => it.upload_batch_id === item.id)[0].percent * 100);
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
                gridId: this.gridSelect,
                batchId: this.batchSelect,
                batchType: 1
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
        getUploadFile(res, file, fileList) {
            //上传成功后获取上传的文件名称
            this.uploadFileName = file.name;
            this.unzipPath = res.unzip_path;
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
            if (this.uploadFileName) {
                const form = {
                    fileName: this.uploadFileName,
                    batchId: this.tempForm.batchId,
                    operator: this.uploadPeople,
                    batchName: this.tempForm.batchName,
                    resourceIdList: this.resourceIdList,
                    unzipPath: this.unzipPath
                };
                const element = document.querySelector('.tmain');
                const loading = this.$loading({
                    target: element,
                    text: '正在进行全景检测，请稍后。。。',
                    background: 'rgba(0, 0, 0, 0.6)',
                    lock: true
                });
                try {
                    const res = await tempAddUploadBatchApi(form);
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
                this.tempForm.resourceIdList = [];
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
            //重置筛选参数
            this.batchSelect = '';
            this.gridSelect = '';
            this.currentPage = 1;
            this.getTableData();
        },
        query() {
            //筛选数据
            this.currentPage = 1;
            this.getTableData();
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
        async getAutoCreateBatchInfo() {
            const res = await getAutoCreateBatchApi();
            if (res.code === 0) {
                this.tempForm.batchId = res.data.batchId;
                this.tempForm.batchName = res.data.batchName;
            } else {
            }
        }
    },
    async mounted() {
        await this.getAutoCreateBatchInfo();
        this.getResourceOptions();
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
            return [...new Set(this.projects.map((item) => item.grid_id))]; //获取网格编号集合
        }
    },
    created() {
        this.getTableData();
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

.se-data-table {
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

.action-item:hover {
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
    background-color: #00092d;
    margin: 0 auto;
    text-align: center;
    line-height: 40px;
    color: #ccedfa;
    cursor: pointer;
}

.dbox {
    height: 40px;
    width: 320px;
    border-bottom: 1px solid #b4b2b2;
    font-size: 18px;
    font-weight: bold;
    display: grid;
    place-items: center; /* 水平和垂直居中 */
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
    text-align: right;
}

.check-box .number {
    margin-bottom: 20px;
}

.check-box .file-type {
    margin-bottom: 20px;
}

.check-box .file-upload {
    display: flex;
    align-items: center;
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
    background-color: pink;
    margin: 0 auto;
    text-align: center;
    line-height: 220px;
}

.upload-demo {
    max-width: 220px;
}

.icon {
    font-size: 24px;
    color: #177de4;
    padding-right: 5px;
}

.left-content-header,
.right-content-header {
    padding: 0 16px;
    border-bottom: 1px solid #dcdcdc;
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
</style>
