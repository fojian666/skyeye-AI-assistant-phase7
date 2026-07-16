<template>
    <div class="se-container">
        <div class="se-container-top">
            <el-row :gutter="20">
                <el-col :span="14">
                    <div class="grid-content bg-purple">
                        <a-card :bordered="true">
                            <div slot="title"><span class="iconfont icon-geoai-ad-line card-title-font" />全景数量统计</div>
                            <div id="chart1" class="card-content"></div>
                        </a-card>
                    </div>
                </el-col>
                <el-col :span="6">
                    <div class="grid-content bg-purple">
                        <a-card :bordered="true">
                            <div slot="title"><span class="iconfont icon-geoai-ad-line card-title-font" />违法线索发现排行</div>
                            <div class="card-content">
                                <el-table :data="leaderboard" :cell-class-name="tableCellClassName" class="gt-table">
                                    <el-table-column prop="rank" label="排名" width="80"> </el-table-column>
                                    <el-table-column prop="street" label="街道"> </el-table-column>
                                    <el-table-column prop="count" label="数量" width="120"> </el-table-column>
                                </el-table>
                            </div>
                        </a-card>
                    </div>
                </el-col>
                <el-col :span="4">
                    <div class="grid-content3 bg-purple">
                        <div class="card-right-top"></div>
                        <div class="card-right-middle"></div>
                        <div class="card-right-bottom"></div>
                    </div>
                </el-col>
            </el-row>
        </div>
        <div class="se-container-bottom">
            <el-row :gutter="20">
                <el-col :span="8">
                    <div class="grid-content bg-purple">
                        <a-card :bordered="true">
                            <div slot="title"><span class="iconfont icon-geoai-ad-line card-title-font" />违法线索统计</div>
                            <div id="chart2" class="card-content"></div>
                        </a-card>
                    </div>
                </el-col>
                <el-col :span="8">
                    <div class="grid-content bg-purple">
                        <a-card :bordered="true">
                            <div slot="title"><span class="iconfont icon-geoai-ad-line card-title-font" />累计违法线索分布情况</div>
                            <div id="chart3" class="card-content"></div>
                        </a-card>
                    </div>
                </el-col>
                <el-col :span="8">
                    <div class="grid-content bg-purple">
                        <a-card :bordered="true">
                            <div slot="title"><span class="iconfont icon-geoai-ad-line card-title-font" />报告下载</div>
                            <div class="card-content">
                                <el-table :data="reportList" class="gt-table" :show-header="false">
                                    <el-table-column prop="rank" label="排名" width="80">
                                        <template slot-scope="scope">
                                            <img src="@/assets/images/report2.png" alt="" class="rank-image" style="width: 22px; height: 22px" />
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="name" label="报告名称"> </el-table-column>
                                    <el-table-column prop="count" label="下载" width="140">
                                        <template slot-scope="scope">
                                            <img src="@/assets/images/download.png" style="width: 16px; height: 16px" @click="download(scope.row)" />
                                        </template>
                                    </el-table-column>
                                </el-table>
                            </div>
                        </a-card>
                    </div>
                </el-col>
            </el-row>
        </div>
    </div>
</template>

<script>
import * as echarts from 'echarts';

