
<template>
    <div class="se-container">
        <div class="top-content">
            <el-row class="custom-row">
                <el-col :span="8">
                    <div class="grid-content bg-purple">
                        <div class="top-title">
                            <div class="blue-fangkuai"></div>
                            <span>已判读疑似线索总体情况</span>
                            <div class="btn">
                                <el-button type="primary" size="mini" plain
                                           @click="updateClueStatisData('day')"
                                           :style="{'background-color': activeButton === 'day' ? '#409EFF' : '',
                                            'color': activeButton === 'day' ? '#fff' : ''}"
                                >今日</el-button>
                                <el-button type="primary" size="mini" plain
                                           @click="updateClueStatisData('week')"
                                           :style="{'background-color': activeButton === 'week' ? '#409EFF' : '',
                                            'color': activeButton === 'week' ? '#fff' : ''}"
                                >本周</el-button>
                                <el-button type="primary" size="mini" plain
                                           @click="updateClueStatisData('month')"
                                           :style="{'background-color': activeButton === 'month' ? '#409EFF' : '',
                                            'color': activeButton === 'month' ? '#fff' : ''}"
                                >本月</el-button>
                                <el-button type="primary" size="mini" plain
                                           @click="updateClueStatisData('year')"
                                           :style="{'background-color': activeButton === 'year' ? '#409EFF' : '',
                                            'color': activeButton === 'year' ? '#fff' : ''}"
                                >年度</el-button>
                            </div>
                        </div>
                        <div class="gt-chart">
                            <el-row :gutter="20" class="card-row">
                                <el-col :span="8">
                                    <div class="card" style="background: linear-gradient(to bottom, #5946f2 0%, #2575fc 100%);">
                                        <div class="card-header"><i class="iconfont icon-ziyuan"></i>线索总数</div>
                                        <div class="card-content">{{doneClueOverAll.clueTotal}}</div>
                                    </div>
                                </el-col>
                                <el-col :span="8">
                                    <div class="card" style="background: linear-gradient(to bottom, #7600fa 0%, #0083B0 100%);">
                                        <div class="card-header"><i class="iconfont icon-ziyuan"></i>已关闭线索数</div>
                                        <div class="card-content">{{doneClueOverAll.closeClueTotal}}</div>
                                    </div>
                                </el-col>
                                <el-col :span="8">
                                    <div class="card" style="background: linear-gradient(to bottom, #58dea8 0%, #5a9ddd 100%);">
                                        <div class="card-header"><i class="iconfont icon-ziyuan"></i>待核实线索数</div>
                                        <div class="card-content">{{ doneClueOverAll.pendingVerifyClueTotal }}</div>
                                    </div>
                                </el-col>
                            </el-row>
                            <el-row :gutter="20" class="card-row">
                                <el-col :span="8">
                                    <div class="card" style="background: linear-gradient(to bottom, #58dea8 0%, #5a9ddd 100%);">
                                        <div class="card-header"><i class="iconfont icon-ziyuan"></i>已整改线索数</div>
                                        <div class="card-content">{{doneClueOverAll.doneRectifyTotal}}</div>
                                    </div>
                                </el-col>
                                <el-col :span="8">
                                    <div class="card" style="background: linear-gradient(to bottom, #6aa7fa 0%, #5b78e7 100%);">
                                        <div class="card-header"><i class="iconfont icon-ziyuan"></i>待整改线索数</div>
                                        <div class="card-content">{{ doneClueOverAll.pendingRectifyTotal }}</div>
                                    </div>
                                </el-col>
                                <el-col :span="8">
                                    <div class="card" style="background: linear-gradient(to bottom, #ebc84f 0%, #e7867a 100%);">
                                        <div class="card-header"><i class="iconfont icon-ziyuan"></i>整改完成率</div>
                                        <div class="card-content">{{doneClueOverAll.rectifyFinshTotal}}</div>
                                    </div>
                                </el-col>
                            </el-row>
                        </div>
                    </div>
                </el-col>
                <el-col :span="8">
                    <div class="grid-content bg-purple">
                        <div class="top-title">
                            <div class="blue-fangkuai"></div>
                            <span>违法线索统计</span>
                            <div class="tab-btn">
                                <el-button type="primary" size="mini" plain
                                           @click="initBarChart('trend')"
                                           :style="{'background-color': activeButton2 === 'trend' ? '#409EFF' : '',
                                            'color': activeButton2 === 'trend' ? '#fff' : ''}"
                                >线索趋势</el-button>
                                <el-button type="primary" size="mini" plain
                                           @click="initChart('type')"
                                           :style="{'background-color': activeButton2 === 'type' ? '#409EFF' : '',
                                            'color': activeButton2 === 'type' ? '#fff' : ''}"
                                >线索类型</el-button>
                            </div>
                        </div>

                        <div class="gt-chart-pie" id="chart"></div>
                    </div>
                </el-col>
                <el-col :span="7">
                    <div class="grid-content bg-purple">
                        <div class="top-title">
                            <div class="blue-fangkuai"></div>
                            <span>国土所无人机巡查次数排行</span>
                        </div>
                        <div class="gt-rank">
                            <div class="rank-item" v-for="(item,index) in progressList" :key="index">
                                <img :src="getSvgPath(index)">
                                <!--                                <span class="rank-num">{{index}}</span>-->
                                <span>{{item.name}}</span>
                                <div class="progress-container">
                                    <el-progress :percentage=item.value :stroke-width="10" class="custom-progress"></el-progress>
                                </div>
                            </div>
                        </div>
                    </div>
                </el-col>
            </el-row>
        </div>
        <div class="bottom-content">
            <div class="condition">
                <div class="condition-item">
                    <span>行政区划</span>
                    <el-select v-model="condition.region" placeholder="请选择" clearable>
                        <el-option
                                v-for="item in regionOptions"
                                :key="item"
                                :label="item"
                                :value="item">
                        </el-option>
                    </el-select>
                </div>
                <div class="condition-item">
                    <span>线索类别</span>
                    <el-select v-model="condition.clue_type" placeholder="请选择" clearable>
                        <el-option
                                v-for="item in typeOptions"
                                :key="item"
                                :label="item"
                                :value="item">
                        </el-option>
                    </el-select>
                </div>
                <div class="condition-item">
                    <span>开始日期</span>
                    <el-date-picker
                            v-model="condition.start_time"
                            type="date"
                            placeholder="选择日期">
                    </el-date-picker>
                </div>
                <div class="condition-item">
                    <span>结束日期</span>
                    <el-date-picker
                            v-model="condition.end_time"
                            type="date"
                            placeholder="选择日期">
                    </el-date-picker>
                </div>
                <div class="condition-item">
                    <el-button type="primary" class="condition-btn" @click="getClueConfirmedTable">查询</el-button>
                    <!--                    <el-button type="primary" class="condition-btn">导出</el-button>-->
                    <el-button type="info" @click="resetQuery">重置</el-button>
                </div>
            </div>
            <div class="table">
                <el-table
                        :data="tableData"
                        border
                        style="width: 100%"
                        :header-cell-style="{'text-align':'center'}"
                        :cell-style="{'text-align':'center'}"
                >
                    <el-table-column
                            type="index"
                            width="50">
                    </el-table-column>
                    <el-table-column
                            prop="clue_id"
                            label="线索编号"
                            width="180">
                    </el-table-column>
                    <el-table-column
                            prop="label"
                            label="线索类别"
                            width="180">
                    </el-table-column>
                    <el-table-column
                            prop="address"
                            label="所属区域">
                    </el-table-column>
                    <el-table-column
                            prop="create_time"
                            label="发现时间">
                    </el-table-column>
                    <el-table-column
                            prop="verification_conclusion"
                            label="核查结论">
                    </el-table-column>
                    <el-table-column
                            label="线索查看">
                        <template slot-scope="scope">
                            <li style="color: #0f9dfe" @click="handleViewClueDetails(scope.row)">查看详情</li>
                        </template>
                    </el-table-column>
                    <el-table-column
                            prop="status"
                            label="状态">
                        <template slot-scope="scope">
                            <div class="status-cell flexbox">
                                <div :style="{ backgroundColor: getStatusColor(scope.row.status)[0] }" class="status-bg">{{ getStatusColor(scope.row.status)[1]}}</div>
                            </div>
                        </template>
                    </el-table-column>
                    <el-table-column
                            prop="create_time"
                            label="整改日期">
                    </el-table-column>
                </el-table>
            </div>
            <el-pagination
                    small
                    background
                    @current-change="handleCurrentChange"
                    :current-page="page"
                    :page-size="limit"
                    layout="prev, pager, next, total,jumper"
                    :total="dataCount"
                    style="position:fixed;bottom: 25px;right: 20px">
            </el-pagination>
        </div>
        <div class="image" v-show="activeClueImage">
            <div class="gt-header">
                <el-descriptions title="线索详情" style="padding-left: 6px"></el-descriptions>
                <div @click="closeImage"><i class="el-icon-close close-i"></i></div>
            </div>
            <div class="gt-image">
                <img :src="imgSrc">
            </div>
        </div>
    </div>
