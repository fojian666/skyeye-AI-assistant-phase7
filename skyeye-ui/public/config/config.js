const config = {
    baseUrl: 'http://127.0.0.1:8009/',
    panoramaUrl: 'http://127.0.0.1:8009',
    client_id: 'skyeye-app',
    systemName: 'skyeye',
    system_name: '自然资源耕保无人机智能监测系统',
    geoserverBaseUrl: 'http://skyeye.isitai.cn:8086/geoserver',
    gridSampleUrl: 'http://skyeye.isitai.cn:8009/api/panorama/file/download/6282943565907769',
    pointSampleUrl: 'http://skyeye.isitai.cn:8009/api/panorama/file/download/6257645752277550',
    iserverAdress: 'http://skyeye.isitai.cn:8090/iserver/services/imageservice-njimagetest/restjsr/',
    baseMapService:'http://skyeye.isitai.cn:8081/MapServer/mbtiles/tdt_image_global0-10_china11-16/{x}/{y}/{z}',
    //baseMapService:'',
    baseMapServiceType:'3',//1：iserver，2：arcServer 3：天地图
    // iServer EPSG:4528 底图验证（panoramicDetection/mapView/map.vue）
    baseMapUse4528: false,
    baseMap4528Epsg: 'EPSG:4528',
    baseMap4528Proj: '+proj=tmerc +lat_0=0 +lon_0=120 +k=1 +x_0=40500000 +y_0=0 +ellps=GRS80 +units=m +no_defs +type=crs',
    baseMaxNativeZoom:16,//实际放大的层级
    projectCity:'nanjing',
    maxZoom:20,
    minZoom:9,
    zoom:10,
    center:[31.18,119.71],
    circleRadius: 800,
    innerCircleRadius: 300,
    copyright: '版权所有：©空间感知与优化计算研究所',
    //全景图叠加图层颜色配置
    colorList: ['#ddea1f', '#20f309', '#ef0a3f', '#09c9ea'],
    // 统计大屏免登录账号（/data_overview 自动登录，生产环境请修改或关闭）
    overviewAutoLogin: {
        enabled: true,
        username: 'WXSAdmin',
        password: 'WXSAdmin)OKM'
    },
    // 实时视频：webrtc:// / rtmp:// 转浏览器可播放地址
    liveStreamPlay: {
        useHttps: false,
        // 飞控 webrtc:// 转 HTTP 播放接口（xwsoft/SRS 常用 whip-play）
        webrtcPlayPath: '/rtc/v1/whip-play/',
        // 浏览器同源代理前缀（生产 nginx 配置 /live-stream-proxy）
        proxyPrefix: '/live-stream-proxy',
        // 政务网 WHEP 网关路径（内外网同联机 Nginx 转发到 2.20.41.1:8089/drone-whep）
        proxyWhepPath: '/drone-whep',
        // 后端 httpUrl 中的外网流媒体 host，命中后走上面代理
        proxyHosts: ['live.jsonesky.cn:61985'],
        proxyTarget: 'http://2.20.41.1:8089',
        rtmpFlvPort: 8080
    },
    // 无人机实时轨迹 WebSocket（空则使用当前站点 /ws/drone/track/）
    droneTrackWsUrl: '',
    // 实时监控页机巢列表（id 为机库 deviceSn）
    liveStreamUavList: [
        {
            name: '梁东空天数科生态项目（XDG-2025-13号地块）',
            tenantId: 362711,
            projectId: '2054085558198116352',
            id: '8UUXNBH00A0TQC',
            uav_id: '1581F8HGX253U00A0645'
        }
    ],
};

window.config = config;
