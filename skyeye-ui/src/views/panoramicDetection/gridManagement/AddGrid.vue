<template>
    <div class="add-container">
        <div class="left-content-body">
            <div class="grid-upload">
                <!--上传网格表单-->
                <el-form :inline="true" size="small" :model="form" ref="form" :rules="formRules">
                    <el-form-item label="上传网格:" label-width="100px" style="margin-bottom: 5px; display: flex" prop="gridFile">
                        <el-input type="text" placeholder="请上传网格压缩包" v-model="form.grid">
                            <template slot="append">
                                <el-button icon="el-icon-folder-opened" size="medium" @click="checkGridZip"></el-button>
                                <input type="file" id="gridZip" accept=".zip" style="display: none" @change="handleGridSelection" />
                            </template>
                        </el-input>
                        <div class="sample-data">
                            <span style="color: red">*</span>
                            <a :href="gridSampleUrl" download>示例网格数据</a>
                            <i
                                class="el-icon-question"
                                title="网格数据的属性需要包含[WGYNAME,ZXDX,ZXDY,WGNAME,JDNAME,JDID]"
                                style="padding-left: 6px; color: #fff"></i>
                        </div>
                    </el-form-item>
                    <el-form-item label="全景点位:" label-width="100px" style="margin-bottom: 5px; display: flex" prop="panoramicPointFile">
                        <el-input type="text" placeholder="请上传全景点压缩包" v-model="form.panoramicPoint">
                            <template slot="append">
                                <el-button icon="el-icon-folder-opened" size="medium" @click="checkPanoramaZip"></el-button>
                                <input type="file" id="panoramaZip" accept=".zip" style="display: none" @change="handlePanoramaSelection" />
                            </template>
                        </el-input>
                        <div class="sample-data">
                            <span style="color: red">*</span>
                            <a :href="pointSampleUrl" download>示例全景点数据</a>
                            <i
                                class="el-icon-question"
                                title="全景点数据的属性需要包含[PointX,PointY,WGNAME,JDNAME,JDID]"
                                style="padding-left: 6px; color: #fff"></i>
                        </div>
                    </el-form-item>
                    <el-form-item
                        ref="county"
                        class="spacing"
                        label="所属区县:"
                        prop="county"
                        label-width="100px"
                        style="margin-bottom: 20px; display: flex">
                        <el-select
                            v-model="form.county"
                            placeholder="请先输入行政区检索关键字"
                            filterable
                            remote
                            style="width: calc(100% - 100px)"
                            :remote-method="filterCounty"
                            @change="filterCounty">
                            <el-option
                                v-for="d in filterCountyData"
                                :key="d.value + '(' + d.key + ')'"
                                :label="d.value + '(' + d.key + ')'"
                                :value="d.value + '(' + d.key + ')'"
                                @blur="() => $refs.county.onFieldBlur()"></el-option>
                        </el-select>
                    </el-form-item>
                    <el-form-item label="操作用户:" label-width="100px" style="display: flex">
                        <el-input v-model="form.uploadPerson" disabled></el-input>
                    </el-form-item>
                    <el-form-item class="button-container">
                        <el-button type="primary" size="mini" @click="uploadGrid">上传网格</el-button>
                        <el-button type="info" size="mini" @click="resetForm">重置</el-button>
                    </el-form-item>
                </el-form>
            </div>
        </div>
        <!-- 上传进度弹窗 -->
        <el-dialog width="30%" :visible.sync="uploading" append-to-body title="上传中">
            <el-progress :text-inside="true" :stroke-width="18" :percentage="upProgress" status="success" style="margin-top: 10px"></el-progress>
        </el-dialog>
    </div>
</template>

