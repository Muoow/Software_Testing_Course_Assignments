<script setup>
import { ref, onMounted, computed } from 'vue';
import { Download } from '@element-plus/icons-vue'
import { saveAs } from 'file-saver'

// Reactive State
const fileList = ref([]);
const selectedFile = ref('');
const fileType = ref('requirement');
const aiModels = ref([]);
const selectedAi = ref('');
const userRequirement = ref('');
const testCasesData = ref(null);
const uploadFile = ref(null);
const uploadIfExists = ref('reject');
const loading = ref(false);
const API_BASE = ref('http://localhost:8000');

// Computed
const formattedTestCases = computed(() => {
  if (!testCasesData.value) return 'No test cases generated yet.';
  return JSON.stringify(testCasesData.value, null, 2);
});

const downloadTestCasesJson = () => {
  if (!testCasesData.value) {
    showNotification('No test case data available for download', 'warning');
    return
  }

  const jsonStr = JSON.stringify(testCasesData.value, null, 2)
  const blob = new Blob([jsonStr], { type: 'application/json;charset=utf-8' })
  const filename = testCasesData.value.filename?.replace(/\.\w+$/, '') || 'test-cases'

  saveAs(blob, `${filename}-test-cases.json`)
  showNotification('Test cases JSON file downloaded successfully', 'success');
}

// API Functions
const fetchFileList = async () => {
  try {
    const res = await fetch(`${API_BASE.value}/list-files`);
    const data = await res.json();
    if (data.status === 'success') fileList.value = data.files;
    else showNotification('Failed to load file list', 'error');
  } catch (error) {
    showNotification('Network error', 'error');
  }
};

const fetchAiModels = async () => {
  try {
    const res = await fetch(`${API_BASE.value}/supported-ais`);
    const data = await res.json();
    if (data.status === 'success') {
      aiModels.value = data.data;
      if (aiModels.value.length) selectedAi.value = aiModels.value[0].key;
    } else showNotification('Failed to load AI models', 'error');
  } catch (error) {
    showNotification('Network error', 'error');
  }
};

const handleFileUpload = async () => {
  if (!uploadFile.value) {
    showNotification('Please select a file', 'warning');
    return;
  }
  const formData = new FormData();
  formData.append('file', uploadFile.value);
  formData.append('if_exists', uploadIfExists.value);

  try {
    const res = await fetch(`${API_BASE.value}/upload`, { method: 'POST', body: formData });
    const data = await res.json();
    if (res.ok) {
      showNotification(`File ${data.action_taken} successfully`, 'success');
      fetchFileList();
      uploadFile.value = null;
    } else showNotification(data.detail || 'Upload failed', 'error');
  } catch (error) {
    showNotification('Upload failed', 'error');
  }
};

const generateTestCases = async () => {
  if (!selectedFile.value) return showNotification('Select a file first', 'warning');
  if (!selectedAi.value) return showNotification('Select an AI model', 'warning');
  if (!userRequirement.value.trim()) return showNotification('Enter requirements', 'warning');

  loading.value = true;
  try {
    const res = await fetch(`${API_BASE.value}/generate-test-case`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        filename: selectedFile.value,
        ai_name: selectedAi.value,
        user_requirement: userRequirement.value
      })
    });
    const data = await res.json();
    if (res.ok && data.status === 'success') {
      testCasesData.value = data;
      showNotification('Test cases generated', 'success');
    } else showNotification(data.detail || 'Generation failed', 'error');
  } catch (error) {
    showNotification('Generation failed', 'error');
  } finally {
    loading.value = false;
  }
};

// Utils
const showNotification = (message, type = 'info') => {
  const notification = document.createElement('div');
  notification.className = `notification notification-${type}`;
  notification.textContent = message;
  document.body.appendChild(notification);
  setTimeout(() => {
    notification.classList.add('fade-out');
    setTimeout(() => document.body.removeChild(notification), 500);
  }, 3000);
};

// Init
onMounted(() => {
  fetchFileList();
  fetchAiModels();
});
</script>

