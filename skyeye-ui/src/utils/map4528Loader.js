import axios from 'axios';
import proj4 from 'proj4';
import L from 'leaflet';
import { TiledMapLayer } from '@supermap/iclient-leaflet';
import '@supermap/iclient-leaflet';
import { calcResolution } from '@/utils/utils';

const DEFAULT_PROJ =
  '+proj=tmerc +lat_0=0 +lon_0=120 +k=1 +x_0=40500000 +y_0=0 +ellps=GRS80 +units=m +no_defs +type=crs';

function parseBounds(bounds) {
  if (!bounds) return null;
  if (bounds.left != null) {
    return {
      minX: Number(bounds.left),
      minY: Number(bounds.bottom),
      maxX: Number(bounds.right),
      maxY: Number(bounds.top)
    };
  }
  if (bounds.leftBottom && bounds.rightTop) {
    return {
      minX: Number(bounds.leftBottom.x),
      minY: Number(bounds.leftBottom.y),
      maxX: Number(bounds.rightTop.x),
      maxY: Number(bounds.rightTop.y)
    };
  }
  if (bounds.xmin != null) {
    return {
      minX: Number(bounds.xmin),
      minY: Number(bounds.ymin),
      maxX: Number(bounds.xmax),
      maxY: Number(bounds.ymax)
    };
  }
  return null;
}

function normalizeScales(scales) {
  if (!Array.isArray(scales)) return [];
  return scales
    .map((item) => {
      if (typeof item === 'number' && item > 0) return item;
      if (item && typeof item === 'object') {
        const v = item.scale || item.scaleDenominator || item.denominator || item.value;
        return typeof v === 'number' && v > 0 ? v : null;
      }
      return null;
    })
    .filter(Boolean);
}

function buildResolutionsFromExtent(extent) {
  const width = Math.abs(extent.maxX - extent.minX);
  const height = Math.abs(extent.maxY - extent.minY);
  const base = Math.max(width, height) / 256;
  const list = [];
  for (let i = 0; i < 20; i += 1) {
    list.push(base / Math.pow(2, i));
  }
  return list;
}

function lodResolution(lod, dpi) {
  if (lod.resolution > 0) return lod.resolution;
  if (lod.scale > 0) return (lod.scale * 0.0254) / dpi;
  return null;
}

/** iServer：origin 取范围左下角 */
function createIServerCrs(epsgCode, projDef, extent, resolutions) {
  const { minX, minY, maxX, maxY } = extent;
  proj4.defs(epsgCode, projDef);
  return new L.Proj.CRS(epsgCode, {
    def: projDef,
    bounds: L.bounds([minX, maxY], [maxX, minY]),
    origin: [minX, minY],
    resolutions
  });
}

/**
 * ArcGIS 缓存：CRS 只配 tileInfo.origin + lods.resolution（与 Esri 非 Mercator 示例一致）
 * 不要传 fullExtent 作 bounds，否则切片行列号会算偏
 */
function createArcGisCrs(epsgCode, projDef, tileInfo, lods) {
  const dpi = tileInfo.dpi || 96;
  const resolutions = lods.map((lod) => lodResolution(lod, dpi)).filter((n) => n > 0);
  if (!resolutions.length) {
    throw new Error('ArcGIS tileInfo.lods 无有效 resolution');
  }
  const origin = tileInfo.origin;
  if (!origin || origin.x == null || origin.y == null) {
    throw new Error('ArcGIS tileInfo 缺少 origin');
  }
  proj4.defs(epsgCode, projDef);
  return {
    crs: new L.Proj.CRS(epsgCode, {
      def: projDef,
      origin: [origin.x, origin.y],
      resolutions
    }),
    resolutions,
    origin
  };
}

function extentToFitBounds(crs, extent) {
  try {
    const sw = crs.unproject(L.point(extent.minX, extent.minY));
    const ne = crs.unproject(L.point(extent.maxX, extent.maxY));
    if (
      !Number.isFinite(sw.lat) ||
      !Number.isFinite(sw.lng) ||
      !Number.isFinite(ne.lat) ||
      !Number.isFinite(ne.lng)
    ) {
      return null;
    }
    const bounds = L.latLngBounds([sw.lat, sw.lng], [ne.lat, ne.lng]);
    return bounds.isValid() ? bounds : null;
  } catch (e) {
    return null;
  }
}

export function isFiniteLatLngPair(lat, lng) {
  return Number.isFinite(Number(lat)) && Number.isFinite(Number(lng));
}

/** WGS84 [lat,lng] → Leaflet CRS 坐标（4528 为投影米，4326 为度） */
export function wgs84ToCrsLatLng(lat, lng, epsgCode = 'EPSG:4528', projDef = DEFAULT_PROJ) {
  const la = Number(lat);
  const lo = Number(lng);
  if (!Number.isFinite(la) || !Number.isFinite(lo)) return null;
  if (Math.abs(la) > 90 || Math.abs(lo) > 180) {
    return [la, lo];
  }
  proj4.defs('EPSG:4326', '+proj=longlat +datum=WGS84 +no_defs +type=crs');
  proj4.defs(epsgCode, projDef);
  const [x, y] = proj4('EPSG:4326', epsgCode, [lo, la]);
  if (!Number.isFinite(x) || !Number.isFinite(y)) return null;
  return [y, x];
}

