<template>
    <div class="resource-details">
        <div class="resource-detail-header">
            <div class="resource-detail-title">
                <img src="@/assets/images/ic_biaoti_left.png" alt="" />
                <span> 资源详情 </span>
                <img src="@/assets/images/ic_biaoti_right.png" alt="" />
            </div>
            <div class="resource-detail-title-line"></div>
            <a-button type="primary" v-if="available"> 服务可使用 </a-button>
            <a-button type="danger" v-if="!available"> 服务不可用 </a-button>
        </div>
        <div class="resource-detail-content">
            <div class="img-box">
                <img src="@/assets/images/image-service.png" v-if="dataObj.source_type === '影像服务'" />
                <img src="@/assets/images/business-services.png" v-if="dataObj.source_type === '业务数据服务'" />
            </div>
            <div class="resource-content">
                <table style="table-layout: fixed; width: 100%">
                    <tr>
                        <td class="resource-detail-key">服务名称：</td>
                        <td class="resource-detail-value cursor" v-show="nameShow">
                            {{ dataObj.name }}
                            <span class="iconfont icon-geoai-edit card-title-font" @click="nameToggle" />
                        </td>
                        <td class="resource-detail-value" v-show="!nameShow">
                            <a-input v-model="dataObj.name" @blur="edit" @pressEnter="edit" />
                        </td>
                    </tr>
                    <tr>
                        <td class="resource-detail-key">服务类型：</td>
                        <td class="resource-detail-value">{{ dataObj.source_type }}</td>
                    </tr>
                    <tr v-if="source_type === '影像服务' || source_type === '业务数据服务'">
                        <td class="resource-detail-key">影像切片服务：</td>
                        <td class="resource-detail-value" v-show="urlShow">
                            {{ dataObj.url }}
                            <span class="iconfont icon-geoai-edit card-title-font" @click="urlToggle" />
                        </td>
                        <td class="resource-detail-value" v-show="!urlShow">
                            <a-input v-model="dataObj.url" @blur="edit" @pressEnter="edit" />
                        </td>
                    </tr>
                    <tr v-else>
                        <td class="resource-detail-key">成果要素服务：</td>
                        <td class="resource-detail-value" v-show="urlShow">
                            {{ dataObj.url }}
                            <span class="iconfont icon-geoai-edit card-title-font" @click="urlToggle" />
                        </td>
                        <td class="resource-detail-value" v-show="!urlShow">
                            <a-input v-model="dataObj.url" @blur="edit" @pressEnter="edit" />
                        </td>
                    </tr>
                    <tr v-if="source_type === '地类分割成果服务'">
                        <td class="resource-detail-key">成果切片服务：</td>
                        <td class="resource-detail-value" v-show="mapUrlShow">
                            {{ dataObj.mapUrl }}
                            <span class="iconfont icon-geoai-edit card-title-font" @click="mapUrlToggle" />
                        </td>
                        <td class="resource-detail-value" v-show="!mapUrlShow">
                            <a-input v-model="dataObj.mapUrl" @blur="edit" @pressEnter="edit" />
                        </td>
                    </tr>
                    <tr>
                        <td class="resource-detail-key">行政区名称：</td>
                        <td class="resource-detail-value">{{ dataObj.county }}</td>
                    </tr>
                    <tr>
                        <td class="resource-detail-key">数据集名称：</td>
                        <td class="resource-detail-value">{{ dataObj.datasets_name }}</td>
                    </tr>
                    <tr>
                        <td class="resource-detail-key">服务主题：</td>
                        <td class="resource-detail-value">{{ dataObj.data_type }}</td>
                    </tr>
                    <tr>
                        <td class="resource-detail-key">注册人：</td>
                        <td class="resource-detail-value">{{ dataObj.owner }}</td>
                    </tr>
                    <tr>
                        <td class="resource-detail-key">注册时间：</td>
                        <td class="resource-detail-value">{{ dataObj.append_time }}</td>
                    </tr>
                    <tr v-if="source_type === '影像服务'">
                        <td class="resource-detail-key">场景预览：</td>
                        <td class="resource-detail-value">
                            <!-- <router-link :to="mapPreview" style="color: red; font-size: 14px"
                              >预览</router-link
                            > -->
                            <span style="color: red; font-size: 14px; cursor: pointer" @click="preview"> 预览 </span>
                        </td>
                    </tr>
                    <tr>
                        <td class="resource-detail-key">坐标系：</td>
                        <td class="resource-detail-value">EPSG:{{ dataObj.coordinate_system }}</td>
                    </tr>
                    <tr class="separate-line"></tr>
                </table>
            </div>
        </div>
        <scene-preview ref="scenePreviewRef"></scene-preview>
    </div>
</template>

<script>
import { getResourceByIdApi, postResourceByIdApi } from '@/api/commonApi';
import scenePreview from './scene-preview';

