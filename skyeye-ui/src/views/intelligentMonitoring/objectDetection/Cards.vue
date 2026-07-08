<template>
    <div class="gtp-container">
        <el-card class="box-card">
            <div slot="header" class="clearfix">
                <el-tooltip :content="data.task_name" placement="top" effect="light">
                    <p class="card-name">{{ card_name }}</p>
                </el-tooltip>
                <div class="buttons">
                    <el-button class="action-button" type="primary" plain icon="el-icon-view"
                               style="font-size: 18px; padding: 2px 10px 2px 10px" size="medium" @click="openTaskDetails"
                    ></el-button>
                    <el-button class="action-button" type="primary" plain icon="el-icon-delete"
                               style="font-size: 18px; padding: 2px 10px 2px 10px " size="medium" @click="deleteCard"
                    ></el-button>
                </div>
            </div>
            <p class="card-time">创建时间：{{ data.task_create_time }}</p>

        </el-card>

    </div>
</template>

<script>
    import {deleteOdImageApi} from "@/api/commonApi";

    export default {
        name: "cards",
        props: {
            data: {
                type: Object,
                required: true,
            },
        },
        data() {
            return {
                activeName: "first",
                fit: "fit",
            };
        },
        computed: {
            card_name() {
                if (this.data.task_name.length > 15) {
                    return this.data.task_name.slice(0, 15) + '···';
                } else {
                    return this.data.task_name;
                }
            },
            getImageUrl() {
                // 在此处构建 API 地址和图片路径
                if (this.data.pictures ) {
                    const apiBaseUrl = 'api';
                    const imagePath = this.data.pictures[0].result_path;
                    return `/${apiBaseUrl}/${imagePath}`;
                } else {
                    // 如果没有图片，返回默认图片路径或空字符串，根据你的需求而定
                    return 'default_image_path';
                }
            },
        },
        methods: {
            openTaskDetails() {
                this.$emit("open-task-details", this.data);
            },
            deleteCard() {
                this.$confirm('此操作将永久删除该文件, 是否继续?', '提示', {
                    confirmButtonText: '确定',
                    cancelButtonText: '取消',
                    type: 'warning'
                }).then(async () => {
                    const res = await deleteOdImageApi(this.data.task_id)
                    if (res.code === 0) {
                        this.$emit("remove");
                        this.$message({
                            type: 'success',
                            message: '删除成功!'
                        });
                    }
                }).catch(() => {
                    this.$message({
                        type: 'info',
                        message: '已取消删除'
                    });
                });
            },
        },
        created() {
        },
    };
</script>

<style lang="scss" scoped>
  .gtp-container{
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
