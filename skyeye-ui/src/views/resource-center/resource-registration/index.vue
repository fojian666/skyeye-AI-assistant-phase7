<template>
    <div class="resource-container">
        <!-- 面包屑导航 -->
        <div class="gt-breadcrumb-box">
            <i class="iconfont icon-geoai-manage"></i>
            <span class="gt-current-position">服务注册</span>
        </div>
        <div class="gt-breadcrumb-cnt">
            <div class="form-card">
                <div class="form-box-title">
                    <el-tabs v-model="activeKey" class="service-tabs" @tab-click="handleTabClick">
                        <el-tab-pane label="影像服务" name="影像服务" />
                        <el-tab-pane label="业务栅格数据服务" name="业务栅格数据服务" />
                        <el-tab-pane label="业务矢量数据服务" name="业务矢量数据服务" />
                    </el-tabs>
                </div>
                <div class="form-box-content">
                    <el-form ref="ruleForm" :model="form" :rules="rules" label-width="120px">
                        <el-form-item label="服务名称" prop="name" class="spacing">
                            <el-input
                                v-model="form.name"
                                placeholder='请输入服务名称，如"南京市_0.3m_2022年"' />
                        </el-form-item>

                        <el-form-item v-if="activeKey === '影像服务'" label="影像切片服务" prop="restUrl">
                            <el-input
                                v-model.trim="form.restUrl"
                                placeholder="请输入 REST 服务地址"
                                @change="onRestUrlChange" />
                        </el-form-item>
                        <el-form-item label="影像服务类别" prop="gisServiceType">
                            <el-select
                                v-model="form.gisServiceType"
                                placeholder="---请选择影像服务类别---"
                                popper-class="rc-light-popper"
                                style="width: 100%">
                                <el-option
                                    v-for="item in serverTypeList"
                                    :key="item.value"
                                    :label="item.label"
                                    :value="item.value" />
                            </el-select>
                        </el-form-item>
                        <el-form-item v-if="activeKey === '业务栅格数据服务'" label="业务切片服务" prop="restUrl">
                            <el-input
                                v-model.trim="form.restUrl"
                                placeholder="请输入 REST 服务地址"
                                @change="onRestUrlChange" />
                        </el-form-item>

                        <el-form-item v-if="activeKey === '业务矢量数据服务'" label="成果要素服务" prop="dataUrl">
                            <el-input
                                v-model.trim="form.dataUrl"
                                placeholder="请输入矢量服务地址"
                                @change="changeHandler" />
                        </el-form-item>
                        <el-form-item label="数据类型" class="spacing" prop="service_type">
                            <el-select
                                v-model="form.service_type"
                                placeholder="---请选择数据类型---"
                                popper-class="rc-light-popper"
                                style="width: 100%">
                                <el-option
                                    v-for="item in serviceType"
                                    :key="item.id"
                                    :label="item.value"
                                    :value="item.value" />
                            </el-select>
                        </el-form-item>
                        <el-form-item
                            v-if="activeKey === '业务矢量数据服务' || form.gisServiceType === '4'"
                            label="数据源名称"
                            class="spacing"
                            prop="datasource_name">
                            <el-select
                                v-model="form.datasource_name"
                                placeholder="请选择数据源"
                                popper-class="rc-light-popper"
                                style="width: 100%"
                                @change="selectDatasource"
                                @focus="focusDatasource">
                                <el-option
                                    v-for="item in datasourceNames"
                                    :key="item.id"
                                    :label="item.value"
                                    :value="item.value" />
                            </el-select>
                        </el-form-item>

                        <el-form-item
                            v-if="activeKey === '业务矢量数据服务' || form.gisServiceType === '4'"
                            label="数据集名称"
                            class="spacing"
                            prop="datasets_name">
                            <el-select
                                v-model="form.datasets_name"
                                placeholder="请选择数据集"
                                popper-class="rc-light-popper"
                                style="width: 100%"
                                @focus="focusDatasetNames">
                                <el-option
                                    v-for="item in datasetNames"
                                    :key="item.id"
                                    :label="item.value"
                                    :value="item.value" />
                            </el-select>
                        </el-form-item>

                        <el-form-item
                            v-if="activeKey === '业务矢量数据服务' || activeKey === '业务栅格数据服务'"
                            label="服务主题"
                            class="spacing"
                            prop="data_type">
                            <el-select
                                v-model="form.data_type"
                                placeholder="请选择数据类别"
                                popper-class="rc-light-popper"
                                style="width: 100%">
                                <el-option
                                    v-for="item in options"
                                    :key="item.value"
                                    :label="item.label"
                                    :value="item.value" />
                            </el-select>
                        </el-form-item>

                        <template v-if="activeKey === '业务矢量数据服务'">
                            <el-form-item label="边线颜色" class="spacing" prop="polygonColor">
                                <ColorInputPicker v-model="form.polygonColor" />
                            </el-form-item>

                            <el-form-item label="线条粗细" class="spacing" prop="polygonWeight">
                                <div class="width-input-row">
                                    <el-input-number
                                        v-model="form.polygonWeight"
                                        :min="1"
                                        :max="20"
                                        :precision="0"
                                        style="width: 120px" />
                                    <span class="unit-suffix">px</span>
                                </div>
                            </el-form-item>

                            <el-form-item label="图层透明度" class="spacing" prop="polygonOpacity">
                                <div class="opacity-row">
                                    <el-slider v-model="form.polygonOpacity" :min="0" :max="100" :step="1" />
                                    <span class="opacity-value">{{ form.polygonOpacity }}%</span>
                                </div>
                            </el-form-item>
                        </template>

                        <el-form-item class="spacing" label="行政区名称" prop="county">
                            <el-select
                                v-model="form.county"
                                filterable
                                remote
                                reserve-keyword
                                clearable
                                placeholder="请先输入行政区检索关键字"
                                popper-class="rc-light-popper"
                                style="width: 100%"
                                :remote-method="filterCounty">
                                <el-option
                                    v-for="d in filterCountyData"
                                    :key="d.key"
                                    :label="`${d.value}(${d.key})`"
                                    :value="`${d.value}(${d.key})`" />
                            </el-select>
                        </el-form-item>

                        <el-form-item label="服务时间" class="spacing" prop="append_time">
                            <el-date-picker
                                v-model="form.append_time"
                                type="month"
                                placeholder="请输入服务注册的时间"
                                value-format="yyyy-MM"
                                popper-class="rc-light-popper"
                                style="width: 100%" />
                        </el-form-item>

                        <el-form-item label="序号" class="spacing" prop="orderIndex">
                            <el-input v-model="form.orderIndex" />
                        </el-form-item>
                        <el-form-item label="是否默认展示" class="spacing" prop="isShow">
                            <el-switch v-model="form.isShow" :active-value="1" :inactive-value="0" />
                        </el-form-item>
                        <el-form-item label="是否叠加到全景图" class="spacing" prop="isShowOnPanoramaImage">
                            <el-switch v-model="form.isShowOnPanoramaImage" :active-value="1" :inactive-value="0" />
                        </el-form-item>

                        <el-form-item>
                            <el-button type="primary" @click="onSubmit">注册</el-button>
                            <el-button style="margin-left: 10px" @click="resetForm">重置</el-button>
                        </el-form-item>
                    </el-form>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
