<template>
  <div class="content">
    <div class="left">
      <div class="item-258">
        <div class="item-title">
          <span>巡检任务统计</span>
          <i class="iconfont icon-rili"/>
        </div>
        <div class="item-content">
          <div class="cnt-box">
            <div id="inspectionTaskEchart">
            </div>
            <div class="total">
              <span>任务总量</span>
              <span class="number">{{ totalValue }}</span>
            </div>
          </div>
          <div class="legend">
            <div v-for="(item, index) in taskData" :key="index" class="legend-content">
              <div class="dot" :style="{ backgroundColor: item.itemStyle.color }"></div>
              <span>{{ item.name }}</span>
              <span class="legend-number">
                 {{ Math.round((item.value / totalValue) * 100) }}%
              </span>
            </div>
          </div>
        </div>
      </div>
      <div class="item-675">
        <div class="item-title">
          <span>巡检线索统计</span>
        </div>
        <div class="item-content vertical">
          <div class="sub-title">
            <div class="m-10">
              <i class="iconfont icon-lingxing"/>
              <span>趋势统计</span>
            </div>
            <div class="sub-title-button">
              <div class="title-button" :class="{ 'title-button-active': selected === 'month' }"
                   @click="selectMonth" id="month">
                <span>月</span>
              </div>
              <div class="title-button" :class="{ 'title-button-active': selected === 'quarter' }"
                   @click="selectQuarter" id="quarter"><span>季度</span>
              </div>
              <div class="title-button" :class="{ 'title-button-active': selected === 'year' }"
                   @click="selectYear" id="year"><span>年</span>
              </div>
            </div>
          </div>
          <div id="trendStatisticsEchart">
          </div>
          <div class="sub-title">
            <div class="m-10"><i class="iconfont icon-lingxing"/><span>类型统计</span></div>
          </div>
          <div class="typeStatistic">
            <div class="typeStatisticEchart">
              <span>单位：个</span>
              <div id="typeStatisticEchart"></div>
            </div>
            <div class="legend">
              <div v-for="(item, index) in typeData" :key="index" class="type-legend-content">
                <div class="dot" :style="{ backgroundColor: item.itemStyle.color }"></div>
                <span style="width: 56px">{{ item.name }}</span>
                <span class="type-legend-number">
                 {{ Math.round((item.value / typeDataTotal) * 100) }}%
                </span>
                <span class="type-legend-number">
                  {{ item.value }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="center"></div>
    <div class="right">
      <div class="item-433">
        <div class="item-title">
          <span>机巢列表</span>
        </div>
        <div class="item-content">
          <div class="nest-box">
            <div class="nest-title">
              <div class="nest-title-content">
                <div class="nest-dot" style="background-color: #3BD571"></div>
                <div>在线（{{ onlineNum }}）</div>
              </div>
              <div class="action-item">|</div>
              <div class="nest-title-content">
                <div class="nest-dot" style="background-color: #ED3F14"></div>
                <div>离线（{{ offlineNum }}）</div>
              </div>
              <div class="w-220">
                <el-input placeholder="请输入" suffix-icon="el-icon-search" v-model="searchNest"></el-input>
              </div>
            </div>
            <div class="nest-list">
              <template>
                <div>
                  <div class="nest-list-item" v-for="item in nestList" :key="item.id">
                    <div class="nest-item-left">
                      <img :src="require('@/assets/images/portal/gallery.png')" alt=""/>
                      <div class="nest-name">{{ item.name }}</div>
                    </div>
                    <div class="nest-item-right">
                      <img :src="require(`@/assets/images/portal/${item.status}.png`)"
                           :style="{ width: '56px', height: '22px' }"/>
                    </div>
                  </div>
                </div>
              </template>
            </div>
          </div>
        </div>
      </div>

      <div class="item-513">
        <div class="item-title">
          <span>巡检计划列表</span>
        </div>
        <div class="patrol-scheme-item-content pd-10">
          <vue-seamless-scroll :class-option="defineScroll" :data="patrolSchemeList">
            <template>
              <div class="patrol-scheme-item" v-for="item in patrolSchemeList">
                <div class="plane-icon">
                  <img :src="require('@/assets/images/portal/plane.png')" alt=""/>
                </div>
                <div class="patrol-scheme-table">
                  <div class="patrol-scheme-title">{{ item.title }}</div>
                  <div class="patrol-scheme-content">
                    <div class="patrol-scheme-detail">
                      <div class="patrol-scheme-name">机巢</div>
                      <div class="patrol-scheme-value">{{ item.nestName }}</div>
                    </div>
                    <div class="patrol-scheme-detail">
                      <div class="patrol-scheme-name">任务类型</div>
                      <div class="patrol-scheme-value">{{ item.taskType }}</div>
                    </div>
                    <div class="patrol-scheme-detail">
                      <div class="patrol-scheme-name">执行时间</div>
                      <div class="patrol-scheme-value">{{ item.time }}</div>
                    </div>
                    <div class="patrol-scheme-detail">
                      <div class="patrol-scheme-name">采集数据</div>
                      <div class="patrol-scheme-value">{{ item.data }}</div>
                    </div>
                  </div>
                </div>
              </div>
            </template>
          </vue-seamless-scroll>
        </div>
      </div>
    </div>
    <div class="mapcontainer" id="map">
    </div>
  </div>
</template>

<script>
import vueSeamlessScroll from 'vue-seamless-scroll'
import * as echarts from 'echarts';
import 'echarts-gl';
import {getMapInfoApi} from '@/api/commonApi';
import {TiledMapLayer} from '@supermap/iclient-leaflet';
import {getPie3D} from "@/js/echart/pie";

export default {
  name: 'portal',
  data() {
    return {
      map: {},
      center: [],
      mapService: '',
      taskData: [],
      totalValue: 0,
      typeData: [],
      typeDataTotal: 0,
      onlineNum: 3,
      offlineNum: 1,
      searchNest: '',
      nestList: [],
      patrolSchemeList: [],
      selected: 'month'
    };
  },
  watch: {},
  methods: {
    //初始化地图
    initMap() {
      this.map = L.map('map', {
        crs: L.CRS.EPSG4326,
        center: this.center, //中心坐标
        zoom: 14, //缩放级别
        zoomControl: false, //缩放组件
        attributionControl: false //去掉右下角logo
      });
      const layer = new TiledMapLayer(this.mapService).addTo(this.map);

      // 创建图标
      var icon = L.icon({
        iconUrl: require('@/assets/images/portal/planeRange.png'),
        iconSize: [122, 122],
        iconAnchor: [20, 41]
      });

      // 创建标记并设置图标
      L.marker([31.9255, 118.8143], {icon: icon}).addTo(this.map);
      L.marker([31.9174, 118.8013], {icon: icon}).addTo(this.map);

    },
    initCharts() {
      this.inspectionTaskStatistics();
      this.trendStatistics();
      this.typeStatistics();
      this.initPotrolScheme();
    },
    inspectionTaskStatistics() {
      let myChart = echarts.init(
          document.getElementById('inspectionTaskEchart')
      );
      this.taskData = [
        {
          name: "耕地保护",
          value: 110,
          itemStyle: {
            color: "#006cff",
          },
        },
        {
          name: "林地管理",
          value: 200,
          itemStyle: {
            color: "#4ac789",
          },
        },
        {
          name: "城市治理",
          value: 190,
          itemStyle: {
            color: "#43bfec",
          },
        },
        {
          name: "水务执法",
          value: 190,
          itemStyle: {
            color: "#ee8529",
          },
        }
      ];

      this.totalValue = this.taskData.reduce((sum, item) => sum + item.value, 0);

      const series = getPie3D(this.taskData, 0.6);
      // 准备待返回的配置项，把准备好的 legendData、series 传入。
      const option = {
        animation: true,
        tooltip: {
          formatter: (params) => {
            if (
                params.seriesName !== "mouseoutSeries" &&
                params.seriesName !== "pie2d"
            ) {
              return `${
                  params.seriesName
              }<br/><span style="display:inline-block;margin-right:5px;border-radius:10px;width:10px;height:10px;background-color:${
                  params.color
              };"></span>${
                  option.series[params.seriesIndex].pieData.value
              }`;
            }
          },
        },
        backgroundColor: "transparent",
        labelLine: {
          show: true,
          lineStyle: {
            color: "#7BC0CB",
          },
          normal: {
            show: true,
            length: 10,
            length2: 10,
          },
        },
        label: {
          show: true,
          position: "outside",
          formatter: "{b} \n{c}\n{d}%",
          textStyle: {
            color: "rgba(176, 216, 223, 1)",
            fontSize: 24,
          },
        },
        xAxis3D: {
          min: -1,
          max: 1,
        },
        yAxis3D: {
          min: -1,
          max: 1,
        },
        zAxis3D: {
          min: -1,
          max: 1,
        },
        grid3D: {
          show: false,
          boxHeight: 1,
          bottom: '20%',
          viewControl: {
            alpha: 45,
            autoRotate: true,
            zoomSensitivity: 0
          },
        },
        series: series,
      };
      myChart.setOption(option);
      window.addEventListener('resize', () => myChart.resize());
    },
    trendStatistics() {
      let xAxisData = [2025.4, 2025.5, 2025.6, 2025.7]
      let seriesData = [88, 20, 50, 10]
      const getSymbolData = (datas) => {
        let arr = []
        for (var i = 0; i < datas.length; i++) {
          arr.push({
            value: datas[i],
            symbolPosition: 'end',
          })
        }
        return arr
      }
      let myChart = echarts.init(
          document.getElementById('trendStatisticsEchart')
      );
      const option = {
        tooltip: {
          trigger: "axis",
          axisPointer: {
            type: "shadow",
            textStyle: {
              color: "#fff"
            }
          },
        },
        grid: {
          borderWidth: 0,
          top: '18%',
          bottom: '15%',
          left: '12%',
          textStyle: {
            color: "#fff"
          }
        },
        xAxis: [{
          type: "category",
          axisLine: {
            lineStyle: {
              color: '#DCDCDC'
            }
          },
          splitLine: {
            show: false
          },
          axisTick: {
            show: false
          },
          splitArea: {
            show: false
          },
          axisLabel: {
            interval: 0,
            fontSize: 14,
            lineHeight: 16,
            margin: 12
          },
          data: xAxisData,
        }],
        yAxis: {
          name: '单位：条',
          nameTextStyle: {
            fontSize: 12,
            color: '#DCDCDC',
            align: "right"
          },
          axisLabel: {
            color: "#DEF1FF",
          },
          type: 'value',
          axisLine: {
            show: false,
            lineStyle: {
              color: '#fff'
            }
          },
          splitLine: {
            show: true,
            lineStyle: {
              color: 'rgba(4, 187, 255, .2)',
              type: 'dashed'
            }
          },
          axisTick: {
            show: false
          }
        },
        series: [{
          name: '线索数量',
          type: "bar",
          barMaxWidth: 42,
          showBackground: true,
          itemStyle: {
            normal: {
              show: true,
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{
                offset: 0,
                color: 'rgba(18,78,167,0.2)'
              }, {
                offset: 1,
                color: '#0095FF'
              }]),
              barBorderRadius: 0,
              label: {
                show: true,
                position: "top",
                color: '#fff',
                formatter: function (p) {
                  return p.value > 0 ? (p.value) : '';
                }
              }
            },
          },
          data: seriesData,
        },
          {
            type: 'pictorialBar',
            symbol: 'react',
            symbolSize: [40, 3],
            symbolOffset: [0, -2],
            z: 12,
            itemStyle: {
              color: '#6BABFF',
              shadowBlur: 20,
            },
            data: getSymbolData(seriesData),
          },
        ]
      };
      myChart.setOption(option);
      window.addEventListener('resize', () => myChart.resize());

    },
    typeStatistics() {
      let myChart = echarts.init(
          document.getElementById('typeStatisticEchart')
      );
      this.typeData = [
        {
          value: 600,
          name: '非农化',
          itemStyle: {
            color: "#006cff",
          },
        },
        {
          value: 360,
          name: '非粮化',
          itemStyle: {
            color: "#e5b95b",
          },
        },
        {
          value: 374,
          name: '河道排污',
          itemStyle: {
            color: "#4ac789",
          },
        },
        {
          value: 500,
          name: '占道经营',
          itemStyle: {
            color: "#ff5f6f",
          },
        },
        {
          value: 400,
          name: '林地砍伐',
          itemStyle: {
            color: "#ee8529",
          },
        },
        {
          value: 200,
          name: '乱堆垃圾',
          itemStyle: {
            color: "#43bfec",
          },
        }
      ];
      this.typeDataTotal = this.taskData.reduce((sum, item) => sum + item.value, 0);
      const option = {
        tooltip: {
          trigger: 'item',
        },
        series: [{
          type: 'pie',
          radius: ['58%', '72%'],
          center: ['50%', '50%'],
          color: this.typeData.map(item => item.itemStyle.color),
          padAngle: 5,
          label: {
            show: false,
            position: 'center'
          },
          itemStyle: {
            borderRadius: 20,
            borderWidth: 2
          },
          data: this.typeData,
        },
          {
            type: 'gauge',
            splitNumber: 70,
            radius: '90%',
            center: ['50%', '50%'],
            startAngle: 90,
            endAngle: -269.9999,
            axisLine: {
              show: false,
              lineStyle: {
                width: 0,
                shadowBlur: 0,
                color: [
                  [1, '#0FD9DF']
                ]
              }
            },
            axisTick: {
              show: false,
              lineStyle: {
                color: 'auto',
                width: 1
              },
              length: 100,
              splitNumber: 1
            },
            splitLine: {
              show: true,
              length: 1,
              lineStyle: {
                color: 'auto',
              }
            },
            axisLabel: {
              show: false
            }
          },
          {
            type: 'gauge',
            splitNumber: 60, // 刻度数量
            radius: '50%', // 图表尺寸
            center: ['50%', '50%'],
            startAngle: 90,
            endAngle: -269.9999,
            axisLine: {
              show: false,
              lineStyle: {
                width: 0,
                shadowBlur: 0,
                color: [
                  [1, '#0FD9DF']
                ]
              }
            },
            axisTick: {
              show: false,
              lineStyle: {
                color: 'auto',
                width: 1
              },
              length: 100,
              splitNumber: 1
            },
            splitLine: {
              show: true,
              length: 1,
              lineStyle: {
                color: 'auto',
              }
            },
            axisLabel: {
              show: false
            }
          },
          {
            type: 'gauge',
            splitNumber: 4, // 刻度数量
            radius: '100%', // 图表尺寸
            center: ['50%', '50%'],
            startAngle: 90,
            endAngle: -269.9999,
            axisLine: {
              show: false,
              lineStyle: {
                width: 0,
                shadowBlur: 0,
                color: [
                  [1, '#0FD9DF']
                ]
              }
            },
            axisTick: {
              show: false,
              lineStyle: {
                color: 'auto',
                width: 1
              },
              length: 100,
              splitNumber: 1
            },
            splitLine: {
              show: true,
              length: 5,
              lineStyle: {
                color: 'auto',
              }
            },
            axisLabel: {
              show: false
            }
          }
        ]
      };
      myChart.setOption(option);
      window.addEventListener('resize', () => myChart.resize());
    },
    initNestList() {
      this.nestList = [
        {
          "id": 1,
          "name": "浦口区永宁街道机舱",
          "status": "sleep"
        },
        {
          "id": 2,
          "name": "浦口区永宁街道机舱2",
          "status": "offline"
        },
        {
          "id": 3,
          "name": "浦口区永宁街道机舱2",
          "status": "online"
        },
        {
          "id": 4,
          "name": "浦口区永宁街道机舱2",
          "status": "online"
        },
        {
          "id": 5,
          "name": "浦口区永宁街道机舱2",
          "status": "online"
        }
      ]
    },
    initPotrolScheme() {
      this.patrolSchemeList = [
        {
          "id": 1,
          "title": "万亩良田巡检飞行计划",
          "nestName": "浦口区永宁街道机舱",
          "taskType": "耕地保护",
          "time": "2025-03-25 15:23",
          "data": "全景"
        },
        {
          "id": 1,
          "title": "万亩良田巡检飞行计划",
          "nestName": "浦口区永宁街道机舱",
          "taskType": "耕地保护",
          "time": "2025-03-25 15:23",
          "data": "全景"
        },
        {
          "id": 1,
          "title": "万亩良田巡检飞行计划",
          "nestName": "浦口区永宁街道机舱",
          "taskType": "耕地保护",
          "time": "2025-03-25 15:23",
          "data": "全景"
        },
        {
          "id": 1,
          "title": "万亩良田巡检飞行计划",
          "nestName": "浦口区永宁街道机舱",
          "taskType": "耕地保护",
          "time": "2025-03-25 15:23",
          "data": "全景"
        },
        {
          "id": 1,
          "title": "万亩良田巡检飞行计划",
          "nestName": "浦口区永宁街道机舱",
          "taskType": "耕地保护",
          "time": "2025-03-25 15:23",
          "data": "全景"
        },
        {
          "id": 1,
          "title": "万亩良田巡检飞行计划",
          "nestName": "浦口区永宁街道机舱",
          "taskType": "耕地保护",
          "time": "2025-03-25 15:23",
          "data": "全景"
        }
      ]
    },
    selectMonth() {
      this.selected = 'month';
      this.trendStatistics();
    },
    selectQuarter() {
      this.selected = 'quarter';
      this.trendStatistics();
    },
    selectYear() {
      this.selected = 'year';
      this.trendStatistics();
    }
  },
  async mounted() {
    const res = await getMapInfoApi();
    if (res.code === 0) {
      this.mapService = res.data.map_service;
      this.center = res.data.center;
    }
    this.initMap();
    this.initCharts();
    this.initNestList();
  },
  created() {
  },
  computed: {
    defineScroll() {
      return {
        step: 0.3, // 数值越大速度滚动越快
        limitMoveNum: 2, // 开始无缝滚动的数据量 this.dataList.length
        hoverStop: true, // 是否开启鼠标悬停stop
        direction: 1, // 0向下 1向上 2向左 3向右
        openWatch: true, // 开启数据实时监控刷新dom
        // 单步运动停止的高度(默认值0是无缝不停止的滚动) direction => 0/1
        singleHeight: 0,
        // 单步运动停止的宽度(默认值0是无缝不停止的滚动) direction => 2/3
        singleWidth: 0,
        waitTime: 1000, // 单步运动停止的时间(默认值1000ms)
      };
    }
  },
  components: {
    vueSeamlessScroll
  }
};
</script>

