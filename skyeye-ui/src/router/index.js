import Vue from 'vue';
import VueRouter from 'vue-router';
import store from "@/store";
import { checkMenuPermission, subPage } from '@/utils/utils';
import { performAutoLogin } from '@/utils/autoLogin';

Vue.use(VueRouter);

export const subRoutes = [
    {
        path: '/portal',
        name: 'portal',
        meta: {
            title: '门户',
            requireAuth: true
        },
        component: () => import('@/views/portal/index.vue'),
    },
    {
        path: '/',
        name: 'PlatformOverview',
        meta: {
            title: '平台概述',
            requireAuth: true,
            autoLogin: true,
            forceAutoLogin: true
        },
        component: () => import('@/views/statisticHome/index.vue')
    },
    {
        path: '/index',
        name: 'PlatformOverview',
        meta: {
            title: '平台概述',
            requireAuth: true
        },
        component: () => import('@/views/dashboard')
    },
    {
        path: '/algorithm-mall',
        name: 'AlgorithmMall',
        component: () => import('@/views/algorithm-mall/AlgorithmMall.vue'),
        children: [
            {
                path: 'algorithm-detail',
                name: 'AlgorithmDetail',
                component: () => import('@/views/algorithm-mall/AlgorithmDetail.vue'),
            }
        ]
    },
    {
        path: '/intelligent-monitoring',
        name: 'IntelligentMonitoring',
        meta: {
            title: '智能监管页面',
            requireAuth: true
        },
        component: () => import('@/views/intelligentMonitoring/Index.vue')
    },
    {
        path: '/data-management',
        name: 'oneMap',
        meta: {
            title: '低空数据管理',
            requireAuth: true
        },
        component: () => import('@/views/dataManagement'),
        children: [
            {
                path: '/data-management/one-map',
                name: 'oneMap',
                meta: {
                    title: '一张图',
                    requireAuth: true
                },
                component: () => import('@/views/dataManagement/oneMap'),
            },
            {
                path: '/data-management/panorama-image',
                name: 'clueView',
                meta: {
                    title: '全景图片展示',
                    requireAuth: true
                },
                component: () => import('@/views/dataManagement/panoramaImage'),
            },
            {
                path: '/data-management/table',
                name: 'dataManagementTable',
                meta: {
                    title: '低空数据管理',
                    requireAuth: true
                },
                component: () => import('@/views/dataManagement/dataUploadManagement')
            },
            {
                path: '/data-management/order-management',
                name: 'orderManagementTable',
                meta: {
                    title: '低空订单管理',
                    requireAuth: true
                },
                component: () => import('@/views/dataManagement/orderManagement')
            },
        ]
    },
    {
        path: '/task-mgmt',
        name: 'taskManagementModule',
        meta: {
            title: '任务管理模块',
            requireAuth: true
        },
        component: () => import('@/views/taskManagementModule/Index.vue'),
        children: [
            {
                path: '/task-mgmt/verify-clue',
                name: 'taskMgmtVerifyClue',
                meta: {
                    title: '任务管理',
                    requireAuth: true
                },
                component: () => import('@/views/taskManagementModule/verifyClue'),
            },
            {
                path: '/task-mgmt/multi-comparison',
                name: 'taskMgmtMultiComparison',
                meta: {
                    title: '对比',
                    requireAuth: true
                },
                component: () => import('@/views/taskManagementModule/verifyClue/multiComparison'),
            },
            {
                path: '/task-mgmt/data-upload',
                name: 'taskMgmtDataUpload',
                meta: {
                    title: '数据上传管理',
                    requireAuth: true
                },
                component: () => import('@/views/taskManagementModule/dataUploadManagement'),
            },
        ]
    },
    {
        path: '/panoramic-detection',
        name: 'panoramicDetection',
        meta: {
            title: '全景检测页面',
            requireAuth: true
        },
        component: () => import('@/views/panoramicDetection/Index.vue'),
        children: [
            {
                path: '/panoramic-detection/clue-view',
                name: 'clueView',
                meta: {
                    title: '线索总览',
                    requireAuth: true
                },
                component: () => import('@/views/panoramicDetection/clueView'),
            },
            {
                path: '/panoramic-detection/grid-management',
                name: 'gridManagement',
                meta: {
                    title: '网格管理',
                    requireAuth: true
                },
                component: () => import('@/views/panoramicDetection/gridManagement'),
            },
            {
                path: '/panoramic-detection/map-view',
                name: 'mapView',
                meta: {
                    title: '线索统计',
                    requireAuth: true
                },
                component: () => import('@/views/panoramicDetection/mapView'),
            },
            {
                path: '/panoramic-detection/task-management',
                name: 'taskManagement',
                meta: {
                    title: '批次管理',
                    requireAuth: true
                },
                component: () => import('@/views/panoramicDetection/taskManagement'),
            },
            {
                path: '/panoramic-detection/panorama-upload',
                name: 'panoramaUploadNj',
                meta: {
                    title: '批次上传管理',
                    requireAuth: true
                },
                component: () => import('@/views/panoramicDetection/taskManagement/uploadPanorama/index.vue')
            },
            {
                path: '/panoramic-detection/main-detection',
                name: 'mainDetection',
                meta: {
                    title: '全景检测',
                    requireAuth: true
                },
                component: () => import('@/views/panoramicDetection/mainDetection'),
            },
            {
                path: '/panoramic-detection/statistical-analysis',
                name: 'statisticalAnalysis',
                meta: {
                    title: '大屏',
                    requireAuth: true
                },
                component: () => import('@/views/panoramicDetection/statisticalAnalysis/Index.vue'),
                // component:()=>import('@/views/panoramicDetection/statisticalAnalysis/index1.vue'),
            },
            {
                path: '/panoramic-detection/verifyClue',
                name: 'verifyClue',
                meta: {
                    title: '线索查询',
                    requireAuth: true
                },
                component: () => import('@/views/panoramicDetection/verifyClue'),
            },
            {
                path: '/panoramic-detection/multiComparision',
                name: 'multiComparision',
                meta: {
                    title: '对比',
                    requireAuth: true
                },
                component: () => import('@/views/panoramicDetection/verifyClue/multiComparison'),
            },
            {
                path: '/panoramic-detection/scene',
                name: 'sceneManagement',
                meta: {
                    title: '场景管理',
                    requireAuth: true
                },
                component: () => import('@/views/panoramicDetection/sceneManagement'),
            },
            {
                path: '/panoramic-detection/report',
                name: 'reportManagement',
                meta: {
                    title: '报告管理',
                    requireAuth: true
                },
                component: () => import('@/views/panoramicDetection/reportManagement'),
            },
            {
                path: '/panoramic-detection/main-detection-temp',
                name: 'tempMainDetection',
                meta: {
                    title: '临时上传',
                    requireAuth: true
                },
                component:()=>import('@/views/panoramicDetection/tempMainDetection'),
            },
            {
                path: '/panoramic-detection/panorama-change-detection',
                name: 'panoramaChangeDetection',
                meta: {
                    title: '变化检测',
                    requireAuth: true
                },
                component:()=>import('@/views/panoramicDetection/panoramaChangeDetection'),
            },
            {
                path: '/panoramic-detection/frame-area',
                name: 'frameArea',
                meta: {
                    title: '不检测区域',
                    requireAuth: true
                },
                component: () => import('@/views/panoramicDetection/frameArea')
            },
        ]
    },

    {
        path: '/home',
        name: 'home',
        meta: {
            title: '首页页面',
            requireAuth: true
        },
        component: () => import('@/views/home')
    },
    {
        path: '/video-detection',
        name: 'videoDetection',
        meta: {
            title: '视频检测页面',
            requireAuth: true
        },
        component: () => import('@/views/videoDetection/index.vue'),
        children: [
            {
                path: '/video-detection/video-management',
                name: 'video',
                meta: {
                    title: '视频检测',
                    requireAuth: true,
                    noKeepAlive: true
                },
                component: () => import('@/views/videoDetection/videoManagement/index.vue')
            },
            {
                path: '/video-detection/clue-view/:taskId',
                name: 'clueView',
                meta: {
                    title: '线索总览',
                    requireAuth: true
                },
                component: () => import('@/views/videoDetection/clueView')
            }
        ]
    },
    {
        path: '/route-planning',
        name: 'routePlanning',
        meta: {
            title: '航线规划页面',
            requireAuth: true
        },
        component: () => import('@/views/routePlanning/index.vue'),
        children: [
            {
                path: '/route-planning/manual-planning',
                name: 'manualPlanning',
                meta: {
                    title: '资源概览',
                    requireAuth: true
                },
                component: () => import('@/views/routePlanning/components/manualPlanning.vue')
            },
            {
                path: '/route-planning/algorithm-planning',
                name: 'algorithmPlanning',
                meta: {
                    title: '资源概览',
                    requireAuth: true
                },
                component: () => import('@/views/routePlanning/components/algorithmPlanning.vue')
            },
            {
                path: '/route-planning/panoramicpoint-planning',
                name: 'panoramicPointPlanning',
                meta: {
                    title: '资源概览',
                    requireAuth: true
                },
                component: () => import('@/views/routePlanning/components/panoramicPointPlanning.vue')
            },
        ]
    },
    {
        path: '/object-detection/details/:taskId',
        name: 'Details',
        component: () => import('@/views/intelligentMonitoring/objectDetection/details')
    },


    {
        path: '/resource-center',
        redirect: '/resource-center/resource-overview/resource-details',
        name: 'ResourceCenter',
        meta: {
            title: '资源中心',
            requireAuth: true
        },
        component: () => import('@/views/resource-center'),
        children: [
            {
                path: '/resource-center/resource-overview/resource-details',
                name: 'ResourceOverview',
                meta: {
                    title: '资源概览',
                    requireAuth: true
                },
                component: () => import('@/views/resource-center/resource-overview')
            },
            {
                path: '/resource-center/resource-management/resource-registration',
                name: 'ResourceRegistration',
                meta: {
                    title: '资源注册',
                    requireAuth: true
                },
                component: () => import('@/views/resource-center/resource-registration')
            },
            {
                path: '/resource-center/resource-management/resource-directory',
                name: 'ResourceDirectory',
                meta: {
                    title: '资源目录',
                    requireAuth: true
                },
                component: () => import('@/views/resource-center/resource-directory')
            },
            {
                path: '/resource-center/resource-directory/resource-details',
                name: 'ResourceDetails',
                meta: {
                    title: '资源详情',
                    requireAuth: true
                },
                component: () => import('@/views/resource-center/resource-directory/resource-details')
            },
            {
                path: '/resource-center/task-management/task-registration',
                name: 'TaskConfig',
                meta: {
                    title: '任务配置',
                    requireAuth: true
                },
                component: () => import('@/views/resource-center/task-registration')
            },
            {
                path: '/resource-center/task-management/task-directory',
                name: 'TaskDirectory',
                meta: {
                    title: '任务目录',
                    requireAuth: true
                },
                component: () => import('@/views/resource-center/task-directory')
            },
            {
                path: '/resource-center/task-directory/task-details',
                name: 'taskDetails',
                meta: {
                    title: '任务详情',
                    requireAuth: true
                },
                component: () => import('@/views/resource-center/task-directory/task-details')
            },
            {
                path: '/resource-center/sample-model/overview',
                name: 'Overview',
                meta: {
                    title: '概况总览',
                    requireAuth: true
                },
                component: () => import('@/views/resource-center/overview')
            },
            {
                path: '/resource-center/system-management/user-info',
                name: 'UserInfo',
                meta: {
                    title: '用户信息',
                    requireAuth: true
                },
                component: () =>
                    import('@/views/resource-center/system-management/user-info')
            },
            {
                path: '/resource-center/system-management/log-view',
                name: 'LogView',
                meta: {
                    title: '日志查看',
                    requireAuth: true
                },
                component: () =>
                    import('@/views/resource-center/system-management/log-view')
            },
            {
                path: '/resource-center/system-management/menu-management',
                name: 'MenuManagement',
                meta: {
                    title: '菜单管理',
                    requireAuth: true
                },
                component: () =>
                    import('@/views/resource-center/system-management/menu-management')
            },
            {
                path: '/resource-center/system-management/data-dict',
                name: 'DataDict',
                meta: {
                    title: '字典管理',
                    requireAuth: true
                },
                component: () =>
                    import('@/views/resource-center/system-management/dataDict/DictType.vue')
            },
            {
                path: '/resource-center/system-management/data-dict-value',
                name: 'DataDictValue',
                meta: {
                    title: '枚举管理',
                    requireAuth: true
                },
                component: () =>
                    import('@/views/resource-center/system-management/dataDict/DictValue.vue')
            },
            {
                path: '/resource-center/system-management/role-management',
                name: 'AuthorityManagement',
                meta: {
                    title: '权限管理',
                    requireAuth: true
                },
                component: () => import('@/views/resource-center/system-management/role-management')
            },
            {
                path: '/resource-center/system-management/county-management',
                name: 'CountyManagement',
                meta: {
                    title: '区划管理',
                    requireAuth: true
                },
                component: () => import('@/views/resource-center/system-management/county-management')
            },
            {
                path: '/resource-center/logs-management/logs-view',
                name: 'routePlanLogs',
                meta: {
                    title: '航线规划日志管理',
                    requireAuth: true
                },
                component: () => import('@/views/resource-center/logs-management/index.vue')
            },
            {
                path: '/resource-center/model-management/index',
                name: 'nestSet',
                meta: {
                    title: '模型管理',
                    requireAuth: true
                },
                component: () => import('@/views/resource-center/model-management/index.vue')
            },
            {
                path: '/resource-center/model-management/scene',
                name: 'scene',
                meta: {
                    title: '场景配置',
                    requireAuth: true
                },
                component: () => import('@/views/resource-center/model-management/scene.vue')
            },

            {
                path: '/resource-center/nest-management/nest-set',
                name: 'nestSet',
                meta: {
                    title: '机巢设置',
                    requireAuth: true
                },
                component: () => import('@/views/resource-center/nest-management/index.vue')
            }
        ]
    },
    {
        path: '/data_overview',
        name: 'Overview',
        meta: {
            title: '统计大屏',
            requireAuth: true,
            autoLogin: true
        },
        component: () => import('@/views/statisticHome/index.vue')
    },
    {
        path: '/data_overview_proto',
        name: 'OverviewPrototype',
        meta: {
            title: '统计大屏原型',
            requireAuth: false
        },
        component: () => import('@/views/statisticHome/prototype.vue')
    },
    {
        path: '/video_streaming',
        name: 'streaming',
        meta: {
            title: '视频直播',
            requireAuth: true
        },
        component: () => import('@/views/videoStreaming/index.vue')
    },
    {
        path: '/live-monitor',
        name: 'LiveMonitor',
        meta: {
            title: '实时视频监控',
            requireAuth: true
        },
        component: () => import('@/views/liveMonitor/index.vue')
    },
    // {
    //     path: '/test-management',
    //     name: 'LiveMonitor',
    //     meta: {
    //         title: '实时视频监控',
    //         requireAuth: true
    //     },
    //     component: () => import('@/views/liveMonitor/test.vue')
    // },
    {
        path: '/clue_verify',
        name: 'clueVerify',
        meta: {
            title: '全景检测页面',
            requireAuth: true
        },
        component: () => import('@/views/clueVerify/index.vue'),
        children: [
            {
                path: '/clue_verify/map_overview',
                name: 'mapOverview',
                meta: {
                    title: '地图总览',
                    requireAuth: true
                },
                component: () => import('@/views/clueVerify/mapOverview')
            },
            {
                path: '/clue_verify/task_management',
                name: 'taskManagement',
                meta: {
                    title: '任务管理表格',
                    requireAuth: true
                },
                component: () => import('@/views/clueVerify/taskManagement')
            },
        ]
    },
    {
        path: '/pattern-verifiy',
        name: 'patternVerifiy',
        meta: {
            title: '图斑核实页面',
            requireAuth: true
        },
        component: () => import('@/views/pattern-verifiy/index.vue'),
        children: [
            {
                path: '/pattern-verifiy/map_overview',
                name: 'patternMapOverview',
                meta: {
                    title: '图斑核实地图',
                    requireAuth: true
                },
                component: () => import('@/views/pattern-verifiy/patternMapOverview')
            },
            {
                path: '/pattern-verifiy/task_management',
                name: 'patternTaskManagement',
                meta: {
                    title: '任务管理表格',
                    requireAuth: true
                },
                component: () => import('@/views/pattern-verifiy/taskManagement')
            },
        ]
    },
    {
        path: '/data',
        name: 'dataStatisticShow',
        meta: {
            title: '数据综合展示',
            requireAuth: true
        },
        component: () => import('@/views/statisticalAnalysis/index.vue'),
    },
    {
        path: '/intelligent',
        name: 'intelligent',
        meta: {
            title: '智能处理分析',
            requireAuth: true
        },
        component: () => import('@/views/intelligent'),
        children: [
            {
                path: '/intelligent/interpretation-task-management',
                name: 'interpretationTaskManagement',
                meta: {
                    title: '智能处理分析',
                    requireAuth: true
                },
                component: () => import('@/views/intelligent/interpretationTaskManagement'),
            },
            {
                path: '/intelligent/processing-analysis',
                name: 'processingAnalysis',
                meta: {
                    title: '智能处理分析',
                    requireAuth: true
                },
                component: () => import('@/views/intelligent/processingAnalysis'),
            },
            {
                path: '/intelligent/land-change',
                name: 'landChange',
                meta: {
                    title: '地类变化',
                    requireAuth: true
                },
                component: () => import('@/views/intelligent/land-change'),
            },

            {
                path: '/intelligent/land-change/land-change-details',
                name: 'landChangeDetails',
                meta: {
                    title: '变化检测详情',
                    requireAuth: true
                },
                component: () => import('@/views/intelligent/land-change/land-change-details'),
            },
            {
                path: '/intelligent/land-change/land-change-details/spot-view',
                name: 'spotView',
                meta: {
                    title: '变化检测详情',
                    requireAuth: true
                },
                component: () => import('@/views/intelligent/land-change/land-change-details/spot-view'),
            },
            {
                path: '/intelligent/land-dividing',
                name: 'landChange',
                meta: {
                    title: '地类分割',
                    requireAuth: true
                },
                component: () => import('@/views/intelligent/land-dividing'),
            },
            {
                path: '/intelligent/land-dividing/land-dividing-details',
                name: 'landDividingDetails',
                meta: {
                    title: '地类分割详情',
                    requireAuth: true
                },
                component: () => import('@/views/intelligent/land-dividing/land-dividing-details'),
            },
            {
                path: '/intelligent/land-dividing/land-dividing-details/spot-view',
                name: 'dividingSpotView',
                meta: {
                    title: '变化检测详情',
                    requireAuth: true
                },
                component: () => import('@/views/intelligent/land-dividing/land-dividing-details/spot-view'),
            },
        ]
    },
];

