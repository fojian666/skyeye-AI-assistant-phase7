<template>
    <div class="se-card-container">
        <el-card class="box-card" style="width: 100%; height: 100%; position: relative">
            <div slot="header" class="clearfix">
                <span>疑似违法线索——{{ data.clue_name }}</span>
            </div>
            <div class="body">
                <!-- <p>全景点位：{{ data.point_id }}</p> -->
                <p :title="data.create_time">拍摄时间：{{ data.create_time }}</p>
                <p>全景照片：{{ data.panorama_image_name }}</p>
                <p>所属区域：{{ data.region }}</p>
            </div>
            <div :class="status" class="status">{{ currentStatus }}</div>
        </el-card>
    </div>
</template>

<script>
export default {
    name: 'CardsComponent',
    props: {
        data: {
            type: Object,
            required: true
        },
        cardStatus: {
            //所有的业务状态集合
            type: Array,
            required: true
        }
    },
    data() {
        return {};
    },
    computed: {
        status() {
            //线索状态标签css的类
            return {
                'status-checked': this.data.clue_status === 1,
                'status-unchecked': this.data.clue_status === 0, //待审核
                'status-process': this.data.clue_status === 2 || this.data.clue_status === 3, //疑似
                'status-done': this.data.clue_status === 5 //有效
            };
        },
        currentStatus() {
            //当前线索状态
            if (this.data.clue_status === 3) {
                return this.cardStatus.filter((item) => {
                    return item.value === 2;
                })[0].name;
            }
            return this.cardStatus.filter((item) => {
                return item.value === this.data.clue_status;
            })[0].name;
        }
    },
    methods: {},
    created() {}
};
</script>

<style lang="scss" scoped>
.se-card-container {
    width: 100%;
    height: 100%;
    padding-right: 5px;
    cursor: pointer;
}
::v-deep .el-card__header,
::v-deep .el-card__body {
    padding-top: 5px; //设置卡片内边距
    padding-bottom: 5px;
}
.clearfix span {
    white-space: nowrap; /* 不换行 */
    text-overflow: ellipsis; /* 超出部分显示省略号 */
    font-size: 14px;
}
.body {
    white-space: nowrap; /* 不换行 */
    text-overflow: ellipsis; /* 超出部分显示省略号 */
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: space-around;
}
.body p {
    margin-bottom: 2px;
    font-size: 12px;
}
.status {
    position: absolute;
    right: -25px;
    top: 10px;
    width: 100px;
    height: 25px;
    line-height: 25px;
    text-align: center;
    color: #fff;
    font-size: 14px;
    transform: rotate(45deg);
    -ms-transform: rotate(45deg);
    -o-transform: rotate(45deg);
    -webkit-transform: rotate(45deg);
}
.status-checked {
    background: #27be82;
}
.status-unchecked {
    background: #ff6452;
}
.status-process {
    background: #11a8ed;
}
.status-done {
    background: #62de1c;
}
::v-deep .el-card .el-card__header {
    height: 20%;
    display: flex;
    flex-direction: column;
    justify-content: center;
}
::v-deep .el-card .el-card__body {
    height: 80%;
}

@media (max-height: 900px) {
    .clearfix span {
        font-size: 10px;
    }
    .body p {
        font-size: 8px;
    }
}
</style>
