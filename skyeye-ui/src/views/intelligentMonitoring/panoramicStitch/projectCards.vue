<template>
    <div class="gtp-container">
        <el-card class="box-card">
            <div slot="header" class="clearfix">
                <el-tooltip :content="proj.name" placement="top" effect="light">
                    <p class="card-name">{{ card_name }}</p>
                </el-tooltip>
                <div class="buttons">
                    <el-button
                        class="action-button"
                        type="primary"
                        plain
                        icon="el-icon-folder-opened"
                        style="font-size: 18px; padding: 2px 4px"
                        size="medium"
                        @click="opentask"></el-button>
                    <el-button
                        class="action-button"
                        type="primary"
                        plain
                        icon="el-icon-delete"
                        style="font-size: 18px; padding: 2px 4px"
                        size="medium"
                        @click="deleteCard"></el-button>
                </div>
            </div>
            <p class="card-time">任务数量：{{ proj.count }}</p>
            <p class="card-time">创建时间：{{ proj.create_time }}</p>
        </el-card>
    </div>
</template>

<script>
import { deleteProjectApi } from '@/api/commonApi';

export default {
    name: 'ProjectCards',
    props: {
        proj: {
            type: Object,
            required: true
        }
    },
    data() {
        return {
            activeName: 'first',
            fit: 'fit'
        };
    },
    computed: {
        card_name() {
            if (this.proj.name.length > 15) {
                return this.proj.name.slice(0, 15) + '···';
            } else {
                return this.proj.name;
            }
        }
    },
    methods: {
        opentask() {
            this.$emit('opentask', this.proj.id, this.proj.name);
        },
        deleteCard() {
            this.$confirm('此操作将永久删除该项目, 是否继续?', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            })
                .then(async () => {
                    const params = {
                        project_id: this.proj.id
                    };
                    const res = await deleteProjectApi(params);
                    if (res.code === 0) {
                        this.$emit('removeProject');
                        this.$message({
                            type: 'success',
                            message: '删除成功!'
                        });
                    }
                })
                .catch(() => {
                    this.$message({
                        type: 'info',
                        message: '已取消删除'
                    });
                });
        }
    },
    created() {}
};
</script>

<style lang="scss" scoped>
.gtp-container {
    height: 98%;
}

.box-card {
    width: 100%;
    height: 100%;
}

.clearfix {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.card-name {
    /*background-color: orange;*/
    /*设置规定长度*/
    width: 150px;
    /*内容会被修剪，并且其余内容是不可见的*/
    overflow: hidden;
    /*显示省略符号来代表被修剪的文本。*/
    text-overflow: ellipsis;
    /*设置一行显示*/
    white-space: nowrap;
    font-weight: 700;
}

.card-time {
    text-align: left;
}

.buttons {
    margin-left: auto;
    display: flex;
}

.action-button {
    margin-left: 10px; /* Add space between buttons */
}
</style>
