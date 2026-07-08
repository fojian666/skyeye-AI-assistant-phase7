<template>
    <div class="se-container-component">
        <div class="t-query">
            <el-row :gutter='24' class="add">
                <el-col :span='4'>
                    <!-- 搜索检测方式 -->
                    <el-input v-model="searchParams.projectname" placeholder="请输入项目名称"
                              class="gt-query-item" clearable></el-input>
                </el-col>
                <el-col :span='4'>
                    <el-select v-model="searchParams.model" placeholder="请选择模型" clearable
                               class="gt-query-item">
                        <el-option v-for="item in modelTypes" :key="item.model_type_name" :label="item.model_type_name"
                                   :value="item.model_type_name"></el-option>
                    </el-select>
                </el-col>
                <el-col :span='4'><el-select v-model="searchParams.detection_type" placeholder="请选择检测方式" clearable
                               class="gt-query-item">
                        <el-option v-for="item in detectionTypeList" :key="item.value" :label="item.label"
                                   :value="item.value"></el-option>
                    </el-select>
                </el-col>
                <el-col :span='8'>
                    <el-button  type="primary" size="mini" @click="getTableData">查询</el-button>
                    <el-button type="info"  size="mini" @click="resetinput">重置</el-button>
                    <el-button type="danger" @click="batchdelete" size="mini">删除</el-button>
                </el-col>
            </el-row>
        </div>
        <div class="ttable">
            <el-table :data="projects" border
                      :default-sort="{prop: 'create_time', order: 'descending'}"
                      @selection-change="handleSelectionChange"
                      max-height="100%"
                      height="100%"
            >
                <el-table-column type="selection"></el-table-column>
                <el-table-column type="index" label="序号" width="70"></el-table-column>
<!--                <el-table-column prop="id" label="任务编号"></el-table-column>-->
                <el-table-column prop="taskName" label="任务名称"></el-table-column>
                <el-table-column prop="detectionType" label="检测方式"></el-table-column>
                <el-table-column prop="modelName" label="模型名称"></el-table-column>
                <el-table-column prop="status" label="任务状态">
                    <template slot-scope="scope">
                        {{handleStatusText(scope.row.status)}}
                    </template>
                </el-table-column>
                <el-table-column prop="fragment" label="碎斑阈值"></el-table-column>
                <el-table-column prop="createPerson" label="创建用户" width="140"></el-table-column>
<!--                <el-table-column prop="create_time" label="创建时间" sortable></el-table-column>-->
                <el-table-column prop="outputPath" label="输出路径" ></el-table-column>
                <el-table-column label="操作" width="250px">
                    <template slot-scope="scope">
                        <el-button type="text" size="mini"
                                   :disabled="viewbtnIsDisabled(scope.row)"
                                   @click="viewProjectProgress(scope.row)" >查看
                        </el-button>
                        <el-button  type="text" size="mini"
                                   @click="handledelete(scope.row.id)">删除
                        </el-button>
                        <el-button
                                :disabled="terminateIsDisabled(scope.row)"
                                type="text"
                                size="mini"
                                @click="terminateTask(scope.row)"
                        >终止
                        </el-button>
                        <el-button
                                :disabled="isAllowDownload(scope.row)"
                                type="text"
                                size="mini"
                                @click="downloadFiles(scope.row)"

                        >下载
                        </el-button>
                    </template>
                </el-table-column>
            </el-table>
        </div>
        <el-pagination
                background
                layout="total, sizes,  prev, pager, next, jumper"
                v-model="currentPage"
                class="pagination"
                :total="total"
                :page-size="pageSize"
                @size-change="handleSizeChange"
                @current-change="handleCurrentChange">
        </el-pagination>
        <processing title="测试窗口" v-if="openDialog" @closeDialog="closeDialog" ref="processDialog"/>
    </div>
</template>

