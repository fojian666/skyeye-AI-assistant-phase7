<template>
    <div class="se-container">
        <div class="left-content">
            <div class="left-content-header">
                <span class="icon iconfont icon-xinzengtianjia"></span>
                <span class="title">新增解译任务</span>
            </div>
            <div class="left-content-body">
                <div class="left-form">
                    <div class="t_items">
                        <span slot="label" class="gt-main-label">项目名称：</span>
                        <el-input v-model="form.projectName" class="gt-main-form-item-select" placeholder="请输入项目名称"></el-input>
                    </div>
                    <div class="t_items">
                        <span slot="label" class="gt-main-label">检测方式：</span>
                        <el-select v-model="form.selectedDetecT" placeholder="请选择" clearable style="width: 220px">
                            <el-option v-for="item in detecTypesAll" :key="item.value" :label="item.label" :value="item.value"></el-option>
                        </el-select>
                    </div>
                    <div class="t_items" v-if="!isShowChange">
                        <span slot="label" class="gt-main-label">影像文件：</span>
                        <el-select v-model="form.inputPath" placeholder="请选择服务器文件" clearable style="width: 220px">
                            <el-option v-for="item in serverPaths" :key="item" :label="item" :value="item"></el-option>
                        </el-select>
                    </div>

                    <div class="t_items" v-if="isShowChange">
                        <span slot="label" class="gt-main-label">前景文件：</span>
                        <el-select v-model="form.inputPathPrev" placeholder="请选择服务器文件" clearable style="width: 220px">
                            <el-option v-for="item in serverPaths" :key="item" :label="item" :value="item"></el-option>
                        </el-select>
                    </div>
                    <div class="t_items" v-if="isShowChange">
                        <span slot="label" class="gt-main-label">后景文件：</span>
                        <el-select v-model="form.inputNextPath" placeholder="请选择服务器文件" clearable style="width: 220px">
                            <el-option v-for="item in serverPaths" :key="item" :label="item" :value="item"></el-option>
                        </el-select>
                    </div>
                    <div class="t_items">
                        <span slot="label" class="gt-main-label">保存名称：</span>
                        <el-input v-model="form.savedPath" style="width: 220px" placeholder="结果默认存在共享文件下result文件夹中"> </el-input>
                    </div>
                    <div class="t_items">
                        <span slot="label" class="gt-main-label"> 碎斑阈值： </span>
                        <el-input-number v-model="form.threshold" controls-position="right" :min="1" :max="150" :step="1" style="width: 220px">
                        </el-input-number>
                    </div>
                    <div class="t_items">
                        <span slot="label" class="gt-main-label"> 模型选择： </span>
                        <el-select v-model="form.selectedMoldelT" placeholder="请选择" clearable style="width: 220px">
                            <el-option v-for="item in filterModelTypes" :key="item.id" :label="item.model_type_name" :value="item.model_type_name">
                            </el-option>
                        </el-select>
                    </div>
                    <div class="t_items" style="justify-content: center">
                        <el-button type="info" class="gt-main-form-item-btn" size="mini" @click="resetForm">重置表单</el-button>
                        <el-button type="primary" @click="startDataVerify" size="mini" class="gt-main-form-item-btn">开始解译 </el-button>
                    </div>
                </div>
            </div>
        </div>
        <div class="border"></div>
        <div class="right-content">
            <div class="right-content-header">
                <span class="icon iconfont icon-geoai-list"></span>
                <span class="title">任务管理</span>
            </div>
            <div class="right-content-body">
                <div v-if="loading">加载模型中...</div>
                <staticTable v-else :modelTypes="modelTypes" :detectionTypeList="detecTypesAll" ref="staticTable"></staticTable>
            </div>
        </div>
        <verify
            title="验证窗口"
            :form="form"
            :resultPaths="resultPaths"
            v-if="openVerifyDialog"
            @closeDialog="openVerifyDialog = false"
            @continueTranslation="startTranslation" />
        <!-- 开始解译后显示过程组件 -->
    </div>
</template>

<script>
import { addInterpretationTaskApi, getModelListApi, getServerPathApi, getTableDataApi } from '@/api/commonApi';
import staticTable from '@/views/intelligent/interpretationTaskManagement/component/staticTable';
import verify from '@/views/intelligent/interpretationTaskManagement/component/verify';
import processing from '@/views/intelligent/interpretationTaskManagement/component/processing';

