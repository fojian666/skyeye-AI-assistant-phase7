import {getCurrentUser, postLoginByCodeApi} from "@/api/userAPi";
import {getSysMenuListApi} from "@/api/commonApi";

const state = {
    currentUser: {
        alias: '',
        id: '',
        username: '',
        county: '',
        admin: 0
    },
    userMenuList: []
};

const mutations = {
    SET_CURRENT_USER(state, user) {
        state.currentUser = user;
    },
    SET_MENU_LIST(state, list) {
        state.userMenuList = list
    }
};

const actions = {
    async queryUserInfo({ commit }) {
        const res = await getCurrentUser();
        localStorage.setItem('username', res.data.username);
        if (res.data.county) {
            localStorage.setItem('county', res.data.county);
        }
        commit('SET_CURRENT_USER', res.data);
        // 获取用户菜单权限
        const menuRes = await getSysMenuListApi();
        commit('SET_MENU_LIST', menuRes.data)
    },
    // 新增：通过 code 单点登录
    async ssoLoginByCode({ commit }, code) {
        // 调用你后端接口
        const params = {
            code:code
        }
        const res = await postLoginByCodeApi(params)
        commit('SET_CURRENT_USER', res.data);
        localStorage.setItem('tokens', res.data.tokens)
        // 获取用户菜单权限
        const menuRes = await getSysMenuListApi();
        commit('SET_MENU_LIST', menuRes.data)
        return res
    }
};

export default {
    namespaced: true,
    state,
    mutations,
    actions,
};