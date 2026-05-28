<!-- Employee Dashboard - Vue.js Component -->
<template>
  <div class="employee-dashboard">
    <header class="header">
      <h1>Maintenance Dashboard</h1>
      <div class="user-info">
        <span>{{ currentUser }}</span>
        <button @click="logout">Logout</button>
      </div>
    </header>

    <div class="container">
      <!-- Assigned Blocks Section -->
      <section class="assigned-blocks">
        <h2>My Assigned Blocks</h2>
        <div v-if="loading" class="loading">Loading...</div>
        <div v-else class="blocks-grid">
          <div
            v-for="block in assignedBlocks"
            :key="block.id"
            class="block-card"
            @click="selectBlock(block)"
            :class="{ active: selectedBlock?.id === block.id }"
          >
            <h3>{{ block.house_name }} Block {{ block.block_number }}</h3>
            <p>{{ block.unit_count }} Units</p>
          </div>
        </div>
      </section>

      <!-- Units in Selected Block -->
      <section v-if="selectedBlock" class="units-section">
        <h2>Units in {{ selectedBlock.house_name }} Block {{ selectedBlock.block_number }}</h2>
        <div class="units-list">
          <div
            v-for="unit in unitsInBlock"
            :key="unit.id"
            class="unit-card"
            @click="selectUnit(unit)"
          >
            <h4>Unit {{ unit.unit_number }}</h4>
            <p class="unit-type">{{ unit.unit_type_display }}</p>
            <p class="unit-status" :class="unit.status.toLowerCase()">{{ unit.status }}</p>
            <span class="item-count">{{ unit.inventory_items.length }} Items</span>
          </div>
        </div>
      </section>

      <!-- Unit Inventory Details -->
      <section v-if="selectedUnit" class="inventory-section">
        <h2>
          Unit {{ selectedUnit.unit_number }}
          <span class="unit-label">{{ selectedUnit.unit_type_display }}</span>
        </h2>

        <!-- Room/Location Tabs -->
        <div class="location-tabs">
          <button
            @click="selectedLocation = 'A'"
            :class="{ active: selectedLocation === 'A' }"
            class="tab-btn"
          >
            {{ selectedUnit.unit_type_display === 'Shared Unit (A & B)' ? 'Room A' : 'Bedroom' }}
          </button>
          <button
            v-if="selectedUnit.unit_type_display === 'Shared Unit (A & B)'"
            @click="selectedLocation = 'B'"
            :class="{ active: selectedLocation === 'B' }"
            class="tab-btn"
          >
            Room B
          </button>
          <button
            v-if="selectedUnit.unit_type_display === 'Shared Unit (A & B)'"
            @click="selectedLocation = 'K'"
            :class="{ active: selectedLocation === 'K' }"
            class="tab-btn"
          >
            Shared Kitchen
          </button>
        </div>

        <!-- Inventory Items -->
        <div class="inventory-items">
          <table>
            <thead>
              <tr>
                <th>Item</th>
                <th>Serial #</th>
                <th>Status</th>
                <th>Last Checked</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in getLocationItems()" :key="item.id" class="item-row">
                <td>{{ item.part_name }}</td>
                <td>{{ item.serial_number || '-' }}</td>
                <td>
                  <span class="status-badge" :class="item.status.toLowerCase()">
                    {{ item.status_display }}
                  </span>
                </td>
                <td>{{ formatDate(item.last_checked) }}</td>
                <td class="actions">
                  <button
                    v-if="item.status !== 'OK'"
                    @click="markAsOk(item)"
                    class="btn-ok"
                    title="Mark OK"
                  >
                    ✓
                  </button>
                  <button
                    @click="markAsMissing(item)"
                    class="btn-missing"
                    title="Mark Missing"
                  >
                    ✗
                  </button>
                  <button
                    @click="markForRepair(item)"
                    class="btn-repair"
                    title="Mark for Repair"
                  >
                    🔧
                  </button>
                  <button
                    @click="removeItem(item)"
                    class="btn-remove"
                    title="Remove Item"
                  >
                    🗑
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Add New Item Form -->
        <div class="add-item-section">
          <h3>Add New Item</h3>
          <form @submit.prevent="submitAddItem" class="add-item-form">
            <select v-model="newItem.part_id" required>
              <option value="">Select Item Type...</option>
              <option v-for="part in availableParts" :key="part.id" :value="part.id">
                {{ part.name }}
              </option>
            </select>

            <input
              v-model="newItem.serial_number"
              type="text"
              placeholder="Serial Number (optional)"
            />

            <textarea
              v-model="newItem.notes"
              placeholder="Notes (optional)"
              rows="2"
            ></textarea>

            <button type="submit" class="btn-submit">Add Item</button>
          </form>
        </div>

        <!-- Maintenance History -->
        <div class="history-section">
          <h3>Recent Activity</h3>
          <div class="history-list">
            <div
              v-for="log in maintenanceLogs"
              :key="log.id"
              class="history-item"
              :class="log.action.toLowerCase()"
            >
              <span class="action">{{ log.action_display }}</span>
              <span class="part">{{ log.part_name }}</span>
              <span class="timestamp">{{ formatDate(log.timestamp) }}</span>
              <span class="employee">{{ log.employee_name }}</span>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'EmployeeDashboard',
  data() {
    return {
      token: localStorage.getItem('token') || '',
      currentUser: localStorage.getItem('username') || 'Staff',
      loading: false,
      assignedBlocks: [],
      selectedBlock: null,
      unitsInBlock: [],
      selectedUnit: null,
      selectedLocation: 'A',
      availableParts: [],
      maintenanceLogs: [],
      newItem: {
        part_id: '',
        serial_number: '',
        notes: '',
      },
    };
  },
  computed: {
    api() {
      return axios.create({
        baseURL: process.env.VUE_APP_API_URL || 'http://localhost:8000/api/residence/',
        headers: {
          Authorization: `Token ${this.token}`,
          'Content-Type': 'application/json',
        },
      });
    },
  },
  mounted() {
    this.loadDashboard();
    this.loadAvailableParts();
  },
  methods: {
    async loadDashboard() {
      this.loading = true;
      try {
        const response = await this.api.get('employee-dashboard/my_assignments/');
        this.assignedBlocks = response.data.assigned_blocks;
      } catch (error) {
        console.error('Error loading dashboard:', error);
        alert('Failed to load dashboard');
      } finally {
        this.loading = false;
      }
    },
    async loadAvailableParts() {
      try {
        const response = await this.api.get('inventory/');
        const parts = new Map();
        response.data.forEach(item => {
          if (!parts.has(item.part)) {
            parts.set(item.part, {
              id: item.part,
              name: item.part_name,
            });
          }
        });
        this.availableParts = Array.from(parts.values());
      } catch (error) {
        console.error('Error loading parts:', error);
      }
    },
    async selectBlock(block) {
      this.selectedBlock = block;
      this.selectedUnit = null;
      this.loading = true;
      try {
        const response = await this.api.get(`blocks/${block.id}/`);
        this.unitsInBlock = response.data.units || [];
      } catch (error) {
        console.error('Error loading units:', error);
      } finally {
        this.loading = false;
      }
    },
    selectUnit(unit) {
      this.selectedUnit = unit;
      this.selectedLocation = 'A';
      this.loadMaintenanceLogs();
    },
    async loadMaintenanceLogs() {
      try {
        const response = await this.api.get(`maintenance-logs/?unit=${this.selectedUnit.id}`);
        this.maintenanceLogs = response.data.slice(0, 20);
      } catch (error) {
        console.error('Error loading logs:', error);
      }
    },
    getLocationItems() {
      if (!this.selectedUnit) return [];

      const locationMap = {
        A: this.selectedUnit.location_a,
        B: this.selectedUnit.location_b,
        K: this.selectedUnit.location_kitchen,
      };

      const locationName = locationMap[this.selectedLocation];
      return this.selectedUnit.inventory_items.filter(item => item.location_name === locationName);
    },
    async markAsOk(item) {
      try {
        await this.api.post(`inventory/${item.id}/mark_as_ok/`);
        item.status = 'OK';
        this.showNotification('Item marked as OK');
        this.loadMaintenanceLogs();
      } catch (error) {
        alert('Error: ' + error.message);
      }
    },
    async markAsMissing(item) {
      try {
        await this.api.post(`inventory/${item.id}/mark_as_missing/`);
        item.status = 'MISSING';
        this.showNotification('Item marked as missing');
        this.loadMaintenanceLogs();
      } catch (error) {
        alert('Error: ' + error.message);
      }
    },
    async markForRepair(item) {
      const notes = prompt('Enter repair notes:');
      if (notes === null) return;

      try {
        await this.api.post(`inventory/${item.id}/mark_for_repair/`, { notes });
        item.status = 'NEEDS_REPAIR';
        this.showNotification('Item marked for repair');
        this.loadMaintenanceLogs();
      } catch (error) {
        alert('Error: ' + error.message);
      }
    },
    async removeItem(item) {
      if (!confirm('Are you sure you want to remove this item?')) return;

      try {
        await this.api.post(`inventory/${item.id}/remove_item/`);
        const index = this.selectedUnit.inventory_items.findIndex(i => i.id === item.id);
        if (index > -1) {
          this.selectedUnit.inventory_items.splice(index, 1);
        }
        this.showNotification('Item removed');
        this.loadMaintenanceLogs();
      } catch (error) {
        alert('Error: ' + error.message);
      }
    },
    async submitAddItem() {
      if (!this.newItem.part_id) {
        alert('Please select an item type');
        return;
      }

      try {
        const response = await this.api.post(`units/${this.selectedUnit.id}/add_item/`, {
          part_id: this.newItem.part_id,
          location_id: this.selectedUnit[`location_${this.selectedLocation}`],
          serial_number: this.newItem.serial_number,
          notes: this.newItem.notes,
        });

        this.selectedUnit.inventory_items.push(response.data);
        this.newItem = { part_id: '', serial_number: '', notes: '' };
        this.showNotification('Item added successfully');
        this.loadMaintenanceLogs();
      } catch (error) {
        alert('Error adding item: ' + error.message);
      }
    },
    async logout() {
      localStorage.clear();
      window.location.href = '/login';
    },
    formatDate(date) {
      if (!date) return '-';
      return new Date(date).toLocaleDateString();
    },
    showNotification(message) {
      alert(message); // Replace with toast notification in production
    },
  },
};
</script>