export default {
    name: 'Task',
    components: {
        staticTable,
        verify,
        processing
    },
    data() {
        return {
            form: {
                inputPath: '', //影像分割和批量检测的影像路径
                projectName: '', //项目名称
                savedPath: '', //保存路径
                threshold: '50', //碎斑阈值
                selectedDetecT: '', //检测类型
                selectedMoldelT: '', //表单中的模型类别
                inputPathPrev: '',
                inputNextPath: ''
            },
            serverPaths: [], //获取共享路径下额所有影像路径
            resultPaths: [], //获取共享路径下输出结果路径
            detecTypesAll: [
                {
                    label: '地类分割',
                    value: '地类分割'
                },
                {
                    label: '基于地类变化模型预测',
                    value: '基于地类变化模型预测'
                },
                {
                    label: '基于地类分割擦除预测',
                    value: '基于地类分割擦除预测'
                }
            ], //所有的检测类别
            modelTypes: [
                {
                    model_type_name: '道路',
                    model_path: 'E:\\geo_ai_server\\c#_test_data\\models\\models\\DLinkNet_ResNet101_road_QH_2m_256_10k_230622.th',
                    network: 'DLinkNet',
                    model_type: '地类分割',
                    config_path: ''
                },
                {
                    model_type_name: '建设用地变化检测',
                    model_path: 'E:\\geo_ai_server\\c#_test_data\\models\\models/STANet_ResNet18_buildingCD_QH_2m_256_20k_230719_net_A',
                    network: 'STANet',
                    model_type: '地类变化',
                    config_path: ''
                }
            ], //模型类别
            showTable: false,
            translationStatus: [],
            isShowChange: false,
            openVerifyDialog: false,
            openDialog: false,
            loading: false
        };
    },
    computed: {
        //根据选择的检测类型筛选模型
        filterModelTypes() {
            if (this.modelTypes) {
                if (this.form.selectedDetecT === '基于地类变化模型预测') return this.modelTypes.filter((item) => item.model_type === '地类变化');
                else if (this.form.selectedDetecT === '') {
                    return [];
                } else {
                    return this.modelTypes.filter((item) => item.model_type === '地类分割');
                }
            } else {
                return [];
            }
        }
    },
    watch: {
        'form.selectedDetecT': function (newData, oldData) {
            this.isShowChange = newData === '基于地类变化模型预测' || newData === '基于地类分割擦除预测';
        }
    },
    created() {
        this.GetImagesPaths();
        this.GetModelTypes();
    },
    mounted() {},
    methods: {
        //初始化表单
        resetForm() {
            this.form = {
                inputPath: '', //影像分割和批量检测的影像路径
                projectName: '', //项目名称
                savedPath: '', //保存路径
                threshold: '50', //碎斑阈值
                selectedDetecT: '', //检测类型
                selectedMoldelT: '', //表单中的模型类别
                inputPathPrev: '',
                inputNextPath: ''
            };
        },
        //获取共享路径下所有的影像路径
        async GetImagesPaths() {
            const res = await getServerPathApi();
            if (res.code == 0) {
                this.serverPaths = res.data.paths;
                this.resultPaths = res.data.result_path;
            } else {
                this.$message.error(res.msg);
            }
        },
        //获取所有检测模型
        async GetModelTypes() {
            const res = await getModelListApi();
            if (res.code == 0) {
                this.modelTypes = res.data;
            } else {
                this.$message.error(res.msg);
            }
            this.loading = false;
        },
        startDataVerify() {
            this.openVerifyDialog = true;
        },
        async startTranslation(taskIsEmpty) {
            // 验证上传文件格式是否正确，影像分割和变化检测文件输入为tif或tiff
            this.openVerifyDialog = false;
            const selectModelObj = this.modelTypes.find((model) => model.model_type_name === this.form.selectedMoldelT) || null;
            if (!selectModelObj) {
                return this.$message.error('未找到模型');
            }
            const paras = {
                taskName: this.form.projectName,
                taskType: this.form.selectedDetecT === '基于地类分割擦除' ? '地类变化' : selectModelObj.model_type,
                detectionType: this.form.selectedDetecT,
                modelName: this.form.selectedMoldelT,
                modelPath: selectModelObj.model_path,
                modelNetwork: selectModelObj.network,
                fragment: this.form.threshold,
                inputPath: this.form.inputPath,
                inputPathPrev: this.form.inputPathPrev,
                inputPathNext: this.form.inputNextPath,
                outputPath: this.form.savedPath,
                configPath: selectModelObj.config_path
            };
            const res = await addInterpretationTaskApi(paras);
            if (res.code === 0) {
                this.$message.success(res.msg);
                this.$refs.staticTable.getTableData();
            } else {
                this.$message.error(res.msg);
            }
        },
        // 关闭解译过程文件
        closeDialog() {
            this.openDialog = false;
        },
        emptyRedis() {
            this.$confirm('此操作将清空所有Redis任务，是否继续', '提示', {
                type: 'warning',
                confirmButtonText: '确定',
                cancelButtonText: '取消'
            })
                .then(() => {
                    axios
                        .post(config.BASE_URL + 'apps/emptyRedis')
                        .then((response) => {
                            this.$message.success('Redis任务已清空!!!');
                        })
                        .catch((error) => {
                            this.$message.error('清空Redis任务失败!!!', error);
                        });
                })
                .catch((error) => {
                    this.$message('取消清除成功!!!!');
                });
        }
    }
};
</script>

