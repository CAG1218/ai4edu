<template>
  <el-drawer
    :model-value="modelValue"
    title="图谱协作编辑"
    size="720px"
    destroy-on-close
    @update:model-value="emit('update:modelValue', $event)"
    @open="initialize"
  >
    <el-alert
      :title="directApply ? '你的修改会立即生效' : '学生修改将在教师审核通过后生效'"
      :type="directApply ? 'success' : 'warning'"
      :closable="false"
      show-icon
      class="graph-edit__notice"
    />

    <el-tabs v-model="activeTab">
      <el-tab-pane label="概览" name="overview">
        <el-form label-position="top">
          <el-form-item label="知识点名称">
            <el-input v-model="overview.name" maxlength="200" />
          </el-form-item>
          <el-form-item label="概览描述">
            <el-input v-model="overview.description" type="textarea" :rows="6" maxlength="2000" show-word-limit />
          </el-form-item>
          <el-button type="primary" :loading="saving" @click="saveOverview">保存概览</el-button>
        </el-form>
      </el-tab-pane>

      <el-tab-pane label="关联资源" name="resources">
        <el-radio-group v-model="resourceMode" class="graph-edit__mode">
          <el-radio-button label="file">上传文件</el-radio-button>
          <el-radio-button label="link">网页链接</el-radio-button>
        </el-radio-group>

        <el-form label-position="top">
          <el-form-item label="资源标题">
            <el-input v-model="resourceForm.title" placeholder="请输入资源标题" />
          </el-form-item>
          <el-form-item label="资源说明">
            <el-input v-model="resourceForm.description" type="textarea" :rows="3" />
          </el-form-item>
          <el-form-item v-if="resourceMode === 'file'" label="选择文件">
            <el-upload
              :auto-upload="false"
              :limit="1"
              :on-change="handleFileChange"
              :on-remove="() => (selectedFile = null)"
              accept=".doc,.docx,.pdf,.txt,.md,.rtf,.ppt,.pptx,application/pdf,text/plain"
            >
              <el-button><el-icon><Upload /></el-icon> 选择 Word、PDF、TXT 等文件</el-button>
            </el-upload>
          </el-form-item>
          <el-form-item v-else label="网页地址">
            <el-input v-model="resourceForm.url" placeholder="https://example.com/resource" />
          </el-form-item>
          <el-button type="primary" :loading="saving" @click="saveResource">创建并关联</el-button>
        </el-form>

        <el-divider content-position="left">已关联资源</el-divider>
        <el-table :data="resources" empty-text="暂无关联资源" size="small">
          <el-table-column prop="title" label="名称" min-width="160" />
          <el-table-column prop="resource_type" label="类型" width="90" />
          <el-table-column label="操作" width="150">
            <template #default="{ row }">
              <el-button link type="primary" @click="startEditResource(row)">编辑</el-button>
              <el-button link type="danger" @click="unlinkResource(row)">取消关联</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="关联关系" name="relations">
        <el-form label-position="top">
          <el-form-item label="目标知识点">
            <el-select
              v-model="relationForm.target_id"
              filterable
              remote
              :remote-method="searchTargets"
              :loading="searching"
              placeholder="输入名称搜索知识点"
              style="width: 100%"
            >
              <el-option v-for="item in targetOptions" :key="item.id" :label="`${item.name}（${item.subject || ''}）`" :value="item.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="关系类型">
            <el-select v-model="relationForm.rel_type" style="width: 100%">
              <el-option label="相关知识" value="RELATED" />
              <el-option label="前置知识" value="PREREQUISITE" />
              <el-option label="应用关系" value="APPLICATION" />
            </el-select>
          </el-form-item>
          <el-form-item label="关系说明">
            <el-input v-model="relationForm.label" placeholder="例如：理解本知识点的前置基础" />
          </el-form-item>
          <el-button type="primary" :loading="saving" @click="saveRelationship">构建关联关系</el-button>
        </el-form>
        <el-divider content-position="left">已建立关系</el-divider>
        <el-table :data="relations" empty-text="暂无可编辑关系" size="small">
          <el-table-column prop="target" label="目标节点" min-width="160" />
          <el-table-column prop="label" label="关系说明" min-width="160" />
          <el-table-column prop="type" label="类型" width="120" />
          <el-table-column label="操作" width="80">
            <template #default="{ row }">
              <el-button link type="danger" @click="removeRelationship(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="认知目标" name="cognitive">
        <el-form label-position="top">
          <el-form-item v-for="dimension in cognitiveDimensions" :key="dimension.key" :label="dimension.label">
            <el-slider v-model="cognitive[dimension.key]" show-input :min="0" :max="100" />
          </el-form-item>
          <el-button type="primary" :loading="saving" @click="saveCognitive">保存认知目标</el-button>
        </el-form>
      </el-tab-pane>

      <el-tab-pane label="推荐" name="recommendation">
        <el-form label-position="top">
          <el-form-item label="推荐知识点">
            <el-select
              v-model="recommendationForm.target_id"
              filterable
              remote
              :remote-method="searchTargets"
              :loading="searching"
              placeholder="输入名称搜索知识点"
              style="width: 100%"
            >
              <el-option v-for="item in targetOptions" :key="item.id" :label="`${item.name}（${item.subject || ''}）`" :value="item.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="推荐理由">
            <el-input v-model="recommendationForm.label" type="textarea" :rows="3" />
          </el-form-item>
          <el-button type="primary" :loading="saving" @click="saveRecommendation">添加推荐</el-button>
        </el-form>
        <el-divider content-position="left">人工推荐</el-divider>
        <el-table :data="manualRecommendations" empty-text="暂无人工推荐" size="small">
          <el-table-column prop="name" label="知识点" min-width="180" />
          <el-table-column prop="_recommendation_reason" label="推荐理由" min-width="220" />
          <el-table-column label="操作" width="80">
            <template #default="{ row }">
              <el-button link type="danger" @click="removeRecommendation(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane v-if="canAssignTask" label="布置任务" name="task">
        <el-form label-position="top">
          <el-form-item label="任务名称"><el-input v-model="taskForm.name" /></el-form-item>
          <el-form-item label="任务说明"><el-input v-model="taskForm.description" type="textarea" :rows="4" /></el-form-item>
          <el-form-item label="任务类型">
            <el-select v-model="taskForm.type" style="width: 100%">
              <el-option label="学习" value="learning" />
              <el-option label="复习" value="review" />
              <el-option label="诊断" value="diagnosis" />
            </el-select>
          </el-form-item>
          <el-form-item label="截止时间">
            <el-date-picker v-model="taskForm.due_date" type="datetime" value-format="YYYY-MM-DDTHH:mm:ssZ" style="width: 100%" />
          </el-form-item>
          <el-button type="primary" :loading="saving" @click="saveTask">布置任务</el-button>
        </el-form>
      </el-tab-pane>

      <el-tab-pane :label="canReview ? `待审核（${reviewRequests.length}）` : '我的申请'" name="reviews">
        <el-table :data="reviewRequests" v-loading="loadingReviews" empty-text="暂无待处理申请" size="small">
          <el-table-column prop="change_type" label="修改类型" width="130">
            <template #default="{ row }">{{ changeTypeLabel(row.change_type) }}</template>
          </el-table-column>
          <el-table-column label="修改内容" min-width="260">
            <template #default="{ row }"><pre class="graph-edit__payload">{{ formatPayload(row.payload) }}</pre></template>
          </el-table-column>
          <el-table-column v-if="canReview" label="审核" width="140">
            <template #default="{ row }">
              <el-button link type="success" @click="review(row.id, true)">通过</el-button>
              <el-button link type="danger" @click="review(row.id, false)">驳回</el-button>
            </template>
          </el-table-column>
          <el-table-column v-else prop="status" label="状态" width="90" />
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="resourceEditVisible" title="编辑关联资源" width="520px" append-to-body>
      <el-form label-position="top">
        <el-form-item label="资源标题"><el-input v-model="resourceEdit.title" /></el-form-item>
        <el-form-item label="资源说明"><el-input v-model="resourceEdit.description" type="textarea" :rows="4" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="resourceEditVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveResourceEdit">保存</el-button>
      </template>
    </el-dialog>
  </el-drawer>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload } from '@element-plus/icons-vue'