<template>
  <div class="test-case-generator">
    <!-- Left Sidebar -->
    <aside class="sidebar">
      <div class="file-list-container">
        <h3 class="section-title">File List</h3>
        <div class="file-list">
          <div v-if="fileList.length === 0" class="empty-state">No uploaded files yet</div>
          <div
              v-for="file in fileList"
              :key="file.filename"
              class="file-item"
              :class="{ selected: selectedFile === file.filename }"
              @click="selectedFile = file.filename"
          >
            <div class="file-details">
              <div class="filename">{{ file.filename }}</div>
              <div class="file-meta">
                <span>Size: {{ (file.file_size / 1024).toFixed(2) }} KB</span>
                <span>Modified: {{ file.last_modified }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="file-upload-container">
        <h3 class="section-title">File Upload</h3>
        <div class="upload-form">
          <div class="form-group">
            <label class="form-label">Select File</label>
            <input
                type="file"
                @change="uploadFile = $event.target.files[0]"
                class="file-input"
            >
          </div>

          <div class="form-group">
            <label class="form-label">If File Exists</label>
            <div class="radio-group">
              <label class="radio-option">
                <input type="radio" value="reject" v-model="uploadIfExists">
                Reject Upload
              </label>
              <label class="radio-option">
                <input type="radio" value="overwrite" v-model="uploadIfExists">
                Overwrite File
              </label>
            </div>
          </div>

          <button @click="handleFileUpload" class="btn primary-btn upload-btn">
            Upload File
          </button>
        </div>
      </div>
    </aside>

    <!-- Main Content -->
    <main class="main-content">
      <div class="test-case-display">
        <div class="section-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
          <h3 class="section-title">Generated Test Cases</h3>
          <el-button
              type="primary"
              :icon="Download"
              @click="downloadTestCasesJson"
              v-if="testCasesData"
              size="default"
          >
            Download JSON
          </el-button>
        </div>

        <div class="test-case-content">
          <el-table
              v-if="testCasesData?.test_cases?.length"
              :data="testCasesData.test_cases"
              border
              stripe
              style="width: 100%;"
          >
            <el-table-column prop="case_id" label="Case ID" width="100" />
            <el-table-column prop="case_name" label="Case Name" min-width="180" />
            <el-table-column prop="module" label="Module" width="130" />
            <el-table-column prop="priority" label="Priority" width="100" />
            <el-table-column prop="precondition" label="Precondition" min-width="180" />

            <el-table-column label="Test Steps" min-width="240">
              <template #default="scope">
                <div v-for="(step, idx) in scope.row.test_steps" :key="idx">
                  {{ step.step_no }}. {{ step.step_desc }}
                </div>
              </template>
            </el-table-column>

            <el-table-column prop="expected_result" label="Expected Result" min-width="200" />
            <el-table-column prop="api_method" label="API Method" width="110" />
            <el-table-column prop="api_url" label="API URL" min-width="180" />

            <el-table-column label="Request Body" min-width="200">
              <template #default="scope">
                <pre style="margin: 0; font-size: 12px; white-space: pre-wrap;">{{ scope.row.request_body }}</pre>
              </template>
            </el-table-column>

            <el-table-column prop="description" label="Description" min-width="180" />
          </el-table>

          <div v-else class="empty-state" style="padding: 40px; text-align: center; color: #888;">
            No test cases generated yet.
          </div>
        </div>
      </div>

      <div class="generation-controls">
        <h3 class="section-title">AI Generation Settings</h3>
        <div class="control-form">
          <div class="form-group row-layout">
            <div class="form-item">
              <label class="form-label">Select AI Model</label>
              <select v-model="selectedAi" class="form-select">
                <option v-for="model in aiModels" :key="model.key" :value="model.key">
                  {{ model.name }} ({{ model.model }})
                </option>
              </select>
            </div>
            <div class="form-item">
              <label class="form-label">File Type</label>
              <div class="radio-group">
                <label class="radio-option">
                  <input type="radio" v-model="fileType" value="requirement">
                  Requirement Document
                </label>
                <label class="radio-option">
                  <input type="radio" v-model="fileType" value="source_code">
                  Source Code
                </label>
              </div>
            </div>
          </div>

          <div class="form-group">
            <label class="form-label">Test Case Requirements</label>
            <el-input
                v-model="userRequirement"
                type="textarea"
                :rows="4"
                placeholder="Enter your custom test case requirements"
                resize="both"
            />
          </div>

          <button
              @click="generateTestCases"
              class="btn primary-btn generate-btn"
              :disabled="loading"
          >
            <span v-if="!loading">Generate Test Cases</span>
            <span v-if="loading">Generating...</span>
          </button>
        </div>
      </div>
    </main>
  </div>
</template>

<!-- Global Notification Styles (FIXED) -->
<style>
.notification {
  position: fixed;
  top: 20px;
  right: 20px;
  padding: 12px 20px;
  border-radius: 8px;
  color: white;
  font-weight: 500;
  z-index: 9999;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}
.notification-success { background-color: #1677ff; }
.notification-error { background-color: #ff4d4f; }
.notification-warning { background-color: #faad14; }
.notification-info { background-color: #4096ff; }
.fade-out { opacity: 0; transform: translateX(20px); }
</style>

<!-- Scoped Component Styles -->
<style scoped>
.test-case-generator {
  display: flex;
  height: 98vh;
  width: 100%;
  background-color: #f5f7fa;
  font-family: 'Inter', sans-serif;
  color: #1f2937;
}

.sidebar {
  width: 260px;
  background-color: #fff;
  border-right: 1px solid #e5e7eb;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 32px;
  overflow-y: auto;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #111827;
  margin: 0 0 16px 0;
  padding-bottom: 8px;
  border-bottom: 2px solid #e6f7ff;
}

.file-list-container { flex: 1; }
.file-list { display: flex; flex-direction: column; gap: 12px; }

.file-item {
  display: flex;
  align-items: center;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: 0.2s;
}
.file-item.selected { background-color: #e6f7ff; border: 1px solid #91d5ff; }
.file-item:hover { background-color: #f9fafb; }

.file-radio:checked + .radio-indicator {
  border-color: #1677ff;
  background-color: #1677ff;
}
.file-radio:checked + .radio-indicator::after {
  content: '';
  position: absolute;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #fff;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

.file-details { flex: 1; }
.filename { font-weight: 500; font-size: 14px; margin-bottom: 4px; }
.file-meta { font-size: 12px; color: #64748b; display: flex; flex-direction: column; gap: 2px; }
.empty-state { padding: 24px; text-align: center; color: #94a3b8; background: #f8fafc; border-radius: 8px; }

.upload-form { display: flex; flex-direction: column; gap: 16px; }
.form-group { display: flex; flex-direction: column; gap: 8px; }
.form-label { font-size: 14px; font-weight: 500; color: #334155; }

.form-group.row-layout {
  flex-direction: row;
  gap: 20px;
}

.form-group.row-layout .form-item {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 16px;
}

.file-input {
  padding: 8px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  transition: border-color 0.2s;
}
.file-input:focus { outline: none; border-color: #1677ff; box-shadow: 0 0 0 2px rgba(22,119,255,0.2); }

.radio-group { display: flex; gap: 16px; }
.radio-option { display: flex; align-items: center; gap: 6px; font-size: 14px; color: #475569; }

.main-content {
  flex: 1;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 24px;
  overflow-y: hidden;
}

.test-case-display {
  flex: 1;
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  display: flex;
  flex-direction: column;
  overflow: hidden
}
.test-case-content { flex: 1; overflow-y: auto; }

.generation-controls {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.control-form { display: flex; flex-direction: column; gap: 16px; }

.form-select, .form-textarea {
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  transition: border-color 0.2s;
}
.form-select:focus, .form-textarea:focus {
  outline: none;
  border-color: #1677ff;
  box-shadow: 0 0 0 2px rgba(22,119,255,0.2);
}

.btn {
  padding: 12px;
  border-radius: 6px;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: 0.2s;
  border: none;
  width: 100%;
}
.primary-btn { background: #1677ff; color: #fff; }
.primary-btn:hover { background: #0958d9; }
.primary-btn:disabled { background: #94a3b8; cursor: not-allowed; }
</style>