<style lang="scss" scoped>
.se-container {
    @import '@/assets/css/table/new-common';
}

.se-container {
    height: 100%;
    position: relative;
    color: white;
}

.left-content {
    width: 320px;
    height: 100%;
    border-radius: 2px;
    background-color: #00092d;
    box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.5);
}

.right-content {
    width: calc(100% - 325px);
    height: 100%;
    flex-direction: column;
    border-radius: 2px;
    background-color: #00092d;
    box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.5);
}

.border {
    width: 3px;
    height: 100%;
    border-right: 1px solid #fff;
    background-color: #fff;
}

table {
    width: 100%;
}

.left-form {
    margin-left: 5%;
    width: 94%;
    height: 80%;
}

.t_items {
    display: flex;
    padding-top: 20px;
    align-items: center; /* 垂直居中 */
}

.gt-main-form-item {
    display: flex;
    padding-top: 10px;
    align-items: center; /* 垂直居中 */
}

.page {
    position: absolute; //绝对定位
    right: 20px;
    bottom: 20px;
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

.el-button {
    margin-right: 2px; /* 给按钮之间添加一些间隔 */
}

/* 确保这些样式只在 .right-content 类下生效 */
.right-content .el-cascader,
.right-content .el-select,
.right-content .el-input {
    width: 100%; /* 设置宽度为100% */
}

.action-list {
    list-style: none; /* 移除列表前的默认项目符号 */
    padding: 0; /* 移除默认的内边距 */
    margin: 0; /* 移除默认的外边距 */
    display: flex;
}

.el-pagination {
    bottom: 10px;
    right: 30px;
    margin-right: 0px;
    float: right;
    position: fixed;
}

.icon {
    font-size: 24px;
    color: #42b4f2;
    padding-right: 5px;
}

.left-content-header,
.right-content-header {
    padding: 0 16px;
    border-bottom: 1px solid #dcdcdc;
    color: white;
    font-weight: 700;
    font-size: 16px;
    height: 40px;
    line-height: 40px;
}

.right-content-body {
    padding: 10px 10px 10px 10px;
    height: calc(100% - 40px);
}

::v-deep .el-input-number__decrease {
    background: #0b1a39;
    color: #fff;
    border: 1px solid #177de4;
}
::v-deep .el-input-number__increase {
    background: #0b1a39;
    color: #fff;
}
::v-deep .el-input-number.is-controls-right .el-input-number__increase {
    border-radius: 0 4px 0 0;
    border-bottom: 1px solid #177de4;
    border-right: 1px solid #177de4;
}
::v-deep .el-input-number.is-controls-right .el-input-number__decrease {
    border-left: 1px solid #177de4;
    border-right: 1px solid #177de4;
}
::v-deep .el-input-number__increase {
    border-left: 1px solid #177de4;
}
</style>
