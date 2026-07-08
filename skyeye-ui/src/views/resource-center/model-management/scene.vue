<template>
	<div class="model-scene-info">
		<div class="gt-breadcrumb-box">
            <i class="iconfont icon-geoai-manage"></i>
            <span class="gt-current-position">场景配置</span>
		</div>
		<div class="gt-breadcrumb-cnt">
			<el-row :gutter="20" class="add">
				<el-col :span="7">
					<!-- 搜索与添加区域 -->
					<el-input placeholder="请输入场景名称" clearable v-model="queryInfo.name" @clear="initModelList">
						<el-button slot="append" icon="el-icon-search" @click="initModelList"></el-button>
					</el-input>
				</el-col>
				<el-col :span="4">
					<el-button type="primary" @click="addDialogVisible = true"><i class="iconfont icon-tianjia"></i>新增模型场景
					</el-button>
				</el-col>
			</el-row>
			<!-- 用户列表 -->
			<el-table :data="modelSceneList" height="70%" stripe style="width: 100%" border>
				<el-table-column type="index" label="编号" align="center" width="80"></el-table-column>
				<el-table-column prop="name" label="场景名称" align="center"></el-table-column>
				<el-table-column prop="labelRels" label="场景标签" align="center">
					<template slot-scope="scope">
						<div v-if="scope.row.labelRels && scope.row.labelRels.length">
							<el-tooltip placement="top">
								<div slot="content">
									<div v-for="label in scope.row.labelRels" :key="label.id">
										{{ label.labelName }} ({{ label.labelValue }})
									</div>
								</div>
								<div>
                <span v-for="(label, index) in scope.row.labelRels.slice(0, 4)" :key="label.id" class="tag-item">
                    {{ label.labelName }}
                </span>
									<span v-if="scope.row.labelRels.length > 4" class="tag-item">
                    +{{ scope.row.labelRels.length - 4 }}
                </span>
								</div>
							</el-tooltip>
						</div>
						<div v-else class="no-tags">
							无标签
						</div>
					</template>
				</el-table-column>
				<el-table-column prop="orderIndex" label="排序号" align="center" width="150"></el-table-column>
				<el-table-column prop="remark" label="描述" align="center" width="150"></el-table-column>
				<el-table-column label="操作" align="center">
					<template v-slot="scope">
						<!-- 修改按钮 -->
						<el-button type="primary" icon="el-icon-edit" size="medium" @click="showEditDialog(scope.row)"></el-button>
						<!-- 删除按钮 -->
						<el-button type="danger" icon="el-icon-delete" size="medium"
											 @click="removeUserById(scope.row.id)"></el-button>
					</template>
				</el-table-column>
			</el-table>

			<!-- 分页 -->
			<el-pagination
							@current-change="handleCurrentChange"
							:current-page="queryInfo.pageIndex"
							@size-change="handleSizeChange"
							:page-size="queryInfo.pageSize"
							:page-sizes="[5, 10, 15, 20]"
							layout="total, sizes, prev, pager, next, jumper"
							:total="total">
			</el-pagination>

			<!-- 添加模型对话框 -->
			<el-dialog title="添加模型场景" :visible.sync="addDialogVisible" width="50%" custom-class="rc-light-dialog" @close="addDislogClosed"
								 :modal-append-to-body="false">
				<!-- 内容主题区域 -->
				<el-form label-width="100px" ref="addFormRef" :model="addForm" :rules="addFormRules">
					<el-form-item label="场景名称" prop="name">
						<el-input v-model="addForm.name" placeholder="请输入场景名称"></el-input>
					</el-form-item>
					<el-form-item label="关联模型" prop="modelId">
						<el-select v-model="addForm.modelId" placeholder="请选择关联模型" clearable style="width: 100%">
							<el-option v-for="item in modelList" :key="item.id" :label="item.name" :value="item.id"></el-option>
						</el-select>
					</el-form-item>
					<el-form-item label="标签类别:" prop="labels">
						<el-select v-model="addForm.labelRels" placeholder="请选择标签类别" multiple clearable style="width: 100%">
							<el-option v-for="item in labelList" :key="item.labelValue" :label="item.labelName"
												 :value="item.labelValue"></el-option>
						</el-select>
					</el-form-item>
					<el-form-item label="排序号" prop="orderIndex">
						<el-input v-model="addForm.orderIndex" type="number" placeholder="请输入排序号"></el-input>
					</el-form-item>
					<el-form-item label="场景描述" prop="remark">
						<el-input v-model="addForm.remark" type="textarea" placeholder="请输入场景描述"></el-input>
					</el-form-item>
				</el-form>
				<!-- 底部按钮区域 -->
				<span slot="footer" class="dialog-footer">
          <el-button @click="addDialogVisible = false">取 消</el-button>
          <el-button type="primary" @click="addModelScene">确 定</el-button>
        </span>
			</el-dialog>
			<el-dialog title="修改模型" @close="editClosed" :visible.sync="editDialogVisible" width="50%" custom-class="rc-light-dialog"
								 :modal-append-to-body="false">
				<el-form :model="editForm" :rules="addFormRules" ref="editFormRef" label-width="70px">
					<el-form-item label="模型场景ID">
						<el-input v-model="editForm.id" disabled></el-input>
					</el-form-item>
					<el-form-item label="场景名称">
						<el-input v-model="editForm.name"></el-input>
					</el-form-item>
					<el-form-item label="关联模型" prop="modelId">
						<el-select v-model="editForm.modelId" placeholder="请选择关联模型" clearable style="width: 100%">
							<el-option v-for="item in modelList" :key="item.id" :label="item.name" :value="item.id"></el-option>
						</el-select>
					</el-form-item>
					<el-form-item label="标签类别" prop="labelRels">
						<el-select v-model="editForm.labelRels" placeholder="请选择标签类别" multiple clearable style="width: 100%">
							<el-option v-for="item in labelList" :key="item.labelValue" :label="item.labelName"
												 :value="item.labelValue"></el-option>
						</el-select>
					</el-form-item>
					<el-form-item label="排序号" prop="orderIndex">
						<el-input v-model="editForm.orderIndex" type="number"></el-input>
					</el-form-item>
					<el-form-item label="模型描述" prop="remark">
						<el-input v-model="editForm.remark" type="textarea"></el-input>
					</el-form-item>
				</el-form>
				<span slot="footer" class="dialog-footer">
          <el-button @click="editDialogVisible = false">取 消</el-button>
          <el-button type="primary" @click="editModelSceneInfo">确 定</el-button>
        </span>
			</el-dialog>
		</div>
	</div>
