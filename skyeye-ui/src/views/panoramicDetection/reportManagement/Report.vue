<template>
    <div class="se-container">
        <div class="left-content">
            <div class="left-content-header">
                <span class="icon iconfont icon-xinzengtianjia"></span>
                <span class="title">导出报告</span>
            </div>
            <div class="left-content-body">
                <el-form :inline="true" size="small" :model="form" ref="form">
                    <el-form-item label="场景名称:" label-width="80px">
                        <el-select v-model="form.scene_ids" placeholder="请选择" clearable multiple>
                            <el-option v-for="item in sceneCollection" :key="item.value" :label="item.name"
                                       :value="item.value"></el-option>
                        </el-select>
                    </el-form-item>
                    <el-form-item label="批次编号:" label-width="80px">
                        <el-select v-model="form.batch_id" placeholder="请选择" clearable>
                            <el-option-group v-for="group in batchCollection" :key="group.name" :label="group.name">
                                <el-option v-for="item in group.value" :key="item.batch_id" :label="item.batch_name"
                                           :value="item.batch_id"></el-option>
                            </el-option-group>
                        </el-select>
                    </el-form-item>
                    <el-form-item label="操作用户:" label-width="80px">
                        <el-input v-model="form.addPerson" disabled></el-input>
                    </el-form-item>
                    <el-form-item class="button-container">
                        <el-button type="primary" size="mini" @click="addReport">添加报告</el-button>
                        <el-button size="mini" @click="resetForm">重置</el-button>
                    </el-form-item>
                </el-form>
            </div>
        </div>
        <div class="right-content">
            <div class="right-content-header">
                <span class="icon iconfont icon-baogaoguanli"></span>
                <span class="title">报告管理</span>
            </div>
            <div class="right-content-body">
                <div class="filter">
                    <!--数据筛选-->
                    <el-form :inline="true" size="small" :model="filterInfo" ref="filterInfo">
                        <el-form-item>
                            <span>场景名称：</span>
                            <el-select placeholder="请选择" v-model="filterInfo.scene_id" clearable>
                                <el-option v-for="item in sceneCollection" :key="item.value" :label="item.name"
                                           :value="item.value"></el-option>
                            </el-select>
                        </el-form-item>
                        <el-form-item>
                            <el-input type="text" placeholder="请输入批次编号" clearable
                                      v-model="filterInfo.keyword"></el-input>
                        </el-form-item>
                        <el-form-item>
                            <el-button type="primary" size="mini" @click="searchReport">查询</el-button>
                            <el-button size="mini" @click="resetFilter">重置</el-button>
                            <el-button size="mini" @click="deleteReportData">删除</el-button>
                        </el-form-item>
                    </el-form>
                </div>
                <div class="report-cards">
                    <!--报告数据-->
                    <div class="content-card" v-for="item in reportData" :key="item.report_id">
                        <a-checkbox @change="onChange($event, item.report_id)"></a-checkbox>
                        <div @click="reportDownload(item)">
                            <img src="@/assets/images/tupian-renwu1.png"/>
                            <img src="@/assets/images/icon-new.png" class="newest"
                                 v-if="item.report_id === latest_task_id"/>
                            <h3>{{ item.report_name }}</h3>
                            <p class="service-type">场景名称：{{ item.scene_name }}</p>
                            <p class="region">批次编号：{{ item.batch_id }}</p>
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
                                        <p>网格员</p>
                                    </div>
                                    <p>{{ item.grid_operator }}</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="page">
                    <!--分页设置-->
                    <el-pagination
                            background
                            small
                            @size-change="handleSizeChange"
                            @current-change="handleCurrentChange"
                            :current-page="filterInfo.page"
                            :page-sizes="[12]"
                            :page-size="filterInfo.limit"
                            layout="total, sizes, prev, pager, next, jumper"
                            :total="dataCount"
                    >
                    </el-pagination>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
    import {addReportData, getBatchReportData, getReportOverview, deleteReportByIdApi} from '@/api/commonApi';

    export default {
        name: 'reportManagementIndex',
        data() {
            return {
                latest_task_id: 0,
                sceneCollection: [],//场景名称集合
                batchCollection: [],//批次编号集合
                selectedReport: [],//选择的报告数据列表
                form: {
                    scene_ids: [],
                    batch_id: '',
                    addPerson: localStorage.getItem('username'),
                }, //上传表单
                filterInfo: {
                    keyword: '',
                    limit: 12,
                    page: 1,
                    scene_id: '',
                }, //筛选参数
                reportData: [], //报告数据
                dataCount: 0, //数据的总数
                baseUrl: process.env.VUE_APP_API_URL,//请求地址
            };
        },
        methods: {
            onChange(e, id) {
                //监听选中框，更新selectedReport
                if (e.target.checked) {
                    this.selectedReport.push(id)
                } else {
                    this.selectedReport = this.selectedReport.filter((item) => item !== id)
                }
            },
            reportDownload(item) {
                //下载报告
                this.$confirm('是否下载该报告?', '提示', {
                    confirmButtonText: '确定',
                    cancelButtonText: '取消',
                    type: 'warning'
                }).then(() => {
                    try {
                        let url = `${this.baseUrl}/common/download/${item.file_id}`;
                        const link = document.createElement('a');
                        link.href = url;
                        document.body.appendChild(link);
                        link.click();
                        document.body.removeChild(link); // 移除临时链接
                    } catch (error) {
                        console.log(error)
                        if (error.response && error.response.status === 404) {
                            this.$message.error('文件未找到');
                        } else {
                            this.$message.error('下载文件时发生错误');
                        }
                    }
                }).catch(() => {
                    this.$message({type: 'info', message: '已取消下载'});
                });
            },
            async addReport() {
                //添加报告
                if (this.form.scene_ids.length !== 0 && this.form.batch_id) {
                    const res = await addReportData(this.form)
                    if (res.code !== 0) {
                        this.$message.error(res.msg)
                        return
                    }
                    this.resetForm()
                    this.filterInfo.page = 1
                    await this.getReportList()
                } else {
                    this.$message.warning('请输入参数')
                }
            },
            async getReportOverview() {
                //获取场景和批次集合信息
                const res = await getReportOverview()
                if (res.code !== 0) {
                    this.$message.error(res.msg)
                    return
                }
                this.sceneCollection = res.data.scene_list
                this.batchCollection = res.data.batch_objs
            },
            handleSizeChange(val) {
                // 改变每页展示的数据
                this.filterInfo.limit = val;
                this.filterInfo.page = 1
                this.getReportList();
            },
            handleCurrentChange(val) {
                // 改变页码
                this.filterInfo.page = val;
                this.getReportList();
            },
            async getReportList() {
                //  获取报告数据
                const res = await getReportData(this.filterInfo)
                if (res.code !== 0) {
                    this.$message.error(res.msg)
                    return
                }
                this.reportData = res.data
                this.dataCount = res.count
            },

            resetForm() {
                //重置表单数据
                this.form.scene_ids = ''
                this.form.batch_id = ''
            },
            resetFilter() {
                //重置筛选框
                this.filterInfo.keyword = '';
                this.filterInfo.page = 1;
                this.filterInfo.scene_id = ''
                this.getReportList()
            },
            searchReport() {
                //搜索数据
                this.filterInfo.page = 1;
                this.getReportList()
            },
            deleteReportData() {
                //删除选择的数据
                if (this.selectedReport.length === 0) {
                    this.$message.warning('请选择要删除的数据')
                    return
                }
                const params = {
                    ids: this.selectedReport
                }
                this.$confirm('此操作将永久删除报告数据, 是否继续?', '提示', {
                    confirmButtonText: '确定',
                    cancelButtonText: '取消',
                    type: 'warning'
                }).then(async () => {
                    try {
                        const res = await deleteReportByIdApi(params);
                        if (res.code === 0) {
                            this.$message.success("报告删除成功！")
                            this.filterInfo.page = 1
                            this.selectedReport = []
                            await this.getReportList()
                        } else {
                            this.$message.error(res.msg)
                        }
                    } catch {
                        this.$message({type: 'info', message: '删除失败'});
                    }
                }).catch(() => {
                    this.$message({type: 'info', message: '已取消删除'});
                });
            },
        },
        async created() {
            await this.getReportOverview()
            await this.getReportList();
        },
        computed: {},
    };
</script>

<style lang="scss" scoped>
  .se-container {
    padding: 10px;
    height: 100%;
    position: relative;
    background-color: #fff;
  }

  .left-content {
    width: 320px; //侧边栏设置
    height: 100%;
    border-radius: 2px;
    background-color: #fff;
    box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.5);
  }

  .border {
    width: 10px;
    height: 100%;
  }

  ::v-deep .el-form .el-input {
    width: 220px; //输入框设置
  }

  .button-container {
    display: flex;
    justify-content: center;
  }

  .right-content {
    width: calc(100% - 340px); //剩余宽度
    height: 100%;
    flex-direction: column;
    border-radius: 2px;
    background-color: #fff;
    box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.5);
  }

  .page {
    position: absolute; //绝对定位
    right: 20px;
    bottom: 20px;
  }

  .filter .el-form-item {
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
    top: 42px;
  }

  .content-card .service-type {
    position: absolute;
    left: 23px;
    top: 70px;
  }

  .content-card .region {
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

  .ai-banner-title p {
    font-weight: 700;
    color: #000;
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

  .left-content-header, .right-content-header {
    padding: 0 16px;
    border-bottom: 1px solid #dcdcdc;
    color: #000;
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