</template>
<script >
    import * as echarts from "echarts";
    import {
        getClueConfirmedTableApi, getCluePictureApi,
        getClueStatisDataApi,
        getVillageListApi,
        statisticsIllegalCluesApi
    } from "@/api/commonApi";
    export default {
        name:'dataStatics',
        data(){
            return{
                progressList:[
                    {'name':'六合区','value':100},
                    {'name':'高淳区','value':70},
                    {'name':'溧水区','value':50},
                    {'name':'建邺区','value':50},
                ],
                tableData:[],
                page:1,
                limit:5,
                dataCount:0,
                condition:{
                    clue_type:'',
                    region:'',
                    start_time:'',
                    end_time:''
                },
                myChart:null,
                regionOptions:[],
                typeOptions:[],
                doneClueOverAll:{
                    clueTotal:0,
                    closeClueTotal:0,
                    pendingVerifyClueTotal:0,
                    doneRectifyTotal:0,
                    pendingRectifyTotal:0,
                    rectifyFinshTotal:0
                },
                activeButton:'day',
                activeButton2:'trend',
                dayData:{},
                weekData:{},
                monthData:{},
                yearData:{},
                barData:{
                    months:[],
                    counts_fl:[],
                    counts_fn:[],
                    counts_wj:[],
                },
                pieData:[],
                imgSrc:'',
                baseUrl: process.env.VUE_APP_API_URL,//请求地址
                activeClueImage:false
            }
        },
        methods:{
            initChart(tag){
                this.activeButton2 = tag;
                if (this.myChart) {
                    this.myChart.dispose(); // 销毁当前图表实例
                }
                this.myChart = echarts.init(document.getElementById('chart')
                );
                const option = {
                    tooltip: {
                        trigger: 'item',
                        formatter: '{a} <br/>{b} : {c} ({d}%)'
                    },
                    legend: {
                        top:'30%',
                        orient: 'vertical',
                        left: 'right',
                        data: ['违规建房', '耕地非农化', '耕地非粮化', '乱堆垃圾'],
                        textStyle: {
                            color:' #000' // 设置字体颜色为黑色
                        }
                    },
                    series: [
                        {
                            name: '总数量',
                            type: 'pie',
                            radius: ['40%', '90%'],
                            avoidLabelOverlap: false,
                            label: {
                                show: true,
                                position: 'inside',
                                formatter: '{d}%',
                                color: '#fff'
                            },
                            labelLine: {
                                show: false
                            },
                            itemStyle: {
                                borderRadius: 10,
                                borderColor: '#fff',
                                borderWidth: 2
                            },
                            emphasis: {
                                label: {
                                    show: true,
                                    fontSize: '16',
                                    fontWeight: 'bold'
                                }
                            },
                            data: this.pieData
                        }
                    ]
                }
                this.myChart.setOption(option);
            },
            // 根据索引返回不同的 SVG 图案路径
            getSvgPath(index) {
                return require(`@/assets/images/${index + 1}.png`);
            },
            //处理当前页码的转换
            handleCurrentChange(val) {
                // 改变页码
                this.page = val;
            },
            //设置任务状态颜色
            getStatusColor(status) {
                switch (status) {
                    // case '●部分检测':
                    case 5:
                        return ['#f3d6da',"待整改"];
                    case 6:
                        return ['#dfedfd',"已整改"];
                    default:
                        return '#dfedfd';
                }
            },


            initBarChart(tag){
                this.activeButton2 = tag;
                if (this.myChart) {
                    this.myChart.dispose(); // 销毁当前图表实例
                }
                this.myChart = echarts.init(document.getElementById('chart')
                );
                const option = {
                    tooltip: {
                        trigger: 'axis',
                        axisPointer: {
                            type: 'shadow'
                        }
                    },
                    legend: {
                        data: ['耕地非农化', '违规建房', '耕地非粮化'],
                        top: '5%',
                        textStyle: {
                            color:' #000' // 设置字体颜色为黑色
                        }
                    },
                    grid: {
                        left: '3%',
                        right: '4%',
                        bottom: '3%',
                        containLabel: true
                    },
                    xAxis: {
                        type: 'category',
                        data: this.barData.months,
                        axisTick: {
                            alignWithLabel: true,
                            show: true // 显示轴线
                        },
                        axisLabel: {
                            textStyle: {
                                color: '#000' // 设置字体颜色为黑色
                            }
                        },
                        axisLine: {
                            show: true // 显示轴线
                        }
                    },
                    yAxis: {
                        type: 'value',
                        name: '数量（个）',
                        position: 'left',
                        axisLabel: {
                            textStyle: {
                                color: '#000' // 设置字体颜色为黑色
                            }
                        },
                    },
                    series: [
                        {
                            name: '耕地非农化',
                            type: 'bar',
                            data: this.barData.counts_fn,
                            itemStyle: {
                                color: '#06c8f9', // 蓝色
                                borderRadius: [5, 5, 5, 5], // 圆角设置
                                borderColor: '#fff', // 边框颜色
                                borderWidth: 1 // 边框宽度
                            }
                        },
                        {
                            name: '违规建房',
                            type: 'bar',
                            data: this.barData.counts_wj,
                            itemStyle: {
                                color: '#4be4b2', // 青色
                                borderRadius: [5, 5, 5, 5], // 圆角设置
                                borderColor: '#fff', // 边框颜色
                                borderWidth: 1 // 边框宽度
                            }
                        },
                        {
                            name: '耕地非粮化',
                            type: 'bar',
                            data: this.barData.counts_fl,
                            itemStyle: {
                                color: '#ffbe41', // 橙色
                                borderRadius: [5, 5, 5, 5], // 圆角设置
                                borderColor: '#fff', // 边框颜色
                                borderWidth: 1 // 边框宽度
                            }
                        }
                    ]
                };
                this.myChart.setOption(option);
            },
            updateClueStatisData(tag){
                this.activeButton = tag
                if (tag == 'day'){
                    this.doneClueOverAll.clueTotal = this.dayData.day_count
                    this.doneClueOverAll.closeClueTotal = this.dayData.day_closed_count
                    this.doneClueOverAll.pendingVerifyClueTotal = this.dayData.day_verified_count
                    this.doneClueOverAll.doneRectifyTotal = this.dayData.day_rectified_count
                    this.doneClueOverAll.pendingRectifyTotal = this.dayData.day_pending_rectification_count
                    this.doneClueOverAll.rectifyFinshTotal = this.dayData.percent
                }if (tag == 'week'){
                    this.doneClueOverAll.clueTotal = this.weekData.week_count
                    this.doneClueOverAll.closeClueTotal = this.weekData.week_closed_count
                    this.doneClueOverAll.pendingVerifyClueTotal = this.weekData.week_verified_count
                    this.doneClueOverAll.doneRectifyTotal = this.weekData.week_rectified_count
                    this.doneClueOverAll.pendingRectifyTotal = this.weekData.week_pending_rectification_count
                    this.doneClueOverAll.rectifyFinshTotal = this.weekData.percent
                }if ( tag == 'month'){
                    this.doneClueOverAll.clueTotal = this.monthData.month_count
                    this.doneClueOverAll.closeClueTotal = this.monthData.month_closed_count
                    this.doneClueOverAll.pendingVerifyClueTotal = this.monthData.month_verified_count
                    this.doneClueOverAll.doneRectifyTotal = this.monthData.month_rectified_count
                    this.doneClueOverAll.pendingRectifyTotal = this.monthData.month_pending_rectification_count
                    this.doneClueOverAll.rectifyFinshTotal = this.monthData.percent
                }if ( tag == 'year'){
                    this.doneClueOverAll.clueTotal = this.yearData.year_count
                    this.doneClueOverAll.closeClueTotal = this.yearData.year_closed_count
                    this.doneClueOverAll.pendingVerifyClueTotal = this.yearData.year_verified_count
                    this.doneClueOverAll.doneRectifyTotal = this.yearData.year_rectified_count
                    this.doneClueOverAll.pendingRectifyTotal = this.yearData.year_pending_rectification_count
                    this.doneClueOverAll.rectifyFinshTotal = this.yearData.percent
                }
            },
            async getClueStatisData(){
                //获取线索统计
                const res = await getClueStatisDataApi()
                if (res.code === 0){
                    this.dayData = res.data.day
                    this.weekData = res.data.week
                    this.monthData = res.data.month
                    this.yearData = res.data.year
                    this.updateClueStatisData('day')
                }else{
                    this.$message.error(res.msg)
                }
                const res2 = await statisticsIllegalCluesApi() //获取柱状图数据
                if (res2.code === 0){
                    this.barData = res2.data
                    this.pieData = res2.data.values
                    this.initBarChart('trend');
                }else{
                    this.$message.error(res2.msg)
                }

            },
            async getVillageList(){
                const res = await getVillageListApi()
                if (res.code == 0){
                    this.regionOptions = res.data.region_data
                    this.typeOptions = res.data.category_data
                }
            },
            async getClueConfirmedTable(){
                const para = {
                    limit: this.limit,
                    page: this.page,
                    village: this.condition.region,
                    keyword: this.condition.clue_type,
                }
                const res = await getClueConfirmedTableApi(para)
                if (res.code === 0){
                    this.dataCount = res.count
                    this.tableData = res.data
                }
            },
            async handleViewClueDetails(row){
                this.activeClueImage = true
                this.imgSrc = `${this.baseUrl}/common/clue_view/${row.clue_id}`
            },
            closeImage(){
                this.activeClueImage = false
                this.imgSrc = ''
            },
            resetQuery(){
                this.condition.clue_type = ''
                this.condition.region = ''
                this.condition.end_time = ''
                this.condition.start_time = ''
            }

        },
        mounted() {
            this.getClueStatisData()
            this.getClueConfirmedTable()
        },
        created() {
            this.getVillageList()
        }
    }
