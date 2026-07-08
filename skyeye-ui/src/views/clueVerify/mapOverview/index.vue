<template>
    <div class="se-container">
        <div class="left-content">
            <div class="overview">
                <!-- 地图总览图标-->
                <div class="panorama">
                    <div style="background-color: #b9ff91">{{ overViewInfo.total_count }}</div>
                    <div>全部线索</div>
                </div>
                <div class="closed">
                    <div style="background-color: #11A8ED">{{ overViewInfo.total_done_count }}</div>
                    <div>已核实点数</div>
                </div>
                <div class="check">
                    <div style="background-color: #ff6452">{{ overViewInfo.total_todo_count }}</div>
                    <div>待核实点数</div>
                </div>
            </div>
            <div class="filter">
                <!--线索筛选-->
                <el-form :model="formInfo">
                    <el-form-item>
                        <span>所属区域:</span>
                        <el-select style="width: 90px; margin: 0 5px" v-model="formInfo.division_code" clearable>
                            <el-option v-for="(item,index) in xzqNameList" :key="index" :label="item" :value="item"></el-option>
                        </el-select>
                        <span>业务状态:</span>
                        <el-select style="width: 90px; margin: 0 5px" v-model="formInfo.status" clearable>
                            <el-option v-for="(item,index) in statusList" :key="item.value" :label="item.name" :value="item.value"></el-option>
                        </el-select>
                    </el-form-item>
                    <el-form-item>
                        <el-date-picker type="daterange" style="width: 315px; margin: 0 5px 0 0" v-model="formInfo.dataRange"
                                        range-separator="至"
                                        start-placeholder="开始日期"
                                        end-placeholder="结束日期"
                                        :unlink-panels="true"></el-date-picker>
                    </el-form-item>
                    <el-form-item>
                        <span>任务编号:</span>
                        <el-select style="width: 190px; margin: 0 5px" v-model="formInfo.verify_task" clearable>
                            <el-option v-for="(item,index) in taskNumList" :key="index" :label="item.task_name" :value="item.task_id"></el-option>
                        </el-select>
                        <el-button type="primary" @click="searchClue" style="background-color: #11A8ED">搜索</el-button>
                    </el-form-item>
                </el-form>
            </div>
            <div class="cards-container">
                <div v-for="(item, index) in clueList" :key="index" :class="{ 'is-active': index === activeCardIndex }" @click="setActiveCard(index,item)"
                     style="height: 20%">
                    <cards-component :data="item" :cardStatus="statusList"></cards-component>
                </div>
            </div>
            <div class="page">
                <el-pagination
                        small
                        background
                        @current-change="handleCurrentChange"
                        :current-page="formInfo.page"
                        :page-sizes="[5]" :pager-count="5"
                        :page-size="formInfo.limit"
                        layout="prev, pager, next, total"
                        :total="dataCount"
                        style="position:fixed;bottom: 10px">
                </el-pagination>
            </div>
        </div>
        <div class="border"></div>
        <div class="right-content">
            <map-component :activeMarker="activeMarker"
                           :activeItem="activeItem"
                           @marker="getMarker"
                           ref="mapComponent"
            >

            </map-component>
        </div>
    </div>
</template>

<script>
import CardsComponent from './Cards.vue';
import MapComponent from './map.vue';
import {
    getOverViewData,
    getClueData,
    verifyClueApi,
    getVerifyTaskParamsApi
} from '@/api/commonApi'