<style scoped>
.content {
  display: flex;
  width: 100%;
  box-sizing: border-box;
}

.content .mapcontainer {
  position: absolute;
  height: calc(100% - 92px);
  width: 100%;
}

.right {
  width: 463px;
  padding: 18px 18px 18px 0;
  z-index: 1000;
  background: radial-gradient(100% 100% at 80% 50%, rgba(18, 24, 36, 0.5) 65%, rgba(22, 78, 133, 0) 100%)
}

.center {
  width: calc(100% - 926px);
}

.left {
  width: 463px;
  padding: 18px 0 18px 18px;
  z-index: 10000;
  background: radial-gradient(100% 100% at 20% 50%, rgba(18, 24, 36, 0.5) 65%, rgba(22, 78, 133, 0) 100%)
}

.item-258 {
  height: 258px;
  padding-bottom: 18px;
}

.item-675 {
  height: 675px;
}

.item-title {
  width: 100%;
  height: 46px;
  display: flex;
  align-items: center;
  background: url("@/assets/images/portal/tittle-bg.png") no-repeat;
  background-size: 100% 100%;
  justify-content: space-between;

}

.item-title span {
  font-family: YouSheBiaoTiHei, serif;
  font-size: 24px;
  line-height: 24px;
  text-align: left;
  padding-left: 32px;
  background: linear-gradient(180deg, #FFFFFF 0%, #A2B8F2 100%);
  -webkit-background-clip: text;
  color: transparent;
}

.item-content {
  background: url("@/assets/images/portal/box.png") no-repeat;
  background-size: 100% 100%;
  width: 100%;
  height: calc(100% - 46px);
  display: flex;
}

.cnt-box {
  height: 100%;
  width: 255px;
  display: flex;
  align-items: center;
  justify-content: center;
}

#inspectionTaskEchart {
  height: 100%;
  width: 100%;
}

