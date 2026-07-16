<template>
    <div class="se-content-right-body">
        <div class="right-content-header">
            <span class="icon iconfont icon-geoai-grid"></span>
            <span class="title">不检测区域管理</span>
        </div>
        <div class="right-content-body">
            <div class="se-filter-form">
                <!--数据筛选-->
                <el-form :inline="true" size="medium" :model="filterInfo" ref="filterInfo">
                    <el-form-item label="任务编号:">
                        <el-input v-model="filterInfo.taskId" placeholder="请输入任务编号" class="custom-elinput-height" />
                    </el-form-item>
                    <el-form-item>
                        <el-button type="primary" size="mini" @click="getTaskList(filterInfo.taskId)">查询</el-button>
                        <el-button type="danger" size="mini" @click="deleteTask">删除</el-button>
                        <el-button type="info" size="mini" @click="resetTaskList">重置</el-button>
                        <!-- 新增按钮 -->
                        <el-button type="primary" size="mini" @click="openAddDialog">新增不检测区域</el-button>
                    </el-form-item>
                </el-form>
            </div>
            <div class="se-data-table">
                <!--网格数据-->
                <el-table
                    max-height="100%"
                    height="100%"
                    :data="taskData"
                    stripe
                    style="width: 100%"
                    border
                    @selection-change="handleSelectionChange"
                    v-loading="loading">
                    <el-table-column type="selection" width="55" align="center"></el-table-column>
                    <el-table-column
                        type="index"
                        label="序号"
                        align="center"
                        width="60"
                        :index="(index) => (filterInfo.page - 1) * filterInfo.limit + index + 1"></el-table-column>
                    <el-table-column prop="task_id" label="任务编号" align="center" width="240"></el-table-column>
                    <el-table-column prop="street" label="所属街道" align="center"></el-table-column>
                    <el-table-column prop="total_count" label="图斑总数" align="center"></el-table-column>
                    <el-table-column prop="create_person" label="上传人" align="center"></el-table-column>
                    <el-table-column prop="create_time" label="上传时间" align="center"></el-table-column>
                    <el-table-column label="操作" align="center">
                        <template slot-scope="scope">
                            <el-button type="text" size="mini" class="orange" @click="handleExportReport(scope.row)">导出</el-button>
                        </template>
                    </el-table-column>
                </el-table>
            </div>
            <!--分页设置-->
            <el-pagination
                background
                @size-change="handleSizeChange"
                @current-change="handleCurrentChange"
                :current-page="filterInfo.page"
                :page-sizes="[10, 20, 30, 40]"
                :page-size="filterInfo.limit"
                layout="total, sizes, prev, pager, next, jumper"
                :total="dataCount"
                style="margin-top: 15px; text-align: right">
            </el-pagination>
        </div>

        <!-- 新增不检测区域弹窗 -->
        <el-dialog
            title="新增不检测区域"
            width="500px"
            :visible.sync="addDialogVisible"
            append-to-body
            close-on-click-modal="false"
            @closed="resetAddDialog">
            <FrameAddDialog @success="handleAddSuccess" />
        </el-dialog>
    </div>
</template>

<script>
import { deleteTaskApi, patternVerifiTableApi } from '@/api/commonApi';
// 引入新增弹窗组件
import FrameAddDialog from './AddFrameArea.vue';

