<template>
    <div class="landChange-container">
        <div class="main" v-if="loaded">
            <div class="left-container">
                <div class="overall-preview-title">
                    <a-icon class="icon" type="appstore" />
                    <span class="text">总体预览</span>
                </div>
                <div class="overall-preview-content">
                    <div class="overall-preview-main">{{ totalPolygon }}</div>
                    <div class="overall-preview-sub">累计分割图斑(个)</div>
                </div>
                <div class="left-item">
                    <div class="left-item-title">
                        <span> <a-icon type="line" :rotate="90" />累计分割图斑区域分布 </span>
                        <span class="num-text">数量/个</span>
                    </div>
                    <div class="my-chart" ref="chart1"></div>
                </div>
                <div class="left-item">
                    <div class="left-item-title">
                        <span>
                            <a-icon type="line" :rotate="90" />
                            地类分割任务时间分布</span
                        >
                        <span class="num-text">数量/个</span>
                    </div>
                    <div class="my-chart" ref="chart2"></div>
                </div>
            </div>
            <div class="right-container">
                <div class="right-content">
                    <Query :queryParameter="queryParameter" :countyList="countyList" @changeList="changeList"></Query>
                    <ListCard :listCardConfig="listCardConfig"></ListCard>
                    <Pagination :paginationConfig="paginationConfig" @changeList="changeList"></Pagination>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import * as echarts from 'echarts';

const queryParameter = {
    task_type: '地类分割',
    name: '',
    county: '',
    create_time: ''
};
const page = 1;
const limit = 9;