<script>
import { uploadGridData, getRegionInfoListApi } from '@/api/commonApi';
export default {
    name: 'GridAddDialog',
    data() {
        return {
            gridSampleUrl: window.config.gridSampleUrl,
            pointSampleUrl: window.config.pointSampleUrl,
            formRules: {
                gridFile: [{ required: true, message: '请上传网格数据', trigger: ['blur', 'change'] }],
                panoramicPointFile: [{ required: true, message: '请上传全景点数据', trigger: ['blur', 'change'] }],
                county: [{ required: true, message: '请选择行政区', trigger: ['blur', 'change'] }]
            },
            upProgress: 0, //上传进度
            uploading: false, //上传进度表单控制
            filterCountyData: [],
            countyList: [],
            form: {
                grid: '',
                gridFile: '',
                panoramicPoint: '',
                panoramicPointFile: '',
                uploadPerson: '',
                county: ''
            } //上传表单
        };
    },
    methods: {
        //获取区域的级联数据
        async getRegionOptions() {
            const res = await getRegionInfoListApi();
            this.countyList = res.data;
        },
        // 行政区筛选
        filterCounty(value) {
            if (value === '') {
                this.$message.warning('行政区检索条件不能为空！', 3);
                this.filterCountyData = [];
                return;
            }
            let reg = new RegExp(value);
            let arr = [];
            for (let i = 0; i < this.countyList.length; i++) {
                if (reg.test(this.countyList[i].value)) {
                    arr.push(this.countyList[i]);
                }
            }
            this.filterCountyData = arr;
        },
        checkGridZip() {
            //网格标签点击事件
            document.querySelector('#gridZip').click();
        },
        checkPanoramaZip() {
            //全景点标签点击事件
            document.querySelector('#panoramaZip').click();
        },
        handleGridSelection(event) {
            //选择网格压缩包
            const selectedFile = event.target.files[0];
            if (selectedFile) {
                this.form.grid = selectedFile.name;
                this.form.gridFile = selectedFile;
            }
        },
        handlePanoramaSelection(event) {
            //选择全景点压缩包
            const selectedFile = event.target.files[0];
            if (selectedFile) {
                this.form.panoramicPoint = selectedFile.name;
                this.form.panoramicPointFile = selectedFile;
            }
        },
        resetForm() {
            //重置上传表单数据和input数据
            this.form.grid = '';
            this.form.gridFile = '';
            this.form.panoramicPoint = '';
            this.form.panoramicPointFile = '';
            this.form.county = '';
            document.getElementById('gridZip').value = '';
            document.getElementById('panoramaZip').value = '';
            this.$refs.form.resetFields(); // 重置表单校验状态
        },
        async uploadGrid() {
            //上传网格数据
            try {
                this.$refs.form.validate(async (valid) => {
                    if (!valid) return this.$message.warning('请完善必填项并校验通过');
                    if (!this.form.gridFile || !this.form.panoramicPointFile) {
                        return this.$message.warning('请填写数据信息');
                    }
                    let formData = new FormData();
                    formData.append('grid_shp', this.form.gridFile);
                    formData.append('panorama_shp', this.form.panoramicPointFile);
                    formData.append('county', this.form.county);
                    const loading = this.$loading({
                        lock: true,
                        text: '新增网格中',
                        spinner: 'el-icon-loading',
                        background: 'rgba(0, 0, 0, 0.7)'
                    });
                    const res = await uploadGridData(formData);
                    loading.close();
                    if (res.code === 0) {
                        this.resetForm();
                        // 核心：上传成功后向父组件发送事件，通知刷新表格
                        this.$emit('success');
                    } else {
                        this.$message.error(res.msg);
                    }
                });
            } catch (error) {
                this.$message.error('上传失败，请重试。');
            }
        }
    },
    created() {
        this.form.uploadPerson = localStorage.getItem('username'); //获取登录用户
        this.getRegionOptions();
    }
};
</script>

<style lang="scss" scoped>
.left-content-body {
    padding-top: 20px;
    color: #fff;
}
::v-deep .el-form-item {
    padding: 10px;
}
::v-deep .grid-upload .el-input {
    width: 400px;
}

.button-container {
    display: flex;
    justify-content: center;
    margin-top: 10px;
}

::v-deep .el-select .el-input__inner {
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid #11a8ed;
}

::v-deep .el-select-dropdown {
    background: #00092d;
    border: 1px solid #11a8ed;
}

::v-deep .el-select-dropdown__item {
    color: #fff;
}

::v-deep .el-select-dropdown__item:hover {
    background: #108ee9;
}

.sample-data a {
    color: #42b4f2;
    padding-left: 5px;
    cursor: pointer;
}
</style>
