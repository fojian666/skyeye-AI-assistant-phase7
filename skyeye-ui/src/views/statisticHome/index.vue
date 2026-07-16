<template>
    <div class="se-sh-proto">
        <div class="proto-body">
            <div class="proto-col proto-col--side">
                <div class="proto-panel">
                    <div class="proto-panel__title"><h2>大运河线保护监管区域分布</h2></div>
                    <div class="proto-panel__body"><div class="proto-chart" ref="bar1"></div></div>
                </div>
                <div class="proto-panel">
                    <div class="proto-panel__title"><h2>用地类型</h2></div>
                    <div class="proto-panel__body"><div class="proto-chart" ref="bar12"></div></div>
                </div>
                <div class="proto-panel">
                    <div class="proto-panel__title"><h2>全景飞行时间分布</h2></div>
                    <div class="proto-panel__body"><div class="proto-chart" ref="bar2"></div></div>
                </div>
            </div>

            <div class="proto-col proto-col--center">
                <div class="proto-map-stage">
                    <small-map class="proto-map"></small-map>
                </div>
            </div>

            <div class="proto-col proto-col--side">
                <div class="proto-panel">
                    <div class="proto-panel__title"><h2>大运河图斑监察</h2></div>
                    <div class="proto-panel__body"><div class="proto-chart" ref="bar3"></div></div>
                </div>
                <div class="proto-panel">
                    <div class="proto-panel__title"><h2>规划全景点位分布</h2></div>
                    <div class="proto-panel__body"><div class="proto-chart" ref="bar34"></div></div>
                </div>
                <div class="proto-panel">
                    <div class="proto-panel__title"><h2>无人机监管次数</h2></div>
                    <div class="proto-panel__body"><div class="proto-chart" ref="bar4"></div></div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import * as echarts from 'echarts';
import { getDataInfoApi } from '@/api/commonApi';
import smallMap from '@/components/smallMap/index.vue';
import { mergeDarkOption, CYAN_PALETTE, colorizeRegionData } from './chartTheme';

