<template>
  <div class="gtmap">
    <el-row :gutter="10">
      <el-col :xs="24" :sm="12" :md="7">
        <div class="left-box">
          <div class="top">
            <div class="task">
              <h3>您已累计处理任务批次：</h3>
              <ul>
                <li v-for="item in done_batch_count" :key="item">
                  {{ item }}
                </li>
                <li>项</li>
              </ul>
              <img src="@/assets/images/left-top-logo.png"  class="left-top-logo">
              <div class="new-check">
                <el-button class="new-task">新建任务</el-button>
                <el-button class="check-task">查看任务</el-button>
              </div>
            </div>
          </div>
          <div class="bottom">
            <div class="title">
              <div class="left-title">
                <i class="el-icon-menu"></i>
                <span>近七天批次完成情况</span>
              </div>
            </div>
            <div class="menu">
              <div ref="lineChart" class="left-chart"></div>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12" :md="10">
        <div class="middle-box">
          <div class="row1">
            <div class="title">
              <div class="left-title">
                <i class="el-icon-tickets"></i>
                <span>待办任务</span>
              </div>
              <div class="title-middle">
                <div class="total-task">{{todo_list.length}}</div>
              </div>
              <el-button class="more">更多></el-button>
            </div>
              <ul class="upcoming-tasks-content">
                <li v-for="(item,index) in todo_list" class="normal-status" @click="handleSkipPath(item.batch_id)">
                  <i class="iconfont icon-yuandian1"></i>{{item.text}}
                  <div class="status-group">
                      <span>{{item.create_time}}</span>
                  </div>
                </li>
              </ul>
          </div>
          <div class="row2">
            <div class="title">
              <div class="left-title">
                <i class="el-icon-folder-checked"></i>
                <span>已办任务</span>
              </div>
              <div class="title-middle">
                <div class="total-task">{{done_list.length}}</div>
              </div>
              <el-button class="more">更多></el-button>
            </div>
              <ul class="tasks-done-content">
                <li v-for="(item,index) in done_list" class="normal-status">
                  <i class="iconfont icon-zhuangtai_wancheng"></i>{{item.text}}
                  <div class="status-group">
                    <span>{{item.create_time}}</span>
                  </div>
                </li>
              </ul>
          </div>
          <div class="row3">
            <div class="konwledge-share">
              <div class="title">
                <div class="left-title">
                  <i class="el-icon-s-promotion"></i>
                  <span>线索类别分布</span>
                </div>

              </div>
              <div class="content">
                <div ref="piechartleft" class="left-chart"></div>
              </div>
            </div>
            <div class="software-download">
              <div class="title">
                <div class="left-title">
                  <i class="el-icon-mouse"></i>
                  <span>线索网格分布</span>
                </div>
              </div>
              <div class="content">
                <div ref="piechartright" class="left-chart"></div>
              </div>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12" :md="7">
        <div class="right-box">
          <div class="calendar">
            <div class="title">
              <div class="left-title">
                <i class="el-icon-tickets"></i>
                <span>日程安排</span>
              </div>
            </div>
            <div class="rili">
              <el-calendar v-model="selectdate" class="custom-calendar">
                <!-- 这里使用的是 2.5 slot 语法，对于新项目请使用 2.6 slot 语法-->
                <template slot="dateCell" slot-scope="{date, data}">
                  <div class="calendar-cell">
                    <div class="date" >{{ data.day.split('-').slice(2).join('-') }}</div>
                    <div class="events">
                      <!-- 数组循环 -->
                      <div v-for="(item, index) in uniqueDays" :key="index">
                        <div v-if="data.day == item.day" class="red-dot"  @click="handleClickRili(item.day,item.text)"></div>
