<template>
    <div class="gtp-container">
        <div class="detection-filter">
            <div class="filter-all">
                <label class="filter-lab">审核状态：</label>
                <div class="filter-checkb">
                    <el-checkbox-button
                        :indeterminate="isClassIndeterminate"
                        v-model="classcheckAll"
                        @change="handleClassCheckAllChange"
                        class="filter-checkb-all"
                        >全选</el-checkbox-button
                    >
                    <el-checkbox-group v-model="checkedclass" @change="handleCheckedClassChange">
                        <el-checkbox-button v-for="item in classes" :label="item" :key="item" class="filter-checkb-item">{{
                            item
                        }}</el-checkbox-button>
                    </el-checkbox-group>
                </div>
            </div>
            <div class="filter-all">
                <label class="filter-lab">检测类型：</label>
                <div class="filter-checkb">
                    <el-checkbox-button
                        :indeterminate="isIndeterminate"
                        v-model="labelcheckAll"
                        @change="handlelabelCheckAllChange"
                        class="filter-checkb-all"
                        >全选</el-checkbox-button
                    >
                    <el-checkbox-group v-model="checkedlabels" @change="handleCheckedlabelsChange">
                        <el-checkbox-button v-for="label in labels" :label="label" :key="label" class="filter-checkb-item">{{
                            label
                        }}</el-checkbox-button>
                    </el-checkbox-group>
                </div>
            </div>
        </div>
        <div class="panel-fold2"></div>
        <div v-if="this.oddata.pictures.length != 0">
            <div v-for="page in totalPages" :key="page">
                <div class="page-container" v-if="currentPage === page">
                    <el-card
                        class="card-container"
                        v-for="(picture, index) in currentPagePictures"
                        :key="index"
                        v-if="matchesSelectedLabelsAndClass(picture.labels, picstauts)"
                        :body-style="{ padding: '0px' }"
                        shadow="hover">
                        <!-- ！！！！v-if 的picture的属性需要根据后续实际的修改！！！！！ -->
                        <div class="flex-container">
                            <div class="card-body">
                                <div class="clearfix">
                                    <el-tooltip :content="getTooltipContent(picture)" placement="top" effect="light">
                                        <p class="card-name">{{ picture.name }}</p>
                                    </el-tooltip>
                                </div>
                                <div class="image-container">
                                    <el-image
                                        style="width: 100%; height: auto; margin-bottom: 10px; cursor: pointer"
                                        :src="getImageUrl(picture)"
                                        fit="fill"
                                        :preview-src-list="getImageUrl(picture)"></el-image>
                                </div>
                                <div class="info-container">
                                    <p class="info-text">创建时间：{{ picture.create_time }}</p>
                                    <p class="info-text">检测类型：{{ picture.labels }}</p>
                                    <p class="info-text">审核状态：{{ picstauts }}</p>
                                </div>
                                <el-button class="xqbtn" type="primary" plain size="small" @click="openimagemap(picture)">详情</el-button>
                            </div>
                        </div>
                    </el-card>
                </div>
            </div>
        </div>
        <div v-else class="text-info">暂无数据...</div>
        <el-pagination
            @current-change="handleCurrentChange"
            :current-page="currentPage"
            :page-size="pageSize"
            :total="this.oddata.pictures.length"
            layout="total, prev, pager, next, jumper"></el-pagination>

        <el-dialog :visible="isImageMapDialogVisible" @close="clossImageMapDialog" width="80%" center>
            <template slot="title">
                <div style="font-size: 26px; color: black; text-align: left">数据详情</div>
            </template>
            <div class="panel-fold"></div>
            <div style="width: 100%; height: 60vh; padding-top: 10px">
                <image-map :key="uniqueKey" :picture="selectedPicture"></image-map>
            </div>
        </el-dialog>
    </div>
</template>

