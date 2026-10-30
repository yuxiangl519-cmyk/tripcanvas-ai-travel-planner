<template>
  <div class="border-beam" aria-hidden="true"><div class="border-beam__light" /></div>
</template>

<!-- Vue adaptation of Magic UI Border Beam. See MAGIC_UI_LICENSE.md. -->
<style scoped>
.border-beam { position:absolute; inset:0; z-index:1; pointer-events:none; overflow:clip; border:1px solid transparent; border-radius:inherit; mask:linear-gradient(transparent, transparent), linear-gradient(#000, #000); mask-clip:padding-box, border-box; mask-composite:intersect; opacity:.65; transition:opacity .3s ease; }
.border-beam__light { position:absolute; width:150px; aspect-ratio:1; background:linear-gradient(to left, #8fb6a4, #d8bd83, transparent); offset-path:rect(0 auto auto 0 round 150px); animation:border-beam 12s linear infinite; }
@keyframes border-beam { to { offset-distance:100%; } }
@media (prefers-reduced-motion:reduce) { .border-beam { display:none; } }
</style>
