<template>
  <div>
    <el-table :data="dataList" style="width: 100%">
      <!-- 表格列定义 -->
      <el-table-column prop="name" label="姓名"></el-table-column>
      <el-table-column prop="age" label="年龄"></el-table-column>
      <!-- 其他列... -->
      <el-table-column label="操作">
        <template #default="scope">
          <!-- 编辑按钮 -->
          <el-button type="primary" @click="editItem(scope.row)">编辑</el-button>
          <!-- 删除按钮 -->
          <el-button type="danger" @click="deleteItem(scope.row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog title="编辑" :visible.sync="editDialogVisible">
      <!-- 编辑表单 -->
      <el-form :model="editForm">
        <!-- 表单项 -->
        <el-form-item label="姓名">
          <el-input v-model="editForm.name"></el-input>
        </el-form-item>
        <el-form-item label="年龄">
          <el-input v-model="editForm.age"></el-input>
        </el-form-item>
        <!-- 其他表单项... -->
      </el-form>
      <div slot="footer">
        <!-- 保存按钮 -->
        <el-button type="primary" @click="saveItem">保存</el-button>
        <!-- 取消按钮 -->
        <el-button @click="cancelEdit">取消</el-button>
      </div>
    </el-dialog>

    <!-- 添加按钮 -->
    <el-button type="primary" @click="openAddDialog">添加</el-button>
  </div>
</template>

<script>
export default {
  data() {
    return {
      dataList: [], // 数据列表
      editDialogVisible: false, // 编辑对话框可见性
      editForm: { // 编辑表单数据
        name: '',
        age: ''
      }
    };
  },
  methods: {
    editItem(row) {
      // 编辑某一行数据
      // 将该行数据填充到编辑表单中
      this.editForm = { ...row };
      // 打开编辑对话框
      this.editDialogVisible = true;
    },
    deleteItem(row) {
      // 删除某一行数据
      // 根据需求编写删除逻辑
    },
    saveItem() {
      // 保存表单数据
      // 根据需求编写保存逻辑
      // 关闭编辑对话框
      this.editDialogVisible = false;
    },
    cancelEdit() {
      // 取消编辑操作
      // 关闭编辑对话框
      this.editDialogVisible = false;
    },
    openAddDialog() {
      // 打开添加对话框
      // 清空编辑表单数据
      this.editForm = {
        name: '',
        age: ''
      };
      // 打开编辑对话框
      this.editDialogVisible = true;
    }
  }
};
</script>

<style>
/* 在这里编写你的样式代码 */
</style>