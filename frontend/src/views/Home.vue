<template>
  <div class="home-container">
    <div class="home-layout">
      <aside class="intro" aria-label="旅行灵感与最近行程">
        <div class="travel-art" role="img" aria-label="山水之间的小路，晨光中的旅行风景">
          <div class="art-caption"><span>你的旅程</span><strong>从想去的地方，<br />开始。</strong></div>
        </div>
        <p class="intro-footnote">氛围图由 AI 生成，不代表实际景点。</p>
        <div v-if="recentTrips.length" class="recent-trips">
          <div class="recent-heading"><strong>最近的旅程</strong><span>保存在此浏览器</span></div>
          <button v-for="trip in recentTrips.slice(0, showAllTrips ? undefined : 3)" :key="trip.id" type="button" @click="openTrip(trip)">
            <span><b>{{ trip.plan.city }}</b><small>{{ trip.plan.start_date }} — {{ trip.plan.end_date }}</small></span><span aria-hidden="true">↗</span>
          </button>
          <button v-if="recentTrips.length > 3" type="button" class="show-history" @click="showAllTrips = !showAllTrips">{{ showAllTrips ? '收起行程' : '查看全部行程' }}</button>
        </div>
      </aside>

      <section class="planner-card" aria-labelledby="form-title">
        <BorderBeam />
        <div class="card-heading"><h1 id="form-title">下一次，去哪里？</h1><p>填写出行信息，生成专属行程。</p></div>
        <a-form :model="formData" layout="vertical" @finish="handleSubmit" @finishFailed="handleInvalid">
          <div v-if="formErrors.length" ref="errorSummary" class="error-summary" role="alert" tabindex="-1">
            <strong>请先检查以下内容</strong>
            <ul><li v-for="error in formErrors" :key="error.field"><a :href="`#form_item_${error.field}`">{{ error.message }}</a></li></ul>
          </div>
          <div class="form-section">
            <div class="section-heading"><h2>目的地与日期</h2></div>
            <div class="destination-grid">
              <a-form-item name="city" label="目的地城市" :rules="[{ required: true, whitespace: true, message: '请输入目的地城市' }]">
                <a-input v-model:value="formData.city" size="large" placeholder="例如：北京" />
              </a-form-item>
              <a-form-item name="start_date" label="出发日期" :rules="[{ required: true, message: '请选择出发日期' }]">
                <a-date-picker v-model:value="formData.start_date" size="large" style="width: 100%" placeholder="选择日期" />
              </a-form-item>
              <a-form-item name="end_date" label="返程日期" :rules="[{ required: true, message: '请选择返程日期' }]">
                <a-date-picker v-model:value="formData.end_date" size="large" style="width: 100%" placeholder="选择日期" />
              </a-form-item>
            </div>
            <div class="duration-note">旅程长度 <strong>{{ formData.travel_days }}</strong> 天 <span>· 包含出发与返程日</span></div>
          </div>
          <div class="form-section">
            <div class="section-heading"><h2>旅行偏好</h2></div>
            <div class="two-grid">
              <a-form-item name="transportation" label="交通方式"><a-select v-model:value="formData.transportation" size="large"><a-select-option value="公共交通">公共交通</a-select-option><a-select-option value="自驾">自驾</a-select-option><a-select-option value="步行">步行</a-select-option><a-select-option value="混合">混合出行</a-select-option></a-select></a-form-item>
              <a-form-item name="accommodation" label="住宿偏好"><a-select v-model:value="formData.accommodation" size="large"><a-select-option value="经济型酒店">经济型酒店</a-select-option><a-select-option value="舒适型酒店">舒适型酒店</a-select-option><a-select-option value="豪华酒店">豪华酒店</a-select-option><a-select-option value="民宿">民宿</a-select-option></a-select></a-form-item>
            </div>
            <a-form-item name="preferences" label="感兴趣的体验"><a-checkbox-group v-model:value="formData.preferences" class="preference-tags"><a-checkbox value="历史文化">历史文化</a-checkbox><a-checkbox value="自然风光">自然风光</a-checkbox><a-checkbox value="美食">美食</a-checkbox><a-checkbox value="购物">购物</a-checkbox><a-checkbox value="艺术">艺术</a-checkbox><a-checkbox value="休闲">休闲</a-checkbox></a-checkbox-group></a-form-item>
            <div class="three-grid">
              <a-form-item name="traveler_count" label="同行人数" :rules="[{ required: true, message: '请填写同行人数' }]"><a-input-number v-model:value="formData.traveler_count" :min="1" :max="20" :precision="0" size="large" style="width: 100%" /></a-form-item>
              <a-form-item name="budget_limit" label="全程预算（元）"><a-input-number v-model:value="formData.budget_limit" :min="1" :precision="0" size="large" placeholder="可不填" style="width: 100%" /></a-form-item>
              <a-form-item name="daily_hours" label="每日活动（小时）" :rules="[{ required: true, message: '请填写每日活动时长' }]"><a-input-number v-model:value="formData.daily_hours" :min="4" :max="16" :precision="0" size="large" style="width: 100%" /></a-form-item>
            </div>
          </div>
          <div class="form-section final-section">
            <div class="section-heading"><h2>补充要求 <span>选填</span></h2></div>
            <a-form-item name="free_text_input"><a-textarea v-model:value="formData.free_text_input" aria-label="补充要求" :rows="2" size="large" placeholder="例如：带老人出行，希望每天不要太赶……" /></a-form-item>
          </div>
          <a-button type="primary" html-type="submit" :loading="loading" size="large" block class="submit-button"><span v-if="!loading">生成旅行计划</span><span v-else>正在生成行程</span></a-button>
          <div v-if="loading" class="loading-container" role="status" aria-live="polite"><a-spin size="small" /> <span>{{ loadingStatus }}</span></div>
          <p class="form-footnote">基于地图信息与 AI 规划 · 费用为估算，请出行前核实</p>
        </a-form>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch, nextTick } from 'vue'