</template>

<script>
  import {
    deleteModelSceneDataApi,
    getModelListNoPageApi, getModelLabelListApi,
    getModelSceneListApi,
    addModelSceneDataAPi,
    updateModelSceneDataApi
  } from '@/api/commonApi';

  export default {
    name: 'SceneInfo',
    data() {
      return {
        queryInfo: {
          name: '',
          pageIndex: 1,
          pageSize: 10
        },

        modelList: [],
        modelSceneList: [],
        total: 0,
        addForm: {
          name: '',
          modelId: '',
          remark: '',
          orderIndex: '',
          labelRels: [],
        },
        labelList: [],
        editDialogVisible: false,
        setRolesDialogVisible: false,
        addDialogVisible: false,
        userInfo: {},
        // 分配角色列表
        rolesList: [],
        // 保存已经选中的角色id值
        selectRoleId: '',
        // 查询用户的对象
        editForm: {
          id: '',
          name: '',
          modelId: '',
          remark: '',
          orderIndex: '',
          labelRels: [],
        }
      };
    },
    components: {
    },
    created() {
      this.initModelList();
      this.constructTreeSelect(country_dict);
    },
    mounted() {
      this.initModelSceneList();
    },
    watch: {
      'addForm.modelId': {
        handler(newVal, oldVal) {
          if (newVal) {
            this.initLabels(this.addForm.modelId);
          }
        }

      },
      'editForm.modelId': {
        handler(newVal, oldVal) {
          if (newVal) {
            this.initLabels(this.editForm.modelId);
          }
        }

      },
    },
    methods: {
      async initLabels(modelId) {
        const param = {
          id: modelId,
        }
        const res = await getModelLabelListApi(param);
        if (res.code === 0) {
          this.labelList = res.data;
        }
      },
      async initModelList() {
        const params = {
          pageIndex: -1,
          name: ""
        }
        const res = await getModelListNoPageApi(params);
        if (res.code === 0) {
          this.modelList = res.data;
        }
      },
      //获取模型场景数据
      async initModelSceneList() {
        const res = await getModelSceneListApi(this.queryInfo);
        if (res.code === 0) {
          this.modelSceneList = res.data;
          this.total = res.total;
        }
      },

      // 监听 limit 改变事件 每页显示的个数
      handleSizeChange(newSize) {
        this.queryInfo.pageSize = newSize;
        this.initModelSceneList();
      },
      // 监听 页码值 改变的事件 当前页面值
      handleCurrentChange(newPage) {
        this.queryInfo.pageIndex = newPage;
        this.initModelSceneList();
      },
      // 监听添加模型的对话框关闭事件
      addDislogClosed() {
        this.$refs.addFormRef.resetFields();
      },
      // 点击按钮,添加模型
      addModelScene() {
        this.$refs.addFormRef.validate(async (valid) => {
          if (!valid) return;
          const labelRels = [];
          const than = this;
          // 将选中的ID数组转换为对象数组
          this.addForm.labelRels.forEach(function (value) {
            var label = than.labelList.find(function (item) {
              return item.labelValue === value;
            });

            if (label) {
              labelRels.push({
                labelValue: label.labelValue,
                labelName: label.labelName
              });
            }
          });
          //通过URLSearchParams封装请求数据
          let params = {
            name: this.addForm.name,
            modelId: this.addForm.modelId,
            remark: this.addForm.remark,
            orderIndex: this.addForm.orderIndex,
            labelRels: labelRels
          };
          const res = await addModelSceneDataAPi(params);
          if (res.code === 0) {
            this.addDialogVisible = false;
            this.initModelSceneList();
            // 成功
            this.$message.success("新增成功！");
          } else {
            try {
              this.$message.warning(JSON.parse(res.msg).message)
            } catch {
              this.$message.warning(res.msg);
            }
          }
        });
      },
      async showEditDialog(data) {
        this.editForm = JSON.parse(JSON.stringify(data));

        this.initLabels(this.editForm.modelId);
        this.editForm.labelRels = data.labelRels.map(item => item.labelValue) || [];
        this.editDialogVisible = true;
      },
      editClosed() {
        this.$refs.editFormRef.resetFields();
      },
      editModelSceneInfo() {
        this.$refs.editFormRef.validate(async (valid) => {
          if (!valid) return;
          const labelRels = [];
          const than = this;
          // 将选中的ID数组转换为对象数组
          this.editForm.labelRels.forEach(function (value) {
            var label = than.labelList.find(function (item) {
              return item.labelValue === value;
            });

            if (label) {
              labelRels.push({
                labelValue: label.labelValue,
                labelName: label.labelName
              });
            }
          });
          //通过URLSearchParams封装请求数据
          let params = {
            id: this.editForm.id,
            name: this.editForm.name,
            modelId: this.editForm.modelId,
            remark: this.editForm.remark,
            orderIndex: this.editForm.orderIndex,
            labelRels: labelRels
          };
          const res = await updateModelSceneDataApi(params);
          if (res.code === 0) {
            this.editDialogVisible = false;
            this.initModelSceneList();
            this.$message.success(res.msg);
          } else {
            this.$message.warning(res.msg);
          }
        });
      },
      // 根据id删除对应的模型场景信息
      async removeUserById(id) {
        // 询问用户是否删除用户
        const confirmRusult = await this.$confirm('此操作将永久删除该模型, 是否继续?', '永久删除该用户', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }).catch((err) => err);
        // 用户取消了删除,则返回字符串 cancel
        if (confirmRusult !== 'confirm') {
          return this.$message.info('已经取消了删除');
        }
        const params = [id];
        const res = await deleteModelSceneDataApi(params);
        if (res.code === 0) {
          this.$message.success('删除成功');
          this.initModelSceneList();
        } else {
          this.$message.warning('删除失败');
        }
      },

    }
  };
