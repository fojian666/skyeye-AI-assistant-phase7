// ECharts 深色赛博风主题配置
export const CYAN_PALETTE = [
  '#00f2ff', '#00c8e0', '#0099b8', '#00e5a0',
  '#4dd0ff', '#26c6da', '#00bcd4', '#18ffff'
];

// 行政区域彩色分类（玫瑰图 / 饼图按区着色）
export const REGION_COLORS = {
  '滨湖区': '#00f2ff',
  '梁溪区': '#00b4ff',
  '锡山区': '#4dd0ff',
  '惠山区': '#00ff88',
  '新吴区': '#ffb74d',
  '江阴市': '#b388ff',
  '宜兴市': '#ff6b9d'
};

export function colorizeRegionData(data) {
  return data.map(item => ({
    ...item,
    itemStyle: {
      color: REGION_COLORS[item.name] || '#00f2ff',
      borderRadius: 4,
      borderColor: '#050c17',
      borderWidth: 2,
      shadowBlur: item.value > 0 ? 8 : 0,
      shadowColor: `${REGION_COLORS[item.name] || '#00f2ff'}66`
    },
    label: {
      color: REGION_COLORS[item.name] || '#fff'
    },
    labelLine: {
      lineStyle: {
        color: REGION_COLORS[item.name] || '#00f2ff',
        width: 1
      }
    },
    emphasis: {
      itemStyle: {
        shadowBlur: 14,
        shadowColor: `${REGION_COLORS[item.name] || '#00f2ff'}99`
      },
      label: { fontSize: 12, fontWeight: 'bold' }
    }
  }));
}

export const darkChartBase = {
  textStyle: { color: 'rgba(160, 210, 230, 0.85)' },
  tooltip: {
    backgroundColor: 'rgba(6, 18, 36, 0.95)',
    borderColor: 'rgba(0, 242, 255, 0.6)',
    borderWidth: 1,
    textStyle: { color: '#fff', fontSize: 12 },
    extraCssText: 'box-shadow: 0 0 12px rgba(0,242,255,0.25); border-radius: 4px;'
  }
};

export const darkAxis = {
  axisLine: { lineStyle: { color: 'rgba(0, 242, 255, 0.25)' } },
  axisTick: { lineStyle: { color: 'rgba(0, 242, 255, 0.2)' } },
  axisLabel: { color: 'rgba(160, 210, 230, 0.75)', fontSize: 11 },
  splitLine: { lineStyle: { color: 'rgba(0, 242, 255, 0.08)', type: 'dashed' } }
};

export function mergeDarkOption(option) {
  return {
    ...darkChartBase,
    ...option,
    tooltip: { ...darkChartBase.tooltip, ...(option.tooltip || {}) },
    xAxis: Array.isArray(option.xAxis)
      ? option.xAxis.map(a => ({ ...darkAxis, ...a, axisLine: { ...darkAxis.axisLine, ...(a.axisLine || {}) } }))
      : option.xAxis ? { ...darkAxis, ...option.xAxis } : undefined,
    yAxis: Array.isArray(option.yAxis)
      ? option.yAxis.map(a => ({ ...darkAxis, ...a }))
      : option.yAxis ? { ...darkAxis, ...option.yAxis } : undefined
  };
}