import type { UploadFile } from 'element-plus'
import { graphApi } from '@/services/graph'
import type { GraphChangeRequest, GraphLink, KnowledgeNode, NodeTask } from '@/services/graph'
import { resourceApi } from '@/services/resource'

interface LinkedResource {
  id: string | number
  title: string
  description?: string
  resource_type?: string
  url?: string
  file_size?: number
}

const props = defineProps<{
  modelValue: boolean
  node: KnowledgeNode
  initialTab?: string
  directApply: boolean
  canReview: boolean
  canAssignTask: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  changed: []
}>()

const activeTab = ref('overview')
const saving = ref(false)
const searching = ref(false)
const loadingReviews = ref(false)
const selectedFile = ref<File | null>(null)
const resourceMode = ref<'file' | 'link'>('file')
const resources = ref<LinkedResource[]>([])
const relations = ref<GraphLink[]>([])
const manualRecommendations = ref<KnowledgeNode[]>([])
const targetOptions = ref<KnowledgeNode[]>([])
const reviewRequests = ref<GraphChangeRequest[]>([])
const resourceEditVisible = ref(false)

const overview = reactive({ name: '', description: '' })
const resourceForm = reactive({ title: '', description: '', url: '' })
const resourceEdit = reactive({ id: 0, title: '', description: '' })
const relationForm = reactive({ target_id: '', rel_type: 'RELATED', label: '' })
const recommendationForm = reactive({ target_id: '', label: '' })
const taskForm = reactive<{ name: string; description: string; type: NodeTask['type']; due_date: string }>({
  name: '', description: '', type: 'learning', due_date: '',
})
const cognitive = reactive<Record<string, number>>({
  remember: 0, understand: 0, apply: 0, analyze: 0, evaluate: 0, create: 0,
})
const cognitiveDimensions = [
  { key: 'remember', label: '记忆' }, { key: 'understand', label: '理解' },
  { key: 'apply', label: '应用' }, { key: 'analyze', label: '分析' },
  { key: 'evaluate', label: '评价' }, { key: 'create', label: '创造' },
]