<!--                        <el-popover-->
<!--                            placement="bottom"-->
<!--                            title="今日待办事项"-->
<!--                            trigger="click"-->
<!--                            :content="getTooltipContent(item.text)">-->
<!--                          <div v-if="data.day == item.day" class="red-dot" slot="reference"></div>-->
<!--                        </el-popover>-->
                      </div>
                    </div>
                  </div>
                </template>
              </el-calendar>
            </div>
          </div>
          <div class="month-task">
            <div class="title">
              <div class="left-title">
                <i class="el-icon-s-promotion"></i>
                <span>月度线索统计</span>
              </div>
            </div>
            <div class="echart">
              <div ref="histogramchart" class="histgramechart"></div>
            </div>
          </div>
          <div class="system-link">
            <div class="title">
              <div class="left-title">
                <i class="el-icon-s-promotion"></i>
                <span>系统链接</span>
              </div>
            </div>
            <div class="link">
              <ul class="system-link-content">
                <li>
                  <img src="@/assets/images/pingtai-1.png" alt="">
                  <span>智慧耕保系统</span>
                </li>
                <li>
                  <img src="@/assets/images/pingtai-1.png" alt="">
                  <span>激扬档案软件</span>
                </li>
                <li>                  <img src="@/assets/images/pingtai-1.png" alt="">
                  <span>自然资源管理信息工作平台</span>
                </li>
                <li>
                  <img src="@/assets/images/pingtai-1.png" alt="">
                  <span>自然资源基础信息平台</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>

</template>

