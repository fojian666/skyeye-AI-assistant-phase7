<template>
    <div class="landChange-container">
        <div class="main" v-if="loaded">
            <div class="left-container">
                <div class="overall-preview-title">
                    <a-icon class="icon" type="appstore" />
                    <span class="text">总体预览</span>
                </div>
                <div class="overall-preview">
                    <div class="overall-preview-content">
                        <div class="bg-content">
                            <img src="@/assets/images/data-icon.png" alt="" class="data-img" />
                        </div>
                        <div class="num-content">
                            <div class="overall-preview-sub">累计变化图斑(个)</div>
                            <div class="overall-preview-main">{{ staticTotal.totalChangePolygon }}</div>
                        </div>
                    </div>
                    <div class="overall-preview-content">
                        <div class="bg-content">
                            <img src="@/assets/images/data-icon.png" alt="" class="data-img" />
                        </div>
                        <div class="num-content">
                            <div class="overall-preview-sub">累计分割图斑(个)</div>
                            <div class="overall-preview-main">{{ staticTotal.totalSegPolygon }}</div>
                        </div>
                    </div>
                </div>
                <div class="chart-content">
                    <div class="left-item">
                        <div class="left-item-title">
                            <span><a-icon type="line" :rotate="90" />累计变化图斑区域分布</span>
                            <span class="num-text">数量/个</span>
                        </div>
                        <div class="my-chart" ref="chart1"></div>
                    </div>
                    <div class="left-item">
                        <div class="left-item-title">
                            <span><a-icon type="line" :rotate="90" />地类变化任务时间分布</span>
                            <span class="num-text">数量/个</span>
                        </div>
                        <div class="my-chart" ref="chart2"></div>
                    </div>
                    <div class="left-item">
                        <div class="left-item-title">
                            <span><a-icon type="line" :rotate="90" />累计分割图区域分布</span>
                            <span class="num-text">数量/个</span>
                        </div>
                        <div class="my-chart" ref="chart3"></div>
                    </div>
                    <div class="left-item">
                        <div class="left-item-title">
                            <span><a-icon type="line" :rotate="90" />地表分割任务时间分布</span>
                            <span class="num-text">数量/个</span>
                        </div>
                        <div class="my-chart" ref="chart4"></div>
                    </div>
                </div>
            </div>
            <div class="right-container">
                <div class="right-content">
                    <Query
                        :queryParameter="queryParameter"
                        :countyList="countyList"
                        :task_type_list="task_type_list"
                        @changeList="handleQuery"></Query>
                    <ListCard :listCardConfig="listCardConfig"></ListCard>
                    <div class="pagination-container">
                        <div>
                            共 {{ paginationConfig.total }} 条记录 第{{ current + '/' + Math.ceil(paginationConfig.total / 9) }}
                            页
                        </div>
                        <a-pagination v-model="current" :total="paginationConfig.total" :default-page-size="9" @change="changePage"> </a-pagination>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import * as echarts from 'echarts';
import { getInterpretationResultByApi, getLandChangeTaskApi, getStaticInfoApi } from '@/api/commonApi';
const queryParameter = {
    task_type: '地类变化',
    name: '',
    county: '',
    create_time: ''
};
const page = 1;
const limit = 9;

