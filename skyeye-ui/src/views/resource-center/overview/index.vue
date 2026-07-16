<template>
    <div class="library-container">
        <a-card :bordered="false" class="sample-library">
            <div slot="title"><span class="iconfont icon-yangbenku card-title-font" />样本库</div>
            <div class="library-top">
                <div class="top-left" ref="sampleChart"></div>
                <div class="top-right">
                    <div class="title-item"><span class="iconfont icon-geoai-line card-title-font" />多维度统计</div>
                    <template v-for="item in statisticType">
                        <div class="statistic-type">
                            <div class="statistic-type-title">
                                <i class="iconfont icon-yansekuang"></i>
                                按 {{ item.name }}统计
                            </div>
                            <div class="statistic-type-content">
                                <span class="content-item" :style="'width:' + v.value" v-for="v in item.value">{{ v.name }}</span>
                            </div>
                        </div>
                    </template>
                </div>
            </div>
            <div class="sample-bottom">
                <div
                    class="sample-bottom-item"
                    v-for="(item, i) in sampleData"
                    :key="i"
                    @click="sampleType(item.name)"
                    :title="'点击查看' + item.name + '详情'"
                    style="font-size: 17px">
                    <span class="iconfont icon-daoluxuncha icon-font" />
                    <div class="sample-name">{{ item.name }}</div>
                    <div>样本容量：{{ item.value }} 张</div>
                    <div>更新时间：{{ item.updateTime }}</div>
                    <!--          <a-button @click="sampleType(item.name)">查看</a-button>-->
                </div>
            </div>
        </a-card>
        <a-card :bordered="false" class="model-library">
            <div slot="title"><span class="iconfont icon-shitimoxing card-title-font" />模型库</div>
            <div class="library-top">
                <div class="top-left" ref="modelChart"></div>
                <div class="top-right">
                    <div class="title-item"><span class="iconfont icon-geoai-line card-title-font" />遥感智能解译模型平均精度</div>
                    <div class="top-right-model" ref="modelBarChart"></div>
                </div>
            </div>
            <div class="model-bottom">
                <template v-for="i in modelData">
                    <div
                        class="model-bottom-item"
                        v-for="(item, index) in i.library"
                        :key="index"
                        @click="modelType(item.subname)"
                        :title="'点击查看' + item.subname + ''">
                        <div class="model-title">
                            <span class="iconfont icon-moxingguanli icon-font" />
                            <h3 class="model-name">{{ item.subname }}</h3>
                        </div>
                        <div class="model-content">
                            <a-row>
                                <a-col :span="12"> 正确率：{{ item.accuracy }} </a-col>
                                <a-col :span="12"> 召回率：{{ item.recall }} </a-col>
                            </a-row>
                            <a-row justify="end">
                                <a-col :span="8"> IoU：{{ item.iou }} </a-col>
                                <a-col :span="8"> mAp：{{ item.mAP }} </a-col>
                                <a-col :span="8"> F1系数：{{ item.f1 }} </a-col>
                            </a-row>
                        </div>
                    </div>
                </template>
            </div>
        </a-card>
    </div>
</template>