<script>
import * as echarts from 'echarts'
import {getHomeScreenDataApi} from "@/api/commonApi";
export default {
  name:'home',
    components:{

    },
  data(){
    return{
      done_batch_count:'12345678',
      pieEchartLeftData:[
        {'name': '初始化', 'value': 1},
        {'name': '初始化2', 'value': 1},
        {'name': '初始化3','value': 1}
      ],
      pieEchartRightData:[],
      done_list:[],
      todo_list:[],
      month_list:[],
      count_list:[],
      lineChartData:{
        xAxis: ['2024-08-29', '2024-08-30', '2024-09-01', '2024-09-02', '2024-09-03', '2024-09-04', '2024-09-05'],
        series: [1, 1, 1, 1, 1, 1, 1]
      },
      selectdate:''
    }
  },
  methods:{
    initLineChart(){
      let line_chart = echarts.init(this.$refs.lineChart);
        const option = {
          xAxis: {
            type: 'category',
            boundaryGap: false,
            data: this.lineChartData.xAxis
          },
          yAxis: {
            type: 'value'
          },
          series: [
            {
              data: this.lineChartData.series,
              type: 'line',
              areaStyle: {}
            }
          ]
        };
        option && line_chart.setOption(option);
    },
    initPieEchartLeft() {
      let piechartleft = echarts.init(this.$refs.piechartleft);
      const option = {
        textStyle: {
          fontSize: 14,
        },
        toolbox: {
          show : true,
          feature : {
            mark : {show: true},
            dataView : {show: true, readOnly: false},
            magicType : {
              show: true,
              type: ['pie', 'funnel']
            },
            restore : {show: true},
            saveAsImage : {show: true}
          }
        },
        tooltip: {
          trigger: 'item',
          formatter: '{b} : {c}',//b为数据名，d为数据值
        },
        // legend: {
        //   orient: 'vertical',
        //   x: 'left',
        //   data:['张三','李四','王五','赵六']
        // },
        color: ['#49A9EE', '#8996E6','#F7A87E','#98D87D','#F3857B','red','#8996E6','#8996E6'],
        series: [
          {
            name:'线索数量（个）',
            type:'pie',
            selectedMode: 'single',
            radius: '75%',
            label: {

              show: true,
              formatter: '{a|{b}：{c}}\n{hr|}',
              //折线图文字颜色
              color:"black",
              rich: {
                //圆点位置大小配置
                hr: {
                  //auto自定义
                  backgroundColor: "auto",
                  borderRadius: 3,
                  width: 3,
                  height: 3,
                  padding: [3, 3, 0, -12]
                },
                a: {
                  padding: [-12, 10, -20, 15]
                },
              }
            },
            //折线图长度
            labelLine: {
              //第一段
              length: 15,
              //第二段
              length2: 25
            },
            data:this.pieEchartLeftData
          }
        ]
      };
      option && piechartleft.setOption(option);
    },
    initPieEchartRight() {
      let piechartleft = echarts.init(this.$refs.piechartright);
      const option = {
        textStyle: {
          fontSize: 14,
        },
        toolbox: {
          show : true,
          feature : {
            mark : {show: true},
            dataView : {show: true, readOnly: false},
            magicType : {
              show: true,
              type: ['pie', 'funnel']
            },
            restore : {show: true},
            saveAsImage : {show: true}
          }
        },
        tooltip: {
          trigger: 'item',
          formatter: '{b} : {c}',//b为数据名，d为数据值
        },
        // legend: {
        //   orient: 'vertical',
        //   x: 'left',
        //   data:['张三','李四','王五','赵六']
        // },
        series: [
          {
            name:'线索数量（个）',
            type:'pie',
            selectedMode: 'single',
            radius: '75%',
            label: {
              show: true,
              formatter: '{a|{b}：{c}}\n{hr|}',
              //折线图文字颜色
              color:"black",
              rich: {
                //圆点位置大小配置
                hr: {
                  //auto自定义
                  backgroundColor: "auto",
                  borderRadius: 3,
                  width: 3,
                  height: 3,
                  padding: [3, 3, 0, -12]
                },
                a: {
                  padding: [-12, 10, -20, 15]
                },
              }
            },
            //折线图长度
            labelLine: {
              //第一段
              length: 15,
              //第二段
              length2: 25
            },

            data:this.pieEchartRightData
          }
        ]
      };
      option && piechartleft.setOption(option);
    },
    initHistogramChart(){
      var monthlyChart = echarts.init(this.$refs.histogramchart);
      const monthlyChartOption = {
        tooltip: {
          trigger: 'axis',
          axisPointer: {            // 坐标轴指示器，坐标轴触发有效
            type: 'shadow'        // 默认为直线，可选为：'line' | 'shadow'
          }
        },
        color: ['#77b8fb', '#f5293d'],
        // legend: {
        //   data: ['已办', '待办'],
        //   top: 10
        // },
        grid: {
          left: '3%',
          right: '3%',
          bottom: '2%',
          top: '18%',
          containLabel: true
        },
        xAxis: [
          {
            type: 'category',
            data: this.month_list,
            axisTick: false,
            axisLine: {
              lineStyle: {
                color: '#e3e3e3'
              }
            },
            axisLabel: {
              color: '#767676',
              // interval: 0
            }
          }
        ],
        yAxis: [
          {
            type: 'value',
            axisTick: false,
            axisLine: {
              show: false,

            },
            axisLabel: {
              color: '#767676'
            },
            splitLine: {
              lineStyle: {
                color: '#e3e3e3'
              }
            }
          }
        ],
        series: [
          {
            name: '待办',
            type: 'bar',
            data: this.count_list,
            barWidth: 10
          }
        ]
      };
      monthlyChartOption && monthlyChart.setOption(monthlyChartOption);
    },
    getTooltipContent(item){
      return item;
    },
    handlePendingTask(){
      if (this.todo_list.length > 0) {
        this.$confirm('当前有待办任务，请点击日程安排区对应红色圆点查看，及时完成哦!!!','提示', {
          type:'warning',
          confirmButtonText:'确定',
          cancelButtonText:'取消'
        }).then(()=>{

        })
        . catch(()=>{})
      }
    },
    async getinfo(){
      const res = await getHomeScreenDataApi()
      if (res.code === 0){
        this.done_batch_count = res.data.done_batch_count.toString();
        if (res.data.clue_type_count_list.length !== 0){
          this.pieEchartLeftData = res.data.clue_type_count_list
        }
        if (res.data.clue_area_count_list.length !== 0){
          this.pieEchartRightData = res.data.clue_area_count_list
        }
        this.done_list = res.data.done_list
        this.todo_list = res.data.todo_list
        this.month_list = res.data.month_list
        this.count_list = res.data.count_list
        this.lineChartData.xAxis =  res.data.recent_seven_days_data
        this.lineChartData.series = res.data.recent_seven_days_count
        this.initPieEchartLeft()
        this.initPieEchartRight()
        this.initHistogramChart()
        this.initLineChart()
        this.handlePendingTask()
      }else{
        this.initPieEchartLeft()
        this.initPieEchartRight()
        this.initHistogramChart()
      }
    },
    handleSkipPath(batch_id){
      this.$router.push({path:'/panoramic-detection/main-detection',query:{batch_id}})
    },
    handleClickRili(day,item){
      // this.$message.info("点击")
      const i = item
      const tday = day
      this.$notify({
        title: `${tday}今日代办任务`,
        dangerouslyUseHTMLString: true,
        message: `<div style="float: unset;font-size: 1rem;height: 200px">${i}</div>`,
        position:'bottom-right',
        // duration: 0 // 设置通知持续时间，0 表示不自动关闭
      });

    }
  },
  mounted() {
    this.getinfo()

  },
  computed:{
    uniqueDays() {
      const unique = {};
      const regex = /\d{4}-\d{2}-\d{2}/; // 正则表达式匹配 YYYY-MM-DD 格式的日期
      this.todo_list.forEach(item => {
        const day = item.text.match(regex)[0];
        if (!unique[day]) {
          unique[day] = { day, count: 1, text: '<li>' + item.text +'</li>' };
        } else {
          unique[day].count += 1;
          unique[day].text += '<li>' + item.text +'</li>';
        }
      });
      return Object.values(unique);
    },
  }


}
</script>