const routes = [
    {
        path: '/login',
        name: 'login',
        meta: {
            title: '登录'
        },
        component: () => import('@/views/login')
    },
    // {
    //   path: '/portal',
    //   name: 'portal',
    //   meta: {
    //     title: '首页页面',
    //     requireAuth: true
    //   },
    //   component: () => import('@/views/portal')
    // },
    {
        path: '/map-screenshot/:clueId',
        name: 'mapScreenshot',
        meta: {
            title: '截图',
            requireAuth: false
        },
        component: () => import('@/views/mapScreenshot/Index.vue')
    },
    {
        path: '/mapview-screenshot/:clueId',
        name: 'mapViewScreenshot',
        meta: {
            title: '截图1',
            requireAuth: false
        },
        component: () => import('@/views/mapScreenshot/MapView.vue')
    },
    {
        path: '/panorama-embed',
        name: 'PanoramaEmbed',
        meta: {
            title: '全景嵌入',
            requireAuth: false,
            autoLogin: true
        },
        component: () => import('@/views/panoramaView/embed.vue')
    },

    {
        path: '/',
        name: 'HomePage',
        meta: {
            title: '主容器',
            requireAuth: true
        },
        component: () => import('@/layout'),
        children: subRoutes
    },
    {
        path: '*',
        name: 'NotFound',
        component: () => import('@/layout/components/404')
    }
];


