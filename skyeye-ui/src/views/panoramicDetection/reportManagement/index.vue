<template>
    <div class="se-container">
        <div class="se-left-content">
            <div class="left-content-header">
                <span class="icon iconfont icon-xinzengtianjia"></span>
                <span class="title">导出批次报告</span>
            </div>
            <div class="left-content-body">
                <el-form :inline="true" size="small" :model="form" ref="form" :rules="rules">
                    <el-form-item label="场景名称:" label-width="100px" prop="sceneIds">
                        <el-select v-model="form.sceneIds" placeholder="请选择" clearable multiple>
                            <el-option v-for="item in sceneCollection" :key="item.value" :label="item.name" :value="item.value"></el-option>
                        </el-select>
                    </el-form-item>
                    <el-form-item label="批次编号:" label-width="100px" prop="batchId">
                        <el-select v-model="form.batchId" placeholder="请选择" clearable>
                            <el-option-group v-for="group in batchCollection" :key="group.name" :label="group.name">
                                <el-option
                                    v-for="item in group.value"
                                    :key="item.batch_id"
                                    :label="item.batch_name"
                                    :value="item.batch_id"></el-option>
                            </el-option-group>
                        </el-select>
                    </el-form-item>
                    <el-form-item label="报告划分:" label-width="100px" prop="division">
                        <el-select v-model="form.division" placeholder="请选择" clearable>
                            <el-option v-for="item in divisionCollection" :key="item.name" :label="item.name" :value="item.value"></el-option>
                        </el-select>
                    </el-form-item>
                    <el-form-item label="操作用户:" label-width="100px">
                        <el-input v-model="form.addPerson" disabled></el-input>
                    </el-form-item>
                    <el-form-item class="button-container">
                        <el-button size="mini" type="primary" @click="submitForm('form')">生成批次报告</el-button>
                        <el-button size="mini" type="info" @click="resetForm">重置</el-button>
                    </el-form-item>
                </el-form>
            </div>
        </div>
        <div class="se-right-content">
            <div class="right-content-header">
                <span class="icon iconfont icon-baogaoguanli"></span>
                <span class="title">批次报告管理</span>
            </div>
            <div class="right-content-body">
                <div class="se-filter-form">
                    <!--数据筛选-->
                    <el-form :inline="true" size="small" :model="filterInfo" ref="filterInfo" :rules="rules">
                        <el-form-item>
                            <span>场景名称：</span>
                            <el-select placeholder="请选择" v-model="filterInfo.sceneId" clearable>
                                <el-option v-for="item in sceneCollection" :key="item.value" :label="item.name" :value="item.value"></el-option>
                            </el-select>
                        </el-form-item>
                        <el-form-item>
                            <el-input type="text" placeholder="请输入批次编号" clearable v-model="filterInfo.batchId"></el-input>
                        </el-form-item>
                        <el-form-item>
                            <el-button type="primary" size="mini" @click="searchReport">查询</el-button>
                            <el-button type="info" size="mini" @click="resetFilter">重置</el-button>
                            <el-button type="danger" size="mini" @click="deleteReportData">删除</el-button>
                        </el-form-item>
                    </el-form>
                </div>
                <div class="report-cards">
                    <!--报告数据-->
                    <div class="content-card" v-for="item in reportData" :key="item.id">
                        <a-checkbox @change="onChange($event, item.id)"></a-checkbox>
                        <div @click="reportDownload(item)">
                            <img src="@/assets/images/tupian-renwuzx-6.png" />
                            <img src="@/assets/images/icon-new.png" class="newest" v-if="item.id === latest_task_id" />
                            <h3>{{ item.batch_name }}</h3>
                            <p class="service-type">场景名称：{{ item.scene_name }}</p>
                            <p class="region">批次编号：{{ item.batch_id }}</p>
                            <p class="count">报告数量：{{ item.count }}</p>
                            <div class="service-content">
                                <div class="content-item">
                                    <div class="ai-banner-title">
                                        <div></div>
                                        <p>生成时间</p>
                                    </div>
                                    <p>{{ item.create_time }}</p>
                                </div>
                                <div class="content-item">
                                    <div class="ai-banner-title">
                                        <div></div>
                                        <p>操作用户</p>
                                    </div>
                                    <p>{{ item.username }}</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <el-pagination
                    background
                    small
                    @size-change="handleSizeChange"
                    @current-change="handleCurrentChange"
                    :current-page="filterInfo.page"
                    :page-sizes="[12]"
                    :page-size="filterInfo.limit"
                    layout="total, sizes, prev, pager, next, jumper"
                    :total="dataCount">
                </el-pagination>
            </div>
        </div>
    </div>