async function initialize(): Promise<void> {
  activeTab.value = props.initialTab || 'overview'
  overview.name = props.node.name || ''
  overview.description = props.node.description || ''
  let levels: Record<string, number> = {}
  if (typeof props.node.cognitive_level === 'string') {
    try { levels = JSON.parse(props.node.cognitive_level) } catch { levels = {} }
  } else if (props.node.cognitive_level) {
    levels = props.node.cognitive_level
  }
  cognitiveDimensions.forEach(({ key }) => { cognitive[key] = Number(levels[key] || 0) })
  await Promise.all([loadResources(), loadRelations(), loadRecommendations(), loadReviews()])
}

async function submit(changeType: Parameters<typeof graphApi.submitChange>[1], payload: Record<string, unknown>): Promise<void> {
  saving.value = true
  try {
    const result = await graphApi.submitChange(props.node.id, changeType, payload)
    ElMessage.success(result.status === 'pending' ? '已提交教师审核' : '修改已生效')
    if (result.status === 'pending') await loadReviews()
    else emit('changed')
  } finally {
    saving.value = false
  }
}

async function saveOverview(): Promise<void> {
  if (!overview.name.trim()) { ElMessage.warning('请输入知识点名称'); return }
  await submit('overview', { name: overview.name.trim(), description: overview.description })
}

function handleFileChange(file: UploadFile): void {
  selectedFile.value = file.raw || null
  if (!resourceForm.title) resourceForm.title = file.name
}

async function saveResource(): Promise<void> {
  if (!resourceForm.title.trim()) { ElMessage.warning('请输入资源标题'); return }
  saving.value = true
  try {
    const created = resourceMode.value === 'file'
      ? selectedFile.value
        ? await resourceApi.uploadFile(selectedFile.value, { title: resourceForm.title, description: resourceForm.description })
        : null
      : resourceForm.url.trim()
        ? await resourceApi.createLink({ ...resourceForm })
        : null
    if (!created) { ElMessage.warning(resourceMode.value === 'file' ? '请选择文件' : '请输入网页地址'); return }
    const result = await graphApi.submitChange(props.node.id, 'resource_link', { resource_id: created.id })
    ElMessage.success(result.status === 'pending' ? '资源关联已提交教师审核' : '资源已关联')
    resourceForm.title = ''; resourceForm.description = ''; resourceForm.url = ''; selectedFile.value = null
    if (result.status === 'pending') await loadReviews()
    else { await loadResources(); emit('changed') }
  } finally {
    saving.value = false
  }
}

async function loadResources(): Promise<void> {
  resources.value = (await graphApi.getNodeResources(props.node.id)) as LinkedResource[]
}

function startEditResource(row: LinkedResource): void {
  resourceEdit.id = Number(row.id); resourceEdit.title = row.title; resourceEdit.description = row.description || ''
  resourceEditVisible.value = true
}

