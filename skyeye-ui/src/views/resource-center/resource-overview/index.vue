<template>
    <div
            style="
      margin: 10px auto;
      overflow-y: hidden;
      width: 98%;
      height: 100%;
      background-color: transparent;
    "
    >
        <a-row type="flex" class="resOverviewBox">
            <!-- 第一列： 服务注册数量 + 目标检测种类分布 -->
            <a-col class="card-box">
                <!-- 服务注册数量 -->
                <a-card :bordered="false">
                    <div slot="title">
                        <span class="iconfont icon-geoai-line card-title-font"/>任务数量
                    </div>
                    <div id="serverRegisterId">
                        <a-radio-group
                                :value="serverRegisteCountValue"
                                @change="serverRegisteCount"
                        >
                            <a-radio-button value="week">近一周</a-radio-button>
                            <a-radio-button value="month">近一月</a-radio-button>
                            <a-radio-button value="year">近一年</a-radio-button>
                        </a-radio-group>
                    </div>
                    <div
                            id="serverRegisteCountChart"
                            class="card-content"
                            style="padding-top: 40px"
                    ></div>
                </a-card>
                <!-- 目标检测种类分布 -->
                <a-card :bordered="false">
                    <div slot="title">
                        <span class="iconfont icon-geoai-ad-line card-title-font"/>全景定位误差曲线（0-700米）
                    </div>
                    <div id="objectDetectionCategoryChart" class="card-content"></div>
                </a-card>
            </a-col>
            <!-- 第二列： 全景融合种类分布 + 近七天使用数量 -->
            <a-col class="card-box">
                <!-- 全景融合种类分布 -->
                <a-card :bordered="false">
                    <div slot="title">
                        <span class="iconfont icon-geoai-pie card-title-font"/>线索类型数量分布
                    </div>
                    <div id="mapViewCategoryChart" class="card-content"></div>
                </a-card>
                <!-- 近七天使用数量 -->
                <a-card :bordered="false">
                    <div slot="title">
                        <span class="iconfont icon-geoai-file-download card-title-font"/>近七天使用数量
                    </div>
                    <div id="serviceUsageCountChart" class="card-content">
                        <ul class="task-config-list">
                            <li
                                    class="task-config-list-item"
                                    @click="downloadReport($event)"
                                    v-for="item in reportDownload"
                                    :data-id="item.report_id"
                                    :data-path="item.file_path"
                                    title="点击预览文件"
                            >
                                <i class="iconfont icon-geoai-review1"></i>
                                <span class="task-config-list-text">{{
                                        item.report_name
                                    }}</span>
                                <span class="task-config-list-date">{{
                                        item.report_create_time
                                    }}</span>
                            </li>
                        </ul>
                    </div>
                </a-card>
            </a-col>
        </a-row>
    </div>
</template>