export default {
    name: 'ResourceDetails',
    components: {
        scenePreview
    },
    data() {
        return {
            source_id: '',
            source_type: '',
            dataObj: {},
            serveData: {},
            center: '',
            leftBottom: '',
            rightTop: '',
            minX: 0,
            minY: 0,
            maxX: 0,
            maxY: 0,
            mapPreview: {
                path: '/resourceCenter/serviceCatalog/resourceDetails/scenePreview',
                query: {
                    source_id: ''
                }
            },
            nameShow: true,
            urlShow: true,
            mapUrlShow: true,
            available: true
        };
    },
    mounted() {
        this.source_id = this.$route.query.id;
        this.source_type = this.$route.query.source_type;
        this.getResourceDetails();
    },
    methods: {
        async getResourceDetails() {
            const res = await getResourceByIdApi(this.source_id);
            if (res.code === 0) {
                this.dataObj = res.data;
                this.mapPreview.query.source_id = this.source_id;
                if (this.dataObj.url && this.dataObj.url.includes('iserver')) {
                    this.iserver();
                } else {
                    this.arcgis();
                }
            }
        },
        iserver() {
            this.axios
                .get(this.dataObj.url + '.json', { withCredentials: false })
                .then((res) => {
                    this.serveData = res.data;
                    // this.center = this.serveData.center.x.toFixed(2) + ', ' + this.serveData.center.y.toFixed(2);
                    // this.leftBottom =
                    //   this.serveData.bounds.leftBottom.x.toFixed(2) +
                    //   ', ' +
                    //   this.serveData.bounds.leftBottom.y.toFixed(2);
                    // this.rightTop =
                    //   this.serveData.bounds.rightTop.x.toFixed(2) +
                    //   ', ' +
                    //   this.serveData.bounds.rightTop.y.toFixed(2);
                    // this.minX = this.serveData.bounds.left.toFixed(2);
                    // this.minY = this.serveData.bounds.bottom.toFixed(2);
                    // this.maxX = this.serveData.bounds.right.toFixed(2);
                    // this.maxY = this.serveData.bounds.top.toFixed(2);
                    //this.mapPreview.query.center = res.data.center;
                })
                .catch((err) => {
                    this.available = false;
                });
        },
        arcgis() {
            this.axios.get(this.dataObj.url + '?f=pjson', { withCredentials: false }).catch((err) => {
                this.available = false;
            });
        },
        nameToggle() {
            this.nameShow = false;
        },
        urlToggle() {
            this.urlShow = false;
        },
        mapUrlToggle() {
            this.mapUrlShow = false;
        },
        async edit() {
            this.nameShow = true;
            this.urlShow = true;
            this.mapUrlShow = true;
            let params = this.dataObj;
            const res = await postResourceByIdApi(params);
            if (res.code !== 0) {
                return this.$message.warning(res.msg);
            }
            this.$message.success(res.msg);
            this.getResourceDetails();
        },
        preview() {
            this.$refs.scenePreviewRef.open(this.mapPreview.query);
        }
    }
};
</script>

<style scoped>
.resource-details {
    width: 100%;
    height: 100%;
    padding: 20px 20px 10px;
}

.resource-detail-key {
    text-align: right;
    width: 14%;
}

.resource-detail-value {
    width: 86%;
    padding-left: 30px;
    word-wrap: break-word;
}

.resource-detail-header {
    width: 100%;
    height: 30px;
    line-height: 30px;
    margin-bottom: 10px;
}

.resource-detail-title {
    display: inline-block;
    /* width: 185px; */
    font-size: 14px;
    font-weight: 500;
    color: rgba(153, 153, 153, 1);
}

.resource-detail-title img:nth-child(1) {
    width: 20px;
    margin-right: 20px;
    vertical-align: baseline;
}

.resource-detail-title img:nth-child(3) {
    width: 20px;
    margin-left: 20px;
    vertical-align: baseline;
}

.resource-detail-title > span {
    font-size: 24px;
    font-family: Microsoft YaHei, Microsoft YaHei-Regular;
    font-weight: 400;
    text-align: left;
    color: #333333;
}

.resource-detail-title-line {
    vertical-align: super;
    display: inline-block;
    width: 70%;
    height: 1px;
    background-color: #3e90ff;
    opacity: 0.3;
    margin-left: -5px;
    margin-top: 15px;
    margin-right: 7px;
}

.ant-btn-primary {
    font-size: 12px;
    border-radius: 2px;
}

.img-box {
    width: 152px;
    float: left;
}

.img-box img {
    width: 152px;
    height: 100px;
    padding: 4px;
    background-color: #fff;
    border: 1px solid #ddd;
}

.resource-content {
    width: calc(100% - 170px);
    height: 100%;
    margin-left: 8px;
    float: left;
    overflow: auto;
    position: relative;
}

.separate-line {
    height: 1.5px;
    background-color: #cacaca;
    width: 100%;
    position: absolute;
}

td {
    height: 32px;
}

.cursor {
    cursor: pointer;
}

.card-title-font {
    margin-left: 6px;
    color: #42b4f2;
    font-size: 18px;
}

.ant-input {
    width: 30vw !important;
}

.resource-detail-content {
    width: 100%;
    height: calc(100% - 60px);
}
</style>
