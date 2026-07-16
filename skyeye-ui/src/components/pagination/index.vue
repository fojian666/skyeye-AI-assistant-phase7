<template>
    <div class="pagination-container">
        <div>
            共 {{ paginationConfig.total }} 条记录 第{{ current + '/' + Math.ceil(paginationConfig.total / 9) }}
            页
        </div>
        <a-pagination v-model="current" :total="paginationConfig.total" :default-page-size="9" @change="changePage"> </a-pagination>
    </div>
</template>

<script>
export default {
    name: 'Pagination',
    data() {
        return {
            current: 1
        };
    },
    props: {
        paginationConfig: {
            type: Object,
            required: true
        }
    },
    methods: {
        //点击页面
        changePage(page, size) {
            this.$emit('changeList', { pageIndex: page, pageSize: size });
        }
    }
};
</script>

<style scoped>
.pagination-container {
    box-sizing: border-box;
    height: 3rem;
    position: absolute;
    bottom: 0.5rem;
    right: 0rem;
    left: 0;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 1rem;
}

.pagination-container ul {
    height: 100%;
    display: flex;
    justify-content: right;
    align-items: center;
}
</style>
