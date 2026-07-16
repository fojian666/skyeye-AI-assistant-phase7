<template>
    <div class="se-mv-container">
        <div class="left-content">
            <div class="overview">
                <!-- 地图总览图标-->
                <div class="panorama">
                    <div style="background-color: #62de1c">{{ overViewInfo.effective }}</div>
                    <div>有效线索</div>
                </div>
                <div class="closed">
                    <div style="background-color: #11a8ed">{{ overViewInfo.confirm }}</div>
                    <div>疑似线索</div>
                </div>
                <div class="check">
                    <div style="background-color: #ff6452">{{ overViewInfo.check }}</div>
                    <div>待审核线索</div>
                </div>
            </div>
            <div class="se-filter-form">
                <!--线索筛选-->
                <el-form :model="formInfo">
                    <el-form-item style="display: flex">
                        <el-input placeholder="请输入关键字" v-model="formInfo.keyword" style="width: 240px; margin-right: 10px"></el-input>
                        <el-button type="primary" @click="searchClue" size="mini">搜索</el-button>
                    </el-form-item>
                    <el-form-item>
                        <span>所属区域:</span>
                        <el-select style="width: 90px; margin: 0 4px" v-model="formInfo.grid_name" clearable>
                            <el-option v-for="item in gridNameList" :key="item.value" :label="item.name" :value="item.value"></el-option>
                        </el-select>
                        <span>业务状态:</span>
                        <el-select style="width: 90px; margin: 0 4px" v-model="formInfo.status" clearable>
                            <el-option v-for="item in statusList" :key="item.value" :label="item.name" :value="item.value"></el-option>
                        </el-select>
                    </el-form-item>
                    <el-form-item>
                        <el-date-picker
                            type="daterange"
                            style="width: 315px; margin: 0 5px 0 0"
                            v-model="formInfo.dataRange"
                            range-separator="至"
                            start-placeholder="开始日期"
                            end-placeholder="结束日期"
                            :unlink-panels="true"></el-date-picker>
                    </el-form-item>
                </el-form>
            </div>
            <div class="cards-container">
                <div
                    v-for="(item, index) in clueList"
                    :key="index"
                    :class="{ 'is-active': index === activeCardIndex }"
                    @click="setActiveCard(index, item)"
                    class="card">
                    <cards-component :data="item" :cardStatus="statusList"></cards-component>
                </div>
            </div>
            <div class="page">
                <el-pagination
                    small
                    background
                    @current-change="handleCurrentChange"
                    :current-page="formInfo.page"
                    :page-sizes="[5]"
                    :pager-count="5"
                    :page-size="formInfo.limit"
                    layout="prev, pager, next, total"
                    :total="dataCount"
                    style="position: fixed; bottom: 0px">
                </el-pagination>
            </div>
        </div>
        <div class="right-content">
            <map-component
                :activePanoramaPoint="activePanoramaPoint"
                :activeClueImage="activeClueImage"
                :activeMarker="activeMarker"
                :activeItem="activeItem"
                @updateActiveClueImage="updateActiveClueImage"
                @marker="getMarker"
                ref="mapComponent"
                :clueList="clueList">
            </map-component>
        </div>
    </div>
</template>

<script>
import CardsComponent from './Cards.vue';
import MapComponent from './map.vue';
import { getOverViewData, getClueOverViewData } from '@/api/commonApi';