async function fetchJson(url) {
  const res = await axios.get(url, { withCredentials: false });
  return res.data || {};
}

/** 原生 Leaflet 瓦片层：按 ArcGIS 切片方案拼 /tile/{level}/{row}/{col} */
function createArcGisTileLayer(baseUrl, tileInfo, lods) {
  const tileSize = tileInfo.cols || tileInfo.rows || 256;
  const maxZoom = lods.length - 1;

  return L.tileLayer(`${baseUrl}/tile/{z}/{y}/{x}`, {
    tileSize,
    minZoom: 0,
    maxZoom,
    maxNativeZoom: maxZoom,
    noWrap: true,
    keepBuffer: 3,
    getTileUrl(coords) {
      const lod = lods[coords.z];
      if (!lod) return '';
      const level = lod.level != null ? lod.level : coords.z;
      return `${baseUrl}/tile/${level}/${coords.y}/${coords.x}`;
    }
  });
}

/** iServer REST 地图 (type=1) */
async function loadIServer4528(serviceUrl, options) {
  const layerUrl = serviceUrl.replace(/\.json\/?$/, '').replace(/\/$/, '');
  const jsonUrl = layerUrl.endsWith('.json') ? layerUrl : `${layerUrl}.json`;
  const data = await fetchJson(jsonUrl);
  const extent = parseBounds(data.bounds);
  if (!extent) throw new Error('iServer map.json 缺少 bounds');

  const scales = normalizeScales(data.visibleScales);
  let resolutions = scales.length ? calcResolution(scales) : [];
  if (!resolutions.length && Array.isArray(data.visibleResolution)) {
    resolutions = data.visibleResolution.map(Number).filter((n) => n > 0);
  }
  if (!resolutions.length) resolutions = buildResolutionsFromExtent(extent);

  const epsgCode = options.epsgCode || 'EPSG:4528';
  const projDef = options.projDef || DEFAULT_PROJ;
  const crs = createIServerCrs(epsgCode, projDef, extent, resolutions);
  const maxZoom = resolutions.length - 1;
  const layer = new TiledMapLayer(layerUrl, {
    maxZoom,
    maxNativeZoom: maxZoom,
    noWrap: true,
    keepBuffer: 3,
    tileSize: 256
  });

  return {
    crs,
    layer,
    maxZoom,
    minZoom: 0,
    fitBounds: extentToFitBounds(crs, extent),
    initialZoom: Math.min(maxZoom, options.initialZoom != null ? options.initialZoom : maxZoom - 2)
  };
}

/** ArcGIS MapServer 缓存 (type=2) */
async function loadArcGis4528(serviceUrl, options) {
  const baseUrl = serviceUrl.replace(/\/$/, '');
  const data = await fetchJson(`${baseUrl}?f=json`);
  const tileInfo = data.tileInfo;
  const extent = parseBounds(data.fullExtent || data.extent);
  if (!tileInfo || !tileInfo.lods || !tileInfo.lods.length) {
    throw new Error('ArcGIS 服务无 tileInfo.lods，请确认已缓存且为 MapServer');
  }
  if (!extent) throw new Error('ArcGIS 服务缺少 fullExtent');

  const wkid = (data.spatialReference && data.spatialReference.wkid) || 4528;
  const epsgCode = options.epsgCode || `EPSG:${wkid}`;
  const projDef = options.projDef || DEFAULT_PROJ;
  const { crs, origin } = createArcGisCrs(epsgCode, projDef, tileInfo, tileInfo.lods);
  const maxZoom = tileInfo.lods.length - 1;
  const layer = createArcGisTileLayer(baseUrl, tileInfo, tileInfo.lods);

  console.log('[4528 ArcGIS]', {
    origin,
    lodCount: tileInfo.lods.length,
    levels: tileInfo.lods.map((l) => l.level),
    maxZoom
  });

  return {
    crs,
    layer,
    maxZoom,
    minZoom: 0,
    fitBounds: extentToFitBounds(crs, extent),
    initialZoom: Math.min(maxZoom, options.initialZoom != null ? options.initialZoom : maxZoom - 2)
  };
}

/**
 * 加载 EPSG:4528 底图
 * @param {string} serviceUrl 服务地址
 * @param {'1'|'2'} serviceType 1=iServer 2=ArcGIS
 */
export async function load4528BaseMap(serviceUrl, serviceType, options = {}) {
  if (!serviceUrl) throw new Error('底图服务地址为空');
  if (String(serviceType) === '1') {
    return loadIServer4528(serviceUrl, options);
  }
  if (String(serviceType) === '2') {
    return loadArcGis4528(serviceUrl, options);
  }
  throw new Error(`4528 底图仅支持 iServer(1) 与 ArcGIS(2)，当前 type=${serviceType}`);
}