<script>
import * as echarts from 'echarts';
let sampleData = [
    {
        // name: '建筑物样本库',
        name: '低空目标检测样本库',
        value: 105467,
        updateTime: '2024-10-30'
    },
    {
        name: '道路样本库',
        value: 208897,
        updateTime: '2024-08-04'
    },
    {
        name: '多分类地类样本库',
        value: 360450,
        updateTime: '2024-07-30'
    },
    {
        name: '土地整治图斑样本库',
        value: 147695,
        updateTime: '2024-06-25'
    },
    {
        name: '建设行为样本库',
        value: 15055,
        updateTime: '2024-07-10'
    },
    {
        name: '变化检测样本库',
        value: 150690,
        updateTime: '2024-06-30'
    }
];
let modelData = [
    {
        name: '变化检测模型',
        value: 3,
        color: '#3F7EF3',
        library: [
            {
                subname: '建筑物变化检测模型',
                accuracy: '82.1%',
                recall: '90.3%',
                mAP: '--',
                f1: '0.86',
                iou: '0.76',
                updateTime: '2022-06-10'
            },
            {
                subname: '道路变化检测模型',
                value: 3,
                accuracy: '73.4%',
                recall: '85%',
                iou: '0.69',
                f1: '0.79',
                mAP: '--',
                updateTime: '2022-05-30'
            },
            {
                subname: '多分类地类变化检测模型',
                value: 1,
                accuracy: '66.2%',
                recall: '79.1%',
                mAP: '--',
                iou: '0.78',
                f1: '0.72',
                updateTime: '2022-06-20'
            }
        ]
    },
    {
        name: '图斑分类模型',
        value: 1,
        color: '#B58EE1',
        library: [
            {
                subname: '土地整治图斑分类模型',
                accuracy: '90%',
                recall: '88%',
                f1: '0.89',
                iou: '0.90',
                mAP: '--',
                updateTime: '2022-05-30'
            }
        ]
    },
    {
        name: '影像分割模型',
        value: 3,
        color: '#FCDD7A',
        library: [
            {
                subname: '建筑物分割模型',
                accuracy: '80%',
                recall: '20%',
                mAP: '--',
                f1: '0.79',
                iou: '0.85',
                updateTime: '2022-04-30'
            },
            {
                subname: '道路分割模型',
                accuracy: '74.5%',
                recall: '20%',
                mAP: '--',
                iou: '0.739',
                f1: '0.80',
                updateTime: '2022-04-30'
            },
            {
                subname: '多分类地类分割模型',
                accuracy: '76.6%',
                recall: '20%',
                iou: '0.85',
                mAP: '--',
                f1: '0.76',
                updateTime: '2022-04-30'
            }
        ]
    },
    {
        name: '目标检测模型',
        value: 1,
        color: '#C1DBFC',
        library: [
            {
                subname: '建设行为目标检测模型',
                accuracy: '80%',
                recall: '20%',
                mAP: '71.2%',
                f1: '--',
                iou: '--',
                updateTime: '2022-05-30'
            }
        ]
    }
];
let statisticType = [
    {
        name: '季节',
        value: [
            {
                name: '春天',
                value: '30%'
            },
            {
                name: '夏天',
                value: '30%'
            },
            {
                name: '秋天',
                value: '25%'
            },
            {
                name: '冬天',
                value: '15%'
            }
        ]
    },
    {
        name: '区域',
        value: [
            { name: '江苏省', value: '20%' },
            { name: '青海省', value: '20%' },
            { name: '山东省', value: '20%' },
            { name: '广东省', value: '20%' },
            { name: '湖南省', value: '20%' }
        ]
    },
    {
        name: '分辨率',
        value: [
            {
                name: '2m',
                value: '20%'
            },
            {
                name: '1m',
                value: '40%'
            },
            {
                name: '0.5m',
                value: '20%'
            },
            {
                name: '0.3m',
                value: '20%'
            }
        ]
    }
];
export default {
    name: 'index',
    data() {
        return {
            statisticType: Object.freeze(statisticType),
            sampleData: Object.freeze(sampleData),
            modelData: Object.freeze(modelData)
        };
    },
    created() {},
    mounted() {
        this.initPieEchart('样本库', this.sampleData, 'sampleChart');
        this.initPieEchart('模型库', this.modelData, 'modelChart');
        this.initBarEchart();
    },
    methods: {
        initPieEchart(name, data, ref) {
            let chartDom = this.$refs[`${ref}`];
            let myChart = echarts.init(chartDom);
            let option = {
                tooltip: {
                    trigger: 'item'
                },
                legend: {
                    show: true,
                    type: 'scroll',
                    top: 'bottom'
                },
                series: [
                    {
                        name: '样本库',
                        type: 'pie',
                        radius: ['36%', '60%'],
                        itemStyle: {
                            borderRadius: 10,
                            borderColor: '#ffffff',
                            borderWidth: 2,
                            normal: {
                                color: function (colors) {
                                    const colorList = ['#3F7EF3', '#B58EE1', '#FCDD7A', '#C1DBFC', '#F48C53', '#F27D7D'];
                                    return colorList[colors.dataIndex];
                                }
                            }
                        },
                        label: {
                            show: true,
                            position: 'center',
                            formatter: `${name}总量\n` + this.countValue(data),
                            fontSize: 16,
                            lineHeight: 24
                        },
                        tooltip: {
                            // 鼠标悬浮提示框显示 X和Y 轴数据
                            position: [10, 10],
                            formatter: '{b}：{c}'
                        },
                        data: data
                    }
                ]
            };
            option && myChart.setOption(option);
        },
        initBarEchart() {
            let chartDom = this.$refs.modelBarChart;
            let myChart = echarts.init(chartDom);
            let dataY = [],
                dataX = [];
            this.modelData.forEach((item) => {
                dataX.push(item.name);
                let y = {
                    value: this.getAverage(item.library, 'accuracy'),
                    itemStyle: {
                        color: item.color
                    }
                };
                dataY.push(y);
            });
            let option = {
                title: {
                    show: true,
                    text: ' *变化检测、图斑分类模型精度以精度率衡量；语义分割、\n目标检测模型精度以准确率衡量。',
                    textStyle: {
                        color: 'black',
                        fontSize: '11px',
                        fontWeight: '700'
                    },
                    fontSize: 12,
                    top: 10
                },
                tooltip: {
                    trigger: 'item',
                    formatter: (v) => {
                        return `${v.name}：${v.value.toFixed(4) * 100}%`;
                    }
                },
                xAxis: {
                    type: 'category',
                    data: dataX
                },
                yAxis: {
                    type: 'value',
                    max: 1
                },
                series: [
                    {
                        type: 'bar',
                        data: dataY,
                        barWidth: 20
                    }
                ],
                grid: {
                    width: '80%',
                    height: '50%'
                }
            };
            option && myChart.setOption(option);
        },
        countValue(data) {
            let count = 0;
            data.forEach((item) => {
                count += item.value;
            });
            return count;
        },
        getAverage(data, key) {
            let count = 0;
            data.forEach((item) => {
                count += parseFloat(item[key]);
            });
            return count / data.length / 100;
        },
        showMore(data) {},
        sampleType(name) {
            this.$router.push({
                path: '/resource-center/sample-model/sample-details',
                query: { name }
            });
        },
        modelType(name) {
            this.$router.push({
                path: '/resource-center/sample-model/model-details',
                query: { name }
            });
        }
    }
};
</script>

