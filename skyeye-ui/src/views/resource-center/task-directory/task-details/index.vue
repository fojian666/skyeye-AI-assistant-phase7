<template>
    <div class="resource-details">
        <div class="resource-detail-header">
            <div class="resource-detail-title">
                <img src="@/assets/images/ic_biaoti_left.png" alt="" />
                <span> 任务详情 </span>
                <img src="@/assets/images/ic_biaoti_right.png" alt="" />
            </div>
            <div class="resource-detail-title-line"></div>
            <a-button type="primary" v-if="available"> 任务可使用</a-button>
            <a-button type="danger" v-if="!available"> 任务不可用</a-button>
        </div>
        <div class="resource-detail-content">
            <div class="img-box">
                <img src="@/assets/images/land-change.png" v-if="dataObj.taskType === '地类变化'" />
                <img src="@/assets/images/land-division.png" v-if="dataObj.taskType === '地类分割'" />
            </div>
            <div class="resource-content">
                <table style="table-layout: fixed; width: 100%">
                    <tr>
                        <td class="resource-detail-key">任务名称：</td>
                        <td class="resource-detail-value" v-show="show">
                            {{ dataObj.name }}
                            <span class="iconfont icon-geoai-edit card-title-font" @click="toggle" />
                        </td>
                        <td class="resource-detail-value" v-show="!show">
                            <a-input v-model="dataObj.name" @blur="edit" @pressEnter="edit" />
                        </td>
                    </tr>
                    <tr>
                        <td class="resource-detail-key">任务类型：</td>
                        <td class="resource-detail-value">{{ dataObj.taskType }}</td>
                    </tr>
                    <tr>
                        <td class="resource-detail-key">所属行政区：</td>
                        <td class="resource-detail-value">{{ dataObj.county }}</td>
                    </tr>
                    <tr>
                        <td class="resource-detail-key">注册人：</td>
                        <td class="resource-detail-value">{{ dataObj.owner }}</td>
                    </tr>
                    <tr>
                        <td class="resource-detail-key">注册时间：</td>
                        <td class="resource-detail-value">{{ dataObj.appendTime }}</td>
                    </tr>
                    <tr>
                        <td class="resource-detail-key">成果要素服务：</td>
                        <td class="resource-detail-value">{{ dataObj.dataPath }}</td>
                    </tr>
                    <tr>
                        <td class="resource-detail-key">任务描述：</td>
                        <td class="resource-detail-value">{{ dataObj.desc }}</td>
                    </tr>
                    <tr v-if="task_type === '地类分割'" class="separate-line"></tr>
                    <tr v-if="task_type === '地类分割'">
                        <td class="resource-detail-key">地图预览：</td>
                        <td class="resource-detail-value">
                            <span style="color: red; font-size: 14px; cursor: pointer" @click="previewaChievementSlicing"> 预览 </span>
                        </td>
                    </tr>
                    <tr v-if="task_type === '地类分割'">
                        <td class="resource-detail-key">成果切片服务：</td>
                        <td class="resource-detail-value">{{ dataObj.mapUrl }}</td>
                    </tr>
                    <tr class="separate-line"></tr>
                    <tr v-if="task_type === '地类分割' || task_type === '目标检测'">
                        <td class="resource-detail-key">地图预览：</td>
                        <td class="resource-detail-value">
                            <!-- <router-link :to="mapPreview" style="color: red; font-size: 14px"
                >预览</router-link
              > -->
                            <span style="color: red; font-size: 14px; cursor: pointer" @click="preview"> 预览 </span>
                        </td>
                    </tr>
                    <tr v-if="task_type === '地类变化'">
                        <td class="resource-detail-key">前景影像：</td>
                        <td class="resource-detail-value">
                            <!-- <router-link
                :to="foregroundImage"
                style="color: red; font-size: 14px"
                >预览</router-link
              > -->
                            <span style="color: red; font-size: 14px; cursor: pointer" @click="foregroundImagePreview"> 预览 </span>
                        </td>
                    </tr>
                    <tr>
                        <td class="resource-detail-key">影像切片服务：</td>
                        <td class="resource-detail-value" style="word-wrap: break-word" v-if="task_type === '地类变化'">
                            {{ foregroundImage.query.url }}
                        </td>
                        <td class="resource-detail-value" style="word-wrap: break-word" v-if="task_type !== '地类变化'">
                            {{ mapPreview.query.url }}
                        </td>
                    </tr>
                    <tr>
                        <td class="resource-detail-key">坐标系：</td>
                        <td class="resource-detail-value">EPSG:{{ coordinateSystem }}</td>
                    </tr>
                    <tr class="separate-line"></tr>
                    <tr v-if="task_type === '地类变化'">
                        <td class="resource-detail-key">后景影像：</td>
                        <td class="resource-detail-value">
                            <!-- <router-link
                :to="backgroundImage"
                style="color: red; font-size: 14px"
                >预览</router-link
              > -->
                            <span style="color: red; font-size: 14px; cursor: pointer" @click="backgroundImagePreview"> 预览 </span>
                        </td>
                    </tr>
                    <tr v-if="task_type === '地类变化'">
                        <td class="resource-detail-key">影像切片服务：</td>
                        <td class="resource-detail-value">
                            {{ backgroundImage.query.url }}
                        </td>
                    </tr>
                    <tr v-if="task_type === '地类变化'">
                        <td class="resource-detail-key">坐标系：</td>
                        <td class="resource-detail-value">EPSG:{{ nextCoordinateSystem }}</td>
                    </tr>
                </table>
            </div>
        </div>
        <map-preview ref="mapPreviewRef"></map-preview>
    </div>
