<template>
    <div class="se-content-right-body">
        <div class="right-content-header">
            <span class="icon iconfont icon-changjing"></span>
            <span class="title">场景管理</span>
        </div>
        <div class="right-content-body">
            <div class="se-filter-form">
                <div class="se-filter-item">
                    <span class="se-filter-label">场景名称:</span>
                    <el-input type="text" placeholder="请输入场景名称" size="mini" clearable v-model="filterInfo.keyword"></el-input>
                </div>
                <div>
                    <el-button type="primary" size="mini" @click="searchScene">查询</el-button>
                    <el-button type="info" size="mini" @click="resetFilter">重置</el-button>
                    <el-button type="danger" size="mini" @click="deleteSceneData">删除</el-button>
                    <!-- 新增场景按钮 -->
                    <el-button type="primary" size="mini" @click="openAddDialog">新增场景</el-button>
                </div>
            </div>
            <div class="se-data-table">
                <!--场景数据-->
                <el-table
                    max-height="100%"
                    height="100%"
                    :data="sceneData"
                    stripe
                    style="width: 100%"
                    border
                    @selection-change="handleSelectionChange">
                    <el-table-column type="selection" width="55" align="center"></el-table-column>
                    <el-table-column type="index" label="序号" width="80"></el-table-column>
                    <el-table-column prop="sceneName" label="场景名称" align="center" width="200"></el-table-column>
                    <el-table-column prop="labels" label="标签类别" align="center"></el-table-column>
                    <el-table-column prop="operator" label="添加人员" align="center" width="120"></el-table-column>
                    <el-table-column prop="createTime" label="添加时间" align="center" width="200"></el-table-column>
                    <el-table-column label="操作" width="100px" align="center">
                        <template slot-scope="scope">
                            <!-- 修改按钮 -->
                            <el-button type="text" size="mini" style="color: blue" @click="handleEdit(scope.row)">编辑</el-button>
                        </template>
                    </el-table-column>
                </el-table>
            </div>
            <el-pagination
                background
                small
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
        <!-- 原有：编辑弹窗 -->
        <el-dialog :visible.sync="editShow" width="400px" class="edit-dialog" title="场景编辑" :modal-append-to-body="false">
            <el-form :model="editForm" ref="form">
                <el-form-item label="场景名称:">
                    <el-input v-model="editForm.sceneName" placeholder="请输入" clearable disabled></el-input>
                </el-form-item>
                <el-form-item label="标签类别:">
                    <el-select v-model="editForm.labels" placeholder="请选择" multiple clearable>
                        <el-option v-for="item in labelsCollection" :label="item.name" :value="item.value"></el-option>
                    </el-select>
                </el-form-item>
                <el-form-item>
                    <el-button type="primary" size="mini" @click="saveEditData">保存</el-button>
                    <el-button size="mini" @click="editShow = false">取消</el-button>
                </el-form-item>
            </el-form>
        </el-dialog>
        <!-- 新增：新增场景弹窗 -->
        <el-dialog
            title="新增场景"
            width="500px"
            :visible.sync="addDialogVisible"
            append-to-body
            close-on-click-modal="false"
            @closed="resetAddDialog">
            <SceneAddDialog @success="handleAddSuccess" />
        </el-dialog>
    </div>
</template>

<script>
import { deleteSceneByIdApi, editSceneData, getEnumOptionApi, getSceneData } from '@/api/commonApi';
// 引入新增弹窗组件
import SceneAddDialog from './AddScene.vue';