<style scoped>
.gtmap {
  height: calc(100% - 4rem); /* 使用视窗的100%高度，使页面自适应 */
  padding: 10px;
  background-color: #eef2fa;
}

/* 左边盒子 */
.left-box {
  height: 100%;
  font-size: 1rem;
}
.left-chart{
  height: 100%;
}

.left-box .top,
.left-box .bottom{
  background-color: #fff;
  border-radius: 15px;
  padding: 10px;
  height: 49%;
  overflow: hidden;
}

.left-box .top {
  margin-bottom: 2%;
}
.task {
  width: 100%;
  height: 100%;
  background-color: #f0f5fc;
  padding: 0 0 20px;
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}
.task h3 {
  font-weight: 700;
  margin-left: 30px;
  font-style: italic;
  font-size: 1.5rem;
  margin-bottom: 5px;
}
.task ul {
  display: flex;
  width: 70%;
  height: 10%;
  margin-left: 20%;
}
.task ul li {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 25%;
  background-color: #f8c053;
  margin-right: 1px;
  border-radius: 5px;
  color: #fff;
  font-weight: 700;
  font-size: 1.2rem;
}
.task ul li:last-child{
  background-color: #ec775f;
}
.task .left-top-logo {
  margin: 0px auto;
  position: relative;
  display: block;
  width: 80%;
  height: 60%;
}
.new-check {
  width: 75%;
  height: 13%;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  margin-top: 20px;
}
.new-task,
.check-task{
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40%;
  height: 90%;
  border-radius: 5px;
  font-size: 1rem;
  text-align: center;
  line-height: 50px;
}
.new-task {
  background-color: #77b8fb;
  color: #fff;
}
.check-task {
  color: #77b8fb;
  background-color: #fff;
  border: 1px solid #77b8fb;
}

.title {
  width: 100%;
  height: 10%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: #77b8fb;
  display: flex;
}
.left-title {
  font-size: 1.2rem;
  line-height: 40px;
  border-bottom: 3px solid #77b8fb;

}
.left-title span {
  margin-left: 5px;
}
.title .edit {
  color: #77b8fb;
  line-height: 40px;
  font-size: 1rem;
}
.left-box .bottom {
  padding: 15px;
}
.left-box .bottom .menu {
  width: 100%;
  height: 100%;
  padding: 20px;
}
.left-box .bottom .menu ul {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  overflow-y: auto;
  width: 90;
  height: 90%;
}
.left-box .bottom .menu li {
  width: 25%;
  height: 20%;
  margin-bottom: 10px;
}
.left-box .bottom .menu li i {
  font-size: 4rem;
}
.left-box .bottom .menu p {
  font-size: 1.2rem;
}

  /* 中间盒子 */