import BorderBeam from '@/components/magic/BorderBeam.vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { generateTripPlan } from '@/services/api'
import type { TripFormData } from '@/types'
import type { Dayjs } from 'dayjs'
import { readHistory, saveTrip, type SavedTrip } from '@/services/history'

const router = useRouter()
const recentTrips = ref(readHistory())
const showAllTrips = ref(false)

const openTrip = (trip: SavedTrip) => {
  sessionStorage.setItem('tripPlan', JSON.stringify(trip.plan))
  sessionStorage.setItem('tripPlanId', trip.id)
  router.push('/result')
}
const formErrors = ref<{ field: string; message: string }[]>([])
const errorSummary = ref<HTMLElement | null>(null)
const handleInvalid = async ({ errorFields }: { errorFields: { name: (string | number)[]; errors: string[] }[] }) => {
  formErrors.value = errorFields.map(item => ({ field: String(item.name[0]), message: item.errors[0] }))
  await nextTick()
  errorSummary.value?.focus()
}
const loading = ref(false)
const loadingStatus = ref('')

type TripFormState = Omit<TripFormData, 'start_date' | 'end_date'> & {
  start_date: Dayjs | null
  end_date: Dayjs | null
}

const formData = reactive<TripFormState>({
  city: '',
  start_date: null,
  end_date: null,
  travel_days: 1,
  transportation: '公共交通',
  accommodation: '经济型酒店',
  preferences: [],
  free_text_input: '',
  traveler_count: 1,
  budget_limit: null,
  daily_hours: 8
})

// 监听日期变化,自动计算旅行天数
watch([() => formData.start_date, () => formData.end_date], ([start, end]) => {
  if (start && end) {
    const days = end.diff(start, 'day') + 1
    if (days > 0 && days <= 30) {
      formData.travel_days = days
    } else if (days > 30) {
      message.warning('旅行天数不能超过30天')
      formData.end_date = null
    } else {
      message.warning('结束日期不能早于开始日期')
      formData.end_date = null
    }
  }
})

const handleSubmit = async () => {
  formErrors.value = []
  if (!formData.start_date || !formData.end_date) {
    message.error('请选择日期')
    return
  }

  loading.value = true
  loadingStatus.value = '正在查询旅行信息并生成行程，请稍候...'

  try {
    const requestData: TripFormData = {
      city: formData.city,
      start_date: formData.start_date.format('YYYY-MM-DD'),
      end_date: formData.end_date.format('YYYY-MM-DD'),
      travel_days: formData.travel_days,
      transportation: formData.transportation,
      accommodation: formData.accommodation,
      preferences: formData.preferences,
      free_text_input: formData.free_text_input,
      traveler_count: formData.traveler_count,
      budget_limit: formData.budget_limit,
      daily_hours: formData.daily_hours
    }

    const response = await generateTripPlan(requestData)

    loadingStatus.value = '行程已生成'

    if (response.success && response.data) {
      // 保存到sessionStorage
      saveTrip(response.data)

      message.success('旅行计划生成成功!')

      // 短暂延迟后跳转
      setTimeout(() => {
        router.push('/result')
      }, 500)
    } else {
      message.error(response.message || '生成失败')
    }
  } catch (error: any) {
    message.error(error.message || '生成旅行计划失败,请稍后重试')
  } finally {
    setTimeout(() => {
      loading.value = false
      loadingStatus.value = ''
    }, 1000)
  }
}
</script>