export default {
    name: 'sceneManagementIndex',
    components: { SceneAddDialog }, // 注册新增组件
    data() {
        return {
            addDialogVisible: false, // 新增弹窗显示/隐藏
            editForm: {
                sceneId: '',
                sceneName: '',
                labels: [],
                operator: '',
                createTime: ''
            }, //编辑表单
            editShow: false, //编辑弹窗
            selectedScene: [], //选择的场景数据列表
            labelsCollection: [],
            filterInfo: {
                keyword: '',
                limit: 10,
                page: 1
            }, //筛选参数
            sceneData: [], //场景数据
            dataCount: 0, //数据的总数
            baseUrl: process.env.VUE_APP_API_URL //请求地址
        };
    },
    methods: {
        async saveEditData() {
            //保存编辑场景数据
            this.editForm.id = this.editForm.sceneId;
            this.editForm.labels = JSON.stringify(this.editForm.labels);
            const res = await editSceneData(this.editForm);
            this.editShow = false;
            if (res.code !== 0) {
                this.$message.error(res.msg);
                return;
            }
            this.$message.success('编辑成功');
            await this.getSceneList();
        },
        handleEdit(row) {
            //点击编辑
            this.editForm.sceneId = row.sceneId;
            this.editForm.sceneName = row.sceneName;
            this.editForm.labels = JSON.parse(row.labels.replace(/'/g, '"'));
            this.editForm.operator = row.operator;
            this.editForm.createTime = row.createTime;
            this.editShow = true;
        },
        handleSizeChange(val) {
            // 改变每页展示的数据
            this.filterInfo.limit = val;
            this.filterInfo.page = 1;
            this.getSceneList();
        },
        handleCurrentChange(val) {
            // 改变页码
            this.filterInfo.page = val;
            this.getSceneList();
        },
        async getSceneList() {
            //  获取场景数据
            const res = await getSceneData(this.filterInfo);
            if (res.code !== 0) {
                this.$message.error(res.msg);
                return;
            }
            this.dataCount = res.count;
            this.sceneData = res.data;
        },
        resetFilter() {
            //重置筛选框
            this.filterInfo.keyword = '';
            this.filterInfo.page = 1;
            this.getSceneList();
        },
        searchScene() {
            //搜索数据
            this.filterInfo.page = 1;
            this.getSceneList();
        },
        deleteSceneData() {
            //删除选择的数据
            if (this.selectedScene.length === 0) {
                this.$message.warning('请选择要删除的数据');
                return;
            }
            const params = { ids: this.selectedScene };
            this.$confirm('此操作将永久删除场景数据, 是否继续?', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            })
                .then(async () => {
                    const res = await deleteSceneByIdApi(params);
                    if (res.code === 0) {
                        this.$message.success('场景删除成功！');
                        this.filterInfo.page = 1;
                        await this.getSceneList();
                    } else {
                        this.$message.error(res.msg);
                    }
                })
                .catch(() => {
                    this.$message({ type: 'info', message: '已取消删除' });
                });
        },
        handleSelectionChange(val) {
            //选择的场景数据
            this.selectedScene = val.map((item) => item.sceneId);
        },
        async handleGetLabels() {
            const res = await getEnumOptionApi('Class_Name');
            if (res.code === 0) {
                this.labelsCollection = res.data.Class_Name;
            }
        },
        // 打开新增弹窗
        openAddDialog() {
            this.addDialogVisible = true;
        },
        // 新增成功回调：关闭弹窗+刷新表格+提示成功
        handleAddSuccess() {
            this.addDialogVisible = false;
            this.$message.success('新增场景成功');
            this.filterInfo.page = 1;
            this.getSceneList();
        },
        // 弹窗关闭后重置状态
        resetAddDialog() {
            this.addDialogVisible = false;
        }
    },
    created() {
        this.getSceneList();
        this.handleGetLabels();
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

.edit-dialog .el-form-item {
    display: flex;
    justify-content: center;
}

::v-deep .edit-dialog .el-form-item__label {
    color: black !important;
}

::v-deep .edit-dialog .el-input__inner {
    color: black !important;
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

.se-filter-form {
    display: flex;
    gap: 10px;
    align-items: center;
}
.se-filter-item {
    display: flex;
}

.el-pagination {
    bottom: 10px;
    right: 30px;
    margin-right: 0px;
    float: right;
    position: fixed;
}
</style>