<style scoped>
.employee-dashboard {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #f5f5f5;
  min-height: 100vh;
}

.header {
  background: #2c3e50;
  color: white;
  padding: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.user-info {
  display: flex;
  gap: 10px;
  align-items: center;
}

.container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
}

section {
  margin-bottom: 30px;
}

section h2 {
  color: #2c3e50;
  margin-bottom: 15px;
  border-bottom: 2px solid #3498db;
  padding-bottom: 10px;
}

section h3 {
  color: #34495e;
  margin-bottom: 10px;
}

.blocks-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 15px;
}

.block-card {
  background: white;
  padding: 15px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  border: 2px solid #ecf0f1;
}

.block-card:hover,
.block-card.active {
  border-color: #3498db;
  box-shadow: 0 4px 12px rgba(52, 152, 219, 0.2);
}

.units-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 10px;
}

.unit-card {
  background: white;
  padding: 12px;
  border-radius: 6px;
  border: 1px solid #ecf0f1;
  cursor: pointer;
  transition: all 0.2s;
}

.unit-card:hover {
  border-color: #3498db;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.unit-type {
  font-size: 0.85em;
  color: #7f8c8d;
  margin: 5px 0;
}

.unit-status {
  font-weight: bold;
  font-size: 0.9em;
  margin: 5px 0;
}