</template>

<script>
import { getTaskInfoByIdApi, updateTaskByIdApi } from '@/api/commonApi';
import mapPreview from './map-preview';

export default {
    name: 'TaskDetails',
    components: {
        mapPreview
    },
    data() {
        return {
            task_id: '',
            dataObj: {},
            serveData: {},
            center: '',
            leftBottom: '',
            rightTop: '',
            minX: 0,
            minY: 0,
            maxX: 0,
            maxY: 0,
            nextCenter: '',
            nextLeftBottom: '',
            nextRightTop: '',
            nextMinX: 0,
            nextMinY: 0,
            nextMaxX: 0,
            nextMaxY: 0,
            coordinateSystem: '',
            nextCoordinateSystem: '',
            task_type: '',
            mapPreview: {
                path: '/resourceCenter/taskDirectory/taskDetails/mapPreview',
                query: {
                    task_id: '',
                    preview_type: '地图预览'
                }
            },
            achievementSlicingService: {
                task_id: '',
                preview_type: '成果切片服务'
            },
            foregroundImage: {
                path: '/resourceCenter/taskDirectory/taskDetails/mapPreview',
                query: {
                    task_id: '',
                    preview_type: '前景影像'
                }
            },
            backgroundImage: {
                path: '/resourceCenter/taskDirectory/taskDetails/mapPreview',
                query: {
                    task_id: '',
                    preview_type: '后景影像'
                }
            },
            show: true,
            available: true
        };
    },
    mounted() {
        this.task_id = this.$route.query.id;
        this.mapPreview.query.task_id = this.$route.query.id;
        this.achievementSlicingService.task_id = this.$route.query.id;
        this.foregroundImage.query.task_id = this.$route.query.id;
        this.backgroundImage.query.task_id = this.$route.query.id;
        this.task_type = this.$route.query.task_type;
        this.getTaskById();
    },
    methods: {
        async getTaskById() {
            const res = await getTaskInfoByIdApi(this.task_id);
            if (res.code === 0) {
                this.dataObj = res.data;
                if (this.dataObj.taskType === '地类变化') {
                    this.foregroundImage.query.coordinate_system = this.dataObj.prevImage && this.dataObj.prevImage.coordinateSystem;
                    this.backgroundImage.query.coordinate_system = this.dataObj.nextImage && this.dataObj.nextImage.coordinateSystem;
                    this.backgroundImage.query.center = this.dataObj.center;
                    this.foregroundImage.query.url = res.data.prevImage && res.data.prevImage.url;
                    this.backgroundImage.query.url = res.data.nextImage && res.data.nextImage.url;
                    this.coordinateSystem = res.data.prevImage && res.data.prevImage.coordinateSystem;
                    this.nextCoordinateSystem = res.data.nextImage && res.data.nextImage.coordinateSystem;
                } else {
                    this.mapPreview.query.coordinate_system = this.dataObj.path.coordinateSystem;
                    this.mapPreview.query.center = this.dataObj.center;
                    this.mapPreview.query.url = this.dataObj.path.url;
                    this.coordinateSystem = res.data.path.coordinateSystem;
                }
                if (
                    (this.dataObj.nextImage && this.dataObj.nextImage.url && this.dataObj.nextImage.url.includes('iserver')) ||
                    (this.dataObj.path && this.dataObj.path.url && this.dataObj.path.url.includes('iserver')) ||
                    (this.dataObj.mapurl && this.dataObj.mapUrl.includes('iserver')) ||
                    (this.dataObj.prevImage && this.dataObj.prevImage.url && this.dataObj.prevImage.url.includes('iserver'))
                ) {
                    this.iserver();
                } else {
                    this.arcgis();
                }
            }
        },
        iserver() {
            let url = '',
                nextUrl = '';
            if (this.task_type === '地类分割' || this.task_type === '目标检测') {
                url = this.dataObj.path.url;
            } else if (this.task_type === '地类变化') {
                url = this.dataObj.prevImage && this.dataObj.prevImage.url;
                nextUrl = this.dataObj.nextImage && this.dataObj.nextImage.url;
                this.axios.get(nextUrl + '.json', { withCredentials: false }).then((res) => {
                    this.backgroundImage.query.center = res.data.center;
                });
            }
            this.axios
                .get(url + '.json', { withCredentials: false })
                .then((res) => {
                    this.serveData = res.data;
                    this.mapPreview.query.center = res.data.center;
                    this.foregroundImage.query.center = res.data.center;
                })
                .catch((err) => {
                    this.available = false;
                });
        },
        arcgis() {
            let url = '',
                nextUrl = '';
            if (this.task_type === '地类分割' || this.task_type === '目标检测') {
                url = this.dataObj.path.url;
            } else if (this.task_type === '地类变化') {
                url = this.dataObj.prevImage && this.dataObj.prevImage.url;
                nextUrl = this.dataObj.nextImage && this.dataObj.nextImage.url;
            }
            this.axios.get(url + '?f=pjson', { withCredentials: false }).catch((err) => {
                this.available = false;
            });
        },
        toggle() {
            this.show = false;
        },
        async edit() {
            this.show = true;
            let params = {
                id: this.dataObj.id,
                name: this.dataObj.name
            };
            const res = await updateTaskByIdApi(params);
            if (res.code !== 0) {
                return this.$message.warning(res.msg);
            }
            this.$message.success(res.msg);
            this.getTaskById();
        },
        previewaChievementSlicing() {
            this.$refs.mapPreviewRef.open(this.achievementSlicingService);
        },
        preview() {
            this.$refs.mapPreviewRef.open(this.mapPreview.query);
        },
        foregroundImagePreview() {
            this.$refs.mapPreviewRef.open(this.foregroundImage.query);
        },
        backgroundImagePreview() {
            this.$refs.mapPreviewRef.open(this.backgroundImage.query);
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

.resource-detail-content {
    width: 100%;
    height: calc(100% - 60px);
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

.card-title-font {
    margin-left: 6px;
    color: #42b4f2;
    font-size: 18px;
}
</style>
