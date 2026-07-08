<template>
    <div class="gtp-container">
        <el-card class="box-card" style="width: 100%; height: 100%; position: relative">
            <div slot="header" class="clearfix">
                <span>核查点位——{{ data.address }}</span>
            </div>
            <div class="body">
                <p>线索编号：{{ data.clue_id }}</p>
                <p :title="data.record_time">拍摄时间：{{ data.record_time }}</p>
                <p>所属区域：{{ data.division_code }}</p>
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
        cardStatus:{
            //所有的业务状态集合
            type: Array,
            required: true,
        }
    },
    data() {
        return {};
    },
    computed: {
        status() {
            //线索状态标签css的类
            return {
                'status-checked': this.data.status === '已核实',
                'status-unchecked': this.data.status === '待核实',
            };
        },
        currentStatus(){
            //当前线索状态
            return this.cardStatus.filter(item=>{return item.value===this.data.status})[0].name
        }
    },
    methods: {},
    created() {

    }
};
</script>

<style lang="scss" scoped>
.gtp-container {
  width: 100%;
  height: 100%;
  padding-right: 5px;
  cursor: pointer;
}
::v-deep .el-card__header,
::v-deep .el-card__body {
  padding-top: 5px;//设置卡片内边距
  padding-bottom: 5px;
}
.clearfix span{
  white-space: nowrap; /* 不换行 */
  text-overflow: ellipsis; /* 超出部分显示省略号 */
  font-size: 16px;
}
.body {
  white-space: nowrap; /* 不换行 */
  text-overflow: ellipsis; /* 超出部分显示省略号 */
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: space-around;
}
.body p{
  margin-bottom: 2px;
  font-size: 14px;
}
.status {
  position: absolute;
  right: 10px;
  top: 25px;
  width: 60px;
  height: 25px;
  line-height: 25px;
  text-align: center;
  color: #fff;
  font-size: 14px;
  border-radius: 10px;
}
.status-checked {
  background: #27be82;
}
.status-unchecked {
  background: #ff6452;
}
.status-process{
  background: #2DB6F4;
}
::v-deep .el-card .el-card__header{
  height: 20%;
  display: flex;
  flex-direction: column;
  justify-content: center;
}
::v-deep .el-card .el-card__body{
  height: 80%;
}

@media (max-height: 900px) {
  .clearfix span{
    font-size: 10px;
  }
  .body p{
    font-size: 8px;
  }

}
</style>