const router = new VueRouter({
    routes,
    mode: 'history',
    base: process.env.BASE_URL
});
// 工具函数：获取 URL 中的 code 参数（写在这或放 utils 都行）
function getQueryParam(name) {
    const reg = new RegExp('(^|&)' + name + '=([^&]*)(&|$)', 'i')
    const r = window.location.search.substr(1).match(reg)
    if (r != null) return decodeURIComponent(r[2])
    return null
}
export default router;
//配置访问限制
router.beforeEach((to, from, next) => {
    const code = getQueryParam('code')

    // 如果有 code，直接走 SSO 登录，不进入原有登录逻辑
    if (code) {
        console.log('检测到 code 参数，执行单点登录：', code)

        // 调用后台接口：用 code 换 token + 用户信息
        store.dispatch('user/ssoLoginByCode', code).then(res => {
            // 登录成功 → 去掉 url 里的 code，避免重复触发
            next({ path: to.path, query: {}, replace: true })
        }).catch(err => {
            console.error('SSO 登录失败', err)
            next()
        })
        return // 必须 return，不往下走
    }
    const hasAutoLoginRoute = to.matched.some((record) => record.meta.autoLogin)
        && window.config?.overviewAutoLogin?.enabled !== false;
    const forceAutoLogin = to.matched.some((record) => record.meta.forceAutoLogin)
        && window.config?.overviewAutoLogin?.enabled !== false;

    const enterWithAutoLogin = () => {
        store.commit('user/SET_CURRENT_USER', {
            alias: '',
            id: '',
            username: '',
            county: '',
            admin: 0
        });
        performAutoLogin()
            .then(() => store.dispatch('user/queryUserInfo'))
            .then(() => {
                localStorage.setItem('path', to.path);
                next();
            })
            .catch((err) => {
                console.error('自动登录失败', err);
                next({ path: '/login', query: { redirect: to.fullPath } });
            });
    };

    if (forceAutoLogin) {
        enterWithAutoLogin();
        return;
    }

    if (hasAutoLoginRoute && !localStorage.getItem('tokens')) {
        enterWithAutoLogin();
        return;
    }

    if (to.meta.requireAuth) {
        // 判断该路由是否需要登录权限
        if (localStorage.getItem('tokens')) {
            localStorage.setItem('path', to.path);
            // 检查路由权限
            if (store.state.user.currentUser.id) {
                next();
            } else {
                store.dispatch('user/queryUserInfo').then(() => {
                    next();
                }).catch(() => {
                    if (hasAutoLoginRoute) {
                        enterWithAutoLogin();
                    } else {
                        next({ path: '/login', query: { redirect: to.fullPath } });
                    }
                });
            }
        } else if (hasAutoLoginRoute) {
            enterWithAutoLogin();
        } else {
            next({ path: '/login', query: { redirect: to.fullPath } });
        }
    } else {
        next();
    }
});