<script>
    import * as echarts from 'echarts'
    import {getResourceData} from "@/api/commonApi";

    export default {
        name: 'ResourceOverview',
        data() {
            return {
                serverRegisteCountValue: '',
                reportDownload: [],
                chartsData: {}
            };
        },
        methods: {
            async getAllData() {
                const than = this;

                const res = await getResourceData();
                if (res.code === 0) {
                    than.chartsData = res.data;
                    than.initCharts();
                    // try {
                    //     //  初始化图表
                    //     than.initCharts();
                    // } catch (err) {
                    //     console.log(err)
                    //     than.$message.error('图表初始化失败！', 3);
                    // }
                    // console.log(res);
                } else {
                    than.$message.warning('数据返回失败！', 3);
                }

            },
            initCharts() {
                this.serverRegisteCount();
                this.mapViewCategory();
                this.objectDetectionCategory();
                this.serviceUsageCount();
            },
            serverRegisteCount(e) {
                //  判断时间标签
                typeof e !== 'undefined'
                    ? (this.serverRegisteCountValue = e.target.value)
                    : (this.serverRegisteCountValue = 'week');
                let result = {};
                switch (this.serverRegisteCountValue) {
                    case 'year':
                        result = this.chartsData.year_data;
                        break;
                    case 'month':
                        result = this.chartsData.month_data;
                        break;
                    case 'week':
                        result = this.chartsData.week_data;
                        break;
                }
                //  构建图表
                let myChart = echarts.init(
                    document.getElementById('serverRegisteCountChart')
                );
                let option = {
                    color: ['#5470c6', '#2BC966'],
                    xAxis: {
                        type: 'category',
                        data: result.create_time
                    },
                    yAxis: {
                        type: 'value'
                    },
                    tooltip: {
                        trigger: 'axis',
                        // axisPointer: {
                        //   type: 'cross'
                        // }
                    },
                    legend: {
                        data: ['任务数量', '任务数量 '],
                        right: '10%'
                    },
                    series: [
                        {
                            name: '任务数量',
                            type: 'bar',
                            data: result.count
                        },
                        {
                            name: '任务数量 ',
                            type: 'line',
                            data: result.count
                        }
                    ]
                };
                myChart.setOption(option);
            },
            mapViewCategory() {
                // 格式化数据
                let result = {
                    legendData: [],
                    seriesData: []
                };
                this.chartsData.map_view_info.clue_type.forEach((item) => {
                    result.legendData.push(item.clue_name);
                    result.seriesData.push({
                        name: item.clue_name,
                        value: item.count
                    });
                });
                // 构建图表
                let myChart = echarts.init(
                    document.getElementById('mapViewCategoryChart')
                );
                let option = {
                    tooltip: {
                        trigger: 'item',
                        formatter: '{a} <br/>{b} : {c} ({d}%)'
                    },
                    legend: {
                        type: 'scroll',
                        orient: 'vertical',
                        right: 70,
                        top: 'center',
                        bottom: 20,
                        data: result.legendData
                    },
                    series: [
                        {
                            name: '服务类型',
                            type: 'pie',
                            radius: '55%',
                            center: ['40%', '50%'],
                            data: result.seriesData,
                            emphasis: {
                                itemStyle: {
                                    shadowBlur: 10,
                                    shadowOffsetX: 0,
                                    shadowColor: 'rgba(0, 0, 0, 0.5)'
                                }
                            }
                        }
                    ]
                };
                option && myChart.setOption(option);
            },
            objectDetectionCategory() {
                // 构建图表
                let myChart = echarts.init(
                    document.getElementById('objectDetectionCategoryChart')
                );
                let option = {
                    tooltip: {
                        trigger: 'item',
                    },
                    xAxis: {
                        name: '距离（米）',

                        type: 'category',
                        data:[0.0, 7.1, 14.1, 21.2, 28.3, 35.4, 42.4, 49.5, 56.6, 63.6, 70.7, 77.8, 84.8, 91.9, 99.0, 106.1, 113.1, 120.2, 127.3, 134.3, 141.4, 148.5, 155.6, 162.6, 169.7, 176.8, 183.8, 190.9, 198.0, 205.1, 212.1, 219.2, 226.3, 233.3, 240.4, 247.5, 254.5, 261.6, 268.7, 275.8, 282.8, 289.9, 297.0, 304.0, 311.1, 318.2, 325.3, 332.3, 339.4, 346.5, 353.5, 360.6, 367.7, 374.7, 381.8, 388.9, 396.0, 403.0, 410.1, 417.2, 424.2, 431.3, 438.4, 445.5, 452.5, 459.6, 466.7, 473.7, 480.8, 487.9, 494.9, 502.0, 509.1, 516.2, 523.2, 530.3, 537.4, 544.4, 551.5, 558.6, 565.7, 572.7, 579.8, 586.9, 593.9, 601.0, 608.1, 615.2, 622.2, 629.3, 636.4, 643.4, 650.5, 657.6, 664.6, 671.7, 678.8, 685.9, 692.9, 700.0]
                    },
                    yAxis: {
                        name: '误差（米）',
                        type: 'value'
                    },
                    series: [
                        {
                            name: '误差距离（单位：米）',
                            type: 'line',
                            radius: '55%',
                            center: ['40%', '50%'],
                            data:[0.008, 0.298, 0.127, 0.505, 0.55, 0.021, 0.57, 0.794, 0.97, 0.818, 1.271, 0.86, 1.164, 1.768, 1.292, 1.051, 1.525, 1.234, 2.292, 2.001, 2.353, 1.923, 2.348, 2.372, 2.856, 2.662, 2.791, 2.978, 2.67, 3.279, 2.824, 2.734, 3.066, 3.725, 3.71, 3.378, 3.349, 3.969, 3.344, 4.085, 4.113, 3.643, 3.871, 3.946, 4.521, 4.088, 4.285, 4.284, 4.366, 5.385, 4.672, 5.129, 4.828, 5.845, 5.66, 5.285, 6.012, 6.256, 5.989, 6.026, 5.725, 5.9, 6.612, 5.949, 6.436, 6.646, 6.625, 7.24, 6.924, 7.228, 7.351, 7.575, 7.604, 6.977, 7.326, 8.02, 7.551, 7.997, 7.62, 7.851, 7.674, 8.016, 7.971, 8.705, 8.346, 8.952, 8.785, 9.133, 8.679, 8.949, 9.366, 9.482, 9.669, 9.098, 9.464, 9.273, 9.798, 10.0, 10.0, 9.708],
                            emphasis: {
                                itemStyle: {
                                    shadowBlur: 10,
                                    shadowOffsetX: 0,
                                    shadowColor: 'rgba(0, 0, 0, 0.5)'
                                }
                            }
                        }
                    ]
                };
                option && myChart.setOption(option);
            },
            serviceUsageCount() {
                // 构建图表数据
                let result = {
                    timeLabel: [],
                    keys: [],
                    data: []
                };
                for (let key in this.chartsData.service_usage_week_info) {
                    //  时间标签-横轴
                    result.timeLabel = this.chartsData.service_usage_week_info[key].create_time;
                    // 自变量-legend
                    result.keys.push(key);
                    // 自变量-数值
                    result.data.push({
                        name: key,
                        type: 'line',
                        stack: 'Total',
                        areaStyle: {},
                        emphasis: {
                            focus: 'series'
                        },
                        data: this.chartsData.service_usage_week_info[key].count
                    });
                }
                //  堆叠面积图
                let myChart = echarts.init(document.getElementById('serviceUsageCountChart'));
                let option = {
                    color: ['#42b4f2', '#91cc75', '#FFC75C'],
                    tooltip: {
                        trigger: 'axis',
                        // axisPointer: {
                        //   type: 'cross',
                        //   label: {
                        //     backgroundColor: '#6a7985'
                        //   }
                        // }
                    },
                    legend: {
                        top: 20,
                        data: result.keys
                    },
                    grid: {
                        left: '3%',
                        right: '4%',
                        bottom: '3%',
                        containLabel: true
                    },
                    xAxis: [
                        {
                            type: 'category',
                            boundaryGap: false,
                            data: result.timeLabel
                        }
                    ],
                    yAxis: [
                        {
                            type: 'value'
                        }
                    ],
                    series: result.data
                };
                option && myChart.setOption(option);
            },
            taskConfig() {
                // 构建图表数据
                let result = {
                    timeLabel: [],
                    keys: [],
                    data: []
                };
                for (let key in this.chartsData.task_data) {
                    //  时间标签-横轴
                    result.timeLabel = this.chartsData.task_data[key].create_time;
                    // 自变量-legend
                    result.keys.push(key);
                    // 自变量-数值
                    result.data.push({
                        name: key,
                        type: 'line',
                        stack: 'Total',
                        areaStyle: {},
                        emphasis: {
                            focus: 'series'
                        },
                        data: this.chartsData.task_data[key].count
                    });
                }
                //  堆叠面积图
                let myChart = echarts.init(document.getElementById('taskConfigChart'));
                let option = {
                    color: ['#42b4f2', '#91cc75', '#FFC75C'],
                    tooltip: {
                        trigger: 'axis',
                        // axisPointer: {
                        //   type: 'cross',
                        //   label: {
                        //     backgroundColor: '#6a7985'
                        //   }
                        // }
                    },
                    legend: {
                        top: 20,
                        data: result.keys
                    },
                    grid: {
                        left: '3%',
                        right: '4%',
                        bottom: '3%',
                        containLabel: true
                    },
                    xAxis: [
                        {
                            type: 'category',
                            boundaryGap: false,
                            data: result.timeLabel
                        }
                    ],
                    yAxis: [
                        {
                            type: 'value'
                        }
                    ],
                    series: result.data
                };
                option && myChart.setOption(option);
            },
            downloadReport(e) {
                let file_path = e.target.parentNode.getAttribute('data-path');
            }
        },
        mounted() {
            this.getAllData();
            window.onresize = () => {
                return (() => {
                    this.$router.go(0);
                })();
            };
        }
    };