</template>

<script>
import { addReportData, getBatchReportData, getReportOverview, deleteReportByIdApi, downloadReportData } from '@/api/commonApi';

export default {
    name: 'reportManagementIndex',
    data() {
        return {
            latest_task_id: 0,
            sceneCollection: [], //场景名称集合
            batchCollection: [], //批次编号集合
            selectedReport: [], //选择的报告数据列表
            divisionCollection: [
                { name: '村', value: 'village' },
                { name: '街道', value: 'street' }
            ], //报告区域划分集合
            form: {
                sceneIds: [],
                batchId: '',
                division: '',
                addPerson: localStorage.getItem('username')
            }, //上传表单
            filterInfo: {
                batchId: '',
                limit: 12,
                page: 1,
                sceneId: ''
            }, //筛选参数
            reportData: [], //报告数据
            dataCount: 0, //数据的总数
            baseUrl: process.env.VUE_APP_API_URL, //请求地址
            rules: {
                sceneIds: [{ required: true, message: '请选择场景名称', trigger: 'blur' }],
                batchId: [{ required: true, message: '请选择批次编号', trigger: 'blur' }],
                division: [{ required: true, message: '请选择报告划分', trigger: 'blur' }]
            }
        };
    },
    methods: {
        onChange(e, id) {
            //监听选中框，更新selectedReport
            if (e.target.checked) {
                this.selectedReport.push(id);
            } else {
                this.selectedReport = this.selectedReport.filter((item) => item !== id);
            }
        },
        reportDownload(item) {
            //下载报告
            this.$confirm('是否下载该报告?', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            })
                .then(async () => {
                    try {
                        const response = await downloadReportData(item.id);
                        // 创建一个临时的 Blob URL
                        const blobUrl = window.URL.createObjectURL(new Blob([response]));

                        // 创建一个 <a> 标签来触发下载
                        const link = document.createElement('a');
                        link.href = blobUrl;
                        if (item.count === 1) {
                            link.setAttribute('download', item.batch_id + '_' + item.scene_name + '.docx'); // 设置下载的文件名
                        } else {
                            link.setAttribute('download', item.batch_id + '_' + item.scene_name + '.zip'); // 设置下载的文件名
                        }
                        document.body.appendChild(link);
                        link.click();

                        // 清理
                        link.remove();
                        window.URL.revokeObjectURL(blobUrl); // 释放 Blob URL
                    } catch (error) {
                        console.log(error);
                        if (error.response && error.response.status === 404) {
                            this.$message.error('文件未找到');
                        } else {
                            this.$message.error('下载文件时发生错误');
                        }
                    }
                })
                .catch(() => {
                    this.$message({ type: 'info', message: '已取消下载' });
                });
        },
        //提交表单
        submitForm(formName) {
            this.$refs[formName].validate((valid) => {
                if (valid) {
                    this.addReport();
                } else {
                    console.log('error submit!!');
                    return false;
                }
            });
        },

        async addReport() {
            //添加报告
            if (this.form.sceneIds.length !== 0 && this.form.batchId) {
                this.$message.success('添加中，请稍等');
                const res = await addReportData(this.form);
                if (res.code !== 0) {
                    this.$message.error(res.msg);
                    return;
                }
                this.$message.success(res.msg);
                this.resetForm();
                this.filterInfo.page = 1;
                await this.getReportList();
            } else {
                this.$message.warning('请输入参数');
            }
        },
        async getReportOverview() {
            //获取场景和批次集合信息
            const res = await getReportOverview();
            if (res.code !== 0) {
                this.$message.error(res.msg);
                return;
            }
            this.sceneCollection = res.data.scene_list;
            this.batchCollection = res.data.batch_objs;
        },
        handleSizeChange(val) {
            // 改变每页展示的数据
            this.filterInfo.limit = val;
            this.filterInfo.page = 1;
            this.getReportList();
        },
        handleCurrentChange(val) {
            // 改变页码
            this.filterInfo.page = val;
            this.getReportList();
        },
        async getReportList() {
            //  获取报告数据
            const res = await getBatchReportData(this.filterInfo);
            if (res.code !== 0) {
                this.$message.error(res.msg);
                return;
            }
            this.reportData = res.data;
            this.dataCount = res.count;
        },

        resetForm() {
            //重置表单数据
            this.form.sceneIds = '';
            this.form.batchId = '';
            this.form.division = '';
        },
        resetFilter() {
            //重置筛选框
            this.filterInfo.batchId = '';
            this.filterInfo.page = 1;
            this.filterInfo.sceneId = '';
            this.getReportList();
        },
        searchReport() {
            //搜索数据
            this.filterInfo.page = 1;
            this.getReportList();
        },
        deleteReportData() {
            //删除选择的数据
            if (this.selectedReport.length === 0) {
                this.$message.warning('请选择要删除的数据');
                return;
            }
            const params = {
                ids: this.selectedReport
            };
            this.$confirm('此操作将永久删除报告数据, 是否继续?', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            })
                .then(async () => {
                    try {
                        const res = await deleteReportByIdApi(params);
                        if (res.code === 0) {
                            this.$message.success('报告删除成功！');
                            this.filterInfo.page = 1;
                            this.selectedReport = [];
                            await this.getReportList();
                        } else {
                            this.$message.error(res.msg);
                        }
                    } catch {
                        this.$message({ type: 'info', message: '删除失败' });
                    }
                })
                .catch(() => {
                    this.$message({ type: 'info', message: '已取消删除' });
                });
        }
    },
    async created() {
        await this.getReportOverview();
        await this.getReportList();
    },
    computed: {}
};
</script>