<style scoped>
.library-container {
    width: 100%;
    height: 100%;
    display: flex;
    background-color: transparent !important;
}

.sample-library,
.model-library {
    box-sizing: border-box;
    width: 50%;
    height: 100%;
    /* padding: 0.5rem; */
    background-color: white;
    display: flex;
    flex-direction: column;
}
.create-time {
    text-align: left;
}
.sample-library {
    margin-right: 0.5rem;
}

.library-title {
    font-size: 1rem;
    height: 2rem;
    line-height: 2rem;
    font-weight: 600;
    color: black;
    border-bottom: 0.1rem solid #c8c8c8;
    margin-bottom: 1rem;
}

.library-top {
    height: 20rem;
    width: 100%;
    /* border: 0.1rem solid #c8c8c8;
  border-radius: 0.3rem; */
    display: flex;
    /* align-items: center; */
    padding: 0.5rem;
    position: relative;
}

.sample-bottom {
    width: 100%;
    height: calc(100% - 20rem);
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    margin-top: 0.5rem;
    overflow: auto;
    font-size: 1rem;
    color: black;
}

.model-bottom {
    width: 100%;
    height: calc(100% - 20rem);
    flex: 1;
    display: flex;
    flex-direction: row;
    justify-content: start;
    align-content: flex-start;
    flex-wrap: wrap;
    margin-top: 0.5rem;
    overflow: auto;
}