</script>

<style scoped>
  * {
    font-size: 14px;
  }

  /*  组件布局*/
  .model-scene-info {
    margin: 0;
    padding: 0;
    background-color: #edf0f7 !important;
    color: #333;
    font-size: 14px;
    line-height: 1.5;
  }

  /*  表头面包屑*/
  .gt-breadcrumb-box {
    height: 40px;
    line-height: 40px;
    background-color: #fff;
    z-index: 9999;
    box-sizing: border-box;
    border-left: 1px solid #dcdcdc;
  }

  .gt-breadcrumb-box .icon-geoai-manage {
    font-size: 20px;
    color: rgb(43, 179, 244);
    margin-right: 6px;
  }

  .gt-current-position {
    margin-left: 5px;
    font-size: 18px;
    font-weight: 700;
  }

  .gt-current-position span {
    margin: 0 10px;
    color: #999;
  }

  /*  内容*/
  .gt-breadcrumb-cnt {
    margin-top: 8px;
    padding: 10px;
    height: calc(100% - 48px);
    width: 100%;
    background-color: #fff;
  }

  .el-table {
    margin-top: 15px;
  }

  .el-switch {
    height: 25px !important;
  }

  .box-card {
    height: 100%;
    position: relative;
  }

  .el-card__body,
  .el-main {
    padding: 20px;
    position: relative;
  }

  .el-pagination {
    position: absolute;
    bottom: 10px;
    right: 30px;
    height: 6%;
  }

  ::v-deep(.el-breadcrumb) {
    height: 40px;
    /*变成弹性盒模型*/
    display: flex;
    /*在中间*/
    align-items: center;
    margin-left: 10px;
    margin-bottom: 10px;
  }

  ::v-deep(.el-switch__core) {
    width: 54px !important;
    height: 24px;
    border-radius: 100px;
    border: none;
  }

  ::v-deep(.el-switch__core::after) {
    width: 20px;
    height: 20px;
    top: 2px;
  }

  ::v-deep(.el-switch.is-checked .el-switch__core::after) {
    margin-left: -21px;
  }

  /*关闭时文字位置设置*/
  ::v-deep(.el-switch__label--right) {
    position: absolute;
    z-index: 1;
    right: 6px;
    margin-left: 0px;
    color: rgba(255, 255, 255, 0.9019607843137255);
  }

  span {
    font-size: 12px;
  }

  /* 激活时另一个文字消失 */
  ::v-deep(.el-switch__label.is-active) {
    display: none;
  }

  /*开启时文字位置设置*/
  ::v-deep(.el-switch__label--left) {
    position: absolute;
    z-index: 1;
    left: 5px;
    margin-right: 0px;
    color: rgba(255, 255, 255, 0.9019607843137255);
  }

  span {
    font-size: 12px;
  }

  ::v-deep(.el-card__body) {
    padding-top: 8px;
    height: 100%;
  }

  .bread-crumb {
    height: 6%;
  }

  .add {
    height: 5%;
  }

  ::v-deep .el-input__inner {
    color: #606266;
  }
</style>
