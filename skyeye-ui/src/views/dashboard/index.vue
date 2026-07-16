<template>
    <div class="home">
        <div class="ai-banner-list1" @mouseout="out" @mouseover="over">
            <img v-for="(item, index) in list" v-show="listIndex === index" :key="index" :src="item.imageUrl" alt="" />
            <div class="main_text" v-if="listIndex !== 0">
                <span class="ai-banner-title">{{ list[listIndex].title }}</span>
                <div class="zhixian"></div>
                <span class="text">{{ list[listIndex].text }}</span>
                <router-link :to="list[listIndex].href" class="home_router"><span>立即查看</span></router-link>
            </div>
            <div class="main_text2" v-else>
                <span class="ai-banner-title">{{ list[listIndex].title }}</span>
                <div class="zhixian2"></div>
            </div>
            <p class="left" @click="changePage(prevIndex)"><i class="iconfont icon-xiangzuo"></i></p>
            <ul class="list1">
                <li :class="{ color: index == listIndex }" v-for="(item, index) in list" @click="changePage(index)" :key="index"></li>
            </ul>
            <p class="right" @click="changePage(nextIndex)"><i class="iconfont icon-xiangyou1"></i></p>
        </div>
        <div class="center_box">
            <div class="box_margin">
                <div v-for="(item, index) in show_list" class="home_table">
                    <div class="box-all">
                        <div class="box_img_yh"><img :src="item.imageUrl" style="width: 105px; height: 115px" /></div>
                        <div class="box_font">{{ item.title }}</div>
                        <div class="box_font_count">{{ item.count }}</div>
                    </div>
                </div>
            </div>
        </div>
        <div class="ai-footer">
            <span>{{ footer }}</span>
        </div>
    </div>
</template>

<script>
import { getInfoApi, getMapInfoApi } from '@/api/commonApi';

export default {
    components: {},
    props: {},
    data() {
        return {
            /*轮播图图片*/
            list: [
                {
                    imageUrl: require('@/assets/images/banner-hm1.jpg'),
                    title: '低空全景监测流程'
                },
                {
                    imageUrl: require('@/assets/images/banner-hm2.jpg'),
                    title: '全景融合',
                    text: '全景融合是一种技术，可以将多个不同角度的摄像头拍摄的视频融合成一个完整的全景视频，以便提供更全面、更真实的视觉体验。全景融合方案将实时监控视频画面与三维模型相结合展示，通过这种融合，可以将监控视频作为一部分嵌入到三维环境中，并在虚拟场景中进行展示和分析。',
                    href: '/panoramic-detection/map-view'
                },

                {
                    imageUrl: require('@/assets/images/banner-hm3.jpg'),
                    title: '目标检测',
                    text: '目标检测模块对用户在系统配置的目标检测任务进行展示、管理，按照目标类型和行政区进行分类统计，支持按区域生成目标检测统计报告。',
                    href: '/panoramic-detection/map-view'
                }
            ],
            show_list: [
                /*展示统计数据*/
                {
                    title: '网格数量',
                    imageUrl: require('@/assets/images/icon-data1.png'),
                    count: null
                },
                {
                    title: '全景点位数量',
                    imageUrl: require('@/assets/images/icon-data2.png'),
                    count: null
                },
                {
                    title: '疑似线索数量',
                    imageUrl: require('@/assets/images/icon-data3.png'),
                    count: null
                },
                {
                    title: '批次数量',
                    imageUrl: require('@/assets/images/icon-data4.png'),
                    count: null
                }
            ],
            listIndex: 0, //默认显示第几张图片
            timer: null, //定时器
            footer: window.config.copyright
        };
    },
    computed: {
        //上一张
        prevIndex() {
            if (this.listIndex === 0) {
                return this.list.length - 1;
            } else {
                return this.listIndex - 1;
            }
        },
        //下一张
        nextIndex() {
            if (this.listIndex === this.list.length - 1) {
                return 0;
            } else {
                return this.listIndex + 1;
            }
        }
    },
    methods: {
        changePage(index) {
            this.listIndex = index;
        },
        //移除
        out() {
            this.setTimer();
        },
        //移入
        over() {
            clearInterval(this.timer);
        },

        //1秒切图
        setTimer() {
            this.timer = setInterval(() => {
                this.listIndex++;
                if (this.listIndex === this.list.length) {
                    this.listIndex = 0;
                }
            }, 2000);
        }
    },

    async created() {
        //定时器
        //this.setTimer();
        try {
            const res = await getInfoApi();
            if (res.code === 0) {
                this.show_list[0].count = res.data.total_grid;
                this.show_list[1].count = res.data.total_point;
                this.show_list[2].count = res.data.total_clue;
                this.show_list[3].count = res.data.total_batch;
            }
        } catch (e) {}

        const res1 = await getMapInfoApi();
        if (res1.code === 0) {
            this.mapService = res1.data.map_service;
            this.center = res1.data.center;
            // this.gridService = res1.grid_service;
            // this.gridDatasourceName = res1.grid_datasource_name;
            // this.gridDatasetsName = res1.grid_datasets_name;
            // this.gengdiService = res1.gengdi_service;
            if (this.mapService) {
                localStorage.setItem('mapService', res1.data.map_service);
                localStorage.setItem('center', res1.data.center);
            } else {
            }
        }
    }
};
</script>
<style scoped lang="scss">
.home {
    width: 100%;
    height: 100% !important;
}