export default {
    name: 'LandDividing',
    data() {
        return {
            queryParameter: Object.freeze(queryParameter),
            paginationConfig: {
                total: 0,
                taskType: '地类分割'
            },
            listCardConfig: {
                imgName: 'landSegment',
                data: [],
                latestID: '',
                detailPath: '/intelligent/land-dividing/land-dividing-details'
            },
            totalPolygon: 0,
            chartData: [
                {
                    xAxis: {
                        type: 'category',
                        data: [],
                        axisLine: {
                            show: true,
                            lineStyle: {
                                type: 'solid',
                                color: '#646464', //左边线的颜色
                                width: '1' //坐标线的宽度
                            }
                        },
                        axisLabel: {
                            rotate: 20
                        }
                    },
                    yAxis: {
                        type: 'value',
                        min: 0,
                        axisLine: {
                            show: true,
                            lineStyle: {
                                type: 'solid',
                                color: '#646464', //左边线的颜色
                                width: '1' //坐标线的宽度
                            }
                        }
                    },
                    series: [
                        {
                            data: [],
                            type: 'line',
                            symbol: 'circle',
                            symbolSize: '12',
                            itemStyle: {
                                color: '#8980E2',
                                borderWidth: 10,
                                borderColor: 'rgba(100,100,100,.5)'
                            }
                        },
                        {
                            data: [],
                            type: 'bar',
                            barWidth: 20,
                            itemStyle: {
                                color: 'rgba(100,100,100,.3)'
                            }
                        }
                    ],
                    grid: {
                        width: '90%',
                        left: '14%',
                        height: '50%'
                    },
                    tooltip: {
                        show: true,
                        trigger: 'axis',
                        formatter: '{c}'
                    }
                },
                {
                    xAxis: {
                        type: 'category',
                        data: [],
                        axisLine: {
                            show: true,
                            lineStyle: {
                                type: 'solid',
                                color: '#646464', //左边线的颜色
                                width: '1' //坐标线的宽度
                            }
                        },
                        axisLabel: {
                            rotate: 20
                        }
                    },
                    yAxis: {
                        type: 'value',
                        min: 0,
                        axisLine: {
                            show: true,
                            lineStyle: {
                                type: 'solid',
                                color: '#646464', //左边线的颜色
                                width: '1' //坐标线的宽度
                            }
                        }
                    },
                    series: [
                        {
                            data: [],
                            type: 'pictorialBar',
                            symbol: 'triangle',
                            barWidth: 20,
                            itemStyle: {
                                color: '#3D89F5'
                            }
                        },
                        {
                            data: [],
                            type: 'bar',
                            symbol: 'triangle',
                            barWidth: 20,
                            itemStyle: {
                                color: 'rgba(100,100,100,.2)'
                            }
                        }
                    ],
                    grid: {
                        width: '90%',
                        height: '50%'
                    },
                    tooltip: {
                        show: true,
                        trigger: 'axis',
                        formatter: '{c}'
                    }
                }
            ],
            loaded: false,
            countyList: []
        };
    },
    created() {
        const res = {
            code: 0,
            data: {
                count: 5,
                data: [
                    {
                        id: 297,
                        name: '\u4e50\u90fd\u9053\u8def\u63d0\u53d6',
                        path: {
                            name: '\u4e50\u90fd2021',
                            append_time: '2024-09',
                            url: 'http://192.168.60.51:8090/iserver/services/map-ugcv5-LD2021LD2021/rest/maps/LD2021%40LD2021',
                            data_type: '\u9053\u8def',
                            service_type: 'iServer'
                        },
                        prev_image: {},
                        next_image: {},
                        create_time: '2024-09-09',
                        data_path: 'http://192.168.60.51:8090/iserver/services/data-QHBSDATA/rest/data',
                        data_path_service_type: 'iServer',
                        county: '\u4e50\u90fd\u53bf(632123)',
                        datasets_name: 'LD2021ROAD',
                        owner: 'admin',
                        polygon_count: 969,
                        task_type: '\u5730\u7c7b\u5206\u5272',
                        append_time: '2024-09'
                    },
                    {
                        id: 296,
                        name: '\u5927\u5cad\u6e56\u516c\u56ed\u6d41\u8f6c\u5730\u68c0\u6d4b',
                        path: {
                            name: '\u5927\u5cad\u6e56\u516c\u56ed\u822a\u7247',
                            append_time: '2024-09',
                            url: 'http://192.168.60.51:8090/iserver/services/map-ugcv5-DLHGYYXDLHGYYX/rest/maps/DLHGYYX%40DLHGYYX',
                            data_type: '\u68da\u623f,\u5806\u7816,\u9632\u5c18\u7f51',
                            service_type: 'iServer'
                        },
                        prev_image: {},
                        next_image: {},
                        create_time: '2024-09-07',
                        data_path: 'http://192.168.60.51:8090/iserver/services/data-JIANGJING/rest/data',
                        data_path_service_type: 'iServer',
                        county: '\u6c5f\u6d25\u533a(500116)',
                        datasets_name: 'DLHGY',
                        owner: 'admin',
                        polygon_count: 41,
                        task_type: '\u5730\u7c7b\u5206\u5272', //地类分割
                        append_time: '2024-09'
                    },
                    {
                        id: 295,
                        name: '\u4e2d\u6881\u9996\u5e9c\u8fdd\u5efa\u68c0\u6d4b',
                        path: {
                            name: '\u4e2d\u6881\u9996\u5e9c\u822a\u7247',
                            append_time: '2024-09',
                            url: 'http://192.168.60.51:8090/iserver/services/map-ugcv5-ZLSFYXZLSFYX/rest/maps/ZLSFYX%40ZLSFYX',
                            data_type: '\u7591\u4f3c\u8fdd\u5efa',
                            service_type: 'iServer'
                        },
                        prev_image: {},
                        next_image: {},
                        create_time: '2024-09-07',
                        data_path: 'http://192.168.60.51:8090/iserver/services/data-JIANGJING/rest/data',
                        data_path_service_type: 'iServer',
                        county: '\u6c5f\u6d25\u533a(500116)',
                        datasets_name: 'ZLSF',
                        owner: 'admin',
                        polygon_count: 17,
                        task_type: '\u5730\u7c7b\u5206\u5272',
                        append_time: '2024-09'
                    },
                    {
                        id: 294,
                        name: '\u53cc\u798f\u8def\u8fdd\u5efa\u68c0\u6d4b',
                        path: {
                            name: '\u53cc\u798f\u8def\u822a\u7247',
                            append_time: '2024-09',
                            url: 'http://192.168.60.51:8090/iserver/services/map-ugcv5-SFLYXSFLYX/rest/maps/SFLYX%40SFLYX',
                            data_type: '\u7591\u4f3c\u8fdd\u5efa',
                            service_type: 'iServer'
                        },
                        prev_image: {},
                        next_image: {},
                        create_time: '2024-09-07',
                        data_path: 'http://192.168.60.51:8090/iserver/services/data-JIANGJING/rest/data',
                        data_path_service_type: 'iServer',
                        county: '\u6c5f\u6d25\u533a(500116)',
                        datasets_name: 'SFL',
                        owner: 'admin',
                        polygon_count: 44,
                        task_type: '\u5730\u7c7b\u5206\u5272',
                        append_time: '2024-09'
                    },
                    {
                        id: 293,
                        name: '\u519c\u7231\u6c34\u5e93\u6d41\u8f6c\u5730\u68c0\u6d4b',
                        path: {
                            name: '\u519c\u7231\u6c34\u5e93\u822a\u7247',
                            append_time: '2024-09',
                            url: 'http://192.168.60.51:8090/iserver/services/map-ugcv5-NASKYXNASKYX/rest/maps/NASKYX%40NASKYX',
                            data_type: '\u68da\u623f',
                            service_type: 'iServer'
                        },
                        prev_image: {},
                        next_image: {},
                        create_time: '2024-09-07',
                        data_path: 'http://192.168.60.51:8090/iserver/services/data-JIANGJING/rest/data',
                        data_path_service_type: 'iServer',
                        county: '\u6c5f\u6d25\u533a(500116)',
                        datasets_name: 'NASK',
                        owner: 'admin',
                        polygon_count: 27,
                        task_type: '\u5730\u7c7b\u5206\u5272',
                        append_time: '2024-09'
                    }
                ],
                source_annotate_list: [
                    {
                        county: '\u6c5f\u6d25\u533a',
                        count: 129
                    },
                    {
                        county: '\u4e50\u90fd\u53bf',
                        count: 969
                    }
                ],
                task_annotate_list: [
                    {
                        month: '2024-09',
                        count: 5
                    }
                ],
                total_polygon: 1098,
                county_list: ['\u6c5f\u6d25\u533a(500116)', '\u4e50\u90fd\u53bf(632123)'],
                latest_task_id: 304,
                status: true
            }
        };
        res.data.county_list.forEach((i) => {
            let item = {
                label: i,
                value: i
            };
            this.countyList.push(item);
        });
        this.listCardConfig.data = res.data.data;
        this.listCardConfig.latestID = res.data.latest_task_id;
        this.totalPolygon = res.data.total_polygon;
        this.paginationConfig.total = res.data.count;
        this.loaded = true;
        res.data.source_annotate_list.forEach((item) => {
            this.chartData[0].xAxis.data.push(item.county);
            this.chartData[0].series[0].data.push(item.count);
            this.chartData[0].series[1].data.push(item.count);
        });
        res.data.task_annotate_list.forEach((item) => {
            this.chartData[1].xAxis.data.push(item.month);
            this.chartData[1].series[0].data.push(item.count);
        });
        let len = this.chartData[1].series[0].data.length;
        let max = Math.max.apply(null, this.chartData[1].series[0].data);
        this.chartData[1].series[1].data = Array.from(new Array(len), () => max);
        this.$nextTick(() => {
            this.initChart();
        });
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
            let chart1 = echarts.init(this.$refs.chart1);
            chart1.setOption(this.chartData[0]);
            let chart2 = echarts.init(this.$refs.chart2);
            chart2.setOption(this.chartData[1]);
        }
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
}