export default {
    name: 'MapOverView',
    data() {
        return {
            baseUrl:process.env.VUE_APP_API_URL,//请求地址
            xzqNameList:[],//获取的网格数据列表
            statusList:[{value:'1',name:'待核实'},{value:'0',name:'已核实'}],//获取的业务状态列表
            activeCardIndex: null,//激活的卡片
            activeMarker:0,//激活的线索坐标
            activeItem:'',
            dataCount: 0, //数据总数
            overViewInfo: {
                total_count: '2',
                total_done_count: '2',
                total_todo_count: '0'
            }, //总体线索数据
            formInfo: {
                division_code:'',
                status:'',
                start_data: '',
                end_data: '',
                page: 1,
                limit: 5,
                dataRange:[],
                verify_task:''
            }, //筛选表单参数
            clueList1: [], //线索数据列表
            taskNumList:[],
            clueList:[],
            verifyTaskId:''
        };
    },
    components: {
        CardsComponent,
        MapComponent
    },
    watch:{
    },
    methods:{
        async resetForm(){
            this.formInfo.dataRange = []
            this.formInfo.division_code = ''
            this.formInfo.status = ''
            this.formInfo.verify_task = ''
        },
        async getMarker(clueData){
            // 地图子组件marker点击后设置线索激活
            this.activeCardIndex = null
            this.activeMarker = clueData.alarm_id
            this.activeItem = clueData
        },
        handleCurrentChange(val) {
            // 改变页码
            this.formInfo.page = val;
            this.activeCardIndex = null
            this.activeMarker = 0
            this.activeItem = {}
            this.getClue();
        },
        setActiveCard(index,item) {
            //设置激活的线索卡片
            this.activeCardIndex = index
            // this.activeClueImage = `${this.baseUrl}/common/clue_view/${item.clue_id}`
            this.activeMarker = item.clue_id
            this.activeItem = item
        },

        async getClue(){
            const para = {
                status:this.formInfo.status,
                division_code:this.formInfo.division_code,
                start_date:this.formInfo.start_data,
                end_date:this.formInfo.end_data,
                verify_task_id:this.formInfo.verify_task,
                page: this.formInfo.page,
                limit: 5,
            }
            const res = await verifyClueApi(para)
            if (res.code==0){
                this.clueList = res.data
                this.dataCount = res.count
            }else{
                this.$message.error(res.msg)
            }
        },

        async searchClue(){
            //搜索线索
            this.activeCardIndex = null
            this.activeMarker = 0
            this.formInfo.page = 1
            this.activeItem = {}
            await this.getClue()
            this.$refs.mapComponent.handelUpdateClues(this.formInfo.verify_task)
        },

        async getVerifyTaskParams(){
            const res = await getVerifyTaskParamsApi()
            if (res.code==0){
                this.xzqNameList = res.data.division_code_list
                this.statusList = res.data.verify_clue_status
                this.taskNumList = res.data.verify_task_name_list
                this.overViewInfo.total_count = res.data.total_count
                this.overViewInfo.total_done_count = res.data.total_done_count
                this.overViewInfo.total_todo_count = res.data.total_todo_count

            }else{
                this.$message.error(res.msg)
            }
        }
    },
    async created() {
        await this.getVerifyTaskParams()
        this.formInfo.verify_task = this.$route.query.task_id;

        if (this.formInfo.verify_task){
            // this.formInfo.verify_task = this.formInfo.verify_task
        }else{
            this.formInfo.verify_task = ''
        }
        this.getClue()
    },
    computed:{
    },
};
</script>

<style lang="scss" scoped>
.se-container {
  height: 100%;
}
.overview {
  display: flex;
  flex-direction: row;
  justify-content: space-around;
  height: 90px;//图标高度
}
.panorama div:last-of-type,
.closed div:last-of-type,
.check div:last-of-type {
  //字体设置
  width: 60px;
  height: 20px;
  line-height: 20px;
  text-align: center;
  font-size: 12px;
}
.panorama div:first-of-type,
.closed div:first-of-type,
.check div:first-of-type {
  //符号设置
  width: 60px;
  height: 60px;
  display: flex;
  justify-content: center;
  align-items: center;
  border-radius: 50%;
  color: white;
  font-size: 20px;
  font-weight: bold;
}
.left-content {
  width: 320px;
  height: calc(100% - 20px);
  position: relative;
  margin:10px 0 10px 10px;
}

.right-content {
  width: calc(100% - 340px);//计算剩余宽度
  height: 100%;
}
.border{
  width: 10px;
  margin-right: 10px;
  height: 100%;
  border-right: 1px solid #cccccc; //边框设置
}
.filter {
  height: 120px;//筛选的宽度
}
.page{
  position: absolute;
  left: 0;
  bottom: 0;
}
.el-form-item{
  margin-bottom: 5px;
}
.cards-container{
  height: calc(100% - 250px);//卡片容器高度
  overflow: hidden;
}
::v-deep .is-active .el-card {
  border: 1px solid #42b4f2;
}

.el-pager li,
.el-pagination__editor,
.el-pagination .btn-prev,
.el-pagination .btn-next {
  margin: 0 1px !important;
}
::v-deep .el-form-item .el-range-separator{
  width: 10%;
}
</style>