<style scoped>
.home-container { padding:0 48px 24px; background:var(--paper); }.home-layout { max-width:1344px; margin:auto; display:grid; grid-template-columns:minmax(0,1.15fr) minmax(0,.85fr); gap:24px; align-items:stretch; }
.planner-card { position:relative; grid-column:1; grid-row:1; padding:40px 48px 44px; border:1px solid var(--line); border-radius:16px; background:var(--surface); }.card-heading { padding-bottom:8px; }.card-heading h1 { margin:0 0 14px; color:var(--ink); font-size:32px; font-weight:700; letter-spacing:-.035em; }.card-heading p { margin:0; color:var(--ink-soft); font-size:16px; line-height:1.6; }
.intro { grid-column:2; grid-row:1; display:flex; flex-direction:column; min-width:0; }.travel-art { position:relative; flex:1; min-height:440px; overflow:hidden; border-radius:16px; background:url('../assets/journey-hero.webp') center/cover, #55776b; }.art-caption { position:absolute; left:24px; bottom:24px; padding:16px 20px; border-radius:8px; background:rgba(18,43,38,.82); color:white; }.art-caption span { display:block; margin-bottom:14px; font-size:15px; }.art-caption strong { font-family:"Songti SC","STSong","SimSun",serif; font-size:clamp(32px,3vw,42px); font-weight:600; line-height:1.35; }.intro-footnote { margin:12px 0 0; color:var(--muted); font-size:12px; line-height:1.5; }
.recent-trips { margin-top:28px; padding:24px; border:1px solid var(--line); border-radius:12px; background:var(--surface); }.recent-heading { display:flex; justify-content:space-between; align-items:baseline; gap:12px; margin-bottom:10px; color:var(--ink); font-size:17px; }.recent-heading span { color:var(--muted); font-size:13px; }.recent-trips button { width:100%; display:flex; align-items:center; justify-content:space-between; padding:14px 0; border:0; border-top:1px solid var(--line); background:transparent; color:var(--ink); text-align:left; cursor:pointer; }.recent-trips button { transition:color .2s ease, padding .2s ease; }.recent-trips button:hover { color:var(--primary); padding-left:6px; padding-right:6px; }.recent-trips b,.recent-trips small { display:block; }.recent-trips b { font-size:15px; }.recent-trips small { margin-top:4px; color:var(--muted); font-size:13px; }.recent-trips .show-history { justify-content:center; color:var(--primary); font-size:14px; }
.error-summary { margin:24px 0 0; padding:16px 18px; border:1px solid #e0b0a0; border-radius:8px; background:#fff7f3; color:#8d3d27; font-size:14px; }.error-summary ul { margin:8px 0 0; padding-left:20px; }.error-summary a { color:#8d3d27; text-decoration:underline; }
.form-section { padding:26px 0 6px; border-top:1px solid var(--line); margin-top:24px; }.section-heading { margin-bottom:20px; }.section-heading h2 { margin:0; color:var(--ink); font-size:19px; font-weight:700; }.section-heading h2 span { margin-left:8px; color:var(--muted); font-size:14px; font-weight:400; }
.destination-grid { display:grid; grid-template-columns:1.05fr 1fr 1fr; gap:16px; }.two-grid { display:grid; grid-template-columns:1fr 1fr; gap:16px; }.three-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:16px; }
:deep(.ant-form-item) { margin-bottom:20px; }:deep(.ant-form-item-label > label) { color:var(--ink); font-size:14px; font-weight:600; }:deep(.ant-input),:deep(.ant-input-affix-wrapper),:deep(.ant-picker),:deep(.ant-select-selector),:deep(.ant-input-number) { border-color:#cbd8cf !important; border-radius:6px !important; background:#fff !important; box-shadow:none !important; }:deep(.ant-input:hover),:deep(.ant-picker:hover),:deep(.ant-input-number:hover),:deep(.ant-select-selector:hover) { border-color:#72978b !important; }:deep(.ant-input:focus),:deep(.ant-picker-focused),:deep(.ant-select-focused .ant-select-selector),:deep(.ant-input-number-focused) { border-color:var(--primary) !important; box-shadow:0 0 0 3px #dcece4 !important; }
.duration-note { padding:12px 16px; margin-bottom:8px; border-radius:6px; color:var(--ink-soft); background:var(--soft); font-size:14px; }.duration-note strong { color:var(--primary); font-size:16px; padding:0 4px; }.duration-note span { color:var(--muted); }
.preference-tags { display:flex; flex-wrap:wrap; gap:10px; }.preference-tags :deep(.ant-checkbox-wrapper) { min-height:40px; margin:0; padding:9px 12px; border:1px solid #d7e1d8; border-radius:6px; color:var(--ink-soft); font-size:14px; background:#fff; cursor:pointer; }.preference-tags :deep(.ant-checkbox-wrapper-checked) { border-color:#699688; background:#edf4ef; color:var(--primary); }.preference-tags :deep(.ant-checkbox-checked .ant-checkbox-inner) { background:var(--primary); border-color:var(--primary); }
.final-section { padding-bottom:0; }.submit-button { height:54px; border:0; border-radius:6px; background:var(--primary); font-size:16px; font-weight:700; box-shadow:none !important; }.submit-button { transition:background .2s ease, transform .2s ease !important; }.submit-button:hover { background:var(--primary-hover) !important; transform:translateY(-2px); }.submit-button:active { transform:translateY(0); }.loading-container { display:flex; gap:10px; justify-content:center; align-items:center; margin-top:15px; color:var(--ink-soft); font-size:14px; }.form-footnote { margin:16px 0 0; color:var(--muted); font-size:13px; line-height:1.6; }
/* Magic UI Blur Fade, adapted as a restrained entrance for the two main panels. */
.planner-card,.intro { animation:panel-reveal .6s cubic-bezier(.22,1,.36,1) both; }
.intro { animation-delay:.1s; }
@keyframes panel-reveal { from { opacity:0; filter:blur(4px); transform:translateY(10px); } to { opacity:1; filter:blur(0); transform:translateY(0); } }
@media (prefers-reduced-motion:reduce) { .planner-card,.intro { animation:none; }.submit-button:hover { transform:none; } }

/* A compact desktop workspace keeps the primary task within the first screen. */
@media (min-width:901px) {
  .home-container { padding:0 32px 8px; }
  .home-layout { max-width:1376px; min-height:calc(100svh - 106px); grid-template-columns:minmax(0,1.45fr) minmax(300px,.75fr); gap:16px; }
  .planner-card { padding:20px 28px 18px; }
  .card-heading { padding:0; }
  .card-heading h1 { margin:0 0 4px; font-size:26px; line-height:1.25; }
  .card-heading p { font-size:14px; line-height:1.4; }
  .form-section { margin-top:12px; padding:12px 0 0; }
  .section-heading { margin-bottom:8px; }
  .section-heading h2 { font-size:16px; }
  .destination-grid,.two-grid,.three-grid { gap:12px; }
  :deep(.ant-form-item) { margin-bottom:8px; }
  :deep(.ant-form-item-label) { padding:0 0 3px !important; }
  :deep(.ant-form-item-label > label) { height:auto; font-size:14px; }
  .duration-note { padding:6px 12px; margin-bottom:0; }
  .preference-tags { gap:6px; }
  .preference-tags :deep(.ant-checkbox-wrapper) { min-height:34px; padding:5px 10px; }
  .final-section :deep(textarea.ant-input) { min-height:48px; height:48px; }
  .submit-button { height:44px; }
  .form-footnote { margin-top:7px; }
  .travel-art { min-height:0; }
  .intro-footnote { margin-top:6px; }
  .recent-trips { margin-top:10px; padding:12px 18px; }
  .recent-heading { margin-bottom:4px; }
  .recent-trips button { padding:8px 0; }
  .recent-trips button:hover { padding:8px 6px; }
}

@media (min-width:901px) and (max-width:1100px) { .home-layout { grid-template-columns:minmax(0,1fr) 260px; }.art-caption strong { font-size:24px; } }
@media (min-width:901px) and (max-height:800px) { .planner-card { padding-top:16px; padding-bottom:14px; }.form-section { margin-top:7px; padding-top:7px; }.section-heading { margin-bottom:5px; }:deep(.ant-form-item) { margin-bottom:5px; }.home-layout { min-height:calc(100svh - 100px); } }
@media(max-width:1000px) { .home-container { padding:0 24px 24px; }.planner-card { padding:20px 24px 18px; }.travel-art { min-height:0; }.art-caption strong { font-size:30px; } }
@media(max-width:900px) { .home-container { padding:0 16px 24px; }.home-layout { display:flex; flex-direction:column; gap:16px; }.planner-card { order:1; width:100%; padding:28px 22px 30px; }.intro { order:2; width:100%; }.travel-art { flex:none; min-height:235px; }.art-caption { left:20px; bottom:20px; }.art-caption strong { font-size:28px; }.recent-trips { padding:20px; }.card-heading h1 { font-size:32px; } }
@media(max-width:560px) { .destination-grid { grid-template-columns:1fr 1fr; }.destination-grid> :first-child { grid-column:1/-1; }.three-grid { grid-template-columns:1fr 1fr; }.three-grid> :last-child { grid-column:1/-1; } }
@media(max-width:360px) { .two-grid,.three-grid { grid-template-columns:1fr; }.three-grid> :last-child { grid-column:auto; }.card-heading h1 { font-size:29px; } }
</style>