.middle-box {
  height: 100%;
  font-size: 1rem;
}

.middle-box .row1,
.middle-box .row2,
.middle-box .row3 {
  background-color: #fff;
  border-radius: 15px;
  padding: 10px;
  height: 32%;
  box-sizing: border-box;
}
.p-10{
  padding: 10px;
}
.middle-box .row1,
.middle-box .row2{
  margin-bottom: 1.5%;
}
.middle-box .row1 .title,
.middle-box .row2 .title,
.middle-box .row3 .title {
  height: 40px;
}
.row1 .content {
  height: calc(100% - 40px);
  overflow-y: auto;
}
.more {
  width: 9%;
  height: 70%;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #edf1fa;
  border-radius: 10px;
  color: #77b8fb;
  font-size: 0.9rem;
}
.title-middle {
  flex: 1;
}
.title-middle .total-task {
  margin-left: 10px;
  width: 9%;
  background-color: #d24141;
  color: #fff;
  border-radius: 10px;
  text-align: center;
}
.middle-box .content ul {
  width: 80%;
}
.middle-box ul li {
  width: 100%;
  overflow: hidden; /* 隐藏溢出部分 */
  text-overflow: ellipsis; /* 溢出部分显示省略号 */
  white-space: nowrap; /* 不换行 */
}
.row2 .total-task {
  background-color: #77b8fb;
}
.row2 .content {
  height: 80%;
  overflow-y: auto;
}
.row3 {
    display: flex;
}
.row3 .konwledge-share,
.row3 .software-download{
  width: 50%;
  height: 100%;
}
.row3 .more{
  width: 15%;
  margin-right: 10px;
}
.row3 .konwledge-share {
  margin-right: 5px;
}
.content {
  height: calc(100% - 40px);
  padding: 10px 0;
  overflow-y: scroll;
}
.down-load {
  color: #0a6fc0;
  margin-right: 5px;
}
.middle-box .row3 .content ul{
  width: 95%;
}
.middle-box .row3 .content ul li {
  display: flex;
  justify-content: space-between;
  margin-bottom: 20px;
}

/* 右边盒子 */
.right-box {
  height: 100%;
  display: flex;
  flex-direction: column;
  font-size: 1rem;
}

.calendar{
  height: 45%;
  margin-bottom: 10px;
  overflow: hidden;
  overflow-y: auto;
  background-color: white;
  border-radius: 15px;
  padding: 10px;
}

.month-task,
.system-link {
  background-color: #fff;
  border-radius: 15px;
  padding: 10px;
}

.right-box .calender .title {
  margin-bottom: 0;
}
::v-deep .el-calendar-table .el-calendar-day {
  box-sizing: border-box;
  padding: 2px;
  height: 30px;
}
::v-deep .el-calendar-table thead th{
  padding: 12px 0;
  color: #606266;
  font-weight: 400;
  text-align: center;
}
::v-deep .el-popover__title {
  color: red !important;
  font-size: 16px !important;
  line-height: 1 !important;
  margin-bottom: 12px !important;
  font-weight: bold !important;
}

.custom-calendar .el-calendar-table th,
.custom-calendar .el-calendar-table td {
  border: none; /* 删除单元格的边框 */
}

.custom-calendar .el-calendar-table {
  border-collapse: collapse; /* 确保表格没有分隔线 */
}

.custom-calendar .el-calendar__header {
  border-bottom: none; /* 删除日历头部的边框 */
}