.total {
  position: absolute;
  text-align: center;
  display: flex;
  flex-direction: column;
}

.total span {
  font-size: 12px;
  color: #FFFFFF;
  line-height: 14px;
}

.number {
  font-weight: 800;
  font-size: 24px !important;
  line-height: 28px !important;
}

.legend {
  width: calc(100% - 255px);
  display: flex;
  flex-direction: column;
  justify-content: center;
  font-size: 14px;
  color: #FFFFFF;
  line-height: 16px;
  gap: 8px;
}

.legend-number {
  font-size: 14px;
  color: #00FFFF;
  line-height: 16px;
  margin-left: 60px;
}

.dot {
  width: 8px;
  height: 8px;
  border: 1px solid white;
  border-radius: 50%;
  margin-right: 8px;
}

.nest-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 8px;
}

.legend-content {
  display: flex;
  align-items: center;
  padding: 6px 0;
  border-bottom: 1px solid;
  border-image: linear-gradient(90deg, rgba(63, 117, 144, 0.8), rgba(102, 102, 102, 0)) 1 1;
}

.sub-title {
  height: 40px;
  width: 100%;
  margin-top: 12px;
  background: linear-gradient(41deg, rgba(59, 141, 241, 0.15) 0%, rgba(0, 99, 191, 0) 100%);
  border-radius: 4px;
  border-bottom: 1px solid;
  border-image: linear-gradient(45deg, rgba(58, 214, 255, 1), rgba(0, 62, 255, 0)) 1 1;
  font-size: 14px;
  color: #00FFFF;
  line-height: 16px;
//padding: 10px; margin-left: 8px; display: flex; justify-content: space-between;
}