.top-left {
    /* width: 20rem; */
    width: 60%;
    height: 80%;
}

.top-right {
    width: 60%;
    height: 100%;
    /* flex: 1;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center; */
}

.top-right-model {
    width: 100%;
    height: calc(100% - 30px);
}

.statistic-type-title {
    height: 2.5rem;
    line-height: 2.5rem;
    font-size: 1rem;
    color: black;
    font-weight: 600;
}

.statistic-type-content {
    height: 2rem;
    line-height: 2rem;
}

.content-item {
    display: inline-block;
    color: white;
    text-align: center;
}

.content-item:hover {
    cursor: pointer;
    font-weight: 600;
    transition: all 200ms linear;
}

.content-item:nth-child(even) {
    background-color: #f27d7d;
}

.content-item:nth-child(odd) {
    background-color: #eea6a6;
}

/* .content-item:nth-child(1) {
  background-color: #A9B9FA;
}
.content-item:nth-child(2) {
  background-color: #C7CDFE;
}
.content-item:nth-child(3) {
  background-color: #D7C9FD;
}
.content-item:nth-child(4) {
  background-color: #F4E3FE;
}
.content-item:nth-child(5) {
  background-color: #F4E3FE;
} */

.sample-bottom-item {
    display: flex;
    justify-content: space-around;
    align-items: center;
    height: 6rem;
    min-height: 6rem;
    /* background-color: #c6e8ff; */
    margin-bottom: 0.5rem;
    /* cursor: pointer; */
    border: 2px solid #e4e4e4;
}

.sample-name {
    font-weight: 600;
}

/* .sample-content {
  height: 100%;
  font-size: 1rem;
  color: black;
  display: flex;
  flex-direction: column;
  justify-content: space-around;
} */

.model-bottom-item {
    box-sizing: border-box;
    width: calc(50% - 1rem);
    margin: 0 0.5rem 0.5rem 0.5rem;
    padding: 0.5rem 1rem;
    min-height: 6rem;
    height: calc(25% - 0.5rem);
    /* display: flex;
  flex-direction: column;
  justify-content: center; */
    border: 2px solid #e4e4e4;
    cursor: pointer;
}

.model-name {
    font-size: 1rem;
    color: black;
    font-weight: 600;
    text-align: center;
    margin-bottom: 0 !important;
    margin-left: 10px;
}
.model-title {
    display: flex;
    align-items: center;
    height: 50%;
}
.model-title span {
    font-size: 20px;
}
.model-content {
    height: 50%;
    font-size: 16px;
    color: black;
    display: flex;
    padding-left: 5%;
    flex-direction: column;
    justify-content: center;
    text-align: left;
}
.card-title-font {
    margin-right: 8px;
    color: #42b4f2;
    font-size: 20px;
}
::v-deep(.ant-card-head-title) {
    padding-top: 6px !important;
    padding-bottom: 6px !important;
}
::v-deep(.ant-card-head) {
    min-height: 40px;
}
.title-item {
    width: 100%;
    height: 30px;
    background-image: linear-gradient(to right, #cfecff, #fff);
    /* margin-bottom: 10px; */
}
.icon-font {
    color: #42b4f2;
    font-size: 40px;
}
.ant-btn {
    border-radius: 20px;
}
::v-deep(.ant-card-body) {
    height: calc(100% - 40px);
    padding: 0 8px 24px !important;
}
.model-bottom-item:hover,
.sample-bottom-item:hover {
    border: 2px solid #42b4f2;
    cursor: pointer;
}
.model-title:hover:after {
    content: attr(title);
}
</style>