.calendar-cell {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.date {
  font-size: 14px;
  font-weight: bold;
}

.events {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.event {
  color: red;
  font-size: 10px;
}

.red-dot {
  width: 6px;
  height: 6px;
  background-color: red;
  border-radius: 50%;
}

::v-deep .el-calendar__body {
  padding: 10px;
}

.month-task {
  height: 30%;
  margin-bottom: 10px;
  flex-direction: column;
}

.month-task .more{
  width: 15%;
  height: 100%;
}
.echart {
  width: 100%;
  height: 90%;
  margin-top: 10px;
}
.system-link {
  height: 22%;
  display: flex;
  flex-direction: column;
}

.el-row {
  box-sizing: border-box;
  height: 100%;
}
.el-col-24 {
  height: 100%;
}

.overdue-status .iconfont {
  color: #d81e06;
}

.status-group span {
  background: #d81e06;
  color: #fff;
  font-size: 14px;
  height: 20px;
  line-height: 20px;
  padding: 0 10px;
  border-radius: 5px;
}

.upcoming-tasks-content{
  overflow-y: auto;
  height: 80%;
}
.upcoming-tasks-content .status-group {
  display: inline-block;
  position: absolute;
  right: 0;
  //width: 100px;
}
.upcoming-tasks-content .status-group span {
  display: inline-block;
  margin-right: 2px;
}

.upcoming-tasks-content li {
  height: 35px;
  line-height: 39px;
  padding-left: 8px;
  position: relative;
  cursor: pointer;
}
.upcoming-tasks-content li:hover{
  color: #77b8fb;
}

.upcoming-tasks-content li .iconfont {
  font-size: 18px;
  position: relative;
  top: 1px;
}
.upcoming-tasks-content .prograph {
  display: inline-block;
  font-size: 16px;
  position: absolute;
  left: 28px;
  top: 2px;
  right: 110px;
  white-space: nowrap;
  text-overflow: ellipsis;
  overflow: hidden;
}
.normal-status .iconfont {
  color: #d81e06;
}
.normal-status .status-group span {
  background: #77b8fb;
  color: #fff;
  font-size: 14px;
  height: 20px;
  line-height: 20px;
  padding: 0 10px;
  border-radius: 5px;
  cursor: pointer;
}
.pause-status .iconfont {
  color: #f8c053;
}
.pause-status .status-group span {
  background: #f8c053;
  color: #fff;
  font-size: 12px;
  height: 20px;
  line-height: 20px;
  padding: 0 10px;
  border-radius: 5px;
}
.tasks-done-content{
  overflow-y: auto;
  height: 80%;
}

.tasks-done-content li {
  height: 35px;
  line-height: 39px;
  padding-left: 8px;
  position: relative;
  //cursor: pointer;
}
.tasks-done-content li:hover{
  color: #77b8fb;
}

.tasks-done-content li .iconfont {
  font-size: 18px;
  position: relative;
  top: 1px;
  color: #77b8fb;
}

.tasks-done-content .prograph {
  display: inline-block;
  font-size: 16px;
  position: absolute;
  left: 28px;
  top: 2px;
  right: 0;
  white-space: nowrap;
  text-overflow: ellipsis;
  overflow: hidden;
}

.tasks-done-content .status-group {
  display: inline-block;
  position: absolute;
  right: 0;
}
.tasks-done-content .status-group span {
  display: inline-block;
  margin-right: 2px;
}

.link {
  display: flex;
  justify-content: space-between;
  width: 100%;
  height: 90%;
  margin-top: 20px;
}

.system-link-content {
  display: flex;
  flex-wrap: wrap;
  list-style: none;
  padding: 0;
  margin: 0;
  width: 100%;
}

.system-link-content li{
  flex: 0 0 50%;
  display: flex;
  align-items: center;
  position: relative;
}

.system-link-content img{
  width: 96%;
  height: auto;
  position: absolute;
  height: 90%;
  margin: 5px 5px;
}
.system-link-content span{
  margin-left: 79px;
  position: relative;
  z-index: 2;
  color: white;
  font-size: 14px;
}

.histgramechart{
  height: 100%;
  width: 100%;
}
::v-deep .el-notification__title {
  font-weight: 700;
  font-size: 1.2rem;
  color: #f5222d;
  margin: 0;
}
</style>