</script>
<style scoped>
    .se-container{
        height: calc(100% - 4rem);
        width: 100%;
        display: flex;
        padding: 10px;
        flex-direction: column;
        justify-content: space-between;
        background-color: #f0f0f0;

    }
    .top-content{
        height: 40%;
        width: 100%;
        display: inline-block;
    }
    .bottom-content{
        height: 58%;
        width: 99%;
        background-color: white;
        display: flex;
        flex-direction: column;
        margin-left: 10px;
        margin-right: 10px;
        border-radius: 4px;
    }
    .el-row {
        margin-bottom: 20px;
    &:last-child {
         margin-bottom: 0;
     }
    }
    .el-col {
        border-radius: 4px;
        height: 100%;
    }

    .bg-purple {
        background: white;

    }

    .grid-content {
        border-radius: 4px;
        height: 100%;

    }
    .row-bg {
        padding: 10px 0;
        background-color: #f9fafc;
    }
    .top-title{
        height: 40px;
        display: flex;
        flex-direction: row;
        align-items: center;
        border-bottom: #1a4396 1px solid;
    }
    .blue-fangkuai{
        height: 25px;
        width: 25px;
        background-color: #5b85ef;
        margin-left: 10px;
    }
    .custom-row {
        display: flex;
        justify-content: space-between;
        height: 100%;
    }

    .custom-row .el-col {
        margin: 0 auto; /* 使列居中对齐 */
    }
    .top-title span{
        padding-left: 10px;
        font-weight: bold;
        font-size: 16px;
        width: 45%;
    }
    .btn{
    }
    .gt-chart{
        width: 95%;
        margin: 15px auto;
        height: calc(100% - 70px);
    }

    .gt-rank{
        width: 95%;
        margin: 5px auto;
        height: 100%;
    }
    .gt-chart-pie{
        width: 100%;
        height: calc(100% - 40px);
    }
    .card-row {
        height: calc(50% - 10px);
    }

    .card {
        color: white;
        height: 100%;
        padding: 10px;
        border-radius: 8px;
    }

    .card-header {
        font-size: 16px;
        margin-left: 10px;
        margin-bottom: 5px;
        height: 45%;
    }

    .card-content {
        font-size: 30px;
        font-weight: bold;
        text-align: center;
    }
    .iconfont {
        font-size: 20px;
    }
    .rank-item{
        display: flex;
        flex-direction: row;
        height: calc((100% - 40px)/5 - 10px);
        width: 100%;
        margin-top: 10px;
        overflow-y: auto;
    }
    .rank-item img{
        height: 30px;
        width: 30px;
    }
    .progress-container {
        flex-grow: 1; /* 让进度条容器占据剩余空间 */
        margin-left: 10px; /* 添加一些间距 */
    }
    .rank-item span{
        margin-left: 10px;
        width: 50px;
    }
    .rank-num{
        position: absolute;
        color: black;
    }

    :deep(.custom-progress .el-progress-bar__inner) {
        background-image: linear-gradient(135deg, #43C6AC 0%, #F8FFAE 100%)
    }
    .condition{
        height: 50px;
        width: 100%;
        margin-top: 10px;
        display: flex;
        flex-direction: row;
        align-items: center;
    }
    .condition-item{
        margin-left: 20px;
    }
    .condition-item span{
        margin-right: 5px;
    }
    .condition-btn {
        color: #FFF;
        background-color: #5063cc;
        border-color: #5063cc;
    }
    ::v-deep .el-pagination.is-background .el-pager li:not(.disabled).active {
        background-color: #5063cc;
        color: #FFF;
    }
    li{
        list-style: none;
        cursor: pointer;
        font-weight: bold;
    }
    .table{
        margin: 10px;
    }
    .status-cell {
        display: flex;
        justify-content: center;
        align-items: center;
        width: 100%;
        height: 100%;
    }

    .status-bg {
        width: 50px;
        text-align: center;
        padding: 5px 0; /* 根据需要调整内边距 */
    }
    .gt-image img{
        width: 590px;
        height: 550px;
        padding-top: 5px;
    }
    .image {
        position: absolute;
        width: 600px;
        height: 600px;
        z-index: 1000;
        overflow: auto;
        display: flex;
        flex-direction: column;
        padding: 5px;
        background-color: #f3f3f352;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        box-shadow: 0 0 20px rgba(0,0,0,0.2);
        border-radius: 8px;
    }
    .gt-header {
        display: flex;
        padding-left: 6px;
        height: 32px;
        line-height: 32px;
        background-color: #ebeef5;
    }
    .close-i{
        cursor: pointer;
        font-size: 30px;
    }
</style>
