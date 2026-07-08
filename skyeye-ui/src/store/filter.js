const state = {
    tableFilters: {
        time:[],
        startDate: '',
        endDate:'',
        batchType:'',
        taskName: '',
        queryBatchId:'',
        status: '',
        county: '',
        gridId:'',
        pageIndex: 1,
        pageSize: 10,
        regionSelect:'',
        regionZw:[],
    }
};

const mutations = {
    SET_TABLE_FILTERS(state, filters) {
        state.tableFilters = {...state.tableFilters, ...filters}
    },

    // 如果需要单独设置某个字段
    SET_FILTER_FIELD(state, {field, value}) {
        state.tableFilters[field] = value
    },
    // 重置参数
    RESET_FILTERS(state) {
        state.tableFilters = {
            time:[],
            startDate: '',
            endDate:'',
            taskName: '',
            status: '',
            id:'',
            batchType:'',
            gridId:'',
            county:'',
            pageSize: 10,
            pageIndex: 1,
            regionSelect:'',
            regionZw:[]
        }
    }
}

const actions = {
    updateTableFilters({commit}, filters) {
        commit('SET_TABLE_FILTERS', filters)
    },

    saveFilterBeforeLeave({commit, state}, routeInfo) {
        // 如果需要区分不同页面的筛选条件
        const filterKey = `tableFilters_${routeInfo.pageId || 'default'}`
        localStorage.setItem(filterKey, JSON.stringify(state.tableFilters))
    },

    restoreFilterOnReturn({commit}, routeInfo) {
        const filterKey = `tableFilters_${routeInfo.pageId || 'default'}`
        const savedFilters = localStorage.getItem(filterKey)
        if (savedFilters) {
            commit('SET_TABLE_FILTERS', JSON.parse(savedFilters))
        }
    }
}

const getters = {
    getTableFilters: state => state.tableFilters,
    getFilterField: state => field => state.tableFilters[field]
}

export default {
    namespaced: true,
    state,
    mutations,
    actions,
    getters
}