export default {
    name: 'analysis',
    data() {
        return {
            leaderboard: [
                { rank: 1, street: '龙潭街道', count: 100 },
                { rank: 2, street: '栖霞街道', count: 90 },
                { rank: 3, street: '八卦洲街道', count: 80 },
                { rank: 4, street: '燕子矶街道', count: 66 },
                { rank: 5, street: '西岗街道', count: 60 },
                { rank: 6, street: '马群街道', count: 21 },
                { rank: 7, street: '尧化门街道', count: 11 },
                { rank: 8, street: '仙鹤门街道', count: 6 },
                { rank: 9, street: '江心洲街道', count: 1 }
            ],
            reportList: [{ name: '龙潭街道网格1线索' }, { name: '龙潭街道网格2线索' }, { name: '龙潭街道网格3线索' }, { name: '龙潭街道网格4线索' }]
        };
    },
    methods: {
        initCharts() {
            this.panoramicStatisticsChart();
            this.illegalCluesChart();
            this.clueDistributionChart();
        },
        tableCellClassName({ row, column, rowIndex, columnIndex }) {
            if (rowIndex <= 2) {
                if (columnIndex == 2) {
                    //前三行第三列表红
                    return 'warning-row';
                }
            } else {
                if (columnIndex == 2) {
                    return 'no-warning-row';
                }
            }
        },
        download() {
            this.$message.success('下载成功！');
        },
        panoramicStatisticsChart() {
            //  构建图表
            let myChart = echarts.init(document.getElementById('chart1'));
            const option = {
                xAxis: {
                    type: 'category',
                    boundaryGap: false,
                    data: ['2024-08-29', '2024-08-30', '2024-09-01', '2024-09-02', '2024-09-03', '2024-09-04', '2024-09-05']
                },
                yAxis: {
                    type: 'value'
                },
                series: [
                    {
                        data: [820, 932, 901, 934, 1290, 1330, 1320],
                        type: 'line',
                        areaStyle: {}
                    }
                ]
            };
            myChart.setOption(option);
        },
        illegalCluesChart() {
            //  构建图表
            let myChart2 = echarts.init(document.getElementById('chart2'));
            const option2 = {
                xAxis: {
                    type: 'category',
                    data: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
                },
                yAxis: {
                    type: 'value'
                },
                series: [
                    {
                        data: [120, 200, 150, 80, 70, 110, 130],
                        type: 'bar',
                        itemStyle: {
                            color: '#49A9EE'
                        }
                    }
                ]
            };
            myChart2.setOption(option2);
        },
        clueDistributionChart() {
            let myChart3 = echarts.init(document.getElementById('chart3'));
            const option3 = {
                textStyle: {
                    fontSize: 14
                },
                toolbox: {
                    show: true,
                    feature: {
                        mark: { show: true },
                        dataView: { show: true, readOnly: false },
                        magicType: {
                            show: true,
                            type: ['pie', 'funnel']
                        },
                        restore: { show: true },
                        saveAsImage: { show: true }
                    }
                },
                tooltip: {
                    trigger: 'item',
                    formatter: '{b} : {c}' //b为数据名，d为数据值
                },
                legend: {
                    orient: 'vertical',
                    x: 'left',
                    data: ['张三', '李四', '王五', '赵六']
                },
                color: ['#49A9EE', '#8996E6', '#F7A87E', '#98D87D', '#F3857B'],
                series: [
                    {
                        name: '线索数量（个）',
                        type: 'pie',
                        selectedMode: 'single',
                        radius: '75%',
                        label: {
                            show: true,
                            formatter: '{a|{b}：{c}}\n{hr|}',
                            //折线图文字颜色
                            color: 'black',
                            rich: {
                                //圆点位置大小配置
                                hr: {
                                    //auto自定义
                                    backgroundColor: 'auto',
                                    borderRadius: 3,
                                    width: 3,
                                    height: 3,
                                    padding: [3, 3, 0, -12]
                                },
                                a: {
                                    padding: [-12, 10, -20, 15]
                                }
                            }
                        },
                        //折线图长度
                        labelLine: {
                            //第一段
                            length: 15,
                            //第二段
                            length2: 25
                        },

                        data: [
                            { value: 175, name: '张三' },
                            { value: 57, name: '李四' },
                            { value: 19, name: '赵六' },
                            { value: 352, name: '王五', selected: true }
                        ]
                    }
                ]
            };
            myChart3.setOption(option3);
        }
    },
    mounted() {
        this.initCharts();
    }
};
</script>

<style scoped>
.se-container-top,
.se-container-bottom {
    flex: 1; /* 子元素各自占据50%的高度 */
    padding: 10px;
}
.gt-table {
    padding: 20px;
    width: 100%;
    height: 100%;
}
::v-deep .el-table__body-wrapper {
    overflow-x: hidden;
    overflow-y: scroll;
    height: calc(100% - 40px);
}
/deep/.el-table .warning-row {
    color: #ec5656;
}
/deep/ .el-table .no-warning-row {
    color: #01b79d;
}
.card-content {
    height: 320px;
}
.card-right-top,
.card-right-middle,
.card-right-bottom {
    width: 100%;
    margin-bottom: 10px;
    height: 118px;
}
.card-right-top {
    background-color: #2db6f4;
}
.card-right-middle {
    background-color: #7dc856;
}
.card-right-bottom {
    background-color: #5d6977;
}
.el-row {
    margin-bottom: 20px;
}
.el-col {
    border-radius: 4px;
}
::v-deep .ant-card-body {
    padding: 0;
}
.grid-content {
    border-radius: 1px;
    min-height: 400px;
}
.grid-content3 {
    padding: 2px 0;
}
.grid-content .ant-card {
    height: 100%;
}
.row-bg {
    padding: 10px 0;
    background-color: #f9fafc;
}
</style>