.unit-status.occupied {
  color: #27ae60;
}

.unit-status.vacant {
  color: #e74c3c;
}

.item-count {
  display: inline-block;
  background: #ecf0f1;
  padding: 3px 8px;
  border-radius: 12px;
  font-size: 0.8em;
}

.location-tabs {
  display: flex;
  gap: 10px;
  margin: 15px 0;
}

.tab-btn {
  padding: 8px 15px;
  border: 2px solid #bdc3c7;
  background: white;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.tab-btn.active {
  background: #3498db;
  color: white;
  border-color: #3498db;
}

.inventory-items {
  background: white;
  border-radius: 8px;
  overflow-x: auto;
  margin: 15px 0;
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead {
  background: #ecf0f1;
}

th,
td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #bdc3c7;
}

th {
  font-weight: bold;
  color: #2c3e50;
}

.status-badge {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.85em;
  font-weight: bold;
}

.status-badge.ok {
  background: #d4edda;
  color: #155724;
}

.status-badge.needs_repair {
  background: #fff3cd;
  color: #856404;
}

.status-badge.missing {
  background: #f8d7da;
  color: #721c24;
}

.actions {
  display: flex;
  gap: 5px;
}

.actions button {
  padding: 4px 8px;
  font-size: 1em;
  border: 1px solid #bdc3c7;
  background: white;
  cursor: pointer;
  border-radius: 3px;
  transition: all 0.2s;
}

.actions button:hover {
  background: #ecf0f1;
}

.btn-ok {
  color: #27ae60;
}

.btn-missing {
  color: #e74c3c;
}

.btn-repair {
  color: #f39c12;
}

.btn-remove {
  color: #c0392b;
}

.add-item-section {
  background: white;
  padding: 15px;
  border-radius: 8px;
  margin: 15px 0;
}

.add-item-form {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-top: 10px;
}

.add-item-form textarea {
  grid-column: 1 / -1;
}

select,
input,
textarea {
  padding: 8px;
  border: 1px solid #bdc3c7;
  border-radius: 4px;
  font-family: inherit;
}

.btn-submit {
  grid-column: 1 / -1;
  padding: 10px 20px;
  background: #27ae60;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: bold;
  transition: background 0.2s;
}

.btn-submit:hover {
  background: #229954;
}

.history-section {
  background: white;
  padding: 15px;
  border-radius: 8px;
  margin-top: 15px;
}

.history-list {
  max-height: 300px;
  overflow-y: auto;
}

.history-item {
  padding: 10px;
  border-left: 4px solid #bdc3c7;
  margin-bottom: 8px;
  font-size: 0.9em;
  display: flex;
  gap: 10px;
  align-items: center;
}

.history-item.added {
  border-color: #27ae60;
}

.history-item.repaired {
  border-color: #f39c12;
}

.history-item.removed {
  border-color: #e74c3c;
}

.action {
  font-weight: bold;
  min-width: 80px;
}

.part {
  flex: 1;
}

.timestamp,
.employee {
  font-size: 0.85em;
  color: #7f8c8d;
}

.loading {
  text-align: center;
  padding: 40px;
  color: #7f8c8d;
}

button {
  font-family: inherit;
}

button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