</script>

<style scoped lang="scss">
  .resOverviewBox {
    width: 100%;
    height: 100%;
  }

  /*  页面内两栏卡片的高度*/
  .resOverviewBox .ant-col {
    height: 100%;
  }

  /*  左右两栏的间隙*/
  .resOverviewBox .card-box {
    padding-right: 10px;
    width: 50%;
  }

  .resOverviewBox .card-box .ant-card {
    height: 49%;
  }

  /*  每个卡片*/
  .resOverviewBox .ant-card {
    margin-bottom: 10px;
    width: 100%;
  }

  ::v-deep(.ant-card-head) {
    height: 50px;
    font-weight: 700;
  }

  ::v-deep(.ant-card-body) {
    padding: 0;
    margin: 0;
    height: calc(100% - 50px);
    width: 100%;
  }

  .resOverviewBox .ant-card-body .card-content {
    width: 100%;
    height: 100%;
  }

  /*  卡片图标*/
  .card-title-font {
    margin-right: 8px;
    color: #42b4f2;
    font-size: 20px;
  }

  /*  时间切换*/
  #serverRegisterId {
    position: absolute;
    z-index: 999;
  }

  #serverRegisterId .ant-radio-group {
    position: relative;
    display: flex;
    top: 10px;
    left: 8px;
  }

  /*  任务列表样式*/
  .task-config-list {
    padding: 0;
    margin: 0;
    overflow: auto;
    height: 98%;
  }

  .task-config-list-item {
    position: relative;
    padding-left: 24px;
    padding-right: 100px;
    margin: 5px auto;
    box-sizing: border-box;
    cursor: pointer;
    list-style: none;
    line-height: 45px;
    width: 98%;
    height: 45px;
    background-color: #f3f3f3;
  }

  /*.task-registration-list::-webkit-scrollbar {*/
  /*  display: none;*/
  /*}*/

  .task-config-list-item .icon-geoai-review1 {
    position: absolute;
    left: 5px;
    font-size: 18px;
    color: #f77395;
  }

  .task-config-list-text {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    display: inline-block;
    margin-left: 5px;
    width: 100%;
  }

  .task-config-list-date {
    position: absolute;
    display: inline-block;
    top: 0;
    right: 10px;
    width: 150px;
    text-align: right;
    color: #888;
  }
</style>
