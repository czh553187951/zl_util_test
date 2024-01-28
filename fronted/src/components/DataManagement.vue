<template>
  <div>
    <h1>Data Management Page</h1>
    <el-button type="primary" @click="showAddDialog">Add Data</el-button>
    <el-table :data="dataList" style="width: 100%">
      <el-table-column prop="name" label="Name"></el-table-column>
      <el-table-column prop="age" label="Age"></el-table-column>
      <el-table-column label="Actions">
        <template #default="scope">
          <el-button type="primary" size="mini" @click="showEditDialog(scope.row)">Edit</el-button>
          <el-button type="danger" size="mini" @click="deleteData(scope.row)">Delete</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- Add Dialog -->
    <el-dialog title="Add Data" :visible.sync="addDialogVisible">
      <el-form :model="addForm" label-width="80px">
        <el-form-item label="Name">
          <el-input v-model="addForm.name"></el-input>
        </el-form-item>
        <el-form-item label="Age">
          <el-input v-model="addForm.age"></el-input>
        </el-form-item>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="addDialogVisible = false">Cancel</el-button>
        <el-button type="primary" @click="addData">Add</el-button>
      </div>
    </el-dialog>

    <!-- Edit Dialog -->
    <el-dialog title="Edit Data" :visible.sync="editDialogVisible">
      <el-form :model="editForm" label-width="80px">
        <el-form-item label="Name">
          <el-input v-model="editForm.name"></el-input>
        </el-form-item>
        <el-form-item label="Age">
          <el-input v-model="editForm.age"></el-input>
        </el-form-item>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="editDialogVisible = false">Cancel</el-button>
        <el-button type="primary" @click="saveEditedData">Save</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script>
export default {
  data() {
    return {
      dataList: [
        { id: 1, name: 'John', age: 25 },
        { id: 2, name: 'Jane', age: 30 },
        // Other data items
      ],
      addDialogVisible: false,
      addForm: {
        name: '',
        age: ''
      },
      editDialogVisible: false,
      editForm: {
        id: '',
        name: '',
        age: ''
      }
    };
  },
  methods: {
    showAddDialog() {
      this.addDialogVisible = true;
    },
    addData() {
      // Perform API call to add data
      // After success, update dataList and close dialog
      const newData = {
        id: this.dataList.length + 1,
        name: this.addForm.name,
        age: this.addForm.age
      };
      this.dataList.push(newData);
      this.addForm.name = '';
      this.addForm.age = '';
      this.addDialogVisible = false;
    },
    showEditDialog(row) {
      this.editForm.id = row.id;
      this.editForm.name = row.name;
      this.editForm.age = row.age;
      this.editDialogVisible = true;
    },
    saveEditedData() {
      // Perform API call to update data
      // After success, update dataList and close dialog
      const editedData = {
        id: this.editForm.id,
        name: this.editForm.name,
        age: this.editForm.age
      };
      const index = this.dataList.findIndex((item) => item.id === editedData.id);
      if (index !== -1) {
        this.dataList.splice(index, 1, editedData);
      }
      this.editDialogVisible = false;
    },
    deleteData(row) {
      // Perform API call to delete data
      // After success, remove item from dataList
      const index = this.dataList.findIndex((item) => item.id === row.id);
      if (index !== -1) {
        this.dataList.splice(index, 1);
      }
    }
  }
};
</script>

<style>
/* 样式 */
</style>