<style lang="scss" scoped>
.border {
    width: 10px;
    height: 100%;
}

.button-container {
    display: flex;
    justify-content: center;
}
.se-filter-form .el-form-item {
    margin: 0 30px 0 0;
}

.report-cards {
    height: calc(100% - 100px);
    width: 100%;
    overflow: auto;
}

.content-card {
    width: calc(25% - 16px);
    border: 1px solid #e9e9e9;
    position: relative;
    float: left;
    margin: 16px 16px 0 0;
    cursor: pointer;
    color: black;
}

.ant-checkbox-wrapper {
    position: absolute;
    left: 6px;
    top: 6px;
}

.content-card:hover {
    border: 1px solid #1890ff;
}

.content-card img {
    width: 100%;
    height: 130px;
}

.content-card h3 {
    font-weight: 700;
    font-size: 16px;
    position: absolute;
    left: 23px;
    top: 22px;
}

.content-card .service-type {
    position: absolute;
    left: 23px;
    top: 50px;
}

.content-card .region {
    position: absolute;
    left: 23px;
    top: 73px;
}
.content-card .count {
    position: absolute;
    left: 23px;
    top: 93px;
}
.content-card h3,
.content-card .region {
    text-overflow: ellipsis;
    overflow: hidden;
    white-space: nowrap;
    width: calc(100% - 40px);
    display: block;
    word-break: break-all;
    word-wrap: break-word;
}

.service-content {
    display: flex;
    height: 45px;
    margin: 16px 0;
}

.service-content .content-item {
    width: 50%;
    border-right: 1px solid #ededed;
    display: flex;
    align-items: center;
    flex-direction: column;
}

.content-item > p {
    margin-top: 3px;
}

.ai-banner-title {
    display: flex;
    align-items: center;
    justify-content: center;
}

.ai-banner-title div {
    width: 5px;
    height: 5px;
    background-color: #0077e8;
    margin-right: 4px;
}

.content-card .newest {
    width: 22%;
    height: 30px;
    position: absolute;
    top: 0;
    right: 0;
}

.icon {
    font-size: 24px;
    color: #42b4f2;
    padding-right: 5px;
}
.el-input {
    width: 190px;
}

.left-content-body {
    padding-top: 20px;
}

.right-content-body {
    padding: 20px 10px 10px 10px;
    height: calc(100% - 40px);
}
</style>