/**
 * @author: Zhang Siyu
 * @date: 2022-04-06
 * @Description: 资源注册
 */

import { postResourceApi,getRegionInfoListApi } from '@/api/commonApi';
import axios from "axios";
import ColorInputPicker from '@/components/ColorInputPicker/index.vue';
import { isValidHexColor, normalizeHexColor } from '@/utils/colorHex';

const VECTOR_STYLE_DEFAULTS = {
    polygonColor: '#FF0000',
    polygonWeight: 1,
    polygonOpacity: 0,
};

export default {
    name: 'ResourceRegistration',
    components: {
        ColorInputPicker,
    },
    data() {
        const validRestUrl = (rule, value, callback) => {
          return callback()
        };
        const validDataUrl = (rule, value, callback) => {
            if (value.indexOf('iserver') !== -1 || value.indexOf('arcgis') !== -1 || value.indexOf('geoserver') !== -1) {
                if (value.indexOf('/rest') !== -1 || value.indexOf('MapServer') !== -1 || value.indexOf('geoserver') !== -1) {
                    return callback();
                } else {
                    return callback(new Error('服务类型不匹配，请输入数据服务地址！'));
                }
            } else {
                return callback(new Error('请输入正确的服务地址！'));
            }
        };
        const validMapUrl = (rule, value, callback) => {
            if (value.indexOf('iserver') !== -1 || value.indexOf('arcgis') !== -1 || value.indexOf('geoserver') !== -1) {
                if (value.indexOf('/rest/maps') !== -1 || value.indexOf('MapServer') !== -1) {
                    return callback();
                } else {
                    return callback(new Error('服务类型不匹配,请输入栅格服务地址！'));
                }
            } else {
                return callback(new Error('请输入正确的服务地址！'));
            }
        };
        const requireVectorStyle = (message) => (rule, value, callback) => {
            if (this.activeKey !== '业务矢量数据服务') {
                callback();
                return;
            }
            if (value === '' || value === undefined || value === null) {
                callback(new Error(message));
                return;
            }
            callback();
        };
        const validPolygonColor = (rule, value, callback) => {
            if (this.activeKey !== '业务矢量数据服务') {
                callback();
                return;
            }
            if (!value) {
                callback(new Error('请输入边线颜色！'));
                return;
            }
            if (!isValidHexColor(value)) {
                callback(new Error('请输入合法色值，如 #FF0000 或 #F00'));
                return;
            }
            callback();
        };
        const validpolygonWeight = (rule, value, callback) => {
            if (this.activeKey !== '业务矢量数据服务') {
                callback();
                return;
            }
            const num = Number(value);
            if (!Number.isInteger(num) || num < 1 || num > 20) {
                callback(new Error('线条粗细应为 1~20 的整数（px）'));
                return;
            }
            callback();
        };
        const validPolygonOpacity = (rule, value, callback) => {
            if (this.activeKey !== '业务矢量数据服务') {
                callback();
                return;
            }
            const num = Number(value);
            if (!Number.isInteger(num) || num < 0 || num > 100) {
                callback(new Error('图层透明度应为 0~100 的整数'));
                return;
            }
            callback();
        };
        return {
            geoserverBaseUrl:window.config.geoserverBaseUrl,
            remarkLabel: '备\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0注',
            options: [
                { value: '网格服务', label: '网格服务' },
                { value: '村界服务', label: '村界服务' },
                { value: '航片服务', label: '航片服务' },
                { value: '航片检测服务', label: '航片检测服务' },
                { value: '其他服务', label: '其他服务' },
                { value: '耕地服务', label: '耕地服务' }
            ],
            // 页面高度
            formBoxHeight: '',
            // 注册服务类型
            activeKey: '影像服务',
            registerUrls: '',
            serverTypeList: [
                { value: '1', label: 'iServer服务' },
                { value: '2', label: 'Arcgis服务' },
                { value: '3', label: '天地图' },
                { value: '4', label: 'geoserver' }
            ],

            form: {
                name: '',
                restUrl: '',
                dataUrl: '',
                mapUrl: '',
                url: '',
                service_type: null,
                county: undefined,
                append_time: '',
                datasets_name: undefined,
                datasource_name: undefined,
                otherText: '',
                data_type: undefined,
                orderIndex: undefined,
                isShow:0,
                isShowOnPanoramaImage:0,
                gisServiceType:null,
                polygonColor: VECTOR_STYLE_DEFAULTS.polygonColor,
                polygonWeight: VECTOR_STYLE_DEFAULTS.polygonWeight,
                polygonOpacity: VECTOR_STYLE_DEFAULTS.polygonOpacity,
            },
            rules: {
                name: [
                    {
                        required: true,
                        message: '请输入服务名称，如"南京市_0.3m_2022年"！',
                        trigger: 'blur'
                    }
                ],
                county: [
                    {
                        required: true,
                        message: '请选择适合的行政区名称！',
                        trigger: 'blur'
                    }
                ],
                service_type: [
                    {
                        required: true,
                        message: '请选择数据类型！',
                        trigger: 'blur'
                    }
                ],
                gisServiceType: [
                    {
                        required: true,
                        message: '请选择服务类别！',
                        trigger: 'blur'
                    }
                ],
                datasets_name: [
                    { required: true, message: '请选择数据集！', trigger: 'change' }
                ],
                datasource_name: [{ required: true, message: '请选择数据集！', trigger: 'change' }],
                append_time: [
                    {
                        required: true,
                        message: '请输入服务注册的时间，精确到天！',
                        trigger: 'change'
                    }
                ],
                restUrl: [
                    { required: true, message: 'url地址不合法,请重新输入！', trigger: 'blur' },
                    { validator: validRestUrl, trigger: 'blur' }
                ],
                dataUrl: [
                    { required: true, message: 'url地址不合法,请重新输入！', trigger: 'blur' },
                    { validator: validDataUrl, trigger: 'blur' }
                ],
                mapUrl: [
                    { required: true, message: 'url地址不合法,请重新输入！', trigger: 'blur' },
                    { validator: validMapUrl, trigger: 'blur' }
                ],
                data_type: [
                    {
                        required: true,
                        message: '请选择数据类型！',
                        trigger: 'change'
                    }
                ],
                orderIndex: [
                    {
                        required: true,
                        message: '请输入排序序号！',
                        trigger: 'blur'
                    },
                    {
                        validator: (rule, value, callback) => {
                            if (value === '' || value === undefined) {
                                callback();
                                return;
                            }
                            if (Number.isInteger(Number(value))) {
                                callback();
                            } else {
                                callback(new Error('请输入整数'));
                            }
                        },
                        trigger: 'blur'
                    }
                ],
                polygonColor: [
                    { validator: validPolygonColor, trigger: 'blur' },
                    { validator: validPolygonColor, trigger: 'change' },
                ],
                polygonWeight: [
                    { validator: requireVectorStyle('请输入线条粗细！'), trigger: 'blur' },
                    { validator: validpolygonWeight, trigger: 'blur' },
                    { validator: validpolygonWeight, trigger: 'change' },
                ],
                polygonOpacity: [
                    { validator: requireVectorStyle('请设置图层透明度！'), trigger: 'change' },
                    { validator: validPolygonOpacity, trigger: 'change' },
                ],
            },
            filterCountyData: [],
            countyList: [],
            epsgData: [],
            epsgForm: {
                name: '',
                proj: '',
                desc: ''
            },
            formRules: {
                code: [{ required: true, message: '请输入EPSG代号', trigger: 'change' }],
                proj: [
                    { required: true, message: '请输入PROJ.4编码', trigger: 'change' },
                    {
                        pattern: /^[+]proj.*[+]no_defs\s$/,
                        message: 'PROJ.4编码不合法',
                        trigger: 'blur'
                    }
                ],
                desc: [{ required: true, message: '请输入描述', trigger: 'change' }]
            },
            tempArr: [],
            data_counts: [],
            datasourceNames: [],
            serviceType: [
                { id: 1, value: '基础地理数据' },
                { id: 2, value: '资源调查数据' },
                { id: 3, value: '低空业务数据' }
            ],
            datasetNames: [],
        };
    },
    methods: {

        //获取区域的级联数据
        async getRegionOptions() {
            const res = await getRegionInfoListApi();
            this.countyList = res.data;
        },
        handleTabClick() {
            this.resetForm();
        },
        // 表单提交及检验
        onSubmit() {
            this.$refs.ruleForm.validate((valid) => {
                if (valid) {
                    this.resRegister();
                } else {
                    console.log('error submit!!');
                }
            });
        },
        // 行政区筛选
        filterCounty(value) {
            if (!value) {
                this.$message.warning('行政区检索条件不能为空！');
                this.filterCountyData = [];
            } else {
                let reg = new RegExp(value);
                let arr = [];
                for (let i = 0; i < this.countyList.length; i++) {
                    if (reg.test(this.countyList[i].value)) {
                        arr.push(this.countyList[i]);
                    }
                }
                this.filterCountyData = arr;
            }
        },
        // 重置表单事件
        resetForm() {
            this.$refs.ruleForm.resetFields();
            this.applyVectorStyleDefaults();
        },
        applyVectorStyleDefaults() {
            this.form.polygonColor = VECTOR_STYLE_DEFAULTS.polygonColor;
            this.form.polygonWeight = VECTOR_STYLE_DEFAULTS.polygonWeight;
            this.form.polygonOpacity = VECTOR_STYLE_DEFAULTS.polygonOpacity;
        },
        // 资源注册事件
        async resRegister() {
            // 构建资源url
            this.form.restUrl !== '' ? (this.form.url = this.form.restUrl) : (this.form.url = this.form.dataUrl);
            // 构建datasets_name
            if (this.activeKey === '影像服务' && !this.isGeoserverService()) {
                this.form.datasets_name = '影像服务数据集';
            }
            // 构建请求参数
            let params = {
                name: this.form.name,
                url: this.form.url,
                sourceType: this.activeKey,
                serviceType: this.form.service_type,
                county: this.form.county,
                datasetsName: this.form.datasets_name,
                datasourceName: this.form.datasource_name,
                appendTime: this.form.append_time,
                otherText: this.form.otherText,
                dataType: this.form.data_type,
                mapUrl: this.form.mapUrl,
                datasets_count: this.data_counts.join(','),
                orderIndex: Number(this.form.orderIndex),
                isShow: this.form.isShow,
                isShowOnPanoramaImage: this.form.isShowOnPanoramaImage,
                gisServiceType: this.form.gisServiceType,
            };
            if (this.activeKey === '业务矢量数据服务') {
                params.polygonColor = normalizeHexColor(this.form.polygonColor);
                params.polygonWeight = Number(this.form.polygonWeight);
                params.polygonOpacity = Math.round(Number(this.form.polygonOpacity)) / 100;
            }
            const res = await postResourceApi(params);
            if (res.code !== 0) {
                return this.$message.warning(res.msg);
            }
            this.$message({
                type: 'success',
                message: res.msg,
                duration: 1000,
                onClose: () => {
                    this.$router.push('/resource-center/resource-management/resource-directory');
                }
            });
        },

        isGeoserverService() {
            return String(this.form.gisServiceType) === '4';
        },
        getCatalogServiceUrl() {
            if (this.activeKey === '业务矢量数据服务') {
                return (this.form.dataUrl || '').trim();
            }
            return (this.form.restUrl || '').trim();
        },
        onRestUrlChange() {
            if (!this.isGeoserverService()) return;
            this.datasourceNames = [];
            this.datasetNames = [];
            this.form.datasource_name = undefined;
            this.form.datasets_name = undefined;
            if (this.getCatalogServiceUrl()) {
                this.loadAllWorkspaces();
            }
        },
        changeHandler() {
            this.datasourceNames = [];
            this.datasetNames = [];
            if (this.form.gisServiceType === '1') {
                this.axios.get(`${this.form.dataUrl}/datasources.json`, { withCredentials: false }).then((res) => {
                    res.data.datasourceNames.forEach((item, i) => {
                        this.datasourceNames.push({ value: item, id: i });
                    });
                });
            } else if (this.isGeoserverService()) {
                this.loadAllWorkspaces();
            }
        },
        selectDatasource(value) {
            this.datasetNames = [];
            if (this.form.gisServiceType === '1') {
                this.axios.get(`${this.form.dataUrl}/datasources/${value}/datasets.json`, {withCredentials: false}).then((res) => {
                    res.data.datasetNames.forEach((item, i) => {
                        this.datasetNames.push({value: item, id: i});
                    });
                });
            } else if (this.isGeoserverService()) {
                this.loadLayersByWorkspace();
            }
        },
        async loadAllWorkspaces() {
            this.loading = true;
            this.error = '';
            this.datasourceNames = [];
            try {
                // 调用 Geoserver REST API 获取工作空间
                const response = await axios.get(
                    `${this.geoserverBaseUrl}/rest/workspaces.json`,
                    {
                        // 如果 Geoserver 配置了认证，需要添加用户名密码
                        auth: {
                            username: 'admin', // 默认用户名
                            password: 'geoserver' // 默认密码（实际项目中需修改）
                        },
                      // 关键：允许携带跨域认证信息（与 GeoServer 的 cors.support.credentials 对应）
                      withCredentials: true,
                      // 请求头配置（可选，确保与 GeoServer 允许的 headers 一致）
                      headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                      }
                    }
                );

                // 解析响应数据（Geoserver 返回格式：{ workspaces: { workspace: [...] } }）
                if (response.data.workspaces && response.data.workspaces.workspace) {
                    response.data.workspaces.workspace.forEach((item, i) => {
                        this.datasourceNames.push({value: item.name, id: item.name});
                    });
                } else {
                    this.datasourceNames = [];
                }
            } catch (err) {
                this.error = `获取工作空间失败：${err.message}`;
                console.error('工作空间加载错误:', err);
            } finally {
                this.loading = false;
            }
        },

        /**
         * 根据选中的工作空间加载对应的图层
         */
        async loadLayersByWorkspace() {
            if (!this.form.datasource_name) {
                this.datasetNames = [];
                return;
            }

            this.loading = true;
            this.error = '';
            this.datasetNames = [];
            try {
                // 调用 Geoserver REST API 获取指定工作空间下的图层
                const response = await axios.get(
                    `${this.geoserverBaseUrl}/rest/workspaces/${this.form.datasource_name}/layers.json`,
                    {
                        auth: {
                            username: 'admin',
                            password: 'geoserver'
                        }
                    }
                );

                // 解析响应数据（Geoserver 返回格式：{ layers: { layer: [...] } }）
                if (response.data.layers && response.data.layers.layer) {
                    response.data.layers.layer.forEach((item, i) => {
                        this.datasetNames.push({value: item.name, id: item.name});
                    });
                } else {
                    this.datasetNames = [];
                }
            } catch (err) {
                this.error = `获取图层失败：${err.message}`;
                console.error('图层加载错误:', err);
            } finally {
                this.loading = false;
            }
        },
        focusDatasource() {
            if (!this.isGeoserverService()) {
                if (this.activeKey === '业务矢量数据服务' && !this.form.dataUrl) {
                    return this.$message.warning('请输入服务地址！');
                }
                return;
            }
            const url = this.getCatalogServiceUrl();
            if (!url) {
                return this.$message.warning('请输入服务地址！');
            }
            this.loadAllWorkspaces();
        },
        focusServiceType() {
            if (!this.form.service_type) {
                return this.$message.warning('请输入选择数据类型！');
            }
        },
        focusDatasetNames() {
            if (!this.form.datasource_name) {
                return this.$message.warning('请选择数据源！');
            }
        }
    },
    mounted() {
        this.getRegionOptions();
    }
};
</script>

