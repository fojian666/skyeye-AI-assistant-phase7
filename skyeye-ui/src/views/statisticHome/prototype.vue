<template>
  <div class="se-sh-proto">
    <!-- 顶部 HUD 标题栏 -->
    <div class="proto-header">
      <div class="proto-header__side proto-header__time">
        <span>{{ currentTime }}</span>
      </div>
      <div class="proto-header__center">
        <div class="proto-header__deco proto-header__deco--left"></div>
        <h1 class="proto-header__title">无锡市无人机重大项目跟踪场景</h1>
        <div class="proto-header__deco proto-header__deco--right"></div>
      </div>
      <div class="proto-header__side proto-header__actions">
        <span class="proto-weather">晴 29°C</span>
        <router-link to="/data-management/one-map" class="se-header-action-btn">
          <i class="iconfont icon-a-xitonggailan"></i>进入系统
        </router-link>
      </div>
    </div>

    <!-- 三栏主体 -->
    <div class="proto-body">
      <!-- 左侧图表栏 -->
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

      <!-- 中间区：统计条 + 地图 + 底部列表，纵向分区不重叠 -->
      <div class="proto-col proto-col--center">
        <div class="proto-stats-row">
          <div class="proto-stat-pill" v-for="(item, idx) in flatStats" :key="idx">
            <span class="proto-stat-pill__value">{{ item.value }}</span>
            <span class="proto-stat-pill__label">{{ item.label }}</span>
          </div>
        </div>
        <div class="proto-map-stage">
          <div class="proto-map" id="map"></div>
        </div>
        <div class="proto-bottom-row">
          <div class="proto-list-card" v-for="list in bottomLists" :key="list.title">
            <h3 class="proto-list-card__title">{{ list.title }}</h3>
            <ul class="proto-list-card__body">
              <li
                v-for="(item, idx) in list.items"
                :key="idx"
                :class="{ 'is-highlight': item.highlight }"
              >{{ item.text }}</li>
            </ul>
          </div>
        </div>
      </div>

      <!-- 右侧图表栏 -->
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

    <!-- 原型标识 -->
    <div class="proto-badge">样式原型预览</div>
  </div>
</template>

<script>
import * as echarts from 'echarts';
import { getDataInfoApi } from '@/api/commonApi';
import L from 'leaflet';
import { TiledMapLayer } from '@supermap/iclient-leaflet';
import { mergeDarkOption, CYAN_PALETTE, colorizeRegionData } from './chartTheme';

