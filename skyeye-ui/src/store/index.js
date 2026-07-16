import Vue from 'vue';
import Vuex from 'vuex';
import user from './user';
import { findNodeWithPath, traverseList } from '@/utils/utils';
import { getSysMenuListApi } from '@/api/commonApi';
import filterModule from './filter';
Vue.use(Vuex);

export default new Vuex.Store({
    state: {
        parentNodeData: [],
        menuList: [],
        sideMenuList: [],
        panoramaMenuList: [],
        defaultOpenKeys: [],
        dataMenuList: [],
        clueVerifyMenuList: [],
        patternVerifiyMenuList: [],
        secondMenuList: [],
        currentMenuList: [],
        showHeader: true, //是否显示导航
        theme: localStorage.getItem('ui-theme') || 'dark'
    },
    getters: {},
    mutations: {
        //改变主题风格
        changeTheme(state, theme) {
            state.theme = theme;
            localStorage.setItem('ui-theme', theme);
        },
        //切换显示头部导航栏
        toggleShowHeaderBar(state, flag) {
            state.showHeader = flag;
        },
        initParentNode(state, list) {
            state.parentNodeData = list;
        },
        initMenuList(state, list) {
            state.menuList = list;
        },
        initSecondMenuList(state, list) {
            state.secondMenuList = list;
        },
        initSideMenuList(state, list) {
            state.sideMenuList = list;
        },
        initPanoramaMenuList(state, list) {
            state.panoramaMenuList = list;
        },
        initDefaultOpenKeys(state, url) {
            state.defaultOpenKeys.push(url);
        },
        initClueVerifyMenuList(state, list) {
            state.clueVerifyMenuList = list;
        },
        initDataMenuList(state, list) {
            state.dataMenuList = list;
        },
        initPatternVerifiyMenuList(state, list) {
            state.patternVerifiyMenuList = list;
        },
        MenuList(state, list) {
            state.panoramaMenuList = list;
        },
        initCurrentMenuList(state, list) {
            state.currentMenuList = list;
        },
        toggleMenuActive(state, url) {
            // 获取当前激活的菜单项
            state.menuList.forEach((item, index) => {
                if (url.split('/')[1] === item.url.split('/')[1]) {
                    state.currentMenuList = state.secondMenuList[index].children;
                    localStorage.setItem('menu', JSON.stringify(state.secondMenuList[index]));
                    Vue.set(item, 'active', true);
                } else {
                    Vue.set(item, 'active', false);
                }
            });
        }
    },
    actions: {
        async menu_operation(context) {
            const res = context.state.user.userMenuList.length;
            let sysMenu;
            if (res > 0) {
                sysMenu = context.state.user.userMenuList;
            } else {
                const res = await getSysMenuListApi();
                sysMenu = res.data;
            }
            sysMenu.forEach((item, index) => {
                const url = window.location.pathname;
                if (url.split('/')[1] === item.url.split('/')[1]) {
                    context.state.currentMenuList = sysMenu[index].children;
                    localStorage.setItem('menu', sysMenu[index]);
                }
                if (sysMenu.length === 2) {
                    sysMenu[1].url = sysMenu[1].children[0].url;
                }
                if (findNodeWithPath(item, localStorage.getItem('path'))) {
                    Vue.set(item, 'active', true);
                } else {
                    Vue.set(item, 'active', false);
                }
                if (item.name === '系统运维管理') {
                    context.commit('initSideMenuList', item.children);
                    item.children.forEach((subItem) => {
                        context.commit('initDefaultOpenKeys', subItem.url);
                    });
                }
            });
            context.commit('initSecondMenuList', sysMenu);
            context.commit('initMenuList', sysMenu);
        }
    },
    modules: {
        user,
        filter: filterModule
    },
    plugins: []
});
