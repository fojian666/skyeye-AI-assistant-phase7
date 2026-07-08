<template>
  <div class="se-content-right-body">
      <div class="right-content-header">
        <span class="icon iconfont icon-geoai-grid"></span>
        <span class="title">网格管理</span>
      </div>
      <div class="right-content-body">
        <div class="se-filter-form">
          <!--数据筛选-->
          <el-form :inline="true" size="small" :model="filterInfo" ref="filterInfo">
            <el-form-item>
              <span>所属街道：</span>
              <el-select placeholder="请选择" v-model="filterInfo.street" clearable>
                <el-option v-for="item in streetCollection" :key="item" :label="item" :value="item"></el-option>
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-input type="text" placeholder="请输入网格名称" clearable v-model="filterInfo.gridName"></el-input>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" size="mini" @click="searchGrid">查询</el-button>
              <el-button @click="resetFilter" size="mini" type="info">重置</el-button>
              <el-button @click="deleteGridData" size="mini" type="danger">删除</el-button>
              <el-button type="primary" size="mini" @click="openAddDialog" >新增</el-button>

            </el-form-item>
          </el-form>
        </div>
        <div class="se-data-table">
          <!--网格数据-->
          <el-table
            max-height="100%"
            height="100%"
            :data="gridData"
            stripe
            style="width: 100%"
            border
            @selection-change="handleSelectionChange">
            <el-table-column type="selection" width="55" align="center"></el-table-column>
            <el-table-column prop="grid_id" label="网格编号" align="center"></el-table-column>
            <el-table-column prop="grid_name" label="网格名称" align="center"></el-table-column>
            <el-table-column prop="grid_operator" label="网格员" align="center"></el-table-column>
            <el-table-column prop="street" label="所属街道" align="center"></el-table-column>
            <el-table-column prop="uploader" label="上传人" align="center"></el-table-column>
            <el-table-column prop="count" label="全景点数量（个）" align="center"></el-table-column>
            <el-table-column label="操作" width="200px" align="center">
              <template slot-scope="scope">
                <el-button type="text" size="medium" style="color: blue" @click="download(scope.row)">全景点KML下载</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
        <el-pagination
          background
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
          :current-page="filterInfo.page"
          :page-sizes="[10, 20, 30, 40]"
          :page-size="filterInfo.limit"
          layout="total, sizes,  prev, pager, next, jumper"
          :total="dataCount"
          style="margin-top:15px;text-align:right;"
        >
        </el-pagination>
      </div>
    <!-- 新增网格弹窗 -->
    <el-dialog
      title="新增网格"
      width="600px"
      :visible.sync="addDialogVisible"
      append-to-body
      :close-on-click-modal="false"
      @closed="resetAddDialog"
    >
      <GridAddDialog @success="handleAddSuccess" />
    </el-dialog>
  </div>
</template>

<script>
import {getGridData, deleteGridByIdApi, getDownloadPanoramaPointApi} from '@/api/commonApi';
import axios from 'axios';
// 引入新增弹窗组件
import GridAddDialog from './AddGrid.vue';

export default {
  name: 'GridManagementIndex',
  components: { GridAddDialog }, // 注册组件
  data() {
    return {
      addDialogVisible: false, // 新增弹窗显示隐藏
      selectedGrid: [], //选择的网格数据列表
      filterInfo: {
        street: '',
        gridName: '',
        limit: 10,
        page: 1
      }, //筛选参数
      gridData: [], //网格数据
      dataCount: 0, //数据的总数
      baseUrl: window.config.baseUrl //请求地址
    };
  },
  methods: {
    handleSizeChange(val) {
      // 改变每页展示的数据
      this.filterInfo.limit = val;
      this.filterInfo.page = 1;
      this.getGridList();
    },
    handleCurrentChange(val) {
      // 改变页码
      this.filterInfo.page = val;
      this.getGridList();
    },
    async getGridList() {
      //  获取网格数据
      this.filterInfo.pageIndex = this.filterInfo.page;
      this.filterInfo.pageSize = this.filterInfo.limit;
      const res = await getGridData(this.filterInfo);
      if (res.code !== 0) {
        this.$message.error(res.msg);
        return;
      }
      this.gridData = res.data || [];
      this.dataCount = res.total;
    },
    resetFilter() {
      //重置筛选框
      this.filterInfo.street = '';
      this.filterInfo.gridName = '';
      this.filterInfo.page = 1;
      this.getGridList();
    },
    searchGrid() {
      //搜索数据
      this.filterInfo.page = 1;
      this.getGridList();
    },
    deleteGridData() {
      //删除选择的数据
      if (this.selectedGrid.length === 0) {
        this.$message.warning('请选择要删除的数据');
        return;
      }
      const params = { grid_ids: this.selectedGrid };
      this.$confirm('此操作将永久删除网格数据, 是否继续?', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(async () => {
        const res = await deleteGridByIdApi(params);
        if (res.code === 0) {
          this.$message.success('网格删除成功！');
          this.filterInfo.page = 1;
          await this.getGridList();
        } else {
          this.$message.error(res.msg);
        }
      }).catch(() => {
        this.$message({ type: 'info', message: '已取消删除' });
      });
    },
    handleSelectionChange(val) {
      //选择的网格数据
      this.selectedGrid = val.map((item) => item.grid_id);
    },
    async download(row) {
      //下载全景kml文件
      try {
        const response = await getDownloadPanoramaPointApi(row.kml_path);
        const url = window.URL.createObjectURL(new Blob([response]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', row.grid_name + '.kml');
        document.body.appendChild(link);
        link.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(link);
      } catch (error) {
        console.log(error);
        this.$message.error(error.response?.status ===404 ? '文件未找到':'下载文件时发生错误');
      }
    },
    // 打开新增弹窗
    openAddDialog(){
      this.addDialogVisible = true;
    },
    // 新增成功的回调 - 关闭弹窗+刷新表格
    handleAddSuccess(){
      this.addDialogVisible = false;
      this.$message.success('新增成功，表格已刷新');
      this.getGridList();
    },
    // 弹窗关闭后重置（防止表单缓存数据）
    resetAddDialog(){
      this.addDialogVisible = false;
    }
  },
  created() {
    this.getGridList();
  },
  computed: {
    streetCollection() {
      return [...new Set(this.gridData.map((item) => item.street))]; //获取街道集合
    }
  }
};
</script>

<style lang="scss" scoped>

.border {
  width: 10px;
  height: 100%;
}

.se-data-table {
  margin-top: 20px;
  height: calc(100% - 100px);
}

.se-filter-form .el-form-item {
  margin: 0 30px 0 0;
}

.icon {
  font-size: 24px;
  color: #42b4f2;
  padding-right: 5px;
}

.right-content-body {
  padding: 10px;
  height: calc(100% - 60px);
}


.se-content-right-body {
  width: 100%;
  height: 100%;
  flex-direction: column;
  border-radius: 2px;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.5);
  box-sizing: border-box;
}

.el-pagination {
  bottom: 10px;
  right: 30px;
  margin-right: 0px;
  float: right;
  position: fixed;
}
</style>