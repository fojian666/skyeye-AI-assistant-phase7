<template>
    <el-dialog
        :title="title"
        :visible.sync="dialogVisible"
        width="50vw"
        custom-class="rc-light-dialog"
        @closed="dialogClosed"
        @open="openOpened"
    >
        <el-form ref="formRef" :rules="rules" :model="formData" label-width="100px">
            <el-form-item label="父节点：" prop="cascaderValue">
                <el-cascader
                    v-model="formData.cascaderValue"
                    :options="cascaderOptions"
                    clearable
                    placeholder="不选则为根目录"
                    :show-all-levels="false"
                    popper-class="rc-light-popper"
                    :props="{ label: 'caption', value: 'id', checkStrictly: true }"
                    @change="handleChange"></el-cascader>
            </el-form-item>
            <el-form-item label="菜单名称：" prop="caption">
                <el-input v-model="formData.caption" clearable></el-input>
            </el-form-item>
            <el-form-item label="菜单图标：" prop="icon">
                <el-select
                    v-model="formData._icon"
                    ref="selectRef"
                    popper-class="rc-light-popper"
                    :popper-append-to-body="false"
                    @change="selectChange"
                    clearable
                    placeholder=""
                    :disabled="selectDisabled">
                    <i slot="prefix" class="icon iconfont" :class="[iconClass]"></i>
                    <el-option v-for="item in options" :key="item.id" :value="item.icon" :label="item.label">
                        <span class="icon iconfont" :class="[item.icon]"></span>
                    </el-option>
                </el-select>
            </el-form-item>
            <el-form-item label="菜单链接：" prop="url">
                <el-input v-model="formData.url" clearable></el-input>
            </el-form-item>
            <el-form-item label="排序号：" prop="order">
                <el-input v-model="formData.order" clearable oninput="value=value.replace(/[^\d.]/g,'')"></el-input>
            </el-form-item>
            <el-form-item label="是否显示：" prop="display">
                <el-switch v-model="formData.display"></el-switch>
            </el-form-item>
            <el-form-item label="备注：" prop="remark">
                <el-input type="textarea" v-model="formData.remark" placeholder="请输入内容"></el-input>
            </el-form-item>
        </el-form>
        <span slot="footer" class="dialog-footer">
            <el-button @click="dialogVisible = false">取 消</el-button>
            <el-button type="primary" @click="determine">确 定</el-button>
        </span>
    </el-dialog>
</template>

<script>
import { postMenuDataApi, putMenuDataApi } from '@/api/commonApi';