export default {
    name: 'FrameAreaIndex',
    components: { FrameAddDialog }, // 注册新增组件
    data() {
        return {
            addDialogVisible: false, // 新增弹窗显示/隐藏
            filterInfo: {
                keyword: '',
                dataRange: [],
                task_status: '',
                taskId: '',
                limit: 10,
                page: 1
            }, //筛选参数
            taskData: [],
            selectedTask: [],
            dataCount: 1,
            loading: false
        };
    },
    methods: {
        handleSizeChange(val) {
            // 改变每页展示的数据
            this.filterInfo.limit = val;
            this.filterInfo.page = 1;
            this.getTaskList(this.filterInfo.taskId);
        },
        handleCurrentChange(val) {
            this.loading = true;
            // 改变页码
            this.filterInfo.page = val;
            this.getTaskList(this.filterInfo.taskId);
            this.loading = false;
        },
        handleSelectionChange(val) {
            //选择的网格数据
            this.selectedTask = val.map((item) => item.id);
        },
        async getTaskList(taskId) {
            //  获取线索表格记录
            const para = {
                taskId: taskId,
                taskType: '1',
                pageSize: this.filterInfo.limit,
                pageIndex: this.filterInfo.page
            };
            const res = await patternVerifiTableApi(para);
            if (res.code !== 0) {
                this.$message.error('图斑核实任务数据获取失败！');
                return;
            } else {
                this.taskData = res.data;
                this.dataCount = res.total;
            }
        },
        async resetTaskList() {
            this.filterInfo.taskId = '';
            const para = {
                taskId: '',
                taskType: '1',
                pageSize: this.filterInfo.limit,
                pageIndex: this.filterInfo.page
            };
            const res = await patternVerifiTableApi(para);
            if (res.code !== 0) {
                this.$message.error(res.msg);
                return;
            } else {
                this.taskData = res.data;
                this.dataCount = res.count;
            }
        },
        //删除不检测区域
        deleteTask() {
            if (this.selectedTask.length === 0) return this.$message.warning('请选择要删除的数据');
            this.$confirm('是否确认任务,删除不可撤销?', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            })
                .then(async () => {
                    const res = await deleteTaskApi(JSON.stringify({ task_id_list: this.selectedTask }));
                    if (res.code === 0) {
                        this.$message.success(res.msg);
                        this.getTaskList(this.filterInfo.taskId);
                    } else {
                        this.$message.error(res.msg);
                    }
                })
                .catch(() => {
                    this.$message({
                        type: 'info',
                        message: '已取消删除'
                    });
                });
        },
        //导出
        async handleExportReport(row) {
            try {
                let url = `/lais/site/inspection/polygon-task/export_polygon?id=${row.id}`;
                const link = document.createElement('a');
                link.href = url;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link); // 移除临时链接
                this.$message.success('下载成功！');
            } catch (error) {
                if (error.response && error.response.status === 404) {
                    this.$message.error(error.response.error);
                } else {
                    this.$message.error('下载文件时发生错误');
                }
            }
        },
        // 打开新增弹窗
        openAddDialog() {
            this.addDialogVisible = true;
        },
        // 新增成功回调 - 关闭弹窗+刷新表格+提示成功
        handleAddSuccess() {
            this.addDialogVisible = false;
            this.$message.success('新增不检测区域成功');
            this.getTaskList(this.filterInfo.taskId);
        },
        // 弹窗关闭后重置状态
        resetAddDialog() {
            this.addDialogVisible = false;
        }
    },
    async mounted() {
        this.getTaskList(this.filterInfo.taskId);
    }
};
</script>

<style lang="scss" scoped>
.se-content-right-body {
    width: 100%;
    height: 100%;
    flex-direction: column;
    border-radius: 2px;
    box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.5);
    box-sizing: border-box;
}

.se-data-table {
    margin-top: 20px;
    flex-grow: 1;
    height: calc(100% - 100px);
}
.se-filter-form .el-form-item {
    margin: 0 30px 0 0;
}

.icon {
    font-size: 24px;
    color: #42b4f2;
    padding-right: 5px;
}

.right-content-body {
    padding: 10px;
    height: calc(100% - 60px);
}

.el-input-group {
    line-height: normal;
    display: inline-table;
    border-collapse: separate;
    border-spacing: 0;
}

.el-icon-folder-opened {
    color: white;
}

::v-deep .el-input--medium .el-input__inner {
    height: 32px;
    line-height: 32px;
}

.orange {
    color: #ff9500;
}
.el-pagination {
    bottom: 10px;
    right: 30px;
    margin-right: 0px;
    float: right;
    position: fixed;
}
</style>
