<template>
  <div class="backtest-page">
    <div class="page-header">
      <h2>交易回测</h2>
      <p>管理策略库，按自定义规则通过历史走势分析胜率</p>
    </div>

    <!-- ══════════════════════════════════════════════════════════
         策略库卡片
         ══════════════════════════════════════════════════════════ -->
    <el-card shadow="never" class="lib-card">
      <template #header>
        <div class="card-header-row">
          <span class="card-title">策略库</span>
          <el-tag v-if="strategies.length" size="small" type="info" style="margin-left:8px">
            {{ strategies.length }} 条
          </el-tag>
          <span style="flex:1" />
          <el-button type="primary" size="small" :icon="Plus" @click="openCreateDialog">
            新建策略
          </el-button>
        </div>
      </template>

      <el-table
        :data="strategies"
        v-loading="listLoading"
        size="small"
        :header-cell-style="{ background: '#f1f5f9', fontWeight: '600', color: '#475569', fontSize: '12px' }"
        empty-text="暂无已保存的策略，点击「新建策略」开始"
        :row-class-name="(scope) => scope.row.id === activeStratId ? 'active-strategy-row' : ''"
      >
        <!-- 策略名称 -->
        <el-table-column label="策略名称" min-width="140" align="left">
          <template #default="{ row }">
            <div class="strategy-name-cell">
              <span class="strategy-name">{{ row.name }}</span>
              <el-tag v-if="row.id === activeStratId" size="small" type="success" style="margin-left:6px">
                已加载
              </el-tag>
            </div>
          </template>
        </el-table-column>

        <!-- 标的 -->
        <el-table-column label="标的" width="120" align="left">
          <template #default="{ row }">
            <span class="fund-code">{{ row.target_code }}</span>
            <el-tag size="small" style="margin-left:5px">
              {{ row.target_type === 'index' ? '指数' : '基金' }}
            </el-tag>
          </template>
        </el-table-column>

        <!-- 回测区间 -->
        <el-table-column label="回测区间" min-width="160" align="left">
          <template #default="{ row }">
            <span class="date-range">{{ row.start_date }} ~ {{ row.end_date || '今日' }}</span>
          </template>
        </el-table-column>

        <!-- 规则数 -->
        <el-table-column label="规则" width="80" align="center">
          <template #default="{ row }">
            <span class="rule-count">{{ row.entry_rules.length }}入 {{ row.exit_rules.length }}出</span>
          </template>
        </el-table-column>

        <!-- 备注 -->
        <el-table-column
          prop="description"
          label="备注"
          min-width="120"
          align="left"
          show-overflow-tooltip
        >
          <template #default="{ row }">
            <span class="description-text">{{ row.description || '—' }}</span>
          </template>
        </el-table-column>

        <!-- 操作 -->
        <el-table-column label="操作" width="120" align="right" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" plain @click="loadToForm(row)">
              加载
            </el-button>
            <el-dropdown @command="(cmd) => onLibAction(cmd, row)" trigger="click">
              <el-button size="small" circle :icon="MoreFilled" style="margin-left:4px" />
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="edit">
                    <el-icon><Edit /></el-icon> 编辑
                  </el-dropdown-item>
                  <el-dropdown-item command="delete" class="danger-item">
                    <el-icon><Delete /></el-icon> 删除
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- ══════════════════════════════════════════════════════════
         回测工作台（左：配置 | 右：结果）
         ══════════════════════════════════════════════════════════ -->
    <el-row :gutter="20" class="workspace">

      <!-- ── 左：策略配置 ─────────────────────────────────── -->
      <el-col :span="24" :lg="12">
        <el-card shadow="never" class="config-card">
          <template #header>
            <div class="card-header-row">
              <span class="card-title">策略配置</span>
              <span v-if="activeStratId !== null" class="active-hint">
                <el-icon style="color:#22c55e"><CircleCheckFilled /></el-icon>
                已从策略库加载
              </span>
            </div>
          </template>

          <el-form label-width="88px" size="small" class="strategy-form">

            <el-form-item label="策略名称">
              <el-input v-model="name" placeholder="为策略命名" />
            </el-form-item>

            <el-form-item label="标的">
              <el-input v-model="targetCode" placeholder="基金/指数代码" style="width:130px" />
              <el-select v-model="targetType" style="width:76px;margin-left:6px">
                <el-option label="指数" value="index" />
                <el-option label="基金" value="fund" />
              </el-select>
              <el-button size="small" style="margin-left:6px" :icon="Promotion" @click="loadPresets">
                预设
              </el-button>
            </el-form-item>

            <el-form-item label="起始资金">
              <el-input-number v-model="capital" :min="10000" :step="50000" style="width:170px" />
            </el-form-item>

            <el-form-item label="每笔金额">
              <el-input-number v-model="positionSize" :min="1000" :step="10000" style="width:170px" />
            </el-form-item>

            <el-form-item label="回测区间">
              <el-date-picker
                v-model="dateRange"
                type="daterange"
                range-separator="至"
                start-placeholder="开始"
                end-placeholder="结束"
                value-format="YYYY-MM-DD"
                style="width:280px"
              />
            </el-form-item>

            <!-- 入场规则 -->
            <el-divider>
              <span style="font-size:13px;font-weight:600;color:#475569">入场条件</span>
            </el-divider>

            <div class="rule-list">
              <div v-for="(r, i) in entryRules" :key="'e' + i" class="rule-row">
                <el-select v-model="r.type" style="width:130px" @change="onEntryTypeChange(r)">
                  <el-option label="均线金叉/死叉"  value="ma_cross" />
                  <el-option label="价格跌破均线"   value="price_below_ma" />
                  <el-option label="RSI 低于阈值"  value="rsi_below" />
                </el-select>
                <template v-if="r.type === 'ma_cross'">
                  <el-select v-model="r.direction" style="width:64px;margin-left:6px">
                    <el-option label="金叉" value="golden" />
                    <el-option label="死叉" value="death" />
                  </el-select>
                  <el-input-number v-model="r.params.short" :min="3" :max="60" size="small" style="width:60px;margin-left:6px" />
                  <span class="rule-unit">日</span>
                  <el-input-number v-model="r.params.long" :min="5" :max="120" size="small" style="width:60px;margin-left:4px" />
                  <span class="rule-unit">日</span>
                </template>
                <template v-else-if="r.type === 'price_below_ma'">
                  <el-input-number v-model="r.params.ma" :min="5" :max="60" size="small" style="width:65px;margin-left:6px" />
                  <span class="rule-unit">日均线</span>
                </template>
                <template v-else-if="r.type === 'rsi_below'">
                  <span class="rule-label">低于</span>
                  <el-input-number v-model="r.params.threshold" :min="10" :max="50" size="small" style="width:60px;margin-left:4px" />
                </template>
                <el-button text type="danger" size="small" :icon="Delete" style="margin-left:6px" @click="entryRules.splice(i, 1)" />
              </div>
              <el-button size="small" :icon="Plus" @click="addEntryRule">添加入场条件</el-button>
            </div>

            <!-- 出场规则 -->
            <el-divider>
              <span style="font-size:13px;font-weight:600;color:#475569">出场条件</span>
            </el-divider>

            <div class="rule-list">
              <div v-for="(r, i) in exitRules" :key="'x' + i" class="rule-row">
                <el-select v-model="r.type" style="width:130px">
                  <el-option label="止盈"   value="take_profit" />
                  <el-option label="止损"   value="stop_loss" />
                  <el-option label="持仓天数" value="holding_days" />
                </el-select>
                <template v-if="r.type === 'take_profit' || r.type === 'stop_loss'">
                  <el-input-number
                    v-model="r.value"
                    :min="r.type === 'stop_loss' ? -50 : 1"
                    :max="r.type === 'stop_loss' ? -1 : 100"
                    size="small"
                    style="width:74px;margin-left:6px"
                  />
                  <span class="rule-unit">%</span>
                </template>
                <template v-else-if="r.type === 'holding_days'">
                  <el-input-number v-model="r.value" :min="5" :max="365" size="small" style="width:74px;margin-left:6px" />
                  <span class="rule-unit">天</span>
                </template>
                <el-button text type="danger" size="small" :icon="Delete" style="margin-left:6px" @click="exitRules.splice(i, 1)" />
              </div>
              <el-button size="small" :icon="Plus" @click="exitRules.push({ type: 'take_profit', value: 10 })">
                添加出场条件
              </el-button>
            </div>

            <!-- 执行 + 保存 -->
            <el-divider />

            <el-button
              type="primary"
              :loading="running"
              style="width:100%;margin-bottom:10px"
              @click="runBacktest"
            >
              <el-icon><VideoPlay /></el-icon>
              运行回测
            </el-button>

            <div class="save-action-row">
              <el-button :loading="saving" :icon="DocumentAdd" @click="saveAsNew" style="flex:1">
                另存为新策略
              </el-button>
              <el-button
                v-if="activeStratId !== null"
                type="warning"
                :loading="saving"
                :icon="RefreshRight"
                @click="updateCurrent"
                style="flex:1"
              >
                更新已加载策略
              </el-button>
            </div>
          </el-form>
        </el-card>
      </el-col>

      <!-- ── 右：回测结果 ─────────────────────────────────── -->
      <el-col :span="24" :lg="12">
        <el-card shadow="never" class="result-card">
          <template #header>
            <div class="card-header-row">
              <span class="card-title">回测结果</span>
              <span v-if="result" class="card-badge" style="margin-left:auto">
                {{ result.strategy_name }}
              </span>
            </div>
          </template>

          <div v-if="!result" class="result-empty">
            <el-icon :size="48" color="#cbd5e1"><TrendCharts /></el-icon>
            <p>配置左侧策略后，点击「运行回测」</p>
          </div>

          <template v-else>
            <div class="result-kpi-grid">
              <KpiCard
                label="总收益率"
                :value="result.total_return_pct + '%'"
                :value-color="result.total_return_pct >= 0 ? '#CF1E1E' : '#2A7D3F'"
                icon="TrendCharts"
                :icon-bg="result.total_return_pct >= 0 ? 'linear-gradient(135deg,#fee2e2,#fca5a5)' : 'linear-gradient(135deg,#dcfce7,#86efac)'"
                :icon-color="result.total_return_pct >= 0 ? '#CF1E1E' : '#2A7D3F'"
              />
              <KpiCard
                label="胜率"
                :value="result.win_rate + '%'"
                icon="DataBoard"
                icon-bg="linear-gradient(135deg,#dcfce7,#86efac)"
                icon-color="#2A7D3F"
              />
              <KpiCard
                label="夏普比率"
                :value="result.sharpe_ratio"
                icon="Coin"
                icon-bg="linear-gradient(135deg,#ede9fe,#c4b5fd)"
                icon-color="#7D44A5"
              />
              <KpiCard
                label="年化收益"
                :value="result.annualized_return + '%'"
                icon="TrendCharts"
                icon-bg="linear-gradient(135deg,#dbeafe,#93c5fd)"
                icon-color="#1A5FB4"
              />
              <KpiCard
                label="最大回撤"
                :value="result.max_drawdown + '%'"
                icon="WarnTriangleFilled"
                icon-bg="linear-gradient(135deg,#fee2e2,#fca5a5)"
                icon-color="#CF1E1E"
              />
              <KpiCard
                label="交易次数"
                :value="result.total_trades + ' 笔'"
                icon="Folder"
                icon-bg="linear-gradient(135deg,#fef3c7,#fcd34d)"
                icon-color="#C75000"
              />
            </div>

            <template v-if="result.total_trades > 0">
              <el-card shadow="never" class="chart-inner-card">
                <template #header><span class="card-title" style="font-size:13px">净值曲线</span></template>
                <div class="chart-container">
                  <v-chart :option="equityOption" autoresize />
                </div>
              </el-card>

              <el-card shadow="never" class="chart-inner-card">
                <template #header>
                  <div class="card-header-row">
                    <span class="card-title" style="font-size:13px">交易明细</span>
                    <span class="card-badge" style="margin-left:8px">{{ result.trades.length }} 笔</span>
                  </div>
                </template>
                <el-table
                  :data="result.trades"
                  size="small"
                  max-height="260"
                  :header-cell-style="{ background: '#f1f5f9', fontWeight: '600', color: '#475569', fontSize: '12px' }"
                >
                  <el-table-column prop="entry_date"  label="买入日" width="90" align="left" />
                  <el-table-column prop="entry_price" label="买入价" width="72" align="right">
                    <template #default="{ row }"><span class="num-cell">{{ row.entry_price }}</span></template>
                  </el-table-column>
                  <el-table-column prop="exit_date"   label="卖出日" width="90" align="left" />
                  <el-table-column prop="exit_price"  label="卖出价" width="72" align="right">
                    <template #default="{ row }"><span class="num-cell">{{ row.exit_price }}</span></template>
                  </el-table-column>
                  <el-table-column label="收益率" width="80" align="right">
                    <template #default="{ row }">
                      <span class="return-badge" :class="row.return_pct >= 0 ? 'positive' : 'negative'">
                        {{ row.return_pct >= 0 ? '↑' : '↓' }}{{ Math.abs(row.return_pct) }}%
                      </span>
                    </template>
                  </el-table-column>
                  <el-table-column prop="exit_reason" label="原因" align="left" />
                </el-table>
              </el-card>
            </template>
          </template>
        </el-card>
      </el-col>
    </el-row>

    <!-- ══════════════════════════════════════════════════════════
         新建 / 编辑策略对话框
         ══════════════════════════════════════════════════════════ -->
    <el-dialog
      v-model="dlgVisible"
      :title="dlgMode === 'create' ? '新建策略' : '编辑策略'"
      width="640px"
      :close-on-click-modal="false"
    >
      <el-form :model="dlgData" label-width="88px" size="small" class="strategy-form">
        <el-form-item label="策略名称" required>
          <el-input v-model="dlgData.name" placeholder="为策略命名" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input
            v-model="dlgData.description"
            type="textarea"
            :rows="2"
            placeholder="可选，填写策略适用场景或说明"
          />
        </el-form-item>
        <el-form-item label="标的" required>
          <el-input v-model="dlgData.target_code" placeholder="代码" style="width:110px" />
          <el-select v-model="dlgData.target_type" style="width:76px;margin-left:6px">
            <el-option label="指数" value="index" />
            <el-option label="基金" value="fund" />
          </el-select>
          <el-input v-model="dlgData.target_name" placeholder="名称（可选）" style="width:130px;margin-left:6px" />
        </el-form-item>
        <el-form-item label="起始资金">
          <el-input-number v-model="dlgData.initial_capital" :min="10000" :step="50000" style="width:160px" />
        </el-form-item>
        <el-form-item label="每笔金额">
          <el-input-number v-model="dlgData.position_size" :min="1000" :step="10000" style="width:160px" />
        </el-form-item>
        <el-form-item label="回测区间">
          <el-date-picker
            v-model="dlgDateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始"
            end-placeholder="结束"
            value-format="YYYY-MM-DD"
            style="width:280px"
          />
        </el-form-item>

        <el-divider>
          <span style="font-size:12px;font-weight:600;color:#475569">入场条件</span>
        </el-divider>
        <div class="rule-list">
          <div v-for="(r, i) in dlgData.entry_rules" :key="'de' + i" class="rule-row">
            <el-select v-model="r.type" style="width:130px" @change="onEntryTypeChange(r)">
              <el-option label="均线金叉/死叉" value="ma_cross" />
              <el-option label="价格跌破均线" value="price_below_ma" />
              <el-option label="RSI 低于阈值" value="rsi_below" />
            </el-select>
            <template v-if="r.type === 'ma_cross'">
              <el-select v-model="r.direction" style="width:64px;margin-left:6px">
                <el-option label="金叉" value="golden" />
                <el-option label="死叉" value="death" />
              </el-select>
              <el-input-number v-model="r.params.short" :min="3" :max="60" size="small" style="width:60px;margin-left:6px" />
              <span class="rule-unit">日</span>
              <el-input-number v-model="r.params.long" :min="5" :max="120" size="small" style="width:60px;margin-left:4px" />
              <span class="rule-unit">日</span>
            </template>
            <template v-else-if="r.type === 'price_below_ma'">
              <el-input-number v-model="r.params.ma" :min="5" :max="60" size="small" style="width:65px;margin-left:6px" />
              <span class="rule-unit">日均线</span>
            </template>
            <template v-else-if="r.type === 'rsi_below'">
              <span class="rule-label">低于</span>
              <el-input-number v-model="r.params.threshold" :min="10" :max="50" size="small" style="width:60px;margin-left:4px" />
            </template>
            <el-button text type="danger" size="small" :icon="Delete" style="margin-left:6px" @click="dlgData.entry_rules.splice(i,1)" />
          </div>
          <el-button size="small" :icon="Plus" @click="dlgAddEntryRule">添加入场条件</el-button>
        </div>

        <el-divider>
          <span style="font-size:12px;font-weight:600;color:#475569">出场条件</span>
        </el-divider>
        <div class="rule-list">
          <div v-for="(r, i) in dlgData.exit_rules" :key="'dx' + i" class="rule-row">
            <el-select v-model="r.type" style="width:130px">
              <el-option label="止盈"   value="take_profit" />
              <el-option label="止损"   value="stop_loss" />
              <el-option label="持仓天数" value="holding_days" />
            </el-select>
            <template v-if="r.type === 'take_profit' || r.type === 'stop_loss'">
              <el-input-number
                v-model="r.value"
                :min="r.type === 'stop_loss' ? -50 : 1"
                :max="r.type === 'stop_loss' ? -1 : 100"
                size="small"
                style="width:74px;margin-left:6px"
              />
              <span class="rule-unit">%</span>
            </template>
            <template v-else-if="r.type === 'holding_days'">
              <el-input-number v-model="r.value" :min="5" :max="365" size="small" style="width:74px;margin-left:6px" />
              <span class="rule-unit">天</span>
            </template>
            <el-button text type="danger" size="small" :icon="Delete" style="margin-left:6px" @click="dlgData.exit_rules.splice(i,1)" />
          </div>
          <el-button size="small" :icon="Plus" @click="dlgData.exit_rules.push({type:'take_profit',value:10})">
            添加出场条件
          </el-button>
        </div>
      </el-form>

      <template #footer>
        <el-button @click="dlgVisible = false">取消</el-button>
        <el-button type="primary" :loading="dlgSaving" @click="saveDlg">
          {{ dlgMode === 'create' ? '创建策略' : '保存修改' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
/**
 * Backtest.vue — 交易回测 + 策略库管理
 *
 * 三区布局：
 *   1. 策略库卡片 — 列出所有已保存策略，支持加载 / 编辑 / 删除
 *   2. 策略配置表单 — 配置并运行回测，支持保存 / 更新策略
 *   3. 回测结果 — KPI 指标 + 净值曲线 + 交易明细
 */
import { ref, computed, reactive, onMounted } from 'vue'
import VChart from 'vue-echarts'
import 'echarts'
import {
  TrendCharts, Plus, Delete, Edit, MoreFilled,
  DocumentAdd, RefreshRight, VideoPlay, Promotion,
  CircleCheckFilled,
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import KpiCard from '@/components/KpiCard.vue'
import { backtestApi, strategyApi } from '@/api'

// ── 策略库状态 ─────────────────────────────────────────────
const strategies    = ref([])
const listLoading   = ref(false)
/** 当前已从策略库加载到表单的策略 ID；null 表示未加载 */
const activeStratId = ref(null)

// ── 回测表单状态 ───────────────────────────────────────────
const name         = ref('均线策略')
const targetCode   = ref('000300')
const targetType   = ref('index')
const capital      = ref(100000)
const positionSize = ref(10000)
const dateRange    = ref(['2020-01-01', ''])
const entryRules   = ref([
  { type: 'ma_cross', direction: 'golden', params: { short: 5, long: 20 } },
])
const exitRules    = ref([
  { type: 'take_profit', value: 10  },
  { type: 'stop_loss',   value: -5  },
])
const running      = ref(false)
const saving       = ref(false)
const result       = ref(null)

// ── 对话框状态 ─────────────────────────────────────────────
const dlgVisible = ref(false)
const dlgMode    = ref('create')   // 'create' | 'edit'
const dlgSaving  = ref(false)
const dlgData    = reactive({
  id:              null,
  name:            '',
  description:     '',
  target_code:     '000300',
  target_name:     '',
  target_type:     'index',
  initial_capital: 100000,
  position_size:   10000,
  start_date:      '2020-01-01',
  end_date:        '',
  entry_rules:     [],
  exit_rules:      [],
})

/** 对话框日期区间（双向绑定两个字符串字段）*/
const dlgDateRange = computed({
  get: () => [dlgData.start_date, dlgData.end_date || ''],
  set: (val) => {
    dlgData.start_date = val?.[0] || '2020-01-01'
    dlgData.end_date   = val?.[1] || ''
  },
})

// ── 工具函数 ───────────────────────────────────────────────

/** 根据当前主表单值构建策略 Payload */
function buildFormPayload() {
  return {
    name:            name.value,
    description:     '',
    target_code:     targetCode.value,
    target_name:     targetCode.value,
    target_type:     targetType.value,
    initial_capital: capital.value,
    position_size:   positionSize.value,
    start_date:      dateRange.value?.[0] || '2020-01-01',
    end_date:        dateRange.value?.[1] || '',
    entry_rules:     entryRules.value,
    exit_rules:      exitRules.value,
  }
}

/** 入场规则类型变化时，初始化对应的 params 字段 */
function onEntryTypeChange(r) {
  if (!r.params) r.params = {}
  if (r.type === 'ma_cross'       && !r.params.short)     { r.params.short = 5; r.params.long = 20 }
  if (r.type === 'price_below_ma' && !r.params.ma)        { r.params.ma = 20 }
  if (r.type === 'rsi_below'      && !r.params.threshold) { r.params.threshold = 30 }
}

/** 主表单：添加入场规则 */
function addEntryRule() {
  entryRules.value.push({ type: 'ma_cross', direction: 'golden', params: { short: 5, long: 20 } })
}

/** 对话框：添加入场规则 */
function dlgAddEntryRule() {
  dlgData.entry_rules.push({ type: 'ma_cross', direction: 'golden', params: { short: 5, long: 20 } })
}

// ── 策略库操作 ─────────────────────────────────────────────

/** 从后端加载策略列表 */
async function loadStrategies() {
  listLoading.value = true
  try {
    const res = await strategyApi.list()
    strategies.value = res.data || []
  } catch (e) {
    console.error('[Backtest] 策略列表加载失败:', e)
  } finally {
    listLoading.value = false
  }
}

/**
 * 将策略参数填充到主表单（用于运行回测）
 * 同时记录 activeStratId，供「更新已加载策略」使用
 */
function loadToForm(strategy) {
  name.value          = strategy.name
  targetCode.value    = strategy.target_code
  targetType.value    = strategy.target_type
  capital.value       = strategy.initial_capital
  positionSize.value  = strategy.position_size
  dateRange.value     = [strategy.start_date, strategy.end_date || '']
  entryRules.value    = JSON.parse(JSON.stringify(strategy.entry_rules))
  exitRules.value     = JSON.parse(JSON.stringify(strategy.exit_rules))
  activeStratId.value = strategy.id
  result.value        = null
  ElMessage.success(`已加载「${strategy.name}」，可微调后运行回测`)
}

/** 策略库行操作派发 */
function onLibAction(cmd, strategy) {
  if (cmd === 'edit')   openEditDialog(strategy)
  if (cmd === 'delete') deleteStrategy(strategy)
}

/** 打开新建策略对话框（空表单）*/
function openCreateDialog() {
  dlgMode.value = 'create'
  Object.assign(dlgData, {
    id: null, name: '', description: '',
    target_code: '000300', target_name: '', target_type: 'index',
    initial_capital: 100000, position_size: 10000,
    start_date: '2020-01-01', end_date: '',
    entry_rules: [{ type: 'ma_cross', direction: 'golden', params: { short: 5, long: 20 } }],
    exit_rules:  [{ type: 'take_profit', value: 10 }, { type: 'stop_loss', value: -5 }],
  })
  dlgVisible.value = true
}

/** 打开编辑策略对话框（预填数据）*/
function openEditDialog(strategy) {
  dlgMode.value = 'edit'
  Object.assign(dlgData, {
    id:              strategy.id,
    name:            strategy.name,
    description:     strategy.description || '',
    target_code:     strategy.target_code,
    target_name:     strategy.target_name || '',
    target_type:     strategy.target_type,
    initial_capital: strategy.initial_capital,
    position_size:   strategy.position_size,
    start_date:      strategy.start_date,
    end_date:        strategy.end_date || '',
    entry_rules:     JSON.parse(JSON.stringify(strategy.entry_rules)),
    exit_rules:      JSON.parse(JSON.stringify(strategy.exit_rules)),
  })
  dlgVisible.value = true
}

/** 对话框确认保存（新建 or 更新）*/
async function saveDlg() {
  if (!dlgData.name.trim()) { ElMessage.warning('策略名称不能为空'); return }
  dlgSaving.value = true
  const payload = {
    name:            dlgData.name.trim(),
    description:     dlgData.description,
    target_code:     dlgData.target_code,
    target_name:     dlgData.target_name,
    target_type:     dlgData.target_type,
    initial_capital: dlgData.initial_capital,
    position_size:   dlgData.position_size,
    start_date:      dlgData.start_date,
    end_date:        dlgData.end_date,
    entry_rules:     dlgData.entry_rules,
    exit_rules:      dlgData.exit_rules,
  }
  try {
    if (dlgMode.value === 'create') {
      await strategyApi.create(payload)
      ElMessage.success('策略已创建')
    } else {
      await strategyApi.update(dlgData.id, payload)
      ElMessage.success('策略已更新')
    }
    dlgVisible.value = false
    await loadStrategies()
  } catch {
    ElMessage.error('保存失败，请重试')
  } finally {
    dlgSaving.value = false
  }
}

/** 删除策略（带确认框）*/
async function deleteStrategy(strategy) {
  try {
    await ElMessageBox.confirm(
      `确定要删除策略「${strategy.name}」吗？此操作不可撤销。`,
      '删除确认',
      { type: 'warning', confirmButtonText: '确认删除', cancelButtonText: '取消' },
    )
    await strategyApi.delete(strategy.id)
    if (activeStratId.value === strategy.id) activeStratId.value = null
    ElMessage.success('策略已删除')
    await loadStrategies()
  } catch {
    // 用户取消，不做任何操作
  }
}

// ── 主表单保存操作 ─────────────────────────────────────────

/** 将当前表单内容另存为新策略 */
async function saveAsNew() {
  if (!name.value.trim()) { ElMessage.warning('请先填写策略名称'); return }
  saving.value = true
  try {
    const res = await strategyApi.create(buildFormPayload())
    activeStratId.value = res.data?.id ?? null
    ElMessage.success(`策略「${name.value}」已保存到策略库`)
    await loadStrategies()
  } catch {
    ElMessage.error('保存失败，请重试')
  } finally {
    saving.value = false
  }
}

/** 将当前表单内容更新到已加载的策略 */
async function updateCurrent() {
  if (activeStratId.value === null) return
  saving.value = true
  try {
    await strategyApi.update(activeStratId.value, buildFormPayload())
    ElMessage.success('策略已更新')
    await loadStrategies()
  } catch {
    ElMessage.error('更新失败，请重试')
  } finally {
    saving.value = false
  }
}

// ── 回测操作 ───────────────────────────────────────────────

/** 加载后端内置预设策略到主表单 */
async function loadPresets() {
  try {
    const res = await backtestApi.presets()
    const p   = res.data?.[0]
    if (!p) return
    name.value         = p.name
    targetCode.value   = p.target_code
    targetType.value   = p.target_type
    capital.value      = p.initial_capital
    positionSize.value = p.position_size
    entryRules.value   = p.entry_rules
    exitRules.value    = p.exit_rules
    dateRange.value    = [p.start_date, p.end_date || '']
    activeStratId.value = null
  } catch {
    ElMessage.warning('预设加载失败')
  }
}

/** 运行回测 */
async function runBacktest() {
  running.value = true
  result.value  = null
  try {
    const res = await backtestApi.run({
      name:            name.value,
      target_code:     targetCode.value,
      target_name:     targetCode.value,
      target_type:     targetType.value,
      initial_capital: capital.value,
      position_size:   positionSize.value,
      entry_rules:     entryRules.value,
      exit_rules:      exitRules.value,
      start_date:      dateRange.value?.[0] || '2020-01-01',
      end_date:        dateRange.value?.[1] || '',
    })
    result.value = res.data
    if (res.data?.total_trades === 0) {
      ElMessage.warning('回测完成，未产生任何交易记录，请检查规则配置')
    }
  } catch {
    ElMessage.error('回测失败，请检查标的代码及网络连接')
  } finally {
    running.value = false
  }
}

// ── 净值曲线 ECharts 配置 ──────────────────────────────────
const equityOption = computed(() => {
  const curve = result.value?.equity_curve || []
  return {
    tooltip: {
      trigger: 'axis',
      valueFormatter: (v) => '¥' + Number(v).toLocaleString(),
      borderColor: 'transparent',
      backgroundColor: 'rgba(255,255,255,0.97)',
      extraCssText: 'box-shadow:0 4px 16px rgba(15,23,42,.12);border-radius:8px;padding:10px 14px',
    },
    grid: { left: '2%', right: '3%', bottom: '8%', containLabel: true },
    xAxis: {
      type: 'category',
      data: curve.map((e) => e.date),
      axisLabel: { fontSize: 10, rotate: 20, color: '#94a3b8' },
      axisLine:  { lineStyle: { color: '#e2e8f0' } },
    },
    yAxis: {
      type: 'value',
      axisLabel: { formatter: '¥{value}', color: '#94a3b8', fontSize: 10 },
      splitLine:  { lineStyle: { color: '#f1f5f9', type: 'dashed' } },
    },
    series: [
      {
        type: 'line',
        data: curve.map((e) => e.value),
        smooth: true,
        showSymbol: false,
        lineStyle: { width: 2, color: '#1A5FB4' },
        areaStyle: {
          color: {
            type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(26,95,180,0.25)' },
              { offset: 1, color: 'rgba(26,95,180,0.02)' },
            ],
          },
        },
      },
    ],
    dataZoom: [{ type: 'inside', start: 0, end: 100 }],
  }
})

// ── 生命周期 ────────────────────────────────────────────────
onMounted(() => {
  loadStrategies()
})
</script>

<style scoped>
/* ── 页面 ─────────────────────────────────────────────────── */
.backtest-page { max-width: 1400px; }

/* ── 策略库卡片 ───────────────────────────────────────────── */
.lib-card { margin-bottom: 20px; }
.lib-card :deep(.el-card__body) { padding: 0; }

/* 已加载策略行高亮 */
.lib-card :deep(.active-strategy-row td.el-table__cell) {
  background: #eff6ff !important;
}

/* 策略名称 */
.strategy-name-cell { display: flex; align-items: center; }
.strategy-name { font-weight: 600; color: var(--text-primary); font-size: 13px; }

/* 单元格字体 */
.fund-code {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--color-primary);
  font-weight: 600;
}
.date-range {
  font-size: 12px;
  color: var(--text-secondary);
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
}
.rule-count { font-size: 12px; color: var(--text-muted); }
.description-text { font-size: 12px; color: var(--text-muted); }

/* 危险操作菜单项 */
:global(.danger-item) { color: #CF1E1E !important; }
:global(.danger-item:hover) { background: #fff1f0 !important; }

/* ── 工作台 ───────────────────────────────────────────────── */
.workspace { align-items: flex-start; }
.config-card, .result-card { height: 100%; }

/* ── 卡片标题 ─────────────────────────────────────────────── */
.card-header-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.card-title { font-size: 15px; font-weight: 700; color: var(--text-primary); }
.card-badge {
  font-size: 12px;
  color: var(--text-muted);
  background: var(--bg-table-header);
  padding: 2px 8px;
  border-radius: 10px;
}
.active-hint {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #16a34a;
  font-weight: 500;
  margin-left: auto;
}

/* ── 策略表单 ─────────────────────────────────────────────── */
.strategy-form :deep(.el-form-item) { margin-bottom: 14px; }

/* 规则列表 */
.rule-list { display: flex; flex-direction: column; gap: 8px; padding: 4px 0; }
.rule-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
  background: #f8fafc;
  border: 1px solid #e9eef5;
  border-radius: 8px;
  padding: 8px 10px;
}
.rule-unit  { font-size: 12px; color: var(--text-muted); white-space: nowrap; }
.rule-label { font-size: 12px; color: var(--text-secondary); white-space: nowrap; }

/* 保存按钮行 */
.save-action-row { display: flex; gap: 8px; margin-top: 8px; }

/* ── 结果区 ───────────────────────────────────────────────── */
.result-empty {
  text-align: center;
  padding: 80px 20px;
  color: var(--text-muted);
}
.result-empty p { margin-top: 12px; font-size: 14px; }

/* KPI 网格 */
.result-kpi-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin-bottom: 16px;
}

/* 内嵌子卡片 */
.chart-inner-card { margin-top: 14px; }
.chart-inner-card :deep(.el-card__header) { padding: 10px 16px; }
.chart-inner-card :deep(.el-card__body)   { padding: 12px 16px; }
.chart-container { height: 220px; }

/* 数字等宽 */
.num-cell {
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
  font-size: 12px;
}

/* 收益率胶囊（中国市场：红涨绿跌）*/
.return-badge {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  padding: 2px 7px;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 700;
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
}
.return-badge.positive { background: rgba(207,30,30,.09); color: #CF1E1E; }
.return-badge.negative { background: rgba(42,125,63,.09); color: #2A7D3F; }

/* ── 响应式 ───────────────────────────────────────────────── */
@media (max-width: 768px) {
  .result-kpi-grid { grid-template-columns: repeat(2, 1fr); }
  .save-action-row { flex-direction: column; }
}
</style>