.sub-title span {
  padding-left: 5px;
}

.sub-title-button {
  display: flex;
  margin: 6px 16px;
}

.title-button {
  width: 61px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #D5D5D5;
  border: 1px solid;
  border-image: linear-gradient(180deg, rgba(255, 255, 255, 0), rgba(255, 255, 255, 0.57), rgba(116, 136, 144, 1)) 1 1;
  border-radius: 4px;
}

.title-button-active {
  background: linear-gradient(180deg, rgba(23, 125, 228, 0.2) 0%, #1E3566 100%);
  border: 1px solid;
  border-image: linear-gradient(180deg, rgba(255, 255, 255, 0), rgba(255, 255, 255, 0.57), rgba(0, 184, 251, 1)) 1 1;
}

.title-button-active span {
  background: linear-gradient(90deg, #FFFFFF 0%, #32ACFF 100%);
  font-size: 16px;
  line-height: 19px;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

#trendStatisticsEchart {
  height: 222px;
  width: calc(100% - 16px);
  margin: 11px 8px;
}

.vertical {
  flex-direction: column;
}

.typeStatistic {
  width: 100%;
  height: 300px;
  display: flex;
}

.typeStatisticEchart {
  width: 246px;
  height: 100%;
}

.typeStatisticEchart span {
  font-size: 12px;
  color: #DEF1FF;
  line-height: 30px;
  margin: 10px 14px;
}

#typeStatisticEchart {
  width: 246px;
  height: 246px;
}

.type-legend-content {
  display: flex;
  align-items: center;
  padding: 6px 0;
  border-bottom: 1px solid;
  border-image: linear-gradient(90deg, rgba(63, 117, 144, 0.8), rgba(102, 102, 102, 0)) 1 1;
  justify-content: space-around;
}

.type-legend-number {
  font-size: 14px;
  color: #00FFFF;
  line-height: 16px;
}

.item-433 {
  height: 433px;
  padding-bottom: 18px;
}

.item-513 {
  height: 513px;
}

.m-10 {
  margin: 10px;
}

.icon-rili {
  background: linear-gradient(180deg, #FFFFFF 0%, #A2B8F2 100%);
  -webkit-background-clip: text;
  color: transparent;
  padding-right: 10px;
}

.nest-box {
  height: 100%;
  width: 100%;
}

.nest-title {
  display: flex;
  font-size: 14px;
  color: #FFFFFF;
  line-height: 16px;
  width: 100%;
  height: 48px;
  padding: 0 12px;
  justify-content: space-between;
  align-items: center;
}

.nest-title-content {
  display: flex;
  align-items: center;
}

.action-item {
  color: #3E74B3;
  padding: 5px 8px;
}

::v-deep .el-input__inner {
  background-color: transparent;
}

::v-deep .el-icon-search {
  color: #00FFFF;
}

.w-220 {
  width: 220px;
}

.nest-name {
  font-size: 16px;
  color: #FFFFFF;
  line-height: 19px;
  padding-left: 17px;
}

.nest-list {
  margin: 0 12px;
  border-radius: 4px;
  height: calc(100% - 58px);

  overflow-y: auto;
  scrollbar-width: none;
  -ms-overflow-style: none;

  &::-webkit-scrollbar {
    display: none;
    width: 0;
  }

  /* 移动端优化 */
  -webkit-overflow-scrolling: touch;
}

.nest-list-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-top: 1px solid #0A579E;
  border-left: 1px solid #0A579E;
  border-right: 1px solid #0A579E;
  background: rgba(8, 23, 52, 0.6);
}

.nest-list-item:last-child {
  border-bottom: 1px solid #0A579E;
}

.nest-item-right {
  display: flex;
  padding-right: 16px;
}

.nest-item-left {
  display: flex;
  align-items: center;
}

.pd-10 {
  padding: 10px;
}

.patrol-scheme-item-content {
  background: url("@/assets/images/portal/box.png") no-repeat;
  background-size: 100% 100%;
  width: 100%;
  height: calc(100% - 46px);

  overflow-y: auto;
  scrollbar-width: none;
  -ms-overflow-style: none;

  &::-webkit-scrollbar {
    display: none;
    width: 0;
  }

  /* 移动端优化 */
  -webkit-overflow-scrolling: touch;
}

.patrol-scheme-item {
  width: 100%;
  display: flex;
  height: 130px;
  align-items: center;
  background: rgba(8, 23, 52, 0.6);
  border-radius: 4px;
  border: 1px solid #0A579E;
  margin-bottom: 8px;
}

.patrol-scheme-title {
  font-size: 16px;
  color: #FFFFFF;
  padding: 4px 0;
}

.patrol-scheme-content {
  display: grid;
  grid-template-columns: 65% 30%;
  justify-items: stretch;
  grid-gap: 4px;
}

.patrol-scheme-table {
  width: 100%;
  margin-left: 8px;
}

.patrol-scheme-name {
  font-size: 12px;
  color: #B3CCEF;
}

.patrol-scheme-value {
  font-size: 14px;
  color: #00FFFF;
}

.plane-icon {
  padding: 8px;
}
</style>