export default {
    name: 'DialogForm',
    data() {
        return {
            dialogVisible: false,
            formData: {
                pid: '',
                caption: '',
                cascaderValue: [],
                _icon: '',
                icon: '',
                url: '',
                order: '',
                display: true,
                remark: ''
            },
            options: [
                {
                    id: 1,
                    icon: 'icon-gaishu',
                    label: ''
                },
                {
                    id: 2,
                    icon: 'icon-geoai-landChange',
                    label: ''
                },
                {
                    id: 3,
                    icon: 'icon-geoai-grid',
                    label: ''
                },
                {
                    id: 4,
                    icon: 'icon-geoai-changeDetectionAI',
                    label: ''
                },
                {
                    id: 5,
                    icon: 'icon-geoai-manage',
                    label: ''
                },
                {
                    id: 6,
                    icon: 'icon-bangzhuzhongxin',
                    label: ''
                },
                {
                    id: 7,
                    icon: 'icon-geoai-bar'
                },
                {
                    id: 8,
                    icon: 'icon-a-gengduofenlei-m'
                },
                {
                    id: 9,
                    icon: 'icon-moxingguanli'
                },
                {
                    id: 10,
                    icon: 'icon-geoai-img-transmission'
                },
                {
                    id: 11,
                    icon: 'icon-cloud-service-full'
                },
                {
                    id: 12,
                    icon: 'icon-geoai-comparison'
                },
                {
                    id: 13,
                    icon: 'icon-geoai-distributed-location'
                },
                {
                    id: 14,
                    icon: 'icon-ziyuan'
                },
                {
                    id: 15,
                    icon: 'icon-mubiaojiance1'
                }
            ],
            rules: {
                caption: [{ required: true, message: '请输入菜单名称', trigger: 'blur' }],
                url: [{ required: true, message: '请输入菜单链接', trigger: 'blur' }]
            },
            cascaderOptions: [],
            callback: null,
            type: '',
            title: '新增菜单',
            iconClass: '',
            selectDisabled: false
        };
    },
    methods: {
        buildCascaderOptions(nodeData) {
            const menuTree = JSON.parse(JSON.stringify(nodeData || []));
            return [
                { id: 0, caption: '根目录', leaf: true },
                ...menuTree
            ];
        },
        findMenuPath(nodes, targetId, path = []) {
            for (const node of nodes) {
                const currentPath = [...path, node.id];
                if (String(node.id) === String(targetId)) {
                    return currentPath;
                }
                if (node.children && node.children.length) {
                    const result = this.findMenuPath(node.children, targetId, currentPath);
                    if (result) {
                        return result;
                    }
                }
            }
            return null;
        },
        resolvePid() {
            const path = this.formData.cascaderValue || [];
            this.formData.pid = path.length === 0 ? 0 : path[path.length - 1];
        },
        open(type, nodeData, callback, data) {
            this.type = type;
            this.dialogVisible = true;
            this.callback = callback;
            const menuTree = JSON.parse(JSON.stringify(nodeData || []));
            this.cascaderOptions = this.buildCascaderOptions(menuTree);
            if (type === 'edit') {
                this.title = '编辑菜单';
                this.formData = JSON.parse(JSON.stringify(data));
                this.iconClass = this.formData.icon;
                if (this.formData.pid === 0 || this.formData.pid === '0') {
                    this.formData.cascaderValue = [0];
                } else {
                    const parentPath = this.findMenuPath(menuTree, this.formData.pid);
                    this.formData.cascaderValue = parentPath || [];
                }
                this.selectDisabled = this.formData.cascaderValue.length === 3;
                if (this.formData.display === 1) {
                    this.formData.display = true;
                } else {
                    this.formData.display = false;
                }
            }
        },
        handleChange(value) {
            const path = value || [];
            this.selectDisabled = path.length === 3;
            this.formData.pid = path.length === 0 ? 0 : path[path.length - 1];
        },
        determine() {
            this.$refs.formRef.validate((valid) => {
                if (!valid) return false;
                if (this.type === 'add') {
                    this.add();
                } else if (this.type === 'edit') {
                    this.edit();
                }
            });
        },
        async add() {
            this.resolvePid();
            const res = await postMenuDataApi(this.formData);
            if (res.code === 0) {
                this.$message({
                    message: res.msg,
                    type: 'success',
                    duration: 800
                });
                this.dialogVisible = false;
                this.callback(true);
                this.$store.dispatch('menu_operation');
            } else {
                this.$message.warning(res.msg);
            }
        },
        async edit() {
            this.resolvePid();
            const res = await putMenuDataApi(this.formData);
            if (res.code === 0) {
                this.$message.success(res.msg);
                this.dialogVisible = false;
                this.callback(true);
                this.$store.dispatch('menu_operation');
            } else {
                this.$message.warning(res.msg);
            }
        },
        dialogClosed() {
            this.$refs.formRef.resetFields();
            this.selectDisabled = false;
        },
        openOpened() {
            if (this.type === 'add') {
                this.title = '新增菜单';
                this.iconClass = '';
                for (let k in this.formData) {
                    if (k === 'cascaderValue') {
                        this.formData[k] = [];
                    } else if (k === 'display') {
                        this.formData[k] = false;
                    } else {
                        this.formData[k] = '';
                    }
                }
            }
        },
        selectChange(value) {
            this.formData._icon = '';
            this.formData.icon = value;
            this.iconClass = value;
        }
    },
    mounted() {
        // 读取 iconfont.css 内容（需放在 public 目录）
        fetch('/iconfont.css')
            .then((res) => res.text())
            .then((cssText) => {
                // 用正则匹配所有图标类名
                const iconRegex = /\.icon-([\w-]+):before/g;
                let match;
                const icons = [];
                while ((match = iconRegex.exec(cssText)) !== null) {
                    icons.push({
                        id: icons.length + 1,
                        icon: `icon-${match[1]}`, // 拼接完整类名
                        label: '' // 可手动添加标签或从其他地方获取
                    });
                }
                this.options = icons; // 赋值给 options
            });
    }
};
</script>

<style lang="scss" scoped>
.el-select {
    width: 100%;
}

.el-select-dropdown__item {
    float: left;
}

.el-scrollbar__wrap {
    overflow: hidden !important;
}

::v-deep .el-select-dropdown__list {
    width: 40vw;
}

::v-deep .el-input__prefix {
    margin-left: 11px;
    color: #606266;
}
</style>
