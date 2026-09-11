document.addEventListener('DOMContentLoaded',()=>{
const sections=[...document.querySelectorAll('.main-section[id]')];
const sidebar=document.querySelector('.sidebar-card'); const mobile=document.querySelector('.mobile-on-page details');
const makeLink=s=>{const a=document.createElement('a');a.href='#'+s.id;a.textContent=s.dataset.nav||s.querySelector('h2')?.textContent?.replace(/^Anna University\s*[:–-]?\s*/i,'').trim()||s.id;return a};
if(sidebar){sidebar.innerHTML='<div class="sidebar-title">Anna University</div>';sections.forEach(s=>sidebar.appendChild(makeLink(s)));}
if(mobile){mobile.innerHTML='<summary>On this page</summary>';sections.forEach(s=>mobile.appendChild(makeLink(s)));}
document.querySelectorAll('.accordion').forEach(d=>d.addEventListener('toggle',()=>{if(d.open)document.querySelectorAll('.accordion').forEach(x=>{if(x!==d)x.removeAttribute('open')})}));
document.querySelectorAll('.mobile-on-page a').forEach(a=>a.addEventListener('click',()=>mobile?.removeAttribute('open')));
const links=[...document.querySelectorAll('.sidebar a')]; const io=new IntersectionObserver(es=>es.forEach(e=>{if(e.isIntersecting)links.forEach(a=>a.classList.toggle('active',a.getAttribute('href')==='#'+e.target.id));}),{rootMargin:'-20% 0px -65% 0px'}); sections.forEach(s=>io.observe(s));
});