<style scoped>
.resource-container {
    margin: 0;
    padding: 0;
    background-color: #edf0f7;
    color: #333;
    line-height: 1.5;
}

.form-box-title {
    padding: 10px 20px 5px;
}

.form-card {
    width: 100%;
    height: 100%;
    background: #fff;
}

.service-tabs ::v-deep .el-tabs__header {
    margin-bottom: 0;
}

.form-box-content {
    padding: 16px 20px;
}

h3 {
    font-weight: normal;
    margin-bottom: 10px;
    text-align: center;
    margin-top: 10px;
}

h4 {
    font-weight: normal;
    text-overflow: ellipsis;
    overflow: hidden;
    white-space: nowrap;
    width: 94%;
    display: block;
    word-break: break-all;
    word-wrap: break-word;
    margin-left: 20px;
    margin-top: 10px;
    margin-bottom: 10px;
}

.full ul {
    width: 100%;
    height: calc(100% - 90px);
}

.form {
    padding: 16px 20px 0;
}

.width-input-row,
.opacity-row {
    display: flex;
    align-items: center;
    gap: 8px;
}

.unit-suffix,
.opacity-value {
    color: #666;
    font-size: 14px;
    white-space: nowrap;
}
.opacity-value {
    min-width: 48px;
}
.gt-breadcrumb-box {
    height: 40px;
    line-height: 40px;
    background: #fff;
    padding: 0 16px;
    border-left: 1px solid #dcdcdc;
}

.gt-breadcrumb-box .icon-geoai-manage {
    font-size: 20px;
    color: #2bb3f4;
}
.gt-current-position {
    margin-left: 5px;
    font-size: 18px;
    font-weight: 700;
}

.gt-breadcrumb-cnt {
    margin-top: 8px;
    padding: 10px;
    height: calc(100% - 48px);
    width: 100%;
    background-color: #fff;
}

</style>