.ai-banner-list1 {
    position: relative;
    width: 100%;
    height: 60%;
}

.ai-banner-list1 img {
    width: 100%;
    height: 100%;
    z-index: 100;
}

p {
    cursor: pointer;
    color: white;
    display: flex;
    justify-content: center;
    align-items: center;
    width: 2.5rem;
    height: 2.5rem;
    border-radius: 50%;
    background: rgba(0, 0, 0, 0.2);
}

.left {
    position: absolute;
    top: 50%;
    left: 0;
}

.right {
    position: absolute;
    top: 50%;
    right: 0;
}

ul {
    list-style: none;
    display: flex;
    justify-content: space-around;
    align-items: center;
    position: absolute;
    width: 12%;
    height: 6px;
    top: 90%;
    margin: 0 44%;
}

.zhixian {
    background: #ffffff;
    height: 1px;
    width: 100%;
    margin: 1% 0;
}
.zhixian2 {
    background: #ffffff;
    height: 1px;
    width: 32%;
    margin: 1% 0;
}

.color {
    background: #ffffff;
    color: #ffffff;
    opacity: 1;
}

li {
    cursor: pointer;
    width: 40px;
    height: 6px;
    background: #ffffff;
    opacity: 0.44;
    border-radius: 4px;
}

.home_table {
    width: 22.5%;
    height: 100%;
    float: left;
    text-align: center;
    display: table;
    background-color: #ffffff;
    margin: 0 10px;
    border-radius: 10px;
}

.box-all {
    width: 100%;
    text-align: center;
    display: table-cell;
    vertical-align: middle;
}

.box_img_yh {
    padding: 10px 0;
}

.box_font {
    font-size: calc(100vw * 18 / 1920);
    font-weight: bold;
    color: #3d3d3d;
    width: 100%;
    margin: 4px 0px;
}

.box_font_count {
    font-size: calc(100vw * 36 / 1920);
    width: 100%;
    color: #137ce3;
    font-weight: bold;
    margin: 20px 0px;
}

.box_font_danwei {
    font-size: calc(100vw * 14 / 1920);
    width: 100%;
    color: black;
    margin: 4px 0px 10px 0;
}

.center_box {
    background-color: #e2e7f3;
    width: 100%;
    height: 37%;
    white-space: nowrap;
}

.ai-footer {
    height: 3%;
    background-color: #e2e7f3;
    margin: 0 auto;
    text-align: center;
    width: 100%;
    position: fixed;
    color: #afb3bf;
    display: table;
}

.ai-footer span {
    vertical-align: center;
    margin-bottom: 1rem;
}

.box_margin {
    margin: 0 5%;
    padding: 2% 0;
    height: 100%;
}

.main_text {
    position: absolute;
    top: 35%;
    left: 10%;
    width: 40%;
}
.main_text2 {
    position: absolute;
    top: 20%;
    left: 8%;
    width: 40%;
}
.main_text .ai-banner-title,
.main_text2 .ai-banner-title {
    font-size: calc(100vw * 30 / 1920);
    color: white;
}

.main_text .text {
    font-size: calc(100vw * 16 / 1920);
    color: white;
    letter-spacing: 2px;
}

.home_router {
    display: table;
    background-color: #ffffff;
    width: 24%;
    height: 3rem;
    font-weight: 600;
    border-radius: 50px;
    margin-top: 5%;
}

.home_router span {
    margin: 0 auto;
    text-align: center;
    position: relative;
    vertical-align: middle;
    display: table-cell;
}
</style>
