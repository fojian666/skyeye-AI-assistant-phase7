<template>
    <a-form class="query-container" layout="inline" :form="form">
        <template v-for="(item, i) in config">
            <a-form-item :label="item.label" :key="i" class="input-container">
                <a-input v-if="item.type === 'input'" v-decorator="item.decorator" allow-clear placeholder="请输入任务名称"></a-input>
                <a-date-picker v-else-if="item.type === 'date'" placeholder="请选择日期" v-decorator="item.decorator" format="YYYY-MM-DD" allowClear>
                </a-date-picker>
                <a-select
                    v-else-if="item.type === 'taskselect'"
                    v-decorator="item.decorator"
                    :options="task_type_list"
                    allowClear
                    placeholder="请选择任务类型"></a-select>
                <a-select
                    v-else-if="item.type === 'select'"
                    v-decorator="item.decorator"
                    :options="countyList"
                    allowClear
                    placeholder="请选择检测区域"></a-select>
            </a-form-item>
        </template>
        <a-form-item class="btn-container">
            <a-button type="primary" class="btn-query" @click="getQueryPara">
                <a-icon type="search" />
                查询
            </a-button>
            <a-button @click="resetForm">
                <a-icon />
                重置
            </a-button>
        </a-form-item>
    </a-form>
</template>

<script>
const page = 1;
const limit = 9;
export default {
    name: 'Query',
    beforeCreate() {
        this.form = this.$form.createForm(this);
    },
    data() {
        return {
            config: Object.freeze([
                {
                    label: '任务名称',
                    type: 'input',
                    decorator: ['name']
                },
                {
                    label: '任务类型',
                    type: 'taskselect',
                    decorator: ['taskType'],
                    values: []
                },
                {
                    label: '检测区域',
                    type: 'select',
                    decorator: ['county'],
                    values: []
                },
                {
                    label: '注册时间',
                    type: 'date',
                    decorator: ['createDate']
                }
            ])
        };
    },
    props: {
        queryParameter: {
            type: Object,
            required: true
        },
        countyList: {
            type: Array,
            required: true
        },
        task_type_list: {
            type: Array,
            required: true
        }
    },
    methods: {
        getQueryPara() {
            this.form.validateFields((err, obj) => {
                if (!err) {
                    let queryPara = obj;
                    for (let item in queryPara) {
                        !queryPara[item] ? (queryPara[item] = '') : null;
                    }
                    let queryParaStr = queryPara;
                    this.$emit('changeList', queryParaStr);
                }
            });
        },
        resetForm() {
            this.form.resetFields();
            this.getQueryPara();
        }
    }
};
</script>

<style scoped>
.query-container {
    width: 100%;
    display: flex;
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
    flex-wrap: nowrap;
    height: 4rem;
    padding: 0 0.5rem;
}

.input-container {
    width: 28%;
    display: flex;
}
::v-deep(.btn-container .ant-form-item-children) {
    display: flex;
    flex-wrap: nowrap;
}
::v-deep(.btn-container) {
    margin-right: 0;
}

::v-deep(.ant-form-item-control-wrapper) {
    flex: 1;
}

::v-deep(.ant-form-item-children) {
    display: inline-block;
    width: 100%;
}

::v-deep(.ant-calendar-picker) {
    width: 100%;
}

.btn-query {
    background-color: #137ce3;
    margin-right: 1rem;
}
::v-deep .ant-input {
    color: white;
}
::v-deep .ant-select-selection--single .ant-select-selection__rendered {
    color: white;
}
::v-deep .anticon {
    color: #1890ff;
}
</style>