.left-container {
    box-sizing: border-box;
    width: 320px;
    height: 100%;
    background-color: rgb(255, 255, 255);
    padding: 0.5rem;
    overflow: auto;
}

.right-container {
    flex: 1;
    height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    overflow-y: auto;
    background-color: #f0f2f5;
    position: relative;
}

.right-content {
    margin: 10px 5px;
    height: calc(100% - 20px);
    width: calc(100% - 10px);
    background-color: #fff;
}

.my-chart {
    width: 100%;
    height: 12rem;
}

.overall-preview-title {
    font-size: 1rem;
    color: black;
    padding: 0.5rem 0;
    height: 5%;
}

.overall-preview-title .icon {
    margin-right: 0.5rem;
    color: blue;
}

.overall-preview-content {
    background-image: url('@/assets/images/bg-gailan.png');
    background-size: cover;
    display: flex;
    flex-direction: column;
    justify-content: space-around;
    align-items: center;
    height: 6rem;
    padding: 0.5rem;
    color: white;
    height: 13%;
}

.overall-preview-main {
    font-size: 1.5rem;
    font-weight: 600;
}

.overall-preview-sub {
    font-size: 0.9rem;
}

.left-item {
    margin-top: 0.5rem;
    height: 38%;
}

.left-item1 {
    margin-top: 0.5rem;
    height: 32%;
}

.left-item-title {
    height: 2rem;
    background-image: url('@/assets/images/bg-tittle.png');
    background-repeat: no-repeat;
    display: flex;
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
}

.num-text {
    padding: 0.2rem 0.5rem;
    border: 0.1rem solid blue;
}
.leaflet-sbs-divider {
    background-color: rgb(5, 78, 179) !important;
    width: 0.2rem !important;
}
</style>