function bindTileDebugEvents(layer, callbacks) {
  if (!layer || !callbacks) return;
  const { onTileLoadStart, onTileLoad, onTileError } = callbacks;
  if (typeof onTileLoadStart === 'function') {
    layer.on('loading', () => onTileLoadStart());
  }
  if (typeof onTileLoad === 'function') {
    layer.on('load', () => onTileLoad());
  }
  if (typeof onTileError === 'function') {
    layer.on('tileerror', (e) => {
      const tile = e.tile || {};
      onTileError({
        url: tile.src || tile.currentSrc || '',
        zoom: e.coords != null ? e.coords.z : null
      });
    });
  }
}

/**
 * 创建 EPSG:4528 Leaflet 地图（与 panoramicDetection/mapView init4528Map 一致）
 * @param {string|HTMLElement} container 容器 id 或 DOM 元素
 * @param {object} options
 * @param {string} options.serviceUrl 底图服务地址
 * @param {'1'|'2'} options.serviceType 1=iServer 2=ArcGIS
 * @param {number} [options.initialZoom] 无 fitBounds 时的默认 zoom
 * @param {number[]} [options.center] setView 中心 [lat, lng]（投影坐标）
 * @param {L.LatLngBounds|Array} [options.mapBounds] 优先 fitBounds
 * @param {'serviceExtent'|'none'} [options.initialView='serviceExtent'] 初始视野策略
 * @param {object} [options.tileCallbacks] { onTileLoadStart, onTileLoad, onTileError }
 * @param {object} [options.mapOptions] 传给 L.map 的额外选项
 */
export async function create4528LeafletMap(container, options = {}) {
  const {
    serviceUrl,
    serviceType,
    epsgCode = 'EPSG:4528',
    projDef = DEFAULT_PROJ,
    initialZoom,
    center,
    mapBounds,
    initialView = 'serviceExtent',
    tileCallbacks,
    mapOptions = {}
  } = options;

  const loaded = await load4528BaseMap(serviceUrl, serviceType, {
    epsgCode,
    projDef,
    initialZoom
  });

  const { crs, layer, maxZoom, minZoom, fitBounds, initialZoom: resolvedInitialZoom } = loaded;

  const resolvedCenter =
    center && center.length === 2 && isFiniteLatLngPair(center[0], center[1])
      ? [Number(center[0]), Number(center[1])]
      : null;

  const map = L.map(container, {
    crs,
    zoomControl: false,
    attributionControl: false,
    preferCanvas: true,
    ...mapOptions,
    // 自定义 CRS 必须以底图切片级别为准，不能被 config.maxZoom 覆盖
    maxZoom,
    minZoom
  });

  layer.addTo(map);
  layer.bringToBack();
  bindTileDebugEvents(layer, tileCallbacks);

  let viewSet = false;
  if (mapBounds && mapBounds.length > 0) {
    map.fitBounds(mapBounds);
    viewSet = true;
  } else if (initialView !== 'none') {
    if (fitBounds && fitBounds.isValid()) {
      map.fitBounds(fitBounds);
      viewSet = true;
    } else if (resolvedCenter) {
      map.setView(resolvedCenter, resolvedInitialZoom);
      viewSet = true;
    }
  } else if (resolvedCenter) {
    map.setView(resolvedCenter, resolvedInitialZoom != null ? resolvedInitialZoom : minZoom);
    viewSet = true;
  }

  if (!viewSet) {
    if (initialView === 'none' && resolvedCenter) {
      map.setView(resolvedCenter, resolvedInitialZoom != null ? resolvedInitialZoom : minZoom);
    } else if (fitBounds && fitBounds.isValid()) {
      map.fitBounds(fitBounds);
    } else if (resolvedCenter) {
      map.setView(resolvedCenter, resolvedInitialZoom != null ? resolvedInitialZoom : minZoom);
    }
  }

  return {
    map,
    baseMapLayer: layer,
    crs,
    maxZoom,
    minZoom,
    fitBounds,
    initialZoom: resolvedInitialZoom
  };
}

export function createGeoCrs(projectCity) {
  const resolutions = [];
  for (let i = 0; i < 22; i += 1) {
    resolutions.push(1.40625 / Math.pow(2, i));
  }
  if (projectCity === 'nanjing') {
    return L.CRS.EPSG3857;
  }
  return L.Proj.CRS('EPSG:4326', {
    bounds: L.bounds([-180, -90], [180, 90]),
    origin: [-180, 90],
    resolutions
  });
}

export function createGeoBaseLayer(serviceUrl, serviceType, options = {}) {
  if (!serviceUrl) return null;
  const common = {
    maxZoom: options.maxZoom,
    maxNativeZoom: options.maxNativeZoom,
    noWrap: true
  };
  if (String(serviceType) === '1') {
    return new TiledMapLayer(serviceUrl, { ...common, keepBuffer: 3 });
  }
  if (String(serviceType) === '2') {
    return L.tileLayer(`${serviceUrl.replace(/\/$/, '')}/tile/{z}/{y}/{x}`, {
      ...common,
      minZoom: options.minZoom,
      keepBuffer: 3
    });
  }
  return L.tileLayer(serviceUrl, common);
}