export default {
    name: 'StatisticHome',
    components: { smallMap },
    data() {
        return {
            map: '',
            mapBounds: [],
            layerRandList: [],
            center: window.config.center,
            baseMapService: window.config.baseMapService,
            baseMapServiceType: window.config.baseMapServiceType,
            baseMaxNativeZoom: window.config.baseMaxNativeZoom,
            minZoom: window.config.minZoom,
            maxZoom: window.config.maxZoom,
            zoom: window.config.zoom,
            currentShowZoom: window.config.zoom,
            eightData: {
                gridOperatorNumber: '0',
                gridNumber: '0',
                quanjingPointNumber: '0',
                batchNumber: '0',
                uploadNumber: '0',
                cluesNumber: '0',
                invalidCluesNumber: '0',
                effectiveCluesNumber: '0'
            }
        };
    },
    computed: {
        flatStats() {
            const d = this.eightData;
            return [
                { value: d.gridOperatorNumber, label: '网格员' },
                { value: d.gridNumber, label: '网格' },
                { value: d.quanjingPointNumber, label: '全景点' },
                { value: d.batchNumber, label: '批次' },
                { value: d.uploadNumber, label: '上传次数' },
                { value: '3', label: '全景' },
                { value: d.invalidCluesNumber, label: '无效线索' },
                { value: d.effectiveCluesNumber, label: '有效线索' }
            ];
        }
    },
    methods: {
        initChart(ref, option) {
            const el = this.$refs[ref];
            if (!el) return;
            const chart = echarts.init(el);
            chart.setOption(mergeDarkOption(option));
            const resize = () => chart.resize();
            window.addEventListener('resize', resize);
            this.$once('hook:beforeDestroy', () => {
                window.removeEventListener('resize', resize);
                chart.dispose();
            });
        },
        bar1() {
            const regionData = [
                { value: 0, name: '滨湖区' },
                { value: 4, name: '梁溪区' },
                { value: 0, name: '锡山区' },
                { value: 0, name: '惠山区' },
                { value: 1, name: '新吴区' }
            ];
            this.initChart('bar1', {
                tooltip: {
                    trigger: 'item',
                    formatter: (p) => `<span style="color:${p.color}">●</span> ${p.name}<br/>占比: ${p.percent.toFixed(2)}%`
                },
                series: [
                    {
                        type: 'pie',
                        radius: [16, 72],
                        center: ['50%', '52%'],
                        roseType: 'area',
                        label: {
                            show: true,
                            position: 'outside',
                            fontSize: 11,
                            formatter: (p) => `${p.name}:${p.percent.toFixed(1)}%`
                        },
                        labelLine: { show: true, length: 6, length2: 10, smooth: false },
                        data: colorizeRegionData(regionData)
                    }
                ]
            });
        },
        bar12() {
            this.initChart('bar12', {
                grid: { left: 16, right: 16, top: 24, bottom: 4, containLabel: true },
                tooltip: { trigger: 'axis' },
                xAxis: { type: 'category', data: ['居住用地', '研发型工业用地', '商务金融用地', '医院用地'] },
                yAxis: { type: 'value' },
                series: [
                    {
                        type: 'bar',
                        data: [2, 1, 1, 1],
                        barWidth: '40%',
                        itemStyle: {
                            borderRadius: [4, 4, 0, 0],
                            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                                { offset: 0, color: '#00f2ff' },
                                { offset: 1, color: 'rgba(0, 180, 200, 0.3)' }
                            ])
                        },
                        label: { show: true, position: 'top', color: '#00f2ff', fontSize: 11 }
                    }
                ]
            });
        },
        bar2() {
            this.initChart('bar2', {
                grid: { left: 16, right: 16, top: 24, bottom: 4, containLabel: true },
                tooltip: { trigger: 'axis' },
                xAxis: { type: 'category', data: ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'] },
                yAxis: { type: 'value' },
                series: [
                    {
                        type: 'line',
                        data: [0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0],
                        symbol: 'circle',
                        symbolSize: 6,
                        lineStyle: { color: '#00f2ff', width: 2 },
                        itemStyle: { color: '#00f2ff', borderColor: '#fff', borderWidth: 1 },
                        areaStyle: {
                            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                                { offset: 0, color: 'rgba(0, 242, 255, 0.25)' },
                                { offset: 1, color: 'rgba(0, 242, 255, 0)' }
                            ])
                        }
                    }
                ]
            });
        },
        bar3() {
            this.initChart('bar3', {
                grid: { left: 16, right: 16, top: 24, bottom: 4, containLabel: true },
                tooltip: { trigger: 'axis' },
                xAxis: { type: 'category', data: ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'] },
                yAxis: { type: 'value' },
                series: [
                    {
                        type: 'line',
                        data: [4, 1, 0, 9, 4, 10, 0, 0, 0, 0, 0, 0],
                        symbol: 'circle',
                        symbolSize: 6,
                        lineStyle: { color: '#4dd0ff', width: 2, type: 'dashed' },
                        itemStyle: { color: '#ffb74d', borderColor: '#00f2ff', borderWidth: 2 }
                    }
                ]
            });
        },
        bar34() {
            this.initChart('bar34', {
                tooltip: { trigger: 'item' },
                color: CYAN_PALETTE,
                series: [
                    {
                        type: 'pie',
                        radius: ['35%', '70%'],
                        center: ['50%', '50%'],
                        itemStyle: { borderRadius: 4, borderColor: '#050c17', borderWidth: 2 },
                        label: {
                            show: true,
                            color: 'rgba(160, 210, 230, 0.85)',
                            fontSize: 11,
                            formatter: (p) => `${p.name}:${p.percent.toFixed(1)}%`
                        },
                        data: [
                            { value: 1, name: '华庄街道' },
                            { value: 4, name: '扬名街道' },
                            { value: 4, name: '惠山街道' },
                            { value: 3, name: '太湖街道' }
                        ]
                    }
                ]
            });
        },
        bar4() {
            this.initChart('bar4', {
                grid: { left: 16, right: 16, top: 24, bottom: 4, containLabel: true },
                tooltip: { trigger: 'axis' },
                xAxis: { type: 'category', data: ['滨湖区', '梁溪区', '锡山区', '惠山区', '新吴区'] },
                yAxis: { type: 'value' },
                series: [
                    {
                        type: 'bar',
                        data: [1, 4, 0, 1, 1, 0, 0],
                        barWidth: '45%',
                        itemStyle: {
                            borderRadius: [4, 4, 0, 0],
                            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                                { offset: 0, color: '#4dd0ff' },
                                { offset: 1, color: 'rgba(0, 100, 140, 0.4)' }
                            ])
                        },
                        label: { show: true, position: 'top', color: '#4dd0ff', fontSize: 11 }
                    }
                ]
            });
        },
        async getEightDataInfo() {
            const res = await getDataInfoApi();
            if (res.code === 0) {
                this.eightData.batchNumber = res.data.batch_count;
                this.eightData.cluesNumber = res.data.clue_count;
                this.eightData.effectiveCluesNumber = res.data.clue_effective_count;
                this.eightData.invalidCluesNumber = res.data.clue_invalid_count;
                this.eightData.gridNumber = res.data.grid_count;
                this.eightData.gridOperatorNumber = res.data.grid_operator_count;
                this.eightData.quanjingPointNumber = res.data.point_count;
                this.eightData.uploadNumber = res.data.upload_batch_count;
            } else {
                this.$message.error(res.msg);
            }
        }
    },
    mounted() {
        this.$nextTick(() => {
            this.bar1();
            this.bar12();
            this.bar2();
            this.bar3();
            this.bar34();
            this.bar4();
        });
        this.getEightDataInfo();
    }
};
</script>

<style lang="scss" scoped>
@import './statistic-home.scss';

::v-deep .proto-map-stage .leaflet-container {
    z-index: 1;
}

::v-deep .leaflet-bottom.leaflet-right {
    bottom: 8px;
    right: 8px;
}

::v-deep .leaflet-control-zoom a {
    background: rgba(10, 30, 50, 0.9) !important;
    color: $proto-accent !important;
    border-color: $proto-border !important;

    &:hover {
        background: rgba(0, 242, 255, 0.15) !important;
    }
}
</style>