<script >
import processing from "@/views/intelligent/interpretationTaskManagement/component/processing.vue";
import {
    batchDeleteInterpretationTaskApi, downloadFileApi, getDownloadAiResultApi, getDownloadPanoramaPointApi,
    getProcessStatusApi,
    getTableDataApi,
    JudgeClueApi,
    taskStopApi
} from "@/api/commonApi";
export default {
    name: 'index',
    props:{
        modelTypes: {type: Array, default: () => []},
        detectionTypeList: {type: Array, default: () => []},
    },
    components: {
        processing,
    },
    data() {
        return {
            searchParams: {
                model: "",
                detection_type: "",
                projectname: ''
            },
            projects: [],
            tasks: [],
            taskDialogVisible: false,
            model_name: null,
            currentPage: 1,
            pageSize: 10,
            total: 0,
            selectitems: [],
            is_received: '123',
            openDialog: false,//判断打开解译过程组件表单
            modelnameList: [],
        };
    },
    methods: {
        async getTableData() {
            const para = {
                "pageIndex":this.currentPage,
                "pageSize":this.pageSize,
                "taskName":this.searchParams.projectname,
                "modelName":this.searchParams.model,
                "detectionType":this.searchParams.detection_type

            }
            const res = await getTableDataApi(para)
            if (res.code == 0){
                this.projects = res.data;
                this.total = res.total;
            }
        },
        viewTasks(project) {
            this.$message.info("任务正在开发中，敬请期待");
        },
        handleSizeChange(val) {
            this.pageSize = val;
            this.getTableData();
        },
        handleCurrentChange(val) {
            this.currentPage = val;
            this.getTableData();
        },
        async downloadFiles(row) {
            try {
                // let url = `/lais/site/inspection/interpretation_task/download_result/${row.id}`;

                const response = await getDownloadAiResultApi(row.id);
                const url = window.URL.createObjectURL(new Blob([response]));

                const link = document.createElement('a');
                link.href = url;
                link.setAttribute('download', row.taskName + '.zip'); // 假设文件路径的最后一部分是文件名

                document.body.appendChild(link);
                link.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(link); // 移除临时链接
                this.$message.success("下载成功！");
            } catch (error) {
                console.error('下载失败:', error);
                // 尝试读取错误信息
                if (error.response?.data) {
                    const reader = new FileReader();
                    reader.onload = () => alert(reader.result);
                    reader.readAsText(error.response.data);
                }
            }
        },
        resetinput() {
            this.searchParams.model = '';
            this.searchParams.detection_type = '';
            this.searchParams.projectname = '';
            this.getTableData()
        },
        //获取选中的值
        handleSelectionChange(val) {
            this.selectitems = val.map((item) => item.id)
        },
        async batchdelete(id) {
            if (this.selectitems.length !== 0) {
                this.$confirm('确认删除记录吗？', '提示', {
                    type: 'warning',
                    confirmButtonText: '确定',
                    cancelButtonText: '取消'
                })
                    .then(
                        () => {
                            batchDeleteInterpretationTaskApi(this.selectitems.join(','))
                                .then((response) => {
                                    this.$message.success('批量删除成功！');
                                    this.getTableData();
                                })
                                .catch((error) => {
                                    console.error('Error deleting project:', error);
                                    this.$message.error('项目删除失败，请重试！');
                                })
                        }
                    )
                    .catch((error) => {
                        this.$message({
                            type: 'info',
                            message: '已取消删除'
                        })
                    })
            } else {
                this.$message.error('请选择要删除的项目！');
            }
        },
        terminateTask(rowrecord) {
            this.$confirm('确认终止该任务吗？', '提示', {
                type: 'warning',
                confirmButtonText: '确定',
                cancelButtonText: '取消'
            })
                .then(() => {
                    const task_id = rowrecord.id;
                    taskStopApi(task_id)
                        .then((res) => {
                            if (res.data.code == 0) {
                                if (res.data.tag) {
                                    this.$message.success("任务已终止")
                                } else {
                                    this.is_received = task_id
                                    this.$message.warning(res.data.message)
                                }
                                this.getTableData();
                            }
                        })
                        .catch((error) => {
                            this.$message.error(error)
                        })
                })
                .catch(() => {
                    this.$message({
                        type: 'info',
                        message: '已取消终止任务'
                    })
                })
        },
        // 判断按钮是否应该被禁用
        isDisabled(row, action) {
            // 根据动作类型检查状态
            const statusCheck = action === 'terminate';
            const statusCheckForProgress = action === 'progress' && row.status !== 'Running';
            // 返回是否禁用按钮
            return statusCheck || statusCheckForProgress;
        },

        async viewProjectProgress(row) {
            this.openDialog = true
            this.$nextTick(() => {
                setTimeout(()=>{
                    this.$refs.processDialog.init(row, row.detectionType);
                },3000)
            });

        },
        // 关闭解译过程文件
        closeDialog() {
            this.openDialog = false;
        },
        handleStatusText(status){
            switch (status) {
                case 0:
                    return '初始化';
                case 1:
                    return '进行中';
                case 2:
                    return '已完成';
                case 3:
                    return '报错';
                case 4:
                    return '终止';
            }
        },
        async handledelete(id){
            const res = await batchDeleteInterpretationTaskApi(id)
            if (res.code === 0) {
                this.$message.success('删除成功');
                this.getTableData()
            }else{
                this.$message.error('删除失败');
            }
        },
        viewbtnIsDisabled(row){
            if(row.status === 1){
                return false
            }else{
                return true
            }
        },
        terminateIsDisabled(row){
            if(row.status === 0){
                return false
            }else{
                return true
            }
        },
        isAllowDownload(row){
            if(row.status==2){
                return false
            }else{
                return true
            }
        }

    },
    mounted() {
        this.getTableData();
    },
    created() {

    }
}
</script>

<style lang="scss" scoped  >
.se-container-component{
    height: 100%;
    width: 100%;
}
.t-query {
    display: flex;
    flex-direction: row;
    align-items: center;
    margin-left: 10px;
    flex-wrap: nowrap; /* 禁止子元素换行 */
    margin-top: 10px;
}

.t-query-item {
    white-space: nowrap; /* 防止内容换行 */
    width: 27%;
}
.ttable {
    margin-left: 10px;
    margin-right: 10px;
    margin-top: 10px;
    height: calc(100% - 100px);
}
.t-query div {
    margin-right: 10px;
}
::v-deep .el-button--text {
    color: #40a9ff !important;
}
::v-deep .el-button--text.is-disabled {
    color: #c0c4ccb0 !important;
}

.gt-query-item{
    width: 150px;
}
.t-query div{
    margin-right: 30px;
}
</style>