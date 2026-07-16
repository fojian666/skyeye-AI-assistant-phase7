<template>
    <div class="sample-down">
        <div id="components-layout-side">
            <div class="card-container">
                <a-tabs type="card" @change="callback">
                    <a-tab-pane key="changeDetection" tab="变化检测">
                        <div class="gutter-example">
                            <a-row :gutter="10">
                                <a-col class="gutter-row" :span="24">
                                    <div class="gutter-box-item active">
                                        <i class="iconfont icon-geoai-construction1"></i>
                                        <p>建设用地</p>
                                    </div>
                                </a-col>
                            </a-row>
                        </div>
                        <div class="diver"></div>
                        <div class="sample">
                            <div class="sample-title">示例数据</div>
                            <div class="sample-item">
                                <!--                <div class="sample-cd-image">-->

                                <!--                </div>-->
                                <img :src="conmponentInfo.changeDetectionImg" alt="" />
                                <p>{{ conmponentInfo.layerName }}</p>
                            </div>
                        </div>
                        <div style="font-size: 12px">* IS代表影像分割，CD代表变化检测</div>
                    </a-tab-pane>

                    <a-tab-pane key="imageSegementation" tab="影像分割">
                        <div class="gutter-example">
                            <a-row :gutter="10">
                                <a-col
                                    v-for="(imageSegClass, index) in imageSegClasses"
                                    @click="changeImageSegClass(imageSegClass, index)"
                                    class="gutter-row"
                                    :span="12">
                                    <div
                                        class="gutter-box-item"
                                        :class="index == identityClass.classIndex ? 'gutter-box-item active' : 'gutter-box-item'">
                                        <i :class="'iconfont ' + imageSegClass.icon"></i>
                                        <p>{{ imageSegClass.name }}</p>
                                    </div>
                                </a-col>
                            </a-row>
                        </div>
                        <div class="diver"></div>
                        <div class="sample">
                            <div class="sample-title">示例数据</div>
                            <div class="sample-item">
                                <!--                <div class="sample-is-image">-->
                                <!--                </div>-->
                                <img :src="conmponentInfo.imageSegementationImg" alt="" />

                                <p>{{ conmponentInfo.layerName }}</p>
                            </div>
                        </div>
                        <div style="font-size: 12px">* IS代表影像分割，CD代表变化检测</div>
                    </a-tab-pane>
                </a-tabs>
            </div>
        </div>
        <div id="components-layout-content">
            <component :is="conmponentInfo.templateName" style="height: 100%" ref="child"></component>
        </div>
    </div>
</template>

<script>
import { getExperienceData } from '@/api/commonApi';

export default {
    name: 'changeDetectionInfo',
    components: {
        changeDetection: () => import('./changeDetection'),
        imageSegementation: () => import('./imageSegmentation')
    },
    data() {
        return {
            conmponentInfo: {
                templateName: 'changeDetection',
                layerName: '示例数据',
                changeDetectionImg: '',
                imageSegementationImg: '',
                baseUrl: process.env.VUE_APP_API_URL
            },
            is_auth: true,
            username: '',
            is_login: false,
            imageSegClasses: [],
            identityClass: {}
        };
    },
    methods: {
        callback(key) {
            this.conmponentInfo.templateName = key;
            this.getImgSegClass();
        },
        changeImageSegClass(item, index) {
            this.identityClass.classIndex = index;
            this.identityClass.class = item;
            // 触发子组件事件
            //this.$children[5].selectedModel(item)
            this.$refs.child.selectedModel(item);
        },
        async getImgSegClass() {
            const res = await getExperienceData();
            if (res.code === 0) {
                // 更新模型列表
                this.imageSegClasses = res.data.models;
                // 图层名称
                this.conmponentInfo.layerName = res.data.name;
                // 缩略图
                this.conmponentInfo.changeDetectionImg = res.data.prev_url + '/entireImage.jpg';
                this.conmponentInfo.imageSegementationImg = res.data.is_map_url + '/entireImage.jpg';
                // 默认选中模型类型
                this.identityClass = {
                    classIndex: 0,
                    class: this.imageSegClasses[0]
                };
            } else {
                this.$message.error('数据请求失败！', 3);
            }
        }
    },
    mounted() {
        this.username = localStorage.getItem('username');
        if (this.username) {
            this.is_auth = false;
            this.is_login = true;
        } else {
            this.is_auth = true;
            this.is_login = false;
        }
    },
    async created() {
        import('@/css/ex-pc.css');

        this.getImgSegClass();
    }
};
</script>

<style scoped lang="scss">
.sample-down {
    z-index: 9;
    position: relative;
    height: 100%;
}

/*  左侧选项卡*/
.card-container .ant-tabs-nav-container .ant-tabs-nav {
    width: 100%;
}

.card-container .ant-tabs-nav-container .ant-tabs-nav .ant-tabs-tab {
    width: 49.5%;
}

::v-deep .ant-tabs-nav {
    width: 100%;
}

::v-deep .ant-tabs-tab {
    width: 49%;
    text-align: center;
}

::v-deep .ant-tabs-bar {
    border: none !important;
}

.ant-tabs-nav .ant-tabs-tab {
    width: 50%;
    box-sizing: border-box;
}

.card-container .gutter-box-item.active .iconfont {
    color: white;
}

.card-container .gutter-box-item.active {
    color: white;
    /*background-color: #42b4f2;*/
    border: 1px solid #42b4f2;
    background-color: #2a7be8;
}
</style>