<script>
import ImageMap from './ImageMap.vue';
import axios from 'axios';
const labelOptions = ['防尘网', '水泥管及水泥堆', '推土车', '在建砖房', '土堆', '堆砖', '钢筋', '挖掘机']; //检测类型
const classOptions = ['已审核', '未审核']; //审核状态
export default {
    name: 'OdDetails',
    props: {
        oddata: {
            type: Object,
            required: true
        }
    },
    data() {
        return {
            // taskId: '',
            taskData: {},
            currentPage: 1,
            pageSize: 10, // 每页显示的卡片数量
            labelcheckAll: false,
            checkedlabels: [],
            labels: labelOptions,
            isIndeterminate: true,
            classcheckAll: false,
            checkedclass: [],
            classes: classOptions,
            isClassIndeterminate: true,
            filteredPictures: [],
            isImageMapDialogVisible: false, // 控制弹出框显示状态
            selectedPicture: null, // 存储选中的图片信息
            uniqueKey: 1,
            picstauts: '未审核'
        };
    },
    components: {
        ImageMap: ImageMap
    },
    mounted() {},
    computed: {
        // Calculate total number of pages
        totalPages() {
            const pageSize = 10; // 2 rows x 5 columns
            return Math.ceil(this.oddata.pictures.length / pageSize);
        },
        currentPagePictures() {
            const startIndex = (this.currentPage - 1) * this.pageSize;
            const endIndex = startIndex + this.pageSize;
            return this.oddata.pictures.slice(startIndex, endIndex);
        }
    },
    watch: {
        checkedlabels: {
            handler: 'updateFilteredPictures',
            deep: true
        },
        checkedclass: {
            handler: 'updateFilteredPictures',
            deep: true
        },
        oddata: function (newData) {
            this.taskData = newData;
        }
    },
    methods: {
        openimagemap(picture) {
            this.selectedPicture = picture;
            this.isImageMapDialogVisible = true;
            this.uniqueKey += 1;
        },
        clossImageMapDialog() {
            this.isImageMapDialogVisible = false;
            this.selectedPicture = null;
        },
        getTooltipContent(picture) {
            return picture.name; // 这里显示图片的名字
        },
        getImageUrl(picture) {
            const apiBaseUrl = 'api';
            return [`/${apiBaseUrl}/${picture.result_path}`];
        },
        handleCurrentChange(newPage) {
            this.currentPage = newPage;
        },
        handlelabelCheckAllChange(val) {
            this.checkedlabels = val ? labelOptions : [];
            this.isIndeterminate = false;
        },
        handleCheckedlabelsChange(value) {
            let checkedCount = value.length;
            this.labelcheckAll = checkedCount === this.labels.length;
            this.isIndeterminate = checkedCount > 0 && checkedCount < this.labels.length;
        },
        handleClassCheckAllChange(val) {
            this.checkedclass = val ? classOptions : [];
            this.isClassIndeterminate = false;
        },
        handleCheckedClassChange(value) {
            let checkedCount = value.length;
            this.classcheckAll = checkedCount === this.classes.length;
            this.isClassIndeterminate = checkedCount > 0 && checkedCount < this.classes.length;
        },
        matchesSelectedLabelsAndClass(pictureLabels, pictureClass) {
            // 判断图片是否符合同时选中的 label 和 class 条件
            const labelCondition = this.checkedlabels.length === 0 || this.checkedlabels.some((label) => pictureLabels.includes(label));
            const classCondition = this.checkedclass.length === 0 || this.checkedclass.some((classes) => pictureClass.includes(classes));

            return labelCondition && classCondition;
        },
        updateFilteredPictures() {
            this.filteredPictures = this.oddata.pictures.filter((picture) => {
                return this.matchesSelectedLabelsAndClass(picture.labels, picture.labels);
            });
        }
    }
};
</script>

<style lang="scss" scoped>
.gtp-container {
    width: 95%;
    height: 90%;
    /*display: flex;*/
    margin: 20px;
    justify-content: flex-start;

    .card-container {
        border-radius: 15px;
        width: 18%;
        height: 35%;
        margin: 1%;
        margin-top: 2%;
        float: left; /*卡片横排*/
        .clearfix h4 {
            margin: 15px 0 8px 0;
        }
        .clearfix p {
            margin: 0 0 8px 0;
        }
    }
}
.card-body {
    padding: 15px;
    width: 100%;
}
.card-name {
    font-size: 16px;
    /*设置规定长度*/
    width: 85%;
    /*内容会被修剪，并且其余内容是不可见的*/
    overflow: hidden;
    /*显示省略符号来代表被修剪的文本。*/
    text-overflow: ellipsis;
    /*设置一行显示*/
    white-space: nowrap;
}
.image-container {
    text-align: center;
    padding: 5px;
}
.info-container {
    padding: 5px;
}
.info-text {
    /*设置规定长度*/
    width: 95%;
    /*内容会被修剪，并且其余内容是不可见的*/
    overflow: hidden;
    /*显示省略符号来代表被修剪的文本。*/
    text-overflow: ellipsis;
    /*设置一行显示*/
    white-space: nowrap;
    margin-bottom: 10px;
}

.detection-filter {
    margin-bottom: 15px;
}

.filter-all {
    margin-bottom: 15px;
}

.filter-lab {
    margin-left: 20px;
    font-size: medium;
}

.filter-checkb {
    display: inline-flex;
}

.filter-checkb-all {
    margin-left: 10px;
    margin-right: 20px;
    border: 1px solid #dcdfe6;
    border-radius: 4px !important;
}

.filter-checkb-item {
    margin-right: 20px;
    border: 1px solid #dcdfe6;
    border-radius: 4px !important;
}

.el-pagination {
    position: fixed;
    right: 50px;
    bottom: 20px;
}
.panel-fold {
    height: 1px;
    position: absolute;
    left: 0;
    right: 0; /* 让水平线延伸到父元素的右侧 */
    top: 80px; /* 设置水平线距离父元素顶部的距离 */
    background: #e6e6e6;
    z-index: 999;
}
.panel-fold2 {
    height: 1px;
    position: absolute;
    left: 340px;
    right: 0; /* 让水平线延伸到父元素的右侧 */
    top: 120px; /* 设置水平线距离父元素顶部的距离 */
    background: #e6e6e6;
    z-index: 999;
}
.xqbtn {
}
.text-info {
    margin-top: 50px;
    font-size: 18px;
}
</style>