export default {
    name: 'LandChange',
    data() {
        return {
            queryParameter: Object.freeze(queryParameter),
            paginationConfig: {
                total: 0,
                taskType: '地类变化',
                pageIndex: 1,
                pageSize: 9
            },
            listCardConfig: {
                imgName: 'LandChange',
                data: [],
                latestID: 'c1964278c70244fe905e6f58f0143a32',
                detailPath: '/intelligent/land-change/land-change-details',
                segdetailPath: '/intelligent/land-dividing/land-dividing-details'
            },
            staticTotal: {
                totalChangePolygon: 0,
                totalSegPolygon: 0
            },

            loaded: false,
            countyList: [],
            task_type_list: [
                { label: '地类变化', value: '地类变化' },
                { label: '地类分割', value: '地类分割' }
            ],
            chartData: {
                changeSpotByArea: { xAxis: ['初始化', '初始化', '初始化', '初始化', '初始化'], series: [120, 132, 101, 134, 90] },
                changeSpotByTime: { xAxis: ['2021', '2022', '2023', '2024', '2025'], series: [30.01, 57.07, 49.23, 65.91, 42.67] },
                segSpotByArea: { xAxis: ['初始化', '初始化', '初始化', '初始化', '初始化'], series: [120, 132, 101, 134, 90] },
                segSpotByTime: { xAxis: ['2021', '2022', '2023', '2024', '2025'], series: [30.01, 57.07, 49.23, 65.91, 42.67] }
            },
            current: 1
        };
    },
    async created() {
        // const params = {
        //     page: page,
        //     limit: limit,
        //
        // }
        // //const res = await getLandChangeTaskApi(params)
        // const res = {
        //     "count": 4,
        //     "data": {
        //         "data": [
        //             {
        //                 "id": 303,
        //                 "name": "\u6f06\u6865\u8857\u9053\u53d8\u5316\u68c0\u6d4b",
        //                 "path": {},
        //                 "prev_image": {
        //                     "name": "\u6f06\u6865\u8857\u9053\u822a\u72470521",
        //                     "append_time": "2025-04",
        //                     "url": "http://192.168.60.42:8090/iserver/services/map-ugcv5-gchp0521gchp0521/rest/maps/gchp0521%40gchp0521",
        //                     "service_type": "iServer"
        //                 },
        //                 "next_image": {
        //                     "name": "\u6f06\u6865\u8857\u9053\u822a\u72470527",
        //                     "append_time": "2025-05",
        //                     "url": "http://192.168.60.42:8090/iserver/services/map-ugcv5-gchp0527gchp0527/rest/maps/gchp0527%40gchp0527",
        //                     "service_type": "iServer"
        //                 },
        //                 "create_time": "2025-05-27",
        //                 "data_path": "http://192.168.60.42:8090/iserver/services/data-gcbhjc/rest/data",
        //                 "data_path_service_type": "iServer",
        //                 "county": "\u9ad8\u6df3\u53bf(320125)",
        //                 "datasets_name": "gcbhjc",
        //                 "owner": "admin",
        //                 "polygon_count": 6,
        //                 "task_type": "\u5730\u7c7b\u53d8\u5316", //地类变化
        //                 "task_type_tag":'0',
        //                 "append_time": "2025-05"
        //             },
        //             {
        //                 "id": 297,
        //                 "name": "\u4e50\u90fd\u9053\u8def\u63d0\u53d6",
        //                 "path": {
        //                     "name": "\u4e50\u90fd2021",
        //                     "append_time": "2024-09",
        //                     "url": "http://192.168.60.51:8090/iserver/services/map-ugcv5-LD2021LD2021/rest/maps/LD2021%40LD2021",
        //                     "data_type": "\u9053\u8def",
        //                     "service_type": "iServer"
        //                 },
        //                 "prev_image": {},
        //                 "next_image": {},
        //                 "create_time": "2024-09-09",
        //                 "data_path": "http://192.168.60.51:8090/iserver/services/data-QHBSDATA/rest/data",
        //                 "data_path_service_type": "iServer",
        //                 "county": "\u4e50\u90fd\u53bf(632123)",
        //                 "datasets_name": "LD2021ROAD",
        //                 "owner": "admin",
        //                 "polygon_count": 969,
        //                 "task_type": "\u5730\u7c7b\u5206\u5272",
        //                 "task_type_tag":'1',
        //                 "append_time": "2024-09"
        //             },
        //
        //
        //         ],
        //         "source_annotate_list": [
        //             {
        //                 "county": "\u9ad8\u6df3\u53bf",
        //                 "count": 6
        //             },
        //         ],
        //         "task_annotate_list": [
        //             {
        //                 "month": "2025-05",
        //                 "count": 1
        //             },
        //         ],
        //         // "total_polygon": 6,
        //         // "county_list": ["高淳县(320125)",],
        //         "latest_task_id": 303,
        //         "task_type_list":["地类变化","地类分割"]
        //     },
        //     "code":0
        // }
        // if (res.code !== 0) {
        //     return this.$message.warning(res.data.msg);
        // }
        // // res.data.data.forEach((i) => {
        // //     let item = {
        // //         label: i.county,
        // //         value: i.county
        // //     };
        // //     this.countyList.push(item);
        // // });
        // // res.data.task_type_list.forEach((i) => {
        // //     let item = {
        // //         label: i,
        // //         value: i
        // //     };
        // //     this.task_type_list.push(item);
        // // });
        //
        // this.listCardConfig.data = res.data.data;
        // this.listCardConfig.latestID = res.data.latest_task_id;
        //
        // // this.staticTotal.totalChangePolygon = res.data.total_polygon;
        // this.paginationConfig.total = res.count;
        // this.loaded = true;
        // // res.data.source_annotate_list.forEach((item) => {
        // //     this.chartData[0].xAxis.data.push(item.county);
        // //     this.chartData[0].series[0].data.push(item.count);
        // //     this.chartData[0].series[1].data.push(item.count);
        // // });
        // // res.data.task_annotate_list.forEach((item) => {
        // //     this.chartData[1].xAxis.data.push(item.month);
        // //     this.chartData[1].series[0].data.push(item.count);
        // // });
        // //
        // //
        // // let len = this.chartData[1].series[0].data.length;
        // // let max = Math.max.apply(null, this.chartData[1].series[0].data);
        // // this.chartData[1].series[1].data = Array.from(
        // //     new Array(len),
        // //     () => max
        // // );
        // this.$nextTick(() => {
        //
        // });
        // this.initChart();
    },
    components: {
        Query: () => import('@/components/query'),
        ListCard: () => import('@/components/list-card'),
        Pagination: () => import('@/components/pagination')
    },
    methods: {
        changeList(v) {
            this.listCardConfig.data = v.data;
            this.paginationConfig.total = v.count;
        },
        initChart() {
            this.initChart1();
            this.initChart2();
            this.initChart3();
            this.initChart4();
        },
        fontSize(res) {
            let clientWidth = window.innerWidth || document.documentElement.clientWidth || document.body.clientWidth;
            if (!clientWidth) return;
            let fontSize = 100 * (clientWidth / 1920);
            return res * fontSize;
        },
        initChart1() {
            //累计变化图斑区域分布
            let myChart = echarts.init(this.$refs.chart1);
            // 示例数据 - 替换为实际数据
            const data = this.chartData.changeSpotByArea.series;

            // 计算合适的Y轴最大值和间隔
            const maxDataValue = Math.max(...data);
            // 配置项
            var option = {
                tooltip: {
                    trigger: 'axis',
                    axisPointer: {
                        type: 'shadow'
                    }
                },
                grid: {
                    left: '10%',
                    right: '5%',
                    bottom: '15%',
                    top: '10%'
                },
                xAxis: {
                    type: 'category',
                    data: this.chartData.changeSpotByArea.xAxis,
                    axisLine: {
                        lineStyle: {
                            color: '#333'
                        }
                    },
                    axisTick: {
                        alignWithLabel: true,
                        length: 4,
                        lineStyle: {
                            color: '#FFF'
                        }
                    },
                    axisLabel: {
                        color: '#FFF',
                        fontSize: this.fontSize(0.12),
                        interval: 0
                    }
                },
                yAxis: {
                    type: 'value',
                    min: 0,
                    max: maxDataValue,
                    axisLine: {
                        show: true,
                        lineStyle: {
                            color: '#FFF'
                        }
                    },
                    axisTick: {
                        length: 4,
                        lineStyle: {
                            color: '#FFF'
                        }
                    },
                    axisLabel: {
                        color: '#FFF',
                        fontSize: this.fontSize(0.12),
                        formatter: function (value) {
                            return value === 0 ? '0' : value;
                        }
                    },
                    splitLine: {
                        lineStyle: {
                            type: 'dashed',
                            color: '#e0e0e0'
                        }
                    }
                },
                series: [
                    // 柱状图系列（放在下面）
                    {
                        name: '数量',
                        type: 'bar',
                        barWidth: '15',
                        color: {
                            type: 'linear',
                            x: 1,
                            y: 0,
                            x2: 0,
                            y2: 1,
                            colorStops: [
                                { offset: 0, color: '#3bc5cb' }, // 起始颜色
                                { offset: 1, color: '#1a263a' } // 结束颜色
                            ]
                        },

                        data: data,
                        z: 1 // 设置较低的z-index
                    },
                    // 折线图系列（放在上面）
                    {
                        name: '趋势',
                        type: 'line',
                        symbol: 'circle',
                        symbolSize: 15,
                        lineStyle: {
                            width: 3,
                            color: 'rgba(73, 205, 252,0.5)'
                        },
                        itemStyle: {
                            color: '#3bc5cb',
                            borderWidth: 2,
                            borderColor: '#fff'
                        },
                        data: data,
                        z: 2,
                        tooltip: {
                            show: false // 不显示提示框
                        }
                    }
                ]
            };
            option && myChart.setOption(option);
            window.addEventListener('resize', function () {
                myChart.resize();
            });
        },
        initChart2() {
            //地类变化任务时间分布
            let myChart = echarts.init(this.$refs.chart2);
            const data = this.chartData.changeSpotByTime.series;
            const maxDataValue = Math.max(...data);
            var option = {
                tooltip: {
                    trigger: 'axis',
                    axisPointer: {
                        type: 'shadow'
                    }
                },
                grid: {
                    left: '10%',
                    right: '5%',
                    bottom: '15%',
                    top: '10%'
                },
                xAxis: {
                    type: 'category',
                    data: this.chartData.changeSpotByTime.xAxis,
                    axisLine: {
                        lineStyle: {
                            color: '#FFF'
                        }
                    },
                    axisTick: {
                        alignWithLabel: true,
                        length: 4,
                        lineStyle: {
                            color: '#FFF'
                        }
                    },
                    axisLabel: {
                        color: '#FFF',
                        fontSize: this.fontSize(0.12),
                        margin: 10
                    }
                },
                yAxis: {
                    type: 'value',
                    min: 0,
                    max: maxDataValue,
                    axisLine: {
                        show: true,
                        lineStyle: {
                            color: '#FFF'
                        }
                    },
                    axisTick: {
                        length: 4,
                        lineStyle: {
                            color: '#FFF'
                        }
                    },
                    axisLabel: {
                        color: '#FFF',
                        fontSize: this.fontSize(0.12),
                        margin: 8
                    },
                    splitLine: {
                        lineStyle: {
                            type: 'dashed',
                            color: '#e0e0e0'
                        }
                    }
                },
                series: [
                    {
                        // 背景系列
                        name: '背景',
                        type: 'bar',
                        barWidth: '40%',
                        barGap: '-100%', // 将背景系列放在主系列后面
                        data: [maxDataValue, maxDataValue, maxDataValue, maxDataValue, maxDataValue], // 背景高度设为100%
                        tooltip: {
                            show: false // 不显示提示框
                        },
                        itemStyle: {
                            color: 'rgba(180, 180, 180, 0.2)'
                        },
                        emphasis: {
                            itemStyle: {
                                color: 'rgba(180, 180, 180, 0.2)'
                            }
                        },
                        animation: false
                    },
                    {
                        name: '值',
                        type: 'pictorialBar',
                        barCategoryGap: '40%',
                        symbol: 'triangle',
                        showBackground: true,
                        backgroundStyle: { color: 'rgba(180, 180, 180, 0.2)' },
                        itemStyle: {
                            normal: {
                                opacity: 0.8
                            }
                        },
                        color: '#1a7eef',
                        data: data,
                        z: 10
                    }
                ]
            };
            option && myChart.setOption(option);
            // 响应式调整
            window.addEventListener('resize', function () {
                myChart.resize();
            });
        },
        initChart3() {
            //累计分割图斑区域分布
            let myChart = echarts.init(this.$refs.chart3);
            // 示例数据 - 替换为实际数据
            const data = this.chartData.segSpotByArea.series;

            // 计算合适的Y轴最大值和间隔
            const maxDataValue = Math.max(...data);
            // 配置项
            var option = {
                tooltip: {
                    trigger: 'axis',
                    axisPointer: {
                        type: 'shadow'
                    }
                },
                grid: {
                    left: '10%',
                    right: '5%',
                    bottom: '15%',
                    top: '10%'
                },
                xAxis: {
                    type: 'category',
                    data: this.chartData.segSpotByArea.xAxis,
                    axisLine: {
                        lineStyle: {
                            color: '#333'
                        }
                    },
                    axisTick: {
                        alignWithLabel: true,
                        length: 4,
                        lineStyle: {
                            color: '#FFF'
                        }
                    },
                    axisLabel: {
                        color: '#FFF',
                        fontSize: this.fontSize(0.12),
                        interval: 0
                    }
                },
                yAxis: {
                    type: 'value',
                    min: 0,
                    max: maxDataValue,
                    axisLine: {
                        show: true,
                        lineStyle: {
                            color: '#FFF'
                        }
                    },
                    axisTick: {
                        length: 4,
                        lineStyle: {
                            color: '#FFF'
                        }
                    },
                    axisLabel: {
                        color: '#FFF',
                        fontSize: this.fontSize(0.12),
                        formatter: function (value) {
                            return value === 0 ? '0' : value;
                        }
                    },
                    splitLine: {
                        lineStyle: {
                            type: 'dashed',
                            color: '#e0e0e0'
                        }
                    }
                },
                series: [
                    // 柱状图系列（放在下面）
                    {
                        name: '数量',
                        type: 'bar',
                        barWidth: '15',
                        color: {
                            type: 'linear',
                            x: 1,
                            y: 0,
                            x2: 0,
                            y2: 1,
                            colorStops: [
                                { offset: 0, color: '#9a8139' }, // 起始颜色
                                { offset: 1, color: '#1f232b' } // 结束颜色
                            ]
                        },

                        data: data,
                        z: 1 // 设置较低的z-index
                    },
                    // 折线图系列（放在上面）
                    {
                        name: '趋势',
                        type: 'line',
                        symbol: 'circle',
                        symbolSize: 15,
                        lineStyle: {
                            width: 3,
                            color: 'rgba(73, 205, 252,0.5)'
                        },
                        itemStyle: {
                            color: '#9a8139',
                            borderWidth: 2,
                            borderColor: '#fff'
                        },
                        data: data,
                        z: 2,
                        tooltip: {
                            show: false // 不显示提示框
                        }
                    }
                ]
            };
            option && myChart.setOption(option);
            window.addEventListener('resize', function () {
                myChart.resize();
            });
        },
        initChart4() {
            //地类分割任务时间分布
            let myChart = echarts.init(this.$refs.chart4);
            const data = this.chartData.segSpotByTime.series;
            const maxDataValue = Math.max(...data);
            var option = {
                tooltip: {
                    trigger: 'axis',
                    axisPointer: {
                        type: 'shadow'
                    }
                },
                grid: {
                    left: '10%',
                    right: '5%',
                    bottom: '15%',
                    top: '10%'
                },
                xAxis: {
                    type: 'category',
                    data: this.chartData.segSpotByTime.xAxis,
                    axisLine: {
                        lineStyle: {
                            color: '#FFF'
                        }
                    },
                    axisTick: {
                        alignWithLabel: true,
                        length: 4,
                        lineStyle: {
                            color: '#FFF'
                        }
                    },
                    axisLabel: {
                        color: '#FFF',
                        fontSize: this.fontSize(0.12),
                        margin: 10
                    }
                },
                yAxis: {
                    type: 'value',
                    min: 0,
                    max: maxDataValue,
                    axisLine: {
                        show: true,
                        lineStyle: {
                            color: '#FFF'
                        }
                    },
                    axisTick: {
                        length: 4,
                        lineStyle: {
                            color: '#FFF'
                        }
                    },
                    axisLabel: {
                        color: '#FFF',
                        fontSize: this.fontSize(0.12),
                        margin: 8
                    },
                    splitLine: {
                        lineStyle: {
                            type: 'dashed',
                            color: '#e0e0e0'
                        }
                    }
                },
                series: [
                    {
                        // 背景系列
                        name: '背景',
                        type: 'bar',
                        barWidth: '35%',
                        barGap: '-100%', // 将背景系列放在主系列后面
                        data: [maxDataValue, maxDataValue, maxDataValue, maxDataValue, maxDataValue], // 背景高度设为100%
                        tooltip: {
                            show: false // 不显示提示框
                        },
                        itemStyle: {
                            color: 'rgba(180, 180, 180, 0.2)'
                        },
                        emphasis: {
                            itemStyle: {
                                color: 'rgba(180, 180, 180, 0.2)'
                            }
                        },
                        animation: false
                    },
                    {
                        name: '值',
                        type: 'bar',
                        showBackground: true,
                        backgroundStyle: { color: 'rgba(180, 180, 180, 0.2)' },
                        itemStyle: {
                            normal: {
                                opacity: 0.8
                            }
                        },
                        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                            { offset: 0, color: '#2378f7' },
                            { offset: 0.7, color: '#2378f7' },
                            { offset: 1, color: '#83bff6' }
                        ]),
                        data: data,
                        z: 10
                    }
                ]
            };
            option && myChart.setOption(option);
            // 响应式调整
            window.addEventListener('resize', function () {
                myChart.resize();
            });
        },
        async getTaskInfos(params) {
            const res = await getInterpretationResultByApi(params);
            // const res = {
            //     "total": 4,
            //     "data": [{'taskResultData':[
            //             {
            //                 "id": "c1964278c70244fe905e6f58f0143a32",
            //                 "name": "漆桥街道变化检测",
            //                 "path": {},
            //                 "prevImage": {
            //                     "name": "Feihuacun",
            //                     "appendTime": "2025-04",
            //                     "url": "http://192.168.60.42:8090/iserver/services/imageservice-njimagetest/restjsr",
            //                     "collectId": "imagetestdk",
            //                     "tifName": "Gc_20250601.tif",
            //                     "tifId":3,
            //                     "serviceType": "iServer"
            //                 },
            //                 "nextImage": {
            //                     "name": "lp202506",
            //                     "appendTime": "2025-05",
            //                     "url": "http://192.168.60.42:8090/iserver/services/imageservice-njimagetest/restjsr",
            //                     "collectId":'imagetestdk',
            //                     "tifName":'Gc_20250601.tif',
            //                     "tifId":3,
            //                     "serviceType": "iServer"
            //                 },
            //                 "createTime": "2025-05-27",
            //                 "dataPath": "http://192.168.60.42:8090/iserver/services/data-gcbhjc/rest/data",
            //                 "dataPathServiceType": "iServer",
            //                 "county": "高淳县(320125)",
            //                 "datasetsName": "gcbhjc",
            //                 "owner": "admin",
            //                 "polygonCount": 6,
            //                 "taskType": "地类变化",
            //                 "taskTypeTag": "地类变化",
            //                 "appendTime": "2025-05"
            //             },
            //             {
            //                 "id": 297,
            //                 "name": "乐都道路提取",
            //                 "path": {
            //                     "name": "Gc_20250601",
            //                     "appendTime": "2024-09",
            //                     "url": "http://192.168.60.42:8090/iserver/services/imageservice-njimagetest/restjsr",
            //                     "collectId":'imagetestdk',
            //                     "tifName":'Gc_20250601.tif',
            //                     "tifId":3,
            //                     "data_type": "道路",
            //                     "service_type": "iServer"
            //                 },
            //                 "prevImage": {},
            //                 "nextImage": {},
            //                 "createTime": "2024-09-09",
            //                 "dataPath": "http://192.168.60.42:8090/iserver/services/data-hpjy/rest/data",
            //                 "dataPathServiceType": "iServer",
            //                 "county": "高淳",
            //                 "datasourceName": "hpjyi",
            //                 "datasetsName": "dwfl",
            //                 "owner": "admin",
            //                 "polygonCount": 969,
            //                 "taskType": "地类分割",
            //                 "taskTypeTag": "地类分割",
            //                 "appendTime": "2024-09"
            //             }
            //         ], "latestID": 303}],
            //     "code":0
            // }
            if (res.code === 0) {
                res.data[0].taskResultData.forEach((i) => {
                    let item = {
                        label: i.county,
                        value: i.county
                    };
                    if (!this.countyList.some((existing) => existing.value === item.value)) {
                        this.countyList.push(item);
                    }
                });
                this.listCardConfig.data = res.data[0].taskResultData;
                this.listCardConfig.latestID = res.data[0].latestID;
                this.paginationConfig.total = res.total;
            } else {
                return this.$message.warning(res.data.msg);
            }
        },
        async getStaticData() {
            const res = await getStaticInfoApi();
            if (res.code === 0) {
                this.loaded = true;
                this.chartData = res.data.chartData;
                this.staticTotal.totalChangePolygon = res.data.totalChangePolygon;
                this.staticTotal.totalSegPolygon = res.data.totalSegPolygon;
            }
        },
        handleQuery(para) {
            para.pageIndex = this.paginationConfig.pageIndex;
            para.pageSize = this.paginationConfig.pageSize;
            this.getTaskInfos(para);
        },
        changePage(page, size) {
            this.paginationConfig.pageIndex = page;
            this.paginationConfig.pageSize = size;
        }
    },
    async mounted() {
        await this.getTaskInfos({ pageIndex: 0, pageSize: 10, name: '', taskType: '', createDate: '', county: '' });
        await this.getStaticData();
        this.loaded = true;
        this.$nextTick(() => {
            this.initChart();
        });
    }
};
</script>