export default {
    name: 'MapViewIndex',
    data() {
        return {
            baseUrl: process.env.VUE_APP_API_URL, //请求地址
            gridNameList: [], //获取的网格数据列表
            statusList: [], //获取的业务状态列表
            activeCardIndex: null, //激活的卡片
            activePanoramaPoint: '', //激活的卡片对应的全景点
            activeClueImage: '', //激活的线索图片地址
            activeMarker: -1, //激活的线索坐标
            activeItem: {},
            dataCount: 0, //数据总数
            overViewInfo: {
                panorama: '',
                confirm: '',
                check: '',
                effective: ''
            }, //总体线索数据
            formInfo: {
                grid_name: '',
                status: '',
                keyword: '',
                startDate: '',
                endDate: '',
                page: 1,
                limit: 5,
                dataRange: []
            }, //筛选表单参数
            clueList: [] //线索数据列表
        };
    },
    components: {
        CardsComponent,
        MapComponent
    },
    watch: {
        async 'formInfo.dataRange'(newValue, oldValue) {
            if (newValue) {
                this.formInfo.startDate = this.formatDate(newValue[0]);
                this.formInfo.endDate = this.formatDate(newValue[1]);
            } else {
                this.formInfo.startDate = '';
                this.formInfo.endDate = '';
            }
            await this.searchClue();
        },
        async 'formInfo.grid_name'(newValue, oldValue) {
            await this.searchClue();
        },
        async 'formInfo.status'(newValue, oldValue) {
            await this.searchClue();
        }
    },
    methods: {
        formatDate(date, format = 'yyyy-MM-dd') {
            const o = {
                'M+': date.getMonth() + 1, // 月份 (从0开始)
                'd+': date.getDate(), // 日
                'h+': date.getHours(), // 小时
                'm+': date.getMinutes(), // 分钟
                's+': date.getSeconds(), // 秒
                'q+': Math.floor((date.getMonth() + 3) / 3), // 季度
                S: date.getMilliseconds() // 毫秒
            };

            if (/(y+)/.test(format)) {
                format = format.replace(RegExp.$1, (date.getFullYear() + '').substr(4 - RegExp.$1.length));
            }

            for (let k in o) {
                if (new RegExp('(' + k + ')').test(format)) {
                    format = format.replace(RegExp.$1, RegExp.$1.length === 1 ? o[k] : ('00' + o[k]).substr(('' + o[k]).length));
                }
            }

            return format;
        },
        async resetForm() {
            this.formInfo.dataRange = [];
            this.formInfo.grid_name = '';
            this.formInfo.status = '';
            this.formInfo.keyword = '';
        },
        async getMarker(clueData) {
            // 地图子组件marker点击后设置线索激活
            this.activeCardIndex = null;
            this.activePanoramaPoint = clueData.point_id;
            this.activeClueImage = clueData.image_path;
            this.activeMarker = clueData.clue_id;
            this.activeItem = clueData;
        },
        async handleCurrentChange(val) {
            // 改变页码
            this.formInfo.page = val;
            this.activeCardIndex = null;
            this.activePanoramaPoint = '';
            this.activeClueImage = '';
            this.activeMarker = -1;
            this.activeItem = {};
            await this.getClue();
            this.$refs.mapComponent.updateCluesList(this.clueList);
        },
        //接收子组件关闭详情小卡片通知
        updateActiveClueImage(newImageUrl) {
            this.activeClueImage = newImageUrl;
        },
        setActiveCard(index, item) {
            //设置激活的线索卡片
            this.activeCardIndex = index;
            this.activePanoramaPoint = item.point_id;
            this.activeClueImage = item.image_path;
            this.activeMarker = item.clue_id;
            this.activeItem = item;
        },
        async getOverViewData() {
            //获取线索总览数据
            const res = await getOverViewData();
            if (res.code !== 0) {
                this.$message.error(res.msg);
                return;
            }
            this.overViewInfo.confirm = res.data.clue_confirm_count;
            this.overViewInfo.check = res.data.clue_review_count;
            this.overViewInfo.panorama = res.data.panorama_count;
            this.overViewInfo.effective = res.data.clue_effective;
            this.statusList = res.data.business_status;
            this.gridNameList = res.data.grid_name_list;
        },
        async getClue() {
            const statusList = [];
            this.statusList.forEach((item) => {
                statusList.push(item.value);
            });
            this.formInfo.statusList = statusList;
            //获取线索列表
            const res = await getClueOverViewData(this.formInfo);
            if (res.code !== 0) {
                this.$message.error(res.msg);
                return;
            }
            this.clueList = res.data;
            this.dataCount = res.count;
        },

        async searchClue() {
            //搜索线索
            this.activeCardIndex = null;
            this.activePanoramaPoint = '';
            this.activeClueImage = '';
            this.activeMarker = -1;
            this.formInfo.page = 1;
            this.activeItem = {};
            await this.getClue();
        }
    },
    async created() {
        await this.getOverViewData();
        if (this.$route.query.grid_id) this.formInfo.grid_name = this.$route.query.grid_id; //跳转的网格名称
        await this.getClue();
        this.$refs.mapComponent.updateCluesList(this.clueList);
    },
    computed: {}
};
</script>

<style lang="scss" scoped>
.overview {
    display: flex;
    flex-direction: row;
    justify-content: space-around;
    height: 90px;
}

.panorama div:last-of-type,
.closed div:last-of-type,
.check div:last-of-type {
    //字体设置
    width: 80px;
    height: 20px;
    line-height: 20px;
    text-align: center;
    font-size: 12px;
}

.panorama div:first-of-type,
.closed div:first-of-type,
.check div:first-of-type {
    width: 60px;
    height: 60px;
    display: flex;
    justify-content: center;
    margin-left: 10px;
    align-items: center;
    border-radius: 50%;
    color: white;
    font-size: 20px;
    font-weight: bold;
}

.left-content {
    width: 320px;
    height: 100%;
    position: relative;
    padding: 10px;
}

.right-content {
    width: calc(100% - 320px);
    height: 100%;
}

.se-filter-form {
    height: 110px;
    margin-bottom: 20px;
}

.page {
    position: absolute;
    left: 0;
    bottom: 0;
}

.el-form-item {
    margin-bottom: 10px;
}

.cards-container {
    height: calc(100% - 250px); //卡片容器高度
    overflow: hidden;
    justify-content: space-between; /* 确保卡片之间有间距 */
}

::v-deep .is-active .el-card {
    border: 1px solid #42b4f2;
    background-color: #bfc7cb29;
}

.el-pager li,
.el-pagination__editor,
.el-pagination .btn-prev,
.el-pagination .btn-next {
    margin: 0 1px !important;
}

::v-deep .el-form-item .el-range-separator {
    width: 10%;
}
::v-deep .el-form-item__content {
    line-height: 28px;
    position: relative;
    font-size: 12px;
    display: flex;
}
.card {
    height: calc((100% - 50px) / 5);
    margin-top: 5px;
}
::v-deep .el-range-editor--small .el-range-input {
    font-size: 13px;
    background: transparent;
    color: #fff;
}
::v-deep .el-date-editor .el-range-separator {
    color: #fff;
}
</style>