export default {
  name: 'StatisticHomePrototype',
  data() {
    return {
      map: '',
      mapBounds: [],
      center: window.config.center,
      baseMapService: window.config.baseMapService,
      baseMapServiceType: window.config.baseMapServiceType,
      baseMaxNativeZoom: window.config.baseMaxNativeZoom,
      minZoom: window.config.minZoom,
      maxZoom: window.config.maxZoom,
      currentShowZoom: window.config.zoom,
      currentTime: this.updateDateTime(),
      eightData: {
        gridOperatorNumber: '0',
        gridNumber: '0',
        quanjingPointNumber: '0',
        batchNumber: '0',
        uploadNumber: '0',
        invalidCluesNumber: '0',
        effectiveCluesNumber: '0'
      },
      bottomLists: [
        {
          title: '线索',
          items: [
            { text: '1.WX 20260526(2026-05-26)' },
            { text: '2.WX 20260507(2026-05-07)' },
            { text: '3.WX 20260501(2026-05-19)' },
            { text: '4.WX 20260502(2026-05-19)' }
          ]
        },
        {
          title: '全景',
          items: [
            { text: '1.华润燃东北侧(正常)' },
            { text: '2.华德兴欣钢杆厂(正常)', highlight: true },
            { text: '3.华盛路与扬高路(正常)' },
            { text: '4.惠山古镇三期F地(正常)' },
            { text: '5.经开区贡湖大道(正常)' }
          ]
        },
        {
          title: '视频',
          items: [
            { text: '1.扬名街道监测1 (20260604)' },
            { text: '2.惠山街道监测 (20260604)' },
            { text: '3.太湖街道监测 (20260604)' },
            { text: '4.扬名街道监测2 (20260604)' },
            { text: '5.扬名街道监测3 (20260604)' }
          ]
        }
      ]
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
    updateDateTime() {
      const weekdays = ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六'];
      const now = new Date();
      const year = now.getFullYear();
      let month = now.getMonth() + 1;
      let day = now.getDate();
      const weekday = weekdays[now.getDay()];
      if (month < 10) month = '0' + month;
      if (day < 10) day = '0' + day;
      const date = year + '年' + month + '月' + day + '日 ' + weekday;
      let hours = now.getHours();
      let minutes = now.getMinutes();
      let seconds = now.getSeconds();
      if (hours < 10) hours = '0' + hours;
      if (minutes < 10) minutes = '0' + minutes;
      if (seconds < 10) seconds = '0' + seconds;
      return date + hours + ':' + minutes + ':' + seconds;
    },
    updateTime() {
      this.currentTime = this.updateDateTime();
    },
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
        { value: 0, name: '滨湖区' }, { value: 4, name: '梁溪区' },
        { value: 0, name: '锡山区' }, { value: 0, name: '惠山区' },
        { value: 1, name: '新吴区' }, { value: 0, name: '江阴市' },
        { value: 0, name: '宜兴市' }
      ];
      this.initChart('bar1', {
        tooltip: {
          trigger: 'item',
          formatter: p => `<span style="color:${p.color}">●</span> ${p.name}<br/>占比: ${p.percent.toFixed(2)}%`
        },
        series: [{
          type: 'pie',
          radius: [16, 72],
          center: ['50%', '52%'],
          roseType: 'area',
          label: {
            show: true,
            position: 'outside',
            fontSize: 11,
            formatter: p => `${p.name}:${p.percent.toFixed(1)}%`
          },
          labelLine: {
            show: true,
            length: 6,
            length2: 10,
            smooth: false
          },
          data: colorizeRegionData(regionData)
        }]
      });
    },
    bar12() {
      this.initChart('bar12', {
        grid: { left: 16, right: 16, top: 24, bottom: 4, containLabel: true },
        tooltip: { trigger: 'axis' },
        xAxis: { type: 'category', data: ['居住用地', '研发型工业用地', '商务金融用地', '医院用地'] },
        yAxis: { type: 'value' },
        series: [{
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
        }]
      });
    },
    bar2() {
      this.initChart('bar2', {
        grid: { left: 16, right: 16, top: 24, bottom: 4, containLabel: true },
        tooltip: { trigger: 'axis' },
        xAxis: { type: 'category', data: ['1月','2月','3月','4月','5月','6月','7月','8月','9月','10月','11月','12月'] },
        yAxis: { type: 'value' },
        series: [{
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
        }]
      });
    },
    bar3() {
      this.initChart('bar3', {
        grid: { left: 16, right: 16, top: 24, bottom: 4, containLabel: true },
        tooltip: { trigger: 'axis' },
        xAxis: { type: 'category', data: ['1月','2月','3月','4月','5月','6月','7月','8月','9月','10月','11月','12月'] },
        yAxis: { type: 'value' },
        series: [{
          type: 'line',
          data: [4, 1, 0, 9, 4, 10, 0, 0, 0, 0, 0, 0],
          symbol: 'circle',
          symbolSize: 6,
          lineStyle: { color: '#4dd0ff', width: 2, type: 'dashed' },
          itemStyle: { color: '#ffb74d', borderColor: '#00f2ff', borderWidth: 2 }
        }]
      });
    },
    bar34() {
      this.initChart('bar34', {
        tooltip: { trigger: 'item' },
        color: CYAN_PALETTE,
        series: [{
          type: 'pie',
          radius: ['35%', '70%'],
          center: ['50%', '50%'],
          itemStyle: { borderRadius: 4, borderColor: '#050c17', borderWidth: 2 },
          label: {
            show: true,
            color: 'rgba(160, 210, 230, 0.85)',
            fontSize: 11,
            formatter: p => `${p.name}:${p.percent.toFixed(1)}%`
          },
          data: [
            { value: 1, name: '华庄街道' }, { value: 4, name: '扬名街道' },
            { value: 4, name: '惠山街道' }, { value: 3, name: '太湖街道' }
          ]
        }]
      });
    },
    bar4() {
      this.initChart('bar4', {
        grid: { left: 16, right: 16, top: 24, bottom: 4, containLabel: true },
        tooltip: { trigger: 'axis' },
        xAxis: { type: 'category', data: ['滨湖区', '梁溪区', '锡山区', '惠山区', '新吴区', '江阴市', '宜兴市'] },
        yAxis: { type: 'value' },
        series: [{
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
        }]
      });
    },
    initMap() {
      const myCrs = L.CRS.EPSG3857;
      this.map = L.map('map', {
        crs: myCrs,
        zoom: 12,
        zoomControl: false,
        center: this.center,
        attributionControl: false,
        preferCanvas: true,
        maxZoom: 18,
        minZoom: 2
      });
      if (this.mapBounds.length > 0) {
        this.map.fitBounds(this.mapBounds);
      }
      if (this.baseMapService) {
        let baseMapLayer;
        if (this.baseMapServiceType === '1') {
          baseMapLayer = new TiledMapLayer(this.baseMapService, {
            maxZoom: this.maxZoom,
            maxNativeZoom: this.baseMaxNativeZoom,
            reuseTiles: false,
            updateWhenIdle: false,
            updateWhenZooming: false,
            keepBuffer: 1000,
            updateInterval: 0,
            tileSize: 256,
            fadeAnimation: false,
            zoomAnimation: false,
            preferCanvas: true,
            noWrap: true
          });
        } else if (this.baseMapServiceType === '2') {
          baseMapLayer = L.tileLayer(`${this.baseMapService}/tile/{z}/{y}/{x}`, {
            maxZoom: this.maxZoom,
            maxNativeZoom: this.baseMaxNativeZoom,
            minZoom: this.minZoom,
            updateWhenIdle: false,
            updateWhenZooming: false,
            keepBuffer: 3,
            updateInterval: 200,
            noWrap: true
          });
        } else {
          baseMapLayer = L.tileLayer(this.baseMapService, {
            maxZoom: this.maxZoom,
            maxNativeZoom: this.baseMaxNativeZoom,
            reuseTiles: false,
            updateWhenIdle: true,
            updateInterval: 200,
            keepBuffer: 1,
            noWrap: true
          });
        }
        baseMapLayer.addTo(this.map);
        baseMapLayer.bringToBack();
      }
      L.control.zoom({ position: 'bottomright' }).addTo(this.map);
      this.$nextTick(() => this.resizeMap());
      window.addEventListener('resize', this.resizeMap);
      this.$once('hook:beforeDestroy', () => {
        window.removeEventListener('resize', this.resizeMap);
      });
    },
    resizeMap() {
      if (this.map) {
        setTimeout(() => this.map.invalidateSize(), 100);
      }
    },
    async getEightDataInfo() {
      try {
        const res = await getDataInfoApi();
        if (res.code === 0) {
          this.eightData.batchNumber = res.data.batch_count;
          this.eightData.effectiveCluesNumber = res.data.clue_effective_count;
          this.eightData.invalidCluesNumber = res.data.clue_invalid_count;
          this.eightData.gridNumber = res.data.grid_count;
          this.eightData.gridOperatorNumber = res.data.grid_operator_count;
          this.eightData.quanjingPointNumber = res.data.point_count;
          this.eightData.uploadNumber = res.data.upload_batch_count;
        }
      } catch (e) {
        // 原型页允许离线预览
      }
    }
  },
  mounted() {
    this.updateTime();
    setInterval(this.updateTime, 1000);
    this.$nextTick(() => {
      this.bar1();
      this.bar12();
      this.bar2();
      this.bar3();
      this.bar34();
      this.bar4();
      this.initMap();
    });
    this.getEightDataInfo();
  }
};
</script>

<style lang="scss" scoped>
@import './statistic-home.scss';

.proto-badge {
  position: fixed;
  bottom: 12px;
  right: 16px;
  padding: 4px 12px;
  font-size: 11px;
  color: $proto-accent;
  border: 1px solid $proto-border;
  border-radius: $proto-radius-pill;
  background: rgba(5, 12, 23, 0.85);
  box-shadow: 0 0 10px $proto-accent-glow;
  z-index: 999;
  pointer-events: none;
  letter-spacing: 1px;
}

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
