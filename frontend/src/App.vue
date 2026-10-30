<template>
  <div class="app-shell">
    <header class="site-header">
      <router-link to="/" class="brand" aria-label="旅途手记，返回首页">
        <span class="brand-mark" aria-hidden="true"><svg viewBox="0 0 32 32" fill="none"><path d="M16 4v24M4 16h24M7.5 7.5l17 17m0-17-17 17" stroke="currentColor" stroke-width="1.3"/><circle cx="16" cy="16" r="3" fill="currentColor"/></svg></span>
        <strong>旅途手记</strong>
      </router-link>
      <span class="header-note">计划下一段旅程</span>
    </header>
    <main><router-view /></main>
    <footer class="site-footer"><span>旅途手记</span><span>行程与费用仅供参考，请在出发前核实。</span></footer>
  </div>
</template>

<style>
:root { --ink:#182b2b; --ink-soft:#425957; --muted:#586c69; --primary:#214f4a; --primary-hover:#163e39; --accent:#376e63; --paper:#f1f4f0; --surface:#fff; --line:#dce3dd; --soft:#edf2ee; --focus:#235b97; font-family:"Microsoft YaHei","PingFang SC",sans-serif; color:var(--ink); background:var(--paper); font-synthesis:none; }
* { box-sizing:border-box; } body { margin:0; min-width:320px; } button,input,textarea { font:inherit; } .app-shell .ant-btn, .app-shell .ant-input, .app-shell .ant-picker, .app-shell .ant-select, .app-shell .ant-input-number, .app-shell .ant-checkbox-wrapper, .app-shell .ant-form, .app-shell .ant-menu { font-family:inherit; }
.site-header { height:72px; display:flex; align-items:center; justify-content:space-between; width:min(1440px,100%); padding:0 48px; margin:auto; color:var(--ink); }
.brand { display:flex; align-items:center; gap:12px; color:var(--ink); text-decoration:none; font-size:19px; letter-spacing:.04em; }.brand:hover { color:var(--primary); }.brand-mark { width:34px; height:34px; display:grid; place-items:center; color:var(--primary); }.brand-mark svg { width:32px; height:32px; }
.header-note { color:var(--muted); font-size:14px; }.site-footer { display:flex; justify-content:space-between; gap:16px; width:min(1440px,100%); margin:auto; padding:28px 48px; color:var(--muted); font-size:13px; }
button:focus-visible,a:focus-visible,input:focus-visible,textarea:focus-visible { outline:3px solid var(--focus) !important; outline-offset:3px; }
@media (min-width:901px) { .site-header { height:58px; padding:0 32px; }.site-footer { padding:10px 32px; min-height:40px; } }
@media (min-width:901px) and (max-height:800px) { .site-header { height:52px; } }
@media (max-width:760px) { .site-header { height:64px; padding:0 20px; }.site-footer { padding:24px 20px; flex-wrap:wrap; }.header-note { font-size:13px; } }
@media (prefers-reduced-motion:reduce) { *,*::before,*::after { animation-duration:.01ms !important; scroll-behavior:auto !important; transition-duration:.01ms !important; } }
</style>