async function saveResourceEdit(): Promise<void> {
  await submit('resource_update', { resource_id: resourceEdit.id, title: resourceEdit.title, description: resourceEdit.description })
  resourceEditVisible.value = false
  if (props.directApply) await loadResources()
}

async function unlinkResource(row: LinkedResource): Promise<void> {
  await ElMessageBox.confirm(`确定取消关联“${row.title}”吗？`, '确认操作', { type: 'warning' })
  await submit('resource_unlink', { resource_id: Number(row.id) })
  if (props.directApply) await loadResources()
}

async function searchTargets(query: string): Promise<void> {
  if (!query.trim()) return
  searching.value = true
  try { targetOptions.value = (await graphApi.searchNodes(query)).filter((item) => item.id !== props.node.id) }
  finally { searching.value = false }
}

async function saveRelationship(): Promise<void> {
  if (!relationForm.target_id) { ElMessage.warning('请选择目标知识点'); return }
  await submit('relationship', { ...relationForm })
  if (props.directApply) await loadRelations()
}

async function loadRelations(): Promise<void> {
  const data = await graphApi.getNeighbors(props.node.id, 1, 100)
  relations.value = data.links.filter(
    (link) => link.source === props.node.id && link.type !== 'RECOMMENDS',
  )
}

async function removeRelationship(row: GraphLink): Promise<void> {
  await ElMessageBox.confirm('确定删除这条知识关系吗？', '确认操作', { type: 'warning' })
  await submit('relationship_delete', { target_id: row.target, rel_type: row.type })
  if (props.directApply) await loadRelations()
}

async function saveCognitive(): Promise<void> {
  await submit('cognitive', { cognitive_level: { ...cognitive } })
}

async function saveRecommendation(): Promise<void> {
  if (!recommendationForm.target_id) { ElMessage.warning('请选择推荐知识点'); return }
  await submit('recommendation', { ...recommendationForm })
  if (props.directApply) await loadRecommendations()
}

async function loadRecommendations(): Promise<void> {
  const items = await graphApi.getRecommendations(props.node.id, 50)
  manualRecommendations.value = items.filter((item) => item._manual_recommendation === true)
}

async function removeRecommendation(row: KnowledgeNode): Promise<void> {
  await ElMessageBox.confirm('确定删除这条人工推荐吗？', '确认操作', { type: 'warning' })
  await submit('recommendation_delete', { target_id: row.id })
  if (props.directApply) await loadRecommendations()
}

async function saveTask(): Promise<void> {
  if (!taskForm.name.trim()) { ElMessage.warning('请输入任务名称'); return }
  saving.value = true
  try {
    await graphApi.createNodeTask(props.node.id, { ...taskForm, due_date: taskForm.due_date || undefined })
    ElMessage.success('任务已布置')
    taskForm.name = ''; taskForm.description = ''; taskForm.due_date = ''
    emit('changed')
  } finally { saving.value = false }
}

async function loadReviews(): Promise<void> {
  loadingReviews.value = true
  try { reviewRequests.value = await graphApi.getChangeRequests(props.node.id, 'pending') }
  finally { loadingReviews.value = false }
}

async function review(requestId: string, approved: boolean): Promise<void> {
  let comment = ''
  if (!approved) {
    const result = await ElMessageBox.prompt('请输入驳回原因', '驳回修改', { inputType: 'textarea' })
    comment = result.value
  }
  await graphApi.reviewChange(requestId, approved, comment)
  ElMessage.success(approved ? '审核通过，修改已生效' : '申请已驳回')
  await loadReviews()
  if (approved) {
    await Promise.all([loadResources(), loadRelations(), loadRecommendations()])
    emit('changed')
  }
}

function changeTypeLabel(type: string): string {
  return ({ overview: '概览', cognitive: '认知目标', relationship: '关联关系', relationship_delete: '删除关系', recommendation: '推荐', recommendation_delete: '删除推荐', resource_link: '关联资源', resource_update: '编辑资源', resource_unlink: '取消资源' } as Record<string, string>)[type] || type
}

function formatPayload(payload: Record<string, unknown>): string {
  return JSON.stringify(payload, null, 2)
}
</script>

<style scoped lang="scss">
.graph-edit {
  &__notice { margin-bottom: 16px; }
  &__mode { margin-bottom: 16px; }
  &__payload { margin: 0; white-space: pre-wrap; font-size: 12px; line-height: 1.4; }
}
</style>