<style scoped>
.landChange-container {
    width: 100%;
    height: 100%;
    background-color: rgb(240, 240, 240);
}

.main {
    height: 100%;
    display: flex;
    background: #0b1a39;
}

.left-container {
    box-sizing: border-box;
    width: 320px;
    height: 100%;
    padding: 5px;
    display: flex;
    flex-direction: column;
}

.right-container {
    flex: 1;
    height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    overflow-y: auto;
    position: relative;
}

.right-content {
    margin: 10px 5px;
    height: calc(100% - 20px);
    width: calc(100% - 10px);
}

.my-chart {
    width: 100%;
    height: calc(100% - 20px);
}

.overall-preview-title {
    font-size: 1.2rem;
    color: white;
    padding: 5px 0;
    height: 5%;
}

.overall-preview-title .icon {
    margin-right: 5px;
    color: blue;
}

.overall-preview-content {
    background-image: url(http://192.168.50.42:8082/static/img/databg.dce98c62.png);
    background-size: cover;
    display: flex;
    justify-content: space-between;
    color: white;
    height: 90%;
    width: 48%;
}

.overall-preview-main {
    font-size: 1.5rem;
    font-weight: 600;
}

.overall-preview-sub {
    font-size: 0.7rem;
}

.left-item {
    margin-top: 3px;
    height: calc(100% / 4 - 10px);
}
.left-item-title {
    height: 25px;
    background-image: url('@/assets/images/databg.png');
    background-repeat: no-repeat;
    display: flex;
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
}
.left-item-title span:first-child {
    color: #00f1f3;
}

.num-text {
    padding: 0.2rem 0.5rem;
    font-size: 0.7rem;
    color: white;
}
.leaflet-sbs-divider {
    background-color: rgb(5, 78, 179) !important;
    width: 0.2rem !important;
}
.overall-preview {
    width: 100%;
    height: 10%;
    display: flex;
    flex-direction: row;
    justify-content: space-between;
}
.chart-content {
    flex: 1;
}
.data-img {
    position: absolute;
    width: 50px;
    height: 50px;
}
.bg-content {
    width: 20%;
    display: flex;
    align-items: center;
}
.num-content {
    width: 80%;
    display: flex;
    align-items: center;
    flex-direction: column;
    padding: 2px;
}

::v-deep .ant-form-item-label > label {
    color: #fff;
}
::v-deep .ant-pagination-options-quick-jumper {
    display: inline-block;
    height: 32px;
    line-height: 32px;
    vertical-align: top;
    color: white;
}
.pagination-container {
    box-sizing: border-box;
    height: 3rem;
    position: absolute;
    bottom: 0.5rem;
    right: 0rem;
    left: 0;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 1rem;
}
::v-deep .pagination-container {
    color: white;
}
::v-deep .ant-input {
    background-color: #0b1a39;
    border: 1px solid #264a76;
}
::v-deep .ant-select-selection {
    background-color: #0b1a39;
    border: 1px solid #264a76;
}
::v-deep .ant-pagination-prev .ant-pagination-item-link {
    background-color: #0b1a39;
}
::v-deep .anticon {
    color: #fff;
}
::v-deep .ant-pagination-next .ant-pagination-item-link {
    background-color: #0b1a39;
}
::v-deep .ant-pagination-item-active {
    font-weight: 500;
    background: #0d2d5c;
    border-color: #396aa4;
}
::v-deep .ant-btn {
    color: #fff;
    background-color: #0b1a39;
    border-color: #095295;
}
.query-container {
    width: 100%;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    align-items: center;
    flex-wrap: nowrap;
    height: 4rem;
    padding: 0 0.5rem;
}

.input-container {
    width: 28%;
    display: flex;
}
::v-deep(.btn-container .ant-form-item-children) {
    display: flex;
    flex-wrap: nowrap;
}
::v-deep(.btn-container) {
    margin-right: 0;
}

::v-deep(.ant-form-item-control-wrapper) {
    flex: 1;
}

::v-deep(.ant-form-item-children) {
    display: inline-block;
    width: 100%;
}

::v-deep(.ant-calendar-picker) {
    width: 100%;
}

.btn-query {
    background-color: #137ce3;
    margin-right: 1rem;
}
::v-deep .ant-input {
    color: white;
}
::v-deep .ant-select-selection--single .ant-select-selection__rendered {
    color: white;
}